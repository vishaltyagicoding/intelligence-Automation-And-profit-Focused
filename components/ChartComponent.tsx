'use client';

import { useEffect, useRef, useState } from 'react';
import {
  ColorType,
  CrosshairMode,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type SeriesMarker,
  type Time,
} from 'lightweight-charts';

export type WatchlistAsset = 'BTCUSD' | 'ETHUSD' | 'XAUUSD' | 'LTCUSD';
export type Timeframe = '5m' | '15m' | '30m' | '1h' | '2h' | '4h' | '1d';

export interface AISignal {
  asset: WatchlistAsset;
  timestamp: number;
  price: number;
  action: 'BUY' | 'SELL' | 'HOLD' | 'STOP LOSS' | 'STOP_LOSS';
  message: string;
  color: string;
}

interface ReversalZone {
  bar_index: number;
  center_price: number;
  outer_top: number;
  outer_bottom: number;
  core_top: number;
  core_bottom: number;
  is_bullish: boolean;
  label: string;
  timestamp: string;
}

interface CandleDataPoint {
  time: Time;
  open: number;
  high: number;
  low: number;
  close: number;
}

// Exact payload shape sent by MarketDataConsumer
interface KlinePayload {
  timestamp?: number;
  time?: number;
  open?: number | string;
  high?: number | string;
  low?: number | string;
  close?: number | string;
  price?: number | string;
  type?: string;
  is_closed?: boolean;
}

interface ChartComponentProps {
  asset: WatchlistAsset;
  aiSignals: AISignal[];
  subscriptionActive: boolean;
  wsBaseUrl: string;
  timeframe: Timeframe;
  onTimeframeChange: (timeframe: Timeframe) => void;
  showFullDashboardButton?: boolean;
}


// Live signal payload from backend _emit_live_signal
interface SignalPayload {
  type: 'signal';
  asset: string;
  timeframe: string;
  signal: 'BUY' | 'SELL';
  is_bullish: boolean;
  price: number;
  timestamp: string;
  bar_index: number;
  tracking: string;
  all_zones: Array<{
    is_bullish: boolean;
    center_price: number;
    timestamp: string;
    bar_index: number;
  }>;
}

// ── helpers ──────────────────────────────────────────────────────────────────
function toUnix(v?: number): number {
  if (typeof v !== 'number' || !Number.isFinite(v)) return Math.floor(Date.now() / 1000);
  return v > 9_999_999_999 ? Math.floor(v / 1000) : v;
}
function toFloat(v: number | string | undefined, fallback = 0): number {
  const n = typeof v === 'string' ? parseFloat(v) : (v ?? NaN);
  return Number.isFinite(n) ? n : fallback;
}

// ── constants ─────────────────────────────────────────────────────────────────
const TIMEFRAMES: Timeframe[] = ['5m','15m','30m','1h','2h','4h','1d'];

const TF_BINANCE: Record<Timeframe, string> = {
  '5m':'5m','15m':'15m','30m':'30m','1h':'1h','2h':'2h','4h':'4h','1d':'1d',
};

const TF_SEC: Record<Timeframe, number> = {
  '5m':300,'15m':900,'30m':1800,'1h':3600,'2h':7200,'4h':14400,'1d':86400,
};

// TradingView exact colors
const COLOR_UP   = '#26a69a';   // teal  (bullish candle)
const COLOR_DOWN = '#ef5350';   // red   (bearish candle)

