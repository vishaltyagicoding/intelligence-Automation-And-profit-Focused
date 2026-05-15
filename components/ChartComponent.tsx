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
  /** Called every time the chart receives a new price tick — used to sync watchlist prices */
  onPriceUpdate?: (asset: WatchlistAsset, price: number) => void;
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

// ── How long (ms) with no WS message before we force-reconnect ───────────────
// Binance sends kline updates at least every few seconds for liquid pairs.
// If 15 s pass with no message, the connection is silently dead → reconnect.
const STALE_THRESHOLD_MS = 15_000;

// ─────────────────────────────────────────────────────────────────────────────
export default function ChartComponent({
  asset,
  subscriptionActive,
  wsBaseUrl,
  timeframe,
  onTimeframeChange,
  showFullDashboardButton = false,
  onPriceUpdate,
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

  // ── Detect user's browser timezone (TradingView behavior) ─────────────────
  const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  // ── Create chart (once) ────────────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current) return;

    const formatTimeLocal = (unixSec: number): string => {
      return new Intl.DateTimeFormat(undefined, {
        year:     '2-digit',
        month:    '2-digit',
        day:      '2-digit',
        hour:     '2-digit',
        minute:   '2-digit',
        hour12:   false,
        timeZone: userTimezone,
      }).format(new Date(unixSec * 1000)).replace(',', '');
    };

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
        timeFormatter: formatTimeLocal,
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

    const ASSET_PRICE_FMT: Record<string, {precision: number; minMove: number}> = {
      'BTCUSD':  { precision: 2, minMove: 0.01 },
      'ETHUSD':  { precision: 2, minMove: 0.01 },
      'XAUUSD':  { precision: 2, minMove: 0.01 },
      'LTCUSD':  { precision: 2, minMove: 0.01 },
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
    setSigLoading(true);
    chartStartTimeRef.current = 0;

    const cacheKey = `${asset}:${timeframe}`;
    markerCacheRef.current.set(cacheKey, new Map());
    markersRef.current = markerCacheRef.current.get(cacheKey)!;

    seriesRef.current?.setData([]);
    seriesRef.current?.setMarkers([]);

    const candles: Map<number, CandleDataPoint> = new Map();

    const flushMarkers = (minTime: number = chartStartTimeRef.current) => {
      if (!seriesRef.current) return;
      const all = [...markersRef.current.values()];
      const inWindow = minTime > 0
        ? all.filter(m => (m.time as number) >= minTime)
        : all;
      const sorted = inWindow.sort((a, b) => (a.time as number) - (b.time as number));
      try { seriesRef.current.setMarkers(sorted); } catch { /* ignore */ }
    };

    const preloadBuffer: KlinePayload[] = [];
    let historyLoaded = false;

    const gone = { current: false };
    let socket: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    // ── Stale-data watchdog ───────────────────────────────────────────────────
    // If no message arrives within STALE_THRESHOLD_MS, the WS is silently dead.
    // Force-close it so onclose triggers and the reconnect loop kicks in.
    let staleTimer: ReturnType<typeof setTimeout> | null = null;

    const resetStaleTimer = () => {
      if (staleTimer) clearTimeout(staleTimer);
      staleTimer = setTimeout(() => {
        if (!gone.current && socket && socket.readyState === WebSocket.OPEN) {
          console.warn(`⚠️ Stale WS detected for ${asset} ${timeframe} — forcing reconnect`);
          socket.close(4000, 'stale');
        }
      }, STALE_THRESHOLD_MS);
    };

    const applyKline = (p: KlinePayload) => {
      const ts    = toUnix(p.timestamp ?? p.time);
      const close = toFloat(p.close ?? p.price);
      if (!close || !Number.isFinite(close)) {
        console.warn('⚠️ Invalid close price:', p);
        return;
      }

      const open  = toFloat(p.open,  0);
      const high  = toFloat(p.high,  0);
      const low   = toFloat(p.low,   0);

      const interval = TF_SEC[timeframe];
      const start    = Math.floor(ts / interval) * interval;
      const existing = candles.get(start);

      let candle: CandleDataPoint;

      const hasFullOHLC = open > 0 && high > 0 && low > 0 && high >= low;

      if (hasFullOHLC) {
        if (existing) {
          candle = {
            time:  start as Time,
            open:  existing.open,   // NEVER change the original open
            high:  Math.max(existing.high, high),
            low:   Math.min(existing.low,  low),
            close,
          };
        } else {
          candle = { time: start as Time, open, high, low, close };
        }
        candles.set(start, candle);
      } else if (existing) {
        candle = {
          ...existing,
          close,
          high:  Math.max(existing.high, close),
          low:   Math.min(existing.low,  close),
        };
        candles.set(start, candle);
      } else {
        const sortedKeys = [...candles.keys()].sort((a, b) => a - b);
        const lastKey    = sortedKeys.length > 0 ? sortedKeys[sortedKeys.length - 1] : null;
        const prevClose  = lastKey !== null ? (candles.get(lastKey)?.close ?? close) : close;
        candle = { time: start as Time, open: prevClose, high: close, low: close, close };
        candles.set(start, candle);
      }

      console.log('📊 Chart update:', { time: start, close, hasFullOHLC });

      // Update chart price display
      setLastPrice(close);

      // ── KEY FIX: notify parent so the watchlist shows the SAME price ──────
      // This is the single source of truth for the selected asset's live price.
      onPriceUpdate?.(asset, close);

      try { seriesRef.current?.update(candle); } catch (e) { console.error('Chart update failed:', e); }
    };

    // ── WebSocket reconnection — no cap, retries forever ─────────────────────
    // FIXED: removed MAX_RECONNECT_ATTEMPTS limit that previously caused the
    // WebSocket to silently stop reconnecting after 10 attempts, leaving the
    // chart frozen until the user manually refreshed the page.
    let reconnectAttempts = 0;
    let heartbeatTimer: ReturnType<typeof setInterval> | null = null;

    const zoneToMarker = (z: { is_bullish: boolean; timestamp: string }, interval: number): SeriesMarker<Time> => {
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

    const SIXTY_MIN_S = 60 * 60;

    const mergeAndFlush = (newMarkers: SeriesMarker<Time>[]) => {
      const sorted = [...newMarkers].sort((a, b) => (a.time as number) - (b.time as number));

      for (const m of sorted) {
        const newTime = m.time as number;

        if (markersRef.current.has(newTime)) continue;

        const existingTimes = [...markersRef.current.keys()].sort((a, b) => a - b);
        const lastTime   = existingTimes.length > 0 ? existingTimes[existingTimes.length - 1] : undefined;
        const lastMarker = lastTime !== undefined ? markersRef.current.get(lastTime) : undefined;

        if (lastMarker !== undefined && lastTime !== undefined) {
          const gapSeconds = newTime - lastTime;

          if (gapSeconds < SIXTY_MIN_S) {
            if (lastMarker.text === m.text && newTime > lastTime) {
              markersRef.current.delete(lastTime);
              markersRef.current.set(newTime, m);
            }
            continue;
          }

          if (lastMarker.text === m.text) {
            if (newTime > lastTime) {
              markersRef.current.delete(lastTime);
              markersRef.current.set(newTime, m);
            }
            continue;
          }
        }

        if (chartStartTimeRef.current === 0 || newTime >= chartStartTimeRef.current) {
          markersRef.current.set(newTime, m);
        }
      }

      flushMarkers();
    };

    const applySignal = (s: SignalPayload) => {
      if (!seriesRef.current) return;
      const interval = TF_SEC[timeframe];

      const newMarkers: SeriesMarker<Time>[] = s.all_zones.map(
        (z) => zoneToMarker(z, interval)
      );

      const chartStart = chartStartTimeRef.current;
      const inWindow = chartStart > 0
        ? newMarkers.filter(m => (m.time as number) >= chartStart)
        : newMarkers;

      if (inWindow.length > 0) {
        mergeAndFlush(inWindow);
        setSignalStatus({ last_signal: s.signal, tracking: s.tracking });
      }
    };

    const connect = () => {
      if (gone.current) return;

      if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null; }
      if (staleTimer) { clearTimeout(staleTimer); staleTimer = null; }

      try {
        socket = new WebSocket(`${wsBaseUrl}/ws/market/${asset}/${timeframe}/`);

        socket.onerror = () => {
          console.error(`Chart WebSocket error: ${asset} ${timeframe}`);
          setConnected(false);
        };

        socket.onopen = () => {
          console.log(`✅ WebSocket connected: ${asset} ${timeframe}`);
          setConnected(true);
          reconnectAttempts = 0;

          // Start stale-data watchdog immediately
          resetStaleTimer();

          // Heartbeat — keeps the TCP connection alive through proxies/load-balancers
          heartbeatTimer = setInterval(() => {
            if (socket && socket.readyState === WebSocket.OPEN) {
              try { socket.send(JSON.stringify({ action: 'ping' })); } catch { /* ignore */ }
            }
          }, 20_000); // every 20 s
        };

        socket.onclose = (event) => {
          console.warn(`WebSocket closed: ${asset} ${timeframe} (code: ${event.code})`);
          setConnected(false);

          if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null; }
          if (staleTimer) { clearTimeout(staleTimer); staleTimer = null; }

          if (!gone.current) {
            // ── No cap on reconnect attempts — retries forever ────────────────
            // Previously capped at 10 attempts, which caused the chart to freeze
            // permanently after 10 reconnect failures. Now it always retries.
            reconnectAttempts++;
            // Exponential backoff: 1s → 2s → 4s → … capped at 10s (not 30s)
            // Shorter cap means data resumes faster after a brief network hiccup.
            const delay = Math.min(1000 * Math.pow(2, Math.min(reconnectAttempts - 1, 4)), 10_000);
            console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts})…`);
            retryTimer = setTimeout(connect, delay);
          }
        };

        socket.onmessage = (ev: MessageEvent<string>) => {
          // Every message means the connection is alive — reset stale watchdog
          resetStaleTimer();

          try {
            const raw = JSON.parse(ev.data) as Record<string, unknown>;
            const msgType = raw.type as string | undefined;

            console.log('📨 WS MSG:', {
              type: msgType || 'kline',
              asset: raw.asset,
              close: raw.close || raw.price,
              timestamp: raw.timestamp || raw.time,
              hasOHLC: !!(raw.open && raw.high && raw.low && raw.close)
            });

            if (msgType === 'ping') {
              socket?.send(JSON.stringify({ action:'pong' }));
              return;
            }

            if (msgType === 'signal') {
              console.log('🎯 SIGNAL received:', raw);
              if (historyLoaded) applySignal(raw as unknown as SignalPayload);
              return;
            }

            const p = raw as unknown as KlinePayload;
            if (!historyLoaded) {
              preloadBuffer.push(p);
            } else {
              applyKline(p);
            }
          } catch (err) {
            console.error('❌ WebSocket parse error:', err);
          }
        };
      } catch (e) {
        console.error('Failed to create WebSocket:', e);
        setConnected(false);
      }
    };

    connect();

    const fetchSignals = async (chartStartTime: number = 0) => {
      if (!seriesRef.current || gone.current) return;
      setSigLoading(true);
      const interval = TF_SEC[timeframe];

      markersRef.current.clear();
      const cacheKey = `${asset}:${timeframe}`;
      markerCacheRef.current.delete(cacheKey);

      try {
        const allRawSignals: Array<{is_bullish: boolean; timestamp: string}> = [];

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

        const allMarkers = allRawSignals
          .map(z => zoneToMarker(z, interval))
          .sort((a, b) => (a.time as number) - (b.time as number));

        const SIXTY_MIN = 60 * 60;
        const finalMarkers: SeriesMarker<Time>[] = [];
        const seenTimes = new Set<number>();

        for (const m of allMarkers) {
          const t = m.time as number;

          if (seenTimes.has(t)) continue;

          const last = finalMarkers.length > 0 ? finalMarkers[finalMarkers.length - 1] : undefined;
          const lastTime = last !== undefined ? (last.time as number) : undefined;

          if (lastTime !== undefined) {
            const gapSeconds = t - lastTime;
            if (gapSeconds < SIXTY_MIN) {
              if (last !== undefined && last.text === m.text && t > lastTime) {
                finalMarkers[finalMarkers.length - 1] = m;
                seenTimes.delete(lastTime);
                seenTimes.add(t);
              }
              continue;
            }
          }

          if (last !== undefined && last.text === m.text) {
            finalMarkers[finalMarkers.length - 1] = m;
            seenTimes.delete(last.time as number);
            seenTimes.add(t);
            continue;
          }

          finalMarkers.push(m);
          seenTimes.add(t);
        }

        const inWindowMarkers = chartStartTime > 0
          ? finalMarkers.filter(m => (m.time as number) >= chartStartTime)
          : finalMarkers;

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

    const loadHistory = async () => {
      try {
        const ASSET_TO_BINANCE: Record<string, string> = {
          'XAUUSD': 'PAXGUSDT',
          'BTCUSD': 'BTCUSDT',
          'ETHUSD': 'ETHUSDT',
          'LTCUSD': 'LTCUSDT',
        };
        const sym = ASSET_TO_BINANCE[asset] ?? asset.replace('USD', 'USDT');
        const TF_LIMIT: Record<Timeframe, number> = {
          '5m':  1000,
          '15m': 1000,
          '30m': 1000,
          '1h':  750,
          '2h':  375,
          '4h':  200,
          '1d':  180,
        };
        const limit = TF_LIMIT[timeframe] ?? 1000;
        const res = await fetch(
          `https://api.binance.com/api/v3/klines?symbol=${sym}&interval=${TF_BINANCE[timeframe]}&limit=${limit}`
        );
        const raw = await res.json();
        if (gone.current) return;

        let hist: CandleDataPoint[] = raw.map((k: (string|number)[]) => ({
          time:  Math.floor(Number(k[0]) / 1000) as Time,
          open:  parseFloat(k[1] as string),
          high:  parseFloat(k[2] as string),
          low:   parseFloat(k[3] as string),
          close: parseFloat(k[4] as string),
        }));

        for (const c of hist) candles.set(c.time as number, c);

        seriesRef.current?.setData(hist);
        chartRef.current?.timeScale().fitContent();

        if (hist.length > 0) {
          const latestClose = hist[hist.length - 1].close;
          setLastPrice(latestClose);

          // Immediately sync the watchlist price to match chart on load
          onPriceUpdate?.(asset, latestClose);

          chartStartTimeRef.current = hist[0].time as number;
        }

        historyLoaded = true;
        for (const p of preloadBuffer) applyKline(p);
        preloadBuffer.length = 0;

        if (markersRef.current.size > 0) {
          flushMarkers();
        }

        const chartStartTime = hist.length > 0 ? (hist[0].time as number) : 0;
        await fetchSignals(chartStartTime);

      } catch { /* ignore network errors */ }
    };

    loadHistory();

    return () => {
      gone.current = true;
      if (retryTimer) clearTimeout(retryTimer);
      if (heartbeatTimer) clearInterval(heartbeatTimer);
      if (staleTimer) clearTimeout(staleTimer);
      socket?.close();
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

          {/* Dynamic timezone badge */}
          <div className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm" title="Chart times are displayed in your local timezone">
            <span className="text-slate-400">TZ: </span>
            <span className="font-medium text-cyan-300">
              {userTimezone.split('/').slice(-1)[0].replace(/_/g, ' ')}
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