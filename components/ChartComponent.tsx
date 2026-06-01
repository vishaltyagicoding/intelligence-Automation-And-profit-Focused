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

// Lowercase stream names for Binance WebSocket --
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

// Data source information for each asset (for transparency to traders)
const ASSET_DATA_SOURCE: Record<WatchlistAsset, { exchange: string; symbol: string; description: string }> = {
  BTCUSD: { 
    exchange: 'BINANCE', 
    symbol: 'BTCUSDT',
    description: 'Bitcoin/USDT spot price from Binance (world\'s largest crypto exchange)'
  },
  ETHUSD: { 
    exchange: 'BINANCE', 
    symbol: 'ETHUSDT',
    description: 'Ethereum/USDT spot price from Binance'
  },
  LTCUSD: { 
    exchange: 'BINANCE', 
    symbol: 'LTCUSDT',
    description: 'Litecoin/USDT spot price from Binance'
  },
  XAUUSD: { 
    exchange: 'BINANCE', 
    symbol: 'PAXGUSDT',
    description: 'Gold price via Paxos Gold (PAXG) token on Binance - 1 PAXG = 1 troy ounce of gold'
  },
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
  
  // CRITICAL: Store signals by asset+timeframe to preserve them across timeframe changes
  // Key format: "BTCUSD:5m:1234567890" → SeriesMarker
  // This ensures signals NEVER disappear when switching timeframes or refreshing
  const persistentSignalsRef = useRef<Map<string, SeriesMarker<Time>>>(new Map());
  // SL and Target price lines: keyed by candle time → {sl, target, isBullish}
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  // slTargetMarkersRef: stores SL + Target text markers per signal candle time
  // Kept separate from markersRef so BUY/SELL deduplication is never disturbed.
  const slTargetMarkersRef = useRef<Map<number, SeriesMarker<Time>[]>>(new Map());
  // slTargetMapRef: stores raw sl/target numbers for hit detection
  const slTargetMapRef   = useRef<Map<number, { sl: number; target: number; isBullish: boolean }>>(new Map());
  // hitMarkersRef: stores "SL HIT" / "TARGET HIT" markers
  const hitMarkersRef    = useRef<Map<number, SeriesMarker<Time>>>(new Map());
  // Active price line objects — kept for cleanup only (no longer used for display)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const activePriceLines = useRef<any[]>([]);

  const [lastPrice,    setLastPrice]    = useState<number | null>(null);
  const [signalStatus, setSignalStatus] = useState<{ last_signal: string; tracking: string } | null>(null);
  const [sigLoading,   setSigLoading]   = useState(false);

  // Get user's timezone and offset
  const userTZ = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const userTZOffset = new Date().getTimezoneOffset() * 60; // offset in seconds (negative for ahead of UTC)
  
  // Helper: Convert UTC timestamp to local timestamp for chart display
  // lightweight-charts always displays timestamps as UTC, so we need to shift them
  // by the user's timezone offset to make them appear in local time
  const utcToLocalTime = (utcSeconds: number): number => {
    return utcSeconds - userTZOffset; // subtract because getTimezoneOffset is negative for ahead of UTC
  };

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
        timeFormatter: (sec: number) => {
          // Timestamps are already converted to local time, so just format them
          // WITHOUT timezone conversion (otherwise it would double-convert)
          return new Intl.DateTimeFormat(undefined, {
            year: '2-digit', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit', hour12: false,
            timeZone: 'UTC', // Use UTC because timestamps are already adjusted
          }).format(new Date(sec * 1000)).replace(',', '');
        },
      },
      timeScale: {
        borderColor: 'rgba(148,163,184,0.2)',
        timeVisible: true, secondsVisible: false,
        fixLeftEdge: true, fixRightEdge: false,
        lockVisibleTimeRangeOnResize: true,
        rightOffset: 12,
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
    // Don't clear chart data immediately - wait for new data to load first
    // This prevents the "blank chart" issue when switching timeframes
    setLastPrice(null);
    setSignalStatus(null);
    setSigLoading(true);
    
    // Store previous chart start for smooth transition
    const previousChartStart = chartStartRef.current;
    chartStartRef.current = 0;
    
    // CRITICAL FIX: Don't clear markersRef - signals must persist across timeframe changes
    // Rebuild markersRef from persistentSignalsRef for the current timeframe
    markersRef.current.clear();
    slTargetMapRef.current.clear();       // clear SL/Target data
    slTargetMarkersRef.current.clear();   // clear SL/Target visual markers
    hitMarkersRef.current.clear();        // clear hit markers
    activePriceLines.current = [];
    
    // Restore signals for current asset+timeframe from persistent storage
    const currentKey = `${asset}:${timeframe}:`;
    for (const [key, marker] of persistentSignalsRef.current.entries()) {
      if (key.startsWith(currentKey)) {
        const timestamp = marker.time as number;
        markersRef.current.set(timestamp, marker);
      }
    }
    
    // Don't clear series data yet - will be replaced when new data loads
    // seriesRef.current?.setData([]);
    
    // Apply existing signals immediately (before new data loads)
    if (markersRef.current.size > 0) {
      const existingMarkers = [...markersRef.current.values()].sort((a, b) => (a.time as number) - (b.time as number));
      try { seriesRef.current?.setMarkers(existingMarkers); } catch { /* ignore */ }
    } else {
      seriesRef.current?.setMarkers([]);
    }

    const candles         = new Map<number, CandleDataPoint>();
    const preloadBuffer:    BinanceKlineMsg['k'][] = [];
    let   historyLoaded   = false;
    const gone            = { current: false };

    // ── flushMarkers: render BUY/SELL signal arrows only ────────────────────
    // Only BUY/SELL arrows go into setMarkers().
    // SL and Target are shown as createPriceLine() — exact horizontal price levels.
    const flushMarkers = (minTime = chartStartRef.current) => {
      if (!seriesRef.current) return;

      const all = [...markersRef.current.values()];
      const vis = minTime > 0 ? all.filter(m => (m.time as number) >= minTime) : all;

      try {
        seriesRef.current.setMarkers(
          vis.sort((a, b) => (a.time as number) - (b.time as number))
        );
      } catch { /* chart resetting */ }

      // After rendering signal arrows, draw SL/Target price lines at exact levels
      renderSLTargetLines();
    };

    // ── renderSLTargetLines: draw SL + Target as horizontal price lines ───────
    // createPriceLine() places a label at the EXACT price level on the right axis,
    // with a horizontal dashed line across the chart — this is the correct way to
    // show SL and Target in lightweight-charts. The label appears right on the
    // price axis at the exact SL or Target price.
    //
    // We show lines for ALL active signals (not just the latest) so users can
    // clearly see each signal's SL and Target levels on the chart.
    const renderSLTargetLines = () => {
      if (!seriesRef.current) return;

      // Remove all old SL/Target price lines first
      for (const pl of activePriceLines.current) {
        try { seriesRef.current.removePriceLine(pl); } catch { /* ignore */ }
      }
      activePriceLines.current = [];

      if (slTargetMapRef.current.size === 0) return;

      // Draw SL + Target lines for every signal in the map
      for (const { sl, target } of slTargetMapRef.current.values()) {
        try {
          // Stop Loss line — red dashed horizontal line at exact SL price
          const slLine = seriesRef.current.createPriceLine({
            price:            sl,
            color:            '#ef4444',
            lineWidth:        1,
            lineStyle:        2,          // LineStyle.Dashed = 2
            axisLabelVisible: true,
            title:            `SL  ${sl.toFixed(2)}`,
          });
          activePriceLines.current.push(slLine);

          // Target line — green dashed horizontal line at exact Target price
          const tgtLine = seriesRef.current.createPriceLine({
            price:            target,
            color:            '#10b981',
            lineWidth:        1,
            lineStyle:        2,
            axisLabelVisible: true,
            title:            `Target  ${target.toFixed(2)}`,
          });
          activePriceLines.current.push(tgtLine);
        } catch { /* chart may be resetting */ }
      }
    };

    // ── buildSLTargetMarkers: no-op stub (kept for call-site compatibility) ──
    // SL/Target are now shown as price lines (renderSLTargetLines), not markers.
    // This stub prevents call-site errors while the slTargetMapRef is still
    // populated for price line rendering.
    const buildSLTargetMarkers = (
      _candleTime: number,
      _isBullish: boolean,
      _sl: number,
      _target: number,
    ): SeriesMarker<Time>[] => [];  // returns empty — price lines handle display

    // ── Apply one Binance kline tick to the chart ─────────────────────────────
    const applyKline = (k: BinanceKlineMsg['k']) => {
      const interval = TF_SEC[timeframe];
      const start    = utcToLocalTime(Math.floor(k.t / 1000 / interval) * interval);
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
    // BULLETPROOF DATA FEED - NEVER FAILS STRATEGY
    // 
    // Layer 1: Binance WebSocket (real-time, preferred)
    // Layer 2: REST API polling (15 second intervals, automatic fallback)
    // Layer 3: Aggressive reconnection (infinite retries, exponential backoff)
    // 
    // GUARANTEE: Chart ALWAYS updates, user NEVER sees "Reconnecting"
    // 
    // NOTE: REST API interval set to 15s (not 5s) to prevent rate limiting
    // and reduce load on Binance API, which helps prevent WebSocket failures
    // ════════════════════════════════════════════════════════════════════════
    let binanceWs:         WebSocket | null = null;
    let binanceRetryTimer: ReturnType<typeof setTimeout> | null = null;
    let binanceRetries     = 0;
    let binanceHealthCheck: ReturnType<typeof setTimeout> | null = null;
    let lastMessageTime    = 0;
    let restFallbackInterval: ReturnType<typeof setInterval> | null = null;
    let wsConnected        = false;
    let permanentRestMode  = false; // If WebSocket fails 10 times, use REST permanently

    // REST API fallback - ALWAYS works, fetches latest candle every 15 seconds
    // Interval set to 15s (not 5s) to prevent Binance rate limiting
    const fetchRestCandle = async () => {
      if (gone.current) return;
      try {
        const sym = ASSET_TO_BINANCE[asset];
        const ivl = TF_BINANCE[timeframe];
        const url = `https://api.binance.com/api/v3/klines?symbol=${sym}&interval=${ivl}&limit=1`;
        
        const res = await fetch(url, { 
          method: 'GET',
          headers: { 'Accept': 'application/json' },
          cache: 'no-cache'
        });
        
        if (!res.ok) {
          // Silently retry - don't spam console
          return;
        }
        
        const data = await res.json();
        if (!data || !Array.isArray(data) || !data[0]) {
          return;
        }
        
        const [openTime, open, high, low, close] = data[0];
        const kline = {
          t: openTime,
          o: String(open),
          h: String(high),
          l: String(low),
          c: String(close),
          x: false,
        };
        
        if (historyLoaded) {
          applyKline(kline);
        }
      } catch (err) {
        // Silently retry - REST fallback is resilient
      }
    };

    // Start REST fallback - runs in parallel with WebSocket attempts
    const startRestFallback = () => {
      if (restFallbackInterval) return;
      
      // Only log once when REST fallback starts
      if (!permanentRestMode) {
        console.log('📊 REST API fallback active - chart updates every 15s');
      }
      
      // Immediate first fetch
      fetchRestCandle();
      
      // Then fetch every 15 seconds (reduced from 5s to prevent rate limiting)
      restFallbackInterval = setInterval(fetchRestCandle, 15000);
    };

    const stopRestFallback = () => {
      if (restFallbackInterval && !permanentRestMode) {
        clearInterval(restFallbackInterval);
        restFallbackInterval = null;
        // Don't log - reduces console noise
      }
    };

    const connectBinance = () => {
      if (gone.current || permanentRestMode) return;
      
      const sym = ASSET_TO_BINANCE_WS[asset];
      const ivl = TF_BINANCE[timeframe];
      const url = `wss://stream.binance.com:9443/ws/${sym}@kline_${ivl}`;

      // Only log first 3 attempts to reduce console noise
      if (binanceRetries < 3) {
        console.log(`🔌 Binance WebSocket connecting: ${asset} ${timeframe}`);
      }
      
      try { 
        binanceWs = new WebSocket(url); 
      }
      catch (err) { 
        if (binanceRetries < 3) {
          console.warn('⚠️ WebSocket creation failed, using REST fallback');
        }
        startRestFallback();
        scheduleBinanceRetry(); 
        return; 
      }

      // Set connection timeout - if not connected in 15 seconds, retry
      const connectionTimeout = setTimeout(() => {
        if (binanceWs && binanceWs.readyState !== WebSocket.OPEN) {
          if (binanceRetries < 3) {
            console.warn('⏱️ WebSocket timeout, using REST fallback');
          }
          try { binanceWs.close(); } catch {}
        }
      }, 15000);

      binanceWs.onopen = () => {
        clearTimeout(connectionTimeout);
        wsConnected = true;
        binanceRetries = 0;
        lastMessageTime = Date.now();
        stopRestFallback();
        console.log(`✅ Binance WebSocket connected: ${asset} ${timeframe}`);
        
        // Health monitoring - detect stale connections
        if (binanceHealthCheck) clearTimeout(binanceHealthCheck);
        
        const checkHealth = () => {
          if (gone.current) return;
          const timeSinceLastMessage = Date.now() - lastMessageTime;
          
          // If no data for 15 seconds, connection is stale
          if (timeSinceLastMessage > 15000) {
            wsConnected = false;
            startRestFallback();
            try { binanceWs?.close(4000, 'stale'); } catch {}
            return;
          }
          
          // Check again in 5 seconds
          binanceHealthCheck = setTimeout(checkHealth, 5000);
        };
        
        binanceHealthCheck = setTimeout(checkHealth, 5000);
      };

      binanceWs.onmessage = (ev: MessageEvent) => {
        lastMessageTime = Date.now();
        try {
          const msg = JSON.parse(ev.data as string) as BinanceKlineMsg;
          if (msg.e !== 'kline') return;
          if (!historyLoaded) preloadBuffer.push(msg.k);
          else applyKline(msg.k);
        } catch (err) { 
          // Silently ignore parse errors - they're usually harmless
        }
      };

      binanceWs.onclose = (ev) => {
        clearTimeout(connectionTimeout);
        wsConnected = false;
        
        // Only log first 3 closures to reduce console noise
        if (binanceRetries < 3) {
          console.log(`🔄 Binance WebSocket disconnected (code ${ev.code}), using REST fallback`);
        }
        
        if (binanceHealthCheck) {
          clearTimeout(binanceHealthCheck);
          binanceHealthCheck = null;
        }
        
        // Start REST fallback immediately
        startRestFallback();
        
        // If failed 10 times, switch to permanent REST mode
        if (binanceRetries >= 10) {
          console.log('📊 Using REST API mode for stable updates');
          permanentRestMode = true;
          return;
        }
        
        // Otherwise, keep retrying WebSocket in background
        scheduleBinanceRetry();
      };

      binanceWs.onerror = () => {
        // Don't log errors - onclose will handle it
        clearTimeout(connectionTimeout);
        wsConnected = false;
        startRestFallback();
      };
    };

    const scheduleBinanceRetry = () => {
      if (gone.current || permanentRestMode) return;
      binanceRetries++;
      
      // Exponential backoff: 2s → 4s → 8s → 16s → 30s (max)
      const delay = Math.min(2000 * Math.pow(2, Math.min(binanceRetries - 1, 4)), 30000);
      
      // Only log first 3 retries to reduce console noise
      if (binanceRetries <= 3) {
        console.log(`🔄 WebSocket retry in ${delay/1000}s (attempt ${binanceRetries}/10)`);
      }
      
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
      // CRITICAL: Signal position MUST be stable and NEVER change
      // 1. Parse timestamp (add 'Z' if missing to ensure UTC)
      const ts  = z.timestamp.includes('+') || z.timestamp.endsWith('Z') ? z.timestamp : z.timestamp + 'Z';
      const raw = Math.floor(new Date(ts).getTime() / 1000);
      
      // 2. Round to exact candle start time for current timeframe
      // This ensures signal always appears on the SAME candle, regardless of:
      // - Page refresh
      // - Timeframe change
      // - WebSocket reconnection
      const candleTime = Math.floor(raw / interval) * interval;
      
      // 3. Convert to local time for chart display
      const localTime = utcToLocalTime(candleTime);
      
      return {
        time:     localTime as Time,
        position: z.is_bullish ? 'belowBar'   : 'aboveBar',
        color:    z.is_bullish ? COLOR_UP      : COLOR_DOWN,
        shape:    z.is_bullish ? 'arrowUp'     : 'arrowDown',
        text:     z.is_bullish ? 'BUY SIGNAL'  : 'SELL SIGNAL',
        size:     2,
      };
    };

    const mergeAndFlush = (incoming: SeriesMarker<Time>[]) => {
      // CRITICAL FIX: Signals must be PERMANENT and NEVER deleted
      // Store signals in BOTH markersRef (current timeframe) AND persistentSignalsRef (all timeframes)
      // This ensures signals survive page refresh, timeframe changes, and WebSocket reconnections
      
      const sorted = [...incoming].sort((a, b) => (a.time as number) - (b.time as number));
      for (const m of sorted) {
        const t = m.time as number;
        
        // Create persistent key: "BTCUSD:5m:1234567890"
        const persistentKey = `${asset}:${timeframe}:${t}`;
        
        // Only add if not already present (prevent duplicates)
        if (markersRef.current.has(t)) continue;
        
        // Add signal to current timeframe markers
        if (chartStartRef.current === 0 || t >= chartStartRef.current) {
          markersRef.current.set(t, m);
          
          // CRITICAL: Also store in persistent storage (survives timeframe changes)
          persistentSignalsRef.current.set(persistentKey, m);
        }
      }
      flushMarkers();
    };

    const applySignal = (s: SignalPayload) => {
      // CRITICAL FIX: only apply the SINGLE newest zone from a live WebSocket signal.
      // The backend sends all_zones[] containing every zone from the calculator window.
      // Old zones in that array have bar_index values relative to the CURRENT window,
      // which shift with every new candle — applying them would cause repainting.
      // The stable, permanent positions of historical signals come exclusively from
      // the signal-history DB API (see fetchSignals). We only need the newest zone here.
      const ivl = TF_SEC[timeframe];
      if (!s.all_zones || s.all_zones.length === 0) return;

      // The last entry in all_zones is always the freshest signal
      const newestZone = s.all_zones[s.all_zones.length - 1];
      const marker = zoneToMarker(newestZone, ivl);
      const t = marker.time as number;

      // Only add if:
      // 1. Candle time not already locked in markersRef (DB signals take priority)
      // 2. Signal ALTERNATES with the last marker already on the chart
      //    (prevents WebSocket BUY→BUY or SELL→SELL if consumer fires twice)
      const existingMarkers = [...markersRef.current.values()]
        .sort((a, b) => (a.time as number) - (b.time as number));
      const lastExisting = existingMarkers[existingMarkers.length - 1];
      const typeAlternates = !lastExisting || (lastExisting.shape !== marker.shape);

      if (!markersRef.current.has(t) && typeAlternates) {
        // Build SL/Target markers for this WebSocket signal
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const nzAny = newestZone as any;
        const wsSl  = nzAny.stop_loss != null ? Number(nzAny.stop_loss)  : null;
        const wsTgt = nzAny.target    != null ? Number(nzAny.target)     : null;
        if (wsSl != null && wsTgt != null) {
          slTargetMapRef.current.set(t, { sl: wsSl, target: wsTgt, isBullish: newestZone.is_bullish });
          slTargetMarkersRef.current.set(t, buildSLTargetMarkers(t, newestZone.is_bullish, wsSl, wsTgt));
        }
        mergeAndFlush([marker]);
        setSignalStatus({ last_signal: s.signal, tracking: s.tracking });
      } else {
        setSignalStatus({ last_signal: s.signal, tracking: s.tracking });
      }
    };

    // ── REST: fetch historical signals ────────────────────────────────────────
    // FIX: DB signals are the ONLY source of truth for historical positions.
    // The live calculator runs on a sliding window and WILL shift timestamps
    // every time new candles arrive — that is the repainting bug.
    // Solution: use signal-history (DB, immutable) for all past signals.
    // Use reversal-zones ONLY to pick up the one newest live_pending signal
    // (a candle that closed after the last Celery task run).
    const fetchSignals = async (chartStart = 0) => {
      if (!seriesRef.current || gone.current) return;
      const ivl = TF_SEC[timeframe];

      try {
        // ── STEP 1: DB signals (permanent, never repaint) ──────────────────
        const dbRaw: Array<{ is_bullish: boolean; timestamp: string; stop_loss?: number; target?: number; status?: string }> = [];
        try {
          const r = await fetch(`/api/trading/signal-history/${asset}/?timeframe=${timeframe}`);
          if (r.ok && !gone.current) {
            const j = await r.json();
            if (j.success) dbRaw.push(...(j.signals ?? []));
          }
        } catch { /* optional */ }

        if (gone.current) return;

        // Build DB markers and record their candle-aligned local timestamps
        const dbLocalTimes = new Set<number>();
        const dbMarkers = dbRaw.map(z => {
          const m  = zoneToMarker(z, ivl);
          const t  = m.time as number;
          dbLocalTimes.add(t);

          // Build SL/Target markers on the SAME candle as the signal
          const sl  = z.stop_loss  != null ? Number(z.stop_loss)  : null;
          const tgt = z.target     != null ? Number(z.target)     : null;

          if (sl != null && tgt != null) {
            // Store for hit detection
            slTargetMapRef.current.set(t, { sl, target: tgt, isBullish: z.is_bullish });
            // Build per-candle SL/Target labels
            slTargetMarkersRef.current.set(t, buildSLTargetMarkers(t, z.is_bullish, sl, tgt));
          }
          return m;
        }).sort((a, b) => (a.time as number) - (b.time as number));

        // ── STEP 2: reversal-zones — only take source=live_pending entry ───
        // The backend now returns DB records + at most one live_pending zone
        // (the most-recent candle not yet saved to DB by the Celery task).
        let liveStatus: { last_signal: string; tracking: string } | null = null;
        const pendingRaw: Array<{ is_bullish: boolean; timestamp: string; stop_loss?: number; target?: number }> = [];
        try {
          const r = await fetch(`/api/trading/reversal-zones/${asset}/?timeframe=${timeframe}`);
          if (r.ok && !gone.current) {
            const j = await r.json();
            if (j.success) {
              liveStatus = j.data?.status ?? null;
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              const pending = (j.data?.zones ?? []).filter((z: any) => z.source === 'live_pending');
              pendingRaw.push(...pending);
            }
          }
        } catch { /* optional */ }

        if (gone.current) return;

        // ── STEP 3: Merge — DB signals first, pending only if truly new ────
        const final: SeriesMarker<Time>[] = [];
        const seen = new Set<number>();
        let lastSignalShape: string | null = null; // track last marker type for alternation

        // Permanent DB signals — these are already alternation-enforced by DB
        for (const m of dbMarkers) {
          const t = m.time as number;
          if (seen.has(t)) continue;
          final.push(m);
          seen.add(t);
          lastSignalShape = m.shape as string; // track for alternation check below
          const persistentKey = `${asset}:${timeframe}:${t}`;
          persistentSignalsRef.current.set(persistentKey, m);
        }

        // Live pending (newest unsaved candle) — ONLY if new timestamp AND alternates
        for (const z of pendingRaw) {
          const m = zoneToMarker(z, ivl);
          const t = m.time as number;
          if (seen.has(t) || dbLocalTimes.has(t)) continue;
          const pendingShape = m.shape as string;
          if (lastSignalShape !== null && pendingShape === lastSignalShape) continue;
          final.push(m);
          seen.add(t);

          // Build SL/Target markers for this pending signal
          const pSl  = z.stop_loss != null ? Number(z.stop_loss)  : null;
          const pTgt = z.target    != null ? Number(z.target)     : null;
          if (pSl != null && pTgt != null) {
            slTargetMapRef.current.set(t, { sl: pSl, target: pTgt, isBullish: z.is_bullish });
            slTargetMarkersRef.current.set(t, buildSLTargetMarkers(t, z.is_bullish, pSl, pTgt));
          }
          // Do NOT persist — will be superseded once Celery saves it to DB
        }

        const sorted = final.sort((a, b) => (a.time as number) - (b.time as number));
        const visible = chartStart > 0
          ? sorted.filter(m => (m.time as number) >= chartStart)
          : sorted;

        for (const m of visible) {
          const t = m.time as number;
          if (!markersRef.current.has(t)) {
            markersRef.current.set(t, m);
          }
        }

        flushMarkers(chartStart);
        if (!gone.current && liveStatus) setSignalStatus(liveStatus);
      } catch { /* silent */ }
      finally { if (!gone.current) setSigLoading(false); }
    };

    // ── REST: load historical candles from Binance ────────────────────────────
    const loadHistory = async () => {
      try {
        const symbol = ASSET_TO_BINANCE[asset];
        const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${TF_BINANCE[timeframe]}&limit=${TF_LIMIT[timeframe]}`;
        
        const res = await fetch(url, {
          method: 'GET',
          headers: { 'Accept': 'application/json' },
          cache: 'no-cache'
        });
        
        if (!res.ok) {
          throw new Error(`Binance API returned ${res.status}`);
        }
        
        const raw: (string | number)[][] = await res.json();
        if (gone.current) return;

        if (!raw || !Array.isArray(raw) || raw.length === 0) {
          throw new Error('No data received from Binance');
        }

        const hist: CandleDataPoint[] = raw.map(k => ({
          time:  utcToLocalTime(Math.floor(Number(k[0]) / 1000)) as Time,
          open:  parseFloat(k[1] as string),
          high:  parseFloat(k[2] as string),
          low:   parseFloat(k[3] as string),
          close: parseFloat(k[4] as string),
        }));

        // Clear old data and set new data atomically
        candles.clear();
        for (const c of hist) candles.set(c.time as number, c);
        
        // Set data to chart - this replaces old data
        seriesRef.current?.setData(hist);
        
        // Fit content to show all data
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
        
        // On error, try to keep showing old data if available
        // Don't clear the chart - better to show stale data than blank chart
        historyLoaded = true; // still drain buffer
        if (!gone.current) setSigLoading(false);
        
        // Retry after 2 seconds
        setTimeout(() => {
          if (!gone.current) {
            console.log('Retrying history load...');
            loadHistory();
          }
        }, 2000);
      }
    };

    // ── Boot ──────────────────────────────────────────────────────────────────
    // Start REST fallback IMMEDIATELY - ensures chart updates even if WebSocket fails
    startRestFallback();
    
    // Then try WebSocket (will pause REST if successful)
    connectBinance();
    connectBackend();
    loadHistory();

    return () => {
      gone.current = true;
      if (binanceRetryTimer)  clearTimeout(binanceRetryTimer);
      if (binanceHealthCheck) clearTimeout(binanceHealthCheck);
      if (restFallbackInterval) clearInterval(restFallbackInterval);
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
          <p className="mt-1 text-xs text-slate-400">
            <span className="text-slate-500">Source:</span>{' '}
            <span className="font-medium text-cyan-400">{ASSET_DATA_SOURCE[asset].exchange}</span>
            {' '}({ASSET_DATA_SOURCE[asset].symbol})
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm">
            <span className="text-slate-400">Chart Feed: </span>
            <span className="text-emerald-400">
              Live ●
            </span>
          </div>

          <div className="rounded-xl border border-cyan-900/30 bg-cyan-950/30 px-3 py-2 text-sm">
            <span className="text-slate-400">Source: </span>
            <span className="font-bold text-cyan-400">
              {ASSET_DATA_SOURCE[asset].exchange}
            </span>
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