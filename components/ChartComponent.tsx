'use client';

import { useEffect, useRef, useState } from 'react';
import {
  ColorType, CrosshairMode, createChart,
  type IChartApi, type ISeriesApi, type SeriesMarker, type Time,
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

// ─── Constants ────────────────────────────────────────────────────────────────

const TIMEFRAMES: Timeframe[] = ['5m', '15m', '30m', '1h', '2h', '4h', '1d'];

const ASSET_TO_BINANCE: Record<WatchlistAsset, string> = {
  BTCUSD: 'BTCUSDT', ETHUSD: 'ETHUSDT',
  XAUUSD: 'PAXGUSDT', LTCUSD: 'LTCUSDT',
};

// Lowercase stream names for Binance WebSocket
const ASSET_TO_BINANCE_WS: Record<WatchlistAsset, string> = {
  BTCUSD: 'btcusdt', ETHUSD: 'ethusdt',
  XAUUSD: 'paxgusdt', LTCUSD: 'ltcusdt',
};

const TF_BINANCE: Record<Timeframe, string> = {
  '5m': '5m', '15m': '15m', '30m': '30m',
  '1h': '1h', '2h': '2h', '4h': '4h', '1d': '1d',
};

const TF_SEC: Record<Timeframe, number> = {
  '5m': 300, '15m': 900, '30m': 1800,
  '1h': 3600, '2h': 7200, '4h': 14400, '1d': 86400,
};

const TF_LIMIT: Record<Timeframe, number> = {
  '5m': 1000, '15m': 1000, '30m': 1000,
  '1h': 750, '2h': 375, '4h': 200, '1d': 180,
};

const COLOR_UP   = '#26a69a';
const COLOR_DOWN = '#ef5350';

// ─── Types ────────────────────────────────────────────────────────────────────

interface CandleDataPoint {
  time: Time; open: number; high: number; low: number; close: number;
}

interface SignalPayload {
  type: 'signal';
  asset: string; timeframe: string;
  signal: 'BUY' | 'SELL';
  is_bullish: boolean; price: number;
  timestamp: string; bar_index: number; tracking: string;
  all_zones: Array<{ is_bullish: boolean; center_price: number; timestamp: string; bar_index: number }>;
}

// Binance kline stream message
interface BinanceKlineMsg {
  e: string;
  k: {
    t: number;   // open time ms
    o: string; h: string; l: string; c: string;
    x: boolean;  // is candle closed
  };
}

export interface ChartComponentProps {
  asset: WatchlistAsset;
  aiSignals: AISignal[];
  subscriptionActive: boolean;
  wsBaseUrl: string;
  timeframe: Timeframe;
  onTimeframeChange: (tf: Timeframe) => void;
  showFullDashboardButton?: boolean;
  onPriceUpdate?: (asset: WatchlistAsset, price: number) => void;
}

function toFloat(v: string | number | undefined, fallback = 0): number {
  const n = typeof v === 'string' ? parseFloat(v) : (v ?? NaN);
  return Number.isFinite(n) ? n : fallback;
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function ChartComponent({
  asset, subscriptionActive, wsBaseUrl,
  timeframe, onTimeframeChange,
  showFullDashboardButton = false, onPriceUpdate,
}: ChartComponentProps) {

  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef     = useRef<IChartApi | null>(null);
  const seriesRef    = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const roRef        = useRef<ResizeObserver | null>(null);
  const markersRef   = useRef<Map<number, SeriesMarker<Time>>>(new Map());
  const chartStartRef = useRef<number>(0);

  const [lastPrice,    setLastPrice]    = useState<number | null>(null);
  const [connected,    setConnected]    = useState<boolean | null>(null);
  const [signalStatus, setSignalStatus] = useState<{ last_signal: string; tracking: string } | null>(null);
  const [sigLoading,   setSigLoading]   = useState(false);

  const userTZ = Intl.DateTimeFormat().resolvedOptions().timeZone;

  // ── Create chart once ──────────────────────────────────────────────────────
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
        timeFormatter: (sec: number) =>
          new Intl.DateTimeFormat(undefined, {
            year: '2-digit', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit', hour12: false,
            timeZone: userTZ,
          }).format(new Date(sec * 1000)).replace(',', ''),
      },
      timeScale: {
        borderColor: 'rgba(148,163,184,0.2)',
        timeVisible: true, secondsVisible: false,
        fixLeftEdge: true, fixRightEdge: true,
        lockVisibleTimeRangeOnResize: true,
      },
      handleScroll:  { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: true },
      handleScale:   { axisPressedMouseMove: true, mouseWheel: true, pinch: true },
      kineticScroll: { mouse: false, touch: true },
      watermark:     { visible: false },
    });

    const series = chart.addCandlestickSeries({
      upColor: COLOR_UP, downColor: COLOR_DOWN,
      wickUpColor: COLOR_UP, wickDownColor: COLOR_DOWN,
      borderVisible: true,
      borderUpColor: COLOR_UP, borderDownColor: COLOR_DOWN,
      priceLineVisible: true, priceLineColor: COLOR_UP, priceLineWidth: 1,
      priceFormat: { type: 'price', precision: 2, minMove: 0.01 },
    });

    chartRef.current  = chart;
    seriesRef.current = series;

    roRef.current = new ResizeObserver(() => {
      if (containerRef.current && chartRef.current)
        chartRef.current.applyOptions({
          width:  containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
    });
    roRef.current.observe(containerRef.current);

    return () => { roRef.current?.disconnect(); chart.remove(); chartRef.current = null; seriesRef.current = null; };
  }, []);

  // ── Data + WebSocket per asset/timeframe ───────────────────────────────────
  useEffect(() => {
    setLastPrice(null);
    setSignalStatus(null);
    setSigLoading(true);
    chartStartRef.current = 0;
    markersRef.current.clear();
    seriesRef.current?.setData([]);
    seriesRef.current?.setMarkers([]);

    const candles         = new Map<number, CandleDataPoint>();
    const preloadBuffer:    BinanceKlineMsg['k'][] = [];
    let   historyLoaded   = false;
    const gone            = { current: false };

    const flushMarkers = (minTime = chartStartRef.current) => {
      if (!seriesRef.current) return;
      const all = [...markersRef.current.values()];
      const vis = minTime > 0 ? all.filter(m => (m.time as number) >= minTime) : all;
      try { seriesRef.current.setMarkers(vis.sort((a, b) => (a.time as number) - (b.time as number))); }
      catch { /* chart resetting */ }
    };

    // ── Apply one Binance kline tick to the chart ─────────────────────────────
    const applyKline = (k: BinanceKlineMsg['k']) => {
      const interval = TF_SEC[timeframe];
      const start    = Math.floor(k.t / 1000 / interval) * interval;
      const open     = toFloat(k.o);
      const high     = toFloat(k.h);
      const low      = toFloat(k.l);
      const close    = toFloat(k.c);

      const existing = candles.get(start);
      const candle: CandleDataPoint = existing
        ? { time: start as Time, open: existing.open,
            high: Math.max(existing.high, high),
            low:  Math.min(existing.low,  low), close }
        : { time: start as Time, open, high, low, close };

      candles.set(start, candle);
      setLastPrice(close);
      onPriceUpdate?.(asset, close);
      try { seriesRef.current?.update(candle); } catch { /* ignore */ }
    };

    // ════════════════════════════════════════════════════════════════════════
    // BINANCE WebSocket — DIRECT connection for all price / candle data
    // Bypasses backend → nginx → Redis → Django Channels chain entirely.
    // Binance sends a kline tick every ~1 second for liquid pairs so prices
    // can NEVER get stuck even if the backend is unreachable.
    // ════════════════════════════════════════════════════════════════════════
    let binanceWs:         WebSocket | null = null;
    let binanceRetryTimer: ReturnType<typeof setTimeout> | null = null;
    let binanceRetries     = 0;
    let binancePingInterval: ReturnType<typeof setInterval> | null = null;

    const connectBinance = () => {
      if (gone.current) return;
      const sym = ASSET_TO_BINANCE_WS[asset];
      const ivl = TF_BINANCE[timeframe];
      const url = `wss://stream.binance.com:9443/ws/${sym}@kline_${ivl}`;

      try { binanceWs = new WebSocket(url); }
      catch { scheduleBinanceRetry(); return; }

      binanceWs.onopen = () => {
        setConnected(true);
        binanceRetries = 0;
        console.log(`✅ Binance WS: ${asset} ${timeframe}`);
        
        // Send periodic pings to keep connection alive (every 30 seconds)
        // Binance WebSocket will close if no data is sent/received for 60 seconds
        if (binancePingInterval) clearInterval(binancePingInterval);
        binancePingInterval = setInterval(() => {
          if (binanceWs?.readyState === WebSocket.OPEN) {
            try {
              // Binance doesn't require ping frames, but we send them anyway
              // to keep the connection active through proxies/firewalls
              binanceWs.send(JSON.stringify({ method: 'ping' }));
            } catch (e) {
              console.warn('Binance ping failed:', e);
            }
          }
        }, 30_000);
      };

      binanceWs.onmessage = (ev: MessageEvent<string>) => {
        try {
          const msg = JSON.parse(ev.data) as BinanceKlineMsg;
          if (msg.e !== 'kline') return;
          if (!historyLoaded) preloadBuffer.push(msg.k);
          else applyKline(msg.k);
        } catch { /* ignore */ }
      };

      binanceWs.onclose = (ev) => {
        console.warn(`Binance WS closed: code=${ev.code}, reason=${ev.reason || 'none'}`);
        setConnected(false);
        if (binancePingInterval) {
          clearInterval(binancePingInterval);
          binancePingInterval = null;
        }
        scheduleBinanceRetry();
      };

      binanceWs.onerror = (err) => {
        console.error('Binance WS error:', err);
        setConnected(false);
      };
    };

    const scheduleBinanceRetry = () => {
      if (gone.current) return;
      binanceRetries++;
      // Max 10 s backoff — Binance is rock-solid, fast retry is safe
      const delay = Math.min(1000 * Math.pow(2, Math.min(binanceRetries - 1, 3)), 10_000);
      console.log(`Binance WS retry in ${delay}ms (#${binanceRetries})`);
      binanceRetryTimer = setTimeout(connectBinance, delay);
    };

    // ════════════════════════════════════════════════════════════════════════
    // BACKEND WebSocket — SIGNALS ONLY
    // Only used to receive BUY/SELL signal markers from Django.
    // If this drops, prices still update every second from Binance above.
    // Shows "Reconnecting…" in the signal area if it drops, NOT in the price.
    // ════════════════════════════════════════════════════════════════════════
    let backendWs:         WebSocket | null = null;
    let backendRetryTimer: ReturnType<typeof setTimeout> | null = null;
    let backendRetries     = 0;
    let backendHeartbeat:  ReturnType<typeof setInterval> | null = null;
    let backendStaleTimer: ReturnType<typeof setTimeout> | null = null;

    const BACKEND_STALE_MS = 45_000;

    const resetBackendStale = () => {
      if (backendStaleTimer) clearTimeout(backendStaleTimer);
      backendStaleTimer = setTimeout(() => {
        if (!gone.current && backendWs?.readyState === WebSocket.OPEN) {
          console.warn('Backend WS stale → force-reconnecting');
          backendWs.close(4000, 'stale');
        }
      }, BACKEND_STALE_MS);
    };

    const connectBackend = () => {
      if (gone.current) return;
      const url = `${wsBaseUrl}/ws/market/${asset}/${timeframe}/`;

      try { backendWs = new WebSocket(url); }
      catch { scheduleBackendRetry(); return; }

      backendWs.onopen = () => {
        backendRetries = 0;
        resetBackendStale();
        // Heartbeat every 20 s to keep nginx proxy alive
        backendHeartbeat = setInterval(() => {
          if (backendWs?.readyState === WebSocket.OPEN)
            try { backendWs.send(JSON.stringify({ action: 'ping' })); } catch { /* ignore */ }
        }, 20_000);
      };

      backendWs.onmessage = (ev: MessageEvent<string>) => {
        resetBackendStale();
        try {
          const raw = JSON.parse(ev.data) as Record<string, unknown>;
          if (raw.type === 'ping') {
            backendWs?.send(JSON.stringify({ action: 'pong' }));
            return;
          }
          // Only handle signal events — ignore all kline/price messages
          if (raw.type === 'signal' && historyLoaded)
            applySignal(raw as unknown as SignalPayload);
        } catch { /* ignore */ }
      };

      backendWs.onclose = () => {
        if (backendHeartbeat)  { clearInterval(backendHeartbeat);  backendHeartbeat  = null; }
        if (backendStaleTimer) { clearTimeout(backendStaleTimer);   backendStaleTimer = null; }
        scheduleBackendRetry();
      };

      backendWs.onerror = () => { /* onclose fires next */ };
    };

    const scheduleBackendRetry = () => {
      if (gone.current) return;
      backendRetries++;
      const delay = Math.min(1000 * Math.pow(2, Math.min(backendRetries - 1, 4)), 15_000);
      backendRetryTimer = setTimeout(connectBackend, delay);
    };

    // ── Signal helpers ────────────────────────────────────────────────────────
    const SIXTY_MIN = 3600;

    const zoneToMarker = (z: { is_bullish: boolean; timestamp: string }, interval: number): SeriesMarker<Time> => {
      const ts  = z.timestamp.includes('+') || z.timestamp.endsWith('Z') ? z.timestamp : z.timestamp + 'Z';
      const raw = Math.floor(new Date(ts).getTime() / 1000);
      return {
        time:     Math.floor(raw / interval) * interval as Time,
        position: z.is_bullish ? 'belowBar'   : 'aboveBar',
        color:    z.is_bullish ? COLOR_UP      : COLOR_DOWN,
        shape:    z.is_bullish ? 'arrowUp'     : 'arrowDown',
        text:     z.is_bullish ? 'BUY SIGNAL'  : 'SELL SIGNAL',
        size:     2,
      };
    };

    const mergeAndFlush = (incoming: SeriesMarker<Time>[]) => {
      const sorted = [...incoming].sort((a, b) => (a.time as number) - (b.time as number));
      for (const m of sorted) {
        const t = m.time as number;
        if (markersRef.current.has(t)) continue;
        const times = [...markersRef.current.keys()].sort((a, b) => a - b);
        const lt    = times.length > 0 ? times[times.length - 1] : undefined;
        const last  = lt !== undefined ? markersRef.current.get(lt) : undefined;
        if (last !== undefined && lt !== undefined) {
          if (t - lt < SIXTY_MIN) {
            if (last.text === m.text && t > lt) { markersRef.current.delete(lt); markersRef.current.set(t, m); }
            continue;
          }
          if (last.text === m.text) {
            if (t > lt) { markersRef.current.delete(lt); markersRef.current.set(t, m); }
            continue;
          }
        }
        if (chartStartRef.current === 0 || t >= chartStartRef.current) markersRef.current.set(t, m);
      }
      flushMarkers();
    };

    const applySignal = (s: SignalPayload) => {
      const ivl     = TF_SEC[timeframe];
      const markers = s.all_zones.map(z => zoneToMarker(z, ivl));
      const visible = chartStartRef.current > 0
        ? markers.filter(m => (m.time as number) >= chartStartRef.current)
        : markers;
      if (visible.length > 0) {
        mergeAndFlush(visible);
        setSignalStatus({ last_signal: s.signal, tracking: s.tracking });
      }
    };

    // ── REST: fetch historical signals ────────────────────────────────────────
    const fetchSignals = async (chartStart = 0) => {
      if (!seriesRef.current || gone.current) return;
      const ivl = TF_SEC[timeframe];
      markersRef.current.clear();

      try {
        const allRaw: Array<{ is_bullish: boolean; timestamp: string }> = [];
        try {
          const r = await fetch(`/api/trading/signal-history/${asset}/?timeframe=${timeframe}`);
          if (r.ok && !gone.current) { const j = await r.json(); if (j.success) allRaw.push(...(j.signals ?? [])); }
        } catch { /* optional */ }

        if (gone.current) return;

        let liveStatus: { last_signal: string; tracking: string } | null = null;
        try {
          const r = await fetch(`/api/trading/reversal-zones/${asset}/?timeframe=${timeframe}`);
          if (r.ok && !gone.current) {
            const j = await r.json();
            if (j.success && j.data?.zones?.length > 0) { allRaw.push(...j.data.zones); liveStatus = j.data.status ?? null; }
          }
        } catch { /* optional */ }

        if (gone.current) return;

        const sorted = allRaw.map(z => zoneToMarker(z, ivl)).sort((a, b) => (a.time as number) - (b.time as number));
        const final: SeriesMarker<Time>[] = [];
        const seen = new Set<number>();

        for (const m of sorted) {
          const t = m.time as number;
          if (seen.has(t)) continue;
          const last = final.length > 0 ? final[final.length - 1] : undefined;
          const lt   = last ? (last.time as number) : undefined;
          if (lt !== undefined) {
            if (t - lt < SIXTY_MIN) {
              if (last?.text === m.text && t > lt) { final[final.length - 1] = m; seen.delete(lt); seen.add(t); }
              continue;
            }
            if (last?.text === m.text) { final[final.length - 1] = m; seen.delete(lt!); seen.add(t); continue; }
          }
          final.push(m); seen.add(t);
        }

        const visible = chartStart > 0 ? final.filter(m => (m.time as number) >= chartStart) : final;
        for (const m of visible) markersRef.current.set(m.time as number, m);
        flushMarkers(chartStart);
        if (!gone.current && liveStatus) setSignalStatus(liveStatus);
      } catch { /* silent */ }
      finally { if (!gone.current) setSigLoading(false); }
    };

    // ── REST: load historical candles from Binance ────────────────────────────
    const loadHistory = async () => {
      try {
        const symbol = ASSET_TO_BINANCE[asset];
        const res = await fetch(
          `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${TF_BINANCE[timeframe]}&limit=${TF_LIMIT[timeframe]}`
        );
        const raw: (string | number)[][] = await res.json();
        if (gone.current) return;

        const hist: CandleDataPoint[] = raw.map(k => ({
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
          const latest = hist[hist.length - 1].close;
          setLastPrice(latest);
          onPriceUpdate?.(asset, latest);
          chartStartRef.current = hist[0].time as number;
        }

        // Drain WS ticks that arrived while history was loading
        historyLoaded = true;
        for (const k of preloadBuffer) applyKline(k);
        preloadBuffer.length = 0;

        await fetchSignals(chartStartRef.current);
      } catch (e) {
        console.error('History load failed:', e);
        historyLoaded = true; // still drain buffer
        if (!gone.current) setSigLoading(false);
      }
    };

    // ── Boot ──────────────────────────────────────────────────────────────────
    connectBinance();
    connectBackend();
    loadHistory();

    return () => {
      gone.current = true;
      if (binanceRetryTimer)  clearTimeout(binanceRetryTimer);
      if (binancePingInterval) clearInterval(binancePingInterval);
      if (backendRetryTimer)  clearTimeout(backendRetryTimer);
      if (backendHeartbeat)   clearInterval(backendHeartbeat);
      if (backendStaleTimer)  clearTimeout(backendStaleTimer);
      try { binanceWs?.close(); } catch { /* ignore */ }
      try { backendWs?.close(); } catch { /* ignore */ }
    };
  }, [asset, wsBaseUrl, timeframe]);

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <section className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70 shadow-2xl shadow-black/20">

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
              {connected === null ? 'Connecting…' : connected ? 'Live ●' : 'Reconnecting…'}
            </span>
            {connected === false && (
              <span className="ml-2 text-xs text-slate-500">(auto-retry)</span>
            )}
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm">
            <span className="text-slate-400">Price: </span>
            <span className="font-bold text-white">
              {lastPrice === null ? '—'
                : lastPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm">
            <span className="text-slate-400">TZ: </span>
            <span className="font-medium text-cyan-300">
              {userTZ.split('/').pop()?.replace(/_/g, ' ')}
            </span>
          </div>

          {signalStatus && timeframe !== '4h' && (
            <div className="min-w-[170px] rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Signal:</span>
                <span className={`font-bold ${
                  signalStatus.last_signal === 'BUY'  ? 'text-[#26a69a]' :
                  signalStatus.last_signal === 'SELL' ? 'text-[#ef5350]' : 'text-slate-300'
                }`}>
                  {signalStatus.last_signal === 'BUY' ? '▲ BUY' : signalStatus.last_signal === 'SELL' ? '▼ SELL' : signalStatus.last_signal}
                </span>
              </div>
              <div className="mt-0.5 truncate text-slate-500">{signalStatus.tracking}</div>
            </div>
          )}
        </div>
      </div>

      {showFullDashboardButton && subscriptionActive && (
        <div className="flex justify-center border-b border-slate-800 bg-slate-950/30 px-5 py-4">
          <a href={`/asset/${asset.toLowerCase()}`}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-cyan-500/20 transition hover:from-cyan-600 hover:to-blue-600">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            View Full Dashboard
          </a>
        </div>
      )}

      <div className="border-b border-slate-800 bg-slate-950/50 px-5 py-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Timeframe:</span>
          {TIMEFRAMES.map(tf => (
            <button key={tf} type="button" onClick={() => onTimeframeChange(tf)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                timeframe === tf
                  ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/30'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}>
              {tf.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-5 border-b border-slate-800 bg-slate-950/30 px-5 py-2 text-xs">
        <div className="flex items-center gap-1.5">
          <span style={{ color: COLOR_UP }} className="text-base">▲</span>
          <span className="text-slate-400">BUY SIGNAL — Bullish Reversal</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span style={{ color: COLOR_DOWN }} className="text-base">▼</span>
          <span className="text-slate-400">SELL SIGNAL — Bearish Reversal</span>
        </div>
      </div>

      <div className="relative h-[600px]">
        {sigLoading && (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent" />
              <p className="mt-3 text-sm text-cyan-400">Loading chart data…</p>
            </div>
          </div>
        )}
        <div className={subscriptionActive ? 'h-full w-full' : 'pointer-events-none h-full w-full select-none blur-sm'}>
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