// ─────────────────────────────────────────────────────────────────────────────
export default function ChartComponent({
  asset,
  subscriptionActive,
  wsBaseUrl,
  timeframe,
  onTimeframeChange,
  showFullDashboardButton = false,
}: ChartComponentProps) {
  const containerRef  = useRef<HTMLDivElement | null>(null);
  const chartRef      = useRef<IChartApi | null>(null);
  const seriesRef     = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const roRef         = useRef<ResizeObserver | null>(null);

  // Per-timeframe marker cache — key: "asset:timeframe", value: marker Map
  // This survives timeframe switches so switching back restores labels instantly
  const markerCacheRef = useRef<Map<string, Map<number, SeriesMarker<Time>>>>(new Map());

  // Active marker store for the currently selected timeframe
  const markersRef = useRef<Map<number, SeriesMarker<Time>>>(new Map());

  // Oldest candle timestamp — signals before this are out-of-window and filtered
  const chartStartTimeRef = useRef<number>(0);

  const [lastPrice,    setLastPrice]    = useState<number | null>(null);
  const [connected,    setConnected]    = useState<boolean | null>(null);
  const [signalStatus, setSignalStatus] = useState<{last_signal:string; tracking:string}|null>(null);
  const [sigLoading,   setSigLoading]   = useState(false);

  // ── Create chart (once) ────────────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: '#020617' },
        textColor: '#cbd5e1',
      },
      grid: {
        vertLines: { color: 'rgba(148,163,184,0.07)' },
        horzLines: { color: 'rgba(148,163,184,0.07)' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: '#758BFD', width: 1, style: 2 },
        horzLine: { color: '#758BFD', width: 1, style: 2 },
      },
      rightPriceScale: {
        borderColor: 'rgba(148,163,184,0.2)',
        textColor: '#cbd5e1',
        scaleMargins: { top: 0.08, bottom: 0.08 },
      },
      localization: {
        // Force UTC display — prevents IST (UTC+5:30) or any local timezone
        // from shifting the chart's time axis. All candles show UTC time.
        timeFormatter: (time: number) => {
          const d = new Date(time * 1000);
          const pad = (n: number) => String(n).padStart(2, '0');
          return `${d.getUTCFullYear()}-${pad(d.getUTCMonth()+1)}-${pad(d.getUTCDate())} ` +
                 `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
        },
      },
      timeScale: {
        borderColor: 'rgba(148,163,184,0.2)',
        timeVisible: true,
        secondsVisible: false,
        fixLeftEdge: true,
        fixRightEdge: true,
        lockVisibleTimeRangeOnResize: true,
      },
      handleScroll: { mouseWheel:true, pressedMouseMove:true, horzTouchDrag:true, vertTouchDrag:true },
      handleScale:  { axisPressedMouseMove:true, mouseWheel:true, pinch:true },
      kineticScroll: { mouse:false, touch:true },
      watermark: { visible:false },
    });

    // Per-asset price precision — matches TradingView display
    const ASSET_PRICE_FMT: Record<string, {precision: number; minMove: number}> = {
      'BTCUSD':  { precision: 2, minMove: 0.01 },   // $80,396.00
      'ETHUSD':  { precision: 2, minMove: 0.01 },   // $2,316.30
      'XAUUSD':  { precision: 2, minMove: 0.01 },   // $4,733.63
      'LTCUSD':  { precision: 2, minMove: 0.01 },   // $58.01
    };
    const priceFmt = ASSET_PRICE_FMT[asset] ?? { precision: 2, minMove: 0.01 };

    const series = chart.addCandlestickSeries({
      upColor:          COLOR_UP,
      downColor:        COLOR_DOWN,
      wickUpColor:      COLOR_UP,
      wickDownColor:    COLOR_DOWN,
      borderVisible:    true,
      borderUpColor:    COLOR_UP,
      borderDownColor:  COLOR_DOWN,
      priceLineVisible: true,
      priceLineColor:   COLOR_UP,
      priceLineWidth:   1,
      priceFormat: { type: 'price', ...priceFmt },
    });

    chartRef.current  = chart;
    seriesRef.current = series;

    roRef.current = new ResizeObserver(() => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width:  containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    });
    roRef.current.observe(containerRef.current);

    return () => {
      roRef.current?.disconnect();
      chart.remove();
      chartRef.current  = null;
      seriesRef.current = null;
    };
  }, []);

  // ── Load data + WebSocket per asset/timeframe ─────────────────────────────
  useEffect(() => {
    setLastPrice(null);
    setSignalStatus(null);
    setSigLoading(true); // Show loading immediately to hide label repositioning
    chartStartTimeRef.current = 0; // Reset until new candles load

    // On asset/timeframe switch: always start with a clean marker slate.
    // This prevents labels from jumping between candles when switching assets.
    const cacheKey = `${asset}:${timeframe}`;
    // Create fresh map for this key — never show stale markers from previous load
    markerCacheRef.current.set(cacheKey, new Map());
    markersRef.current = markerCacheRef.current.get(cacheKey)!;

    // Clear chart data and markers immediately
    seriesRef.current?.setData([]);
    seriesRef.current?.setMarkers([]);

    // candle map: candleStartTime(seconds) → CandleDataPoint
    const candles: Map<number, CandleDataPoint> = new Map();

    // ── Flush persistent marker store to chart (sorted + deduped) ────────────
    const flushMarkers = (minTime: number = chartStartTimeRef.current) => {
      if (!seriesRef.current) return;
      const all = [...markersRef.current.values()];
      // Always filter: only show signals within the visible chart window
      const inWindow = minTime > 0
        ? all.filter(m => (m.time as number) >= minTime)
        : all;
      const sorted = inWindow.sort((a, b) => (a.time as number) - (b.time as number));
      try { seriesRef.current.setMarkers(sorted); } catch { /* ignore */ }
    };

    // Messages that arrive BEFORE historical load finishes are buffered here
    // so we never miss a candle
    const preloadBuffer: KlinePayload[] = [];
    let historyLoaded = false;

    const gone = { current: false };
    let socket: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    // ── Apply a single kline payload to the candle map + chart ────────────
    const applyKline = (p: KlinePayload) => {
      const ts    = toUnix(p.timestamp ?? p.time);
      const open  = toFloat(p.open);
      const high  = toFloat(p.high);
      const low   = toFloat(p.low);
      const close = toFloat(p.close ?? p.price);
      if (!close) return;

      const interval = TF_SEC[timeframe];
      // Backend already sends candle-start timestamp, but snap anyway to be safe
      const start = Math.floor(ts / interval) * interval;

      const hasOHLC = open > 0 && high > 0 && low > 0;

      if (hasOHLC) {
        // Real Binance kline OHLCV — exact match
        candles.set(start, { time: start as Time, open, high, low, close });
      } else {
        // Tick fallback (should not happen with our backend)
        const existing = candles.get(start);
        if (!existing) {
          const prev = close;
          candles.set(start, { time: start as Time, open: prev, high: close, low: close, close });
        } else {
          existing.high  = Math.max(existing.high, close);
          existing.low   = Math.min(existing.low,  close);
          existing.close = close;
        }
      }

      setLastPrice(close);
      const candle = candles.get(start)!;
      try { seriesRef.current?.update(candle); } catch { /* ignore */ }
    };

    // ── WebSocket — open IMMEDIATELY so we never miss a live candle ───────
    const connect = () => {
      if (gone.current) return;
      socket = new WebSocket(`${wsBaseUrl}/ws/market/${asset}/${timeframe}/`);

      socket.onerror = (error) => {
        console.error('Chart WebSocket error:', error);
        setConnected(false);
      };
      
      socket.onopen  = () => setConnected(true);
      
      socket.onclose = () => {
        setConnected(false);
        if (!gone.current) retryTimer = setTimeout(connect, 3000);
      };


    // ── Apply a live signal broadcast from backend ────────────────────────────
    // Backend now broadcasts only the single latest new signal in all_zones.
    // We use zoneToMarker (UTC-safe) and mergeAndFlush (1h gap + alternation).
    const applySignal = (s: SignalPayload) => {
      if (!seriesRef.current) return;
      const interval = TF_SEC[timeframe];

      // Convert all_zones to markers using UTC-safe zoneToMarker
      const newMarkers: SeriesMarker<Time>[] = s.all_zones.map(
        (z) => zoneToMarker(z, interval)
      );

      // Only merge if within the chart window — prevents out-of-window signals
      const chartStart = chartStartTimeRef.current;
      const inWindow = chartStart > 0
        ? newMarkers.filter(m => (m.time as number) >= chartStart)
        : newMarkers;

      if (inWindow.length > 0) {
        mergeAndFlush(inWindow);
        setSignalStatus({ last_signal: s.signal, tracking: s.tracking });
      }
    };

      socket.onmessage = (ev: MessageEvent<string>) => {
        try {
          const raw = JSON.parse(ev.data) as Record<string, unknown>;
          const msgType = raw.type as string | undefined;
          const p = raw as unknown as KlinePayload;
          if (msgType === 'ping') { socket?.send(JSON.stringify({ action:'pong' })); return; }

          // Live signal from backend _emit_live_signal — apply markers immediately
          if (msgType === 'signal') {
            if (historyLoaded) applySignal(raw as unknown as SignalPayload);
            return;
          }

          if (!historyLoaded) {
            // Queue the message — will be replayed after history is set
            preloadBuffer.push(p as KlinePayload);
          } else {
            applyKline(p as KlinePayload);
          }
        } catch { /* ignore */ }
      };
    };

    // Start WebSocket right away — before we even fetch history
    connect();

    // ── Fetch BUY/SELL reversal signals ───────────────────────────────────
    // ── Helper: convert a zone object → SeriesMarker ────────────────────────
    const zoneToMarker = (z: { is_bullish: boolean; timestamp: string }, interval: number): SeriesMarker<Time> => {
      // Force UTC interpretation — append Z if no timezone info present.
      // Without this, browsers in IST (UTC+5:30) shift timestamps 5.5h earlier,
      // placing signals on wrong candles.
      const ts = z.timestamp.includes('+') || z.timestamp.endsWith('Z')
        ? z.timestamp
        : z.timestamp + 'Z';
      const rawTs   = Math.floor(new Date(ts).getTime() / 1000);
      const snapped = Math.floor(rawTs / interval) * interval;
      return {
        time:     snapped as Time,
        position: z.is_bullish ? 'belowBar' : 'aboveBar',
        color:    z.is_bullish ? COLOR_UP    : COLOR_DOWN,
        shape:    z.is_bullish ? 'arrowUp'   : 'arrowDown',
        text:     z.is_bullish ? 'BUY SIGNAL': 'SELL SIGNAL',
        size:     2,
      };
    };

    // ── Merge an array of markers into markersRef and flush ───────────────────
    // Enforces BOTH 1-hour minimum gap AND strict BUY→SELL→BUY alternation.
    const SIXTY_MIN_S = 60 * 60; // 3600 seconds

    const mergeAndFlush = (newMarkers: SeriesMarker<Time>[]) => {
      const sorted = [...newMarkers].sort((a, b) => (a.time as number) - (b.time as number));

      for (const m of sorted) {
        const newTime = m.time as number;

        // Skip exact duplicate timestamp
        if (markersRef.current.has(newTime)) continue;

        // Get the last accepted marker by time
        const existingTimes = [...markersRef.current.keys()].sort((a, b) => a - b);
        const lastTime   = existingTimes.length > 0 ? existingTimes[existingTimes.length - 1] : undefined;
        const lastMarker = lastTime !== undefined ? markersRef.current.get(lastTime) : undefined;

        if (lastMarker !== undefined && lastTime !== undefined) {
          const gapSeconds = newTime - lastTime;

          // ── Gap < 1 hour: handle without adding new entry ──────────────
          if (gapSeconds < SIXTY_MIN_S) {
            // Only replace if same type AND newer (keeps most recent)
            if (lastMarker.text === m.text && newTime > lastTime) {
              markersRef.current.delete(lastTime);
              markersRef.current.set(newTime, m);
            }
            continue; // Never add a new entry within 1 hour of last
          }

          // ── Gap >= 1 hour but same type: replace last ──────────────────
          if (lastMarker.text === m.text) {
            if (newTime > lastTime) {
              markersRef.current.delete(lastTime);
              markersRef.current.set(newTime, m);
            }
            continue;
          }
        }

        // Gap >= 1 hour AND different type (or first signal) — accept
        // Only add if within chart window
        if (chartStartTimeRef.current === 0 || newTime >= chartStartTimeRef.current) {
          markersRef.current.set(newTime, m);
        }
      }

      flushMarkers();
    };

    const fetchSignals = async (chartStartTime: number = 0) => {
      if (!seriesRef.current || gone.current) return;
      setSigLoading(true);
      const interval = TF_SEC[timeframe];

      // Always start with a clean slate — clears both active store and cache
      markersRef.current.clear();
      const cacheKey = `${asset}:${timeframe}`;
      markerCacheRef.current.delete(cacheKey);

      try {
        // ── Collect ALL signals from BOTH sources into one array ──────────────
        // Then do a SINGLE sorted alternation-enforcing pass.
        // This is the correct approach — two separate mergeAndFlush calls
        // with overlapping data caused the consecutive BUY/SELL bug.
        const allRawSignals: Array<{is_bullish: boolean; timestamp: string}> = [];

        // Source 1: DB history (permanently stored, 30-day window)
        try {
          const dbRes = await fetch(`/api/trading/signal-history/${asset}/?timeframe=${timeframe}`);
          if (dbRes.ok && !gone.current) {
            const dbJson = await dbRes.json();
            if (dbJson.success && dbJson.signals?.length > 0) {
              for (const z of dbJson.signals as Array<{is_bullish: boolean; timestamp: string}>) {
                allRawSignals.push(z);
              }
            }
          }
        } catch { /* DB history optional */ }

        if (gone.current) return;

        // Source 2: Live calculator signals (current 1000-candle window)
        let liveStatus: {last_signal: string; tracking: string} | null = null;
        try {
          const liveRes = await fetch(`/api/trading/reversal-zones/${asset}/?timeframe=${timeframe}`);
          if (liveRes.ok && !gone.current) {
            const liveJson = await liveRes.json();
            if (liveJson.success && liveJson.data?.zones?.length > 0) {
              for (const z of liveJson.data.zones as Array<{is_bullish: boolean; timestamp: string}>) {
                allRawSignals.push(z);
              }
              liveStatus = liveJson.data.status ?? null;
            }
          }
        } catch { /* live signals optional */ }

        if (gone.current) return;

        // ── Convert ALL signals to markers and sort by time ───────────────────
        const allMarkers = allRawSignals
          .map(z => zoneToMarker(z, interval))
          .sort((a, b) => (a.time as number) - (b.time as number));

        // ── Single pass: enforce BOTH 1-hour gap AND alternation ─────────────
        // Rules (applied in order to each candidate signal):
        //   1. Skip exact duplicate timestamp
        //   2. Must be >= 1 hour after the last ACCEPTED signal
        //   3. Must be different type (BUY vs SELL) from the last ACCEPTED signal
        //      If same type AND newer → replace last (keep most recent of same type)
        const SIXTY_MIN = 60 * 60; // 3600 seconds — 1 hour minimum gap
        const finalMarkers: SeriesMarker<Time>[] = [];
        const seenTimes = new Set<number>();

        for (const m of allMarkers) {
          const t = m.time as number;

          // Rule 1: Skip exact duplicate timestamps
          if (seenTimes.has(t)) continue;

          const last = finalMarkers.length > 0 ? finalMarkers[finalMarkers.length - 1] : undefined;
          const lastTime = last !== undefined ? (last.time as number) : undefined;

          // Rule 2: Must be at least 60 minutes after last accepted signal
          if (lastTime !== undefined) {
            const gapSeconds = t - lastTime; // positive = newer
            if (gapSeconds < SIXTY_MIN) {
              // Too close: if same type keep newer (replace), if different type skip
              if (last !== undefined && last.text === m.text && t > lastTime) {
                // Replace last with this more recent same-type signal
                finalMarkers[finalMarkers.length - 1] = m;
                seenTimes.delete(lastTime);
                seenTimes.add(t);
              }
              // Either way, do not add as a new entry — gap is too small
              continue;
            }
          }

          // Rule 3: Must alternate (BUY→SELL→BUY)
          if (last !== undefined && last.text === m.text) {
            // Same type but >= 1 hour apart — keep the MORE RECENT one
            finalMarkers[finalMarkers.length - 1] = m;
            seenTimes.delete(last.time as number);
            seenTimes.add(t);
            continue;
          }

          // Passed all checks — accept this signal
          finalMarkers.push(m);
          seenTimes.add(t);
        }

        // ── Filter out signals BEFORE the chart's oldest visible candle ────────
        // This prevents out-of-window signals clustering on the first candle.
        // chartStartTime is passed directly from loadHistory — no ref timing issue.
        const inWindowMarkers = chartStartTime > 0
          ? finalMarkers.filter(m => (m.time as number) >= chartStartTime)
          : finalMarkers;

        // ── Apply to chart — single setMarkers call, no race conditions ───────
        for (const m of inWindowMarkers) {
          markersRef.current.set(m.time as number, m);
        }
        flushMarkers(chartStartTime);

        if (!gone.current && liveStatus) {
          setSignalStatus(liveStatus);
        }

      } catch { /* silent */ }
      finally { if (!gone.current) setSigLoading(false); }
    };

    // ── Fetch Binance REST historical OHLCV ───────────────────────────────
    const loadHistory = async () => {
      try {
        // PAXG special case: XAUUSD uses paxgusdt on Binance (gold-backed token)
        // Asset → Binance.US symbol mapping
        const ASSET_TO_BINANCE: Record<string, string> = {
          'XAUUSD': 'PAXGUSDT',   // Paxos Gold on Binance.US
          'BTCUSD': 'BTCUSDT',
          'ETHUSD': 'ETHUSDT',
          'LTCUSD': 'LTCUSDT',
        };
        const sym = ASSET_TO_BINANCE[asset] ?? asset.replace('USD', 'USDT');
        // Candle limits sized to cover the DB signal history window per timeframe
        // Prevents out-of-window signals from clustering on the first candle
        const TF_LIMIT: Record<Timeframe, number> = {
          '5m':  1000,  // ~3.5d
          '15m': 1000,  // ~10d
          '30m': 1000,  // ~21d
          '1h':  750,   // ~31d ✅
          '2h':  375,   // ~31d ✅
          '4h':  200,   // ~33d ✅
          '1d':  180,   // 180d (6 months) ✅
        };
        const limit = TF_LIMIT[timeframe] ?? 1000;
        const res   = await fetch(
          `https://api.binance.us/api/v3/klines?symbol=${sym}&interval=${TF_BINANCE[timeframe]}&limit=${limit}`
        );
        const raw = await res.json();
        if (gone.current) return;

        // Parse into candle array
        let hist: CandleDataPoint[] = raw.map((k: (string|number)[]) => ({
          time:  Math.floor(Number(k[0]) / 1000) as Time,
          open:  parseFloat(k[1] as string),
          high:  parseFloat(k[2] as string),
          low:   parseFloat(k[3] as string),
          close: parseFloat(k[4] as string),
        }));

        // Populate candle map
        for (const c of hist) candles.set(c.time as number, c);

        // Render history on chart
        seriesRef.current?.setData(hist);
        chartRef.current?.timeScale().fitContent();

        if (hist.length > 0) {
          setLastPrice(hist[hist.length - 1].close);
          // Record oldest candle time — signals before this are OUT OF WINDOW
          // and must be filtered to prevent clustering on the first candle
          chartStartTimeRef.current = hist[0].time as number;
        }

        // Replay any WebSocket messages that arrived during the fetch
        historyLoaded = true;
        for (const p of preloadBuffer) applyKline(p);
        preloadBuffer.length = 0;

        // Flush any already-cached markers (from previous visit in this session)
        // This makes switching back to a timeframe instant — no API wait needed
        if (markersRef.current.size > 0) {
          flushMarkers();
        }

        // Fetch full signal history from DB + live calculator
        // Pass chartStartTime directly so filter is guaranteed to work
        const chartStartTime = hist.length > 0 ? (hist[0].time as number) : 0;
        await fetchSignals(chartStartTime);

      } catch { /* ignore network errors */ }
    };

    loadHistory();

    return () => {
      gone.current = true;
      if (retryTimer) clearTimeout(retryTimer);
      socket?.close();
      // Do NOT call setMarkers([]) here — it would wipe the chart markers
      // before the new timeframe's flushMarkers() runs, causing a blank flash
    };
  }, [asset, wsBaseUrl, timeframe]);

  // ── UI ────────────────────────────────────────────────────────────────────
  return (
    <section className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70 shadow-2xl shadow-black/20">

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-cyan-400">Live Chart</p>
          <h2 className="mt-1 text-xl font-semibold text-white">{asset}</h2>
          <p className="text-sm text-slate-400">Real-time candlestick chart with reversal signals.</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm">
            <span className="text-slate-400">Chart Feed: </span>
            <span className={connected === null ? 'text-amber-400' : connected ? 'text-emerald-400' : 'text-rose-400'}>
              {connected === null ? 'Connecting…' : connected ? 'Live ●' : 'Offline'}
            </span>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm">
            <span className="text-slate-400">Price: </span>
            <span className="font-bold text-white">
              {lastPrice === null ? '—' : lastPrice.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}
            </span>
          </div>

          {signalStatus && timeframe !== '4h' && (
            <div className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-xs min-w-[170px]">
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Signal:</span>
                <span className={`font-bold ${
                  signalStatus.last_signal==='BUY'  ? 'text-[#26a69a]' :
                  signalStatus.last_signal==='SELL' ? 'text-[#ef5350]' : 'text-slate-300'
                }`}>
                  {signalStatus.last_signal==='BUY' ? '▲ BUY' : signalStatus.last_signal==='SELL' ? '▼ SELL' : signalStatus.last_signal}
                </span>
              </div>
              <div className="mt-0.5 text-slate-500 truncate">{signalStatus.tracking}</div>
            </div>
          )}
        </div>
      </div>

      {/* Full Dashboard Button */}
      {showFullDashboardButton && subscriptionActive && (
        <div className="border-b border-slate-800 bg-slate-950/30 flex justify-center px-5 py-4">
          <a
            href={`/asset/${asset.toLowerCase()}`}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-cyan-500/20 transition hover:from-cyan-600 hover:to-blue-600"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            View Full Dashboard
          </a>
        </div>
      )}

      {/* Timeframe selector */}
      <div className="border-b border-slate-800 bg-slate-950/50 px-5 py-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Timeframe:</span>
          {TIMEFRAMES.map((tf) => (
            <button key={tf} type="button" onClick={() => onTimeframeChange(tf)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                timeframe===tf
                  ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/30'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              {tf.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-5 border-b border-slate-800 bg-slate-950/30 px-5 py-2 text-xs">
        <div className="flex items-center gap-1.5">
          <span style={{color:COLOR_UP}} className="text-base">▲</span>
          <span className="text-slate-400">BUY SIGNAL — Bullish Reversal</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span style={{color:COLOR_DOWN}} className="text-base">▼</span>
          <span className="text-slate-400">SELL SIGNAL — Bearish Reversal</span>
        </div>
      </div>

      {/* Chart */}
      <div className="relative h-[600px]">
        {/* Loading overlay - hides label repositioning */}
        {sigLoading && (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent"></div>
              <p className="mt-3 text-sm text-cyan-400">Loading chart data...</p>
            </div>
          </div>
        )}

        <div className={subscriptionActive
          ? 'h-full w-full'
          : 'pointer-events-none h-full w-full select-none blur-sm'
        }>
          <div ref={containerRef} className="h-full w-full" />
        </div>

        {!subscriptionActive && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-slate-950/55 backdrop-blur-[2px]">
            <div className="mx-4 max-w-md rounded-2xl border border-amber-500/30 bg-slate-900/95 p-6 text-center shadow-2xl shadow-black/30">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-amber-300">Premium Charts</p>
              <h3 className="mt-2 text-xl font-semibold text-white">Subscribe to unlock full access</h3>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}