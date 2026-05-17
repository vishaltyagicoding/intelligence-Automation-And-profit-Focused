'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import { getWebSocketUrl } from '@/lib/config';
import ChartComponent, { type DataSourceType, type Timeframe, type WatchlistAsset } from '../../components/ChartComponent';
import Watchlist from '../../components/Watchlist';

const ASSETS: WatchlistAsset[] = ['BTCUSD', 'ETHUSD', 'XAUUSD', 'LTCUSD'];
type PriceMap = Record<WatchlistAsset, number | null>;

// ─── Bitstamp ticker REST ─────────────────────────────────────────────────────
const BS_REST: Record<WatchlistAsset, string | null> = {
  BTCUSD: 'btcusd', ETHUSD: 'ethusd', LTCUSD: 'ltcusd', XAUUSD: null,
};

// ─── Binance combined mini-ticker ─────────────────────────────────────────────
const BN_WS_SYM: Record<WatchlistAsset, string> = {
  BTCUSD: 'btcusdt', ETHUSD: 'ethusdt', XAUUSD: 'paxgusdt', LTCUSD: 'ltcusdt',
};
const BN_SYM_TO_ASSET: Record<string, WatchlistAsset> = {
  BTCUSDT: 'BTCUSD', ETHUSDT: 'ETHUSD', PAXGUSDT: 'XAUUSD', LTCUSDT: 'LTCUSD',
};
const BINANCE_COMBINED =
  `wss://stream.binance.com:9443/stream?streams=${ASSETS.map(a => `${BN_WS_SYM[a]}@miniTicker`).join('/')}`;

interface MiniTicker { s: string; c: string; }

// ─── Source options ───────────────────────────────────────────────────────────
interface SourceOption {
  value: DataSourceType;
  cryptoLabel: string;   // label for BTC/ETH/LTC
  xauLabel: string;      // label for XAU/USD
  description: string;
}
const SOURCE_OPTIONS: SourceOption[] = [
  {
    value: 'bitstamp',
    cryptoLabel: 'BITSTAMP',
    xauLabel: 'FOREXCOM',
    description: 'Bitstamp (crypto) · FOREXCOM (gold) — matches TradingView default prices',
  },
  {
    value: 'binance',
    cryptoLabel: 'BINANCE',
    xauLabel: 'OANDA',
    description: 'Binance (crypto) · OANDA (gold) — highest liquidity crypto exchange',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, loading, user } = useAuth();

  const [selectedAsset,     setSelectedAsset]     = useState<WatchlistAsset>('BTCUSD');
  const [selectedTimeframe, setSelectedTimeframe] = useState<Timeframe>('15m');
  const [dataSource,        setDataSource]        = useState<DataSourceType>('bitstamp');
  const [prices,            setPrices]            = useState<PriceMap>({
    BTCUSD: null, ETHUSD: null, XAUUSD: null, LTCUSD: null,
  });

  const wsBaseUrl  = useMemo(() => getWebSocketUrl(), []);
  const mountedRef = useRef(true);

  // ── Route guards ────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!loading && !isAuthenticated) router.push('/login');
  }, [isAuthenticated, loading, router]);

  useEffect(() => {
    if (!loading && isAuthenticated && user) {
      const sub = user.subscription_status;
      if (sub && !sub.is_active && user.manual_subscription !== 'activated')
        router.push('/subscription');
    }
  }, [isAuthenticated, loading, user, router]);

  useEffect(() => () => { mountedRef.current = false; }, []);

  // ── Watchlist prices: Bitstamp source ─────────────────────────────────────
  useEffect(() => {
    if (!isAuthenticated || dataSource !== 'bitstamp') return;

    let cleaned = false;
    const sockets: WebSocket[] = [];
    const retryTimers: ReturnType<typeof setTimeout>[] = [];

    // Fetch initial REST prices for BTC/ETH/LTC from Bitstamp
    ASSETS.forEach(async asset => {
      const pair = BS_REST[asset];
      if (!pair) return; // XAU handled separately
      try {
        const r = await fetch(`https://www.bitstamp.net/api/v2/ticker/${pair}/`);
        const d = await r.json();
        if (d.last && mountedRef.current) {
          setPrices(prev => ({ ...prev, [asset]: parseFloat(d.last) }));
        }
      } catch { /* non-fatal */ }
    });

    // Live WebSocket for BTC/ETH/LTC via Bitstamp live_trades
    ASSETS.forEach(asset => {
      const pair = BS_REST[asset];
      if (!pair) return; // skip XAU

      let retries = 0;
      const connect = () => {
        if (cleaned) return;
        const ws = new WebSocket('wss://ws.bitstamp.net');
        sockets.push(ws);

        ws.onopen = () => {
          retries = 0;
          ws.send(JSON.stringify({ event: 'bts:subscribe', data: { channel: `live_trades_${pair}` } }));
        };

        ws.onmessage = (ev: MessageEvent<string>) => {
          try {
            const msg = JSON.parse(ev.data) as Record<string, unknown>;
            if (msg.event !== 'trade') return;
            const d = msg.data as Record<string, unknown>;
            const price = parseFloat(d.price_str as string || String(d.price));
            if (Number.isFinite(price) && mountedRef.current)
              setPrices(prev => prev[asset] === price ? prev : { ...prev, [asset]: price });
          } catch { /* ignore */ }
        };

        ws.onclose = () => {
          if (cleaned) return;
          retries++;
          const t = setTimeout(connect, Math.min(1000 * Math.pow(2, Math.min(retries - 1, 3)), 10_000));
          retryTimers.push(t);
        };
        ws.onerror = () => { /* onclose fires */ };
      };
      connect();
    });

    // XAU/USD price via backend proxy (FOREXCOM = Yahoo Finance GC=F)
    let xauTimer: ReturnType<typeof setInterval> | null = null;
    const pollXau = async () => {
      if (cleaned) return;
      try {
        const r = await fetch('/api/market/xau-price/?source=forexcom');
        const d = await r.json();
        if (d.success && d.price > 0 && mountedRef.current)
          setPrices(prev => ({ ...prev, XAUUSD: d.price as number }));
      } catch { /* non-fatal */ }
    };
    pollXau();
    xauTimer = setInterval(pollXau, 10_000);

    return () => {
      cleaned = true;
      retryTimers.forEach(clearTimeout);
      if (xauTimer) clearInterval(xauTimer);
      sockets.forEach(ws => { try { ws.close(); } catch { /* ignore */ } });
    };
  }, [isAuthenticated, dataSource]);

  // ── Watchlist prices: Binance source ──────────────────────────────────────
  useEffect(() => {
    if (!isAuthenticated || dataSource !== 'binance') return;

    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let retries = 0;
    let cleaned = false;
    let xauTimer: ReturnType<typeof setInterval> | null = null;

    // Initial REST prices
    ASSETS.forEach(async asset => {
      if (asset === 'XAUUSD') return;
      try {
        const r = await fetch(`https://api.binance.com/api/v3/ticker/price?symbol=${BN_WS_SYM[asset].toUpperCase()}`);
        const d = await r.json();
        if (d.price && mountedRef.current)
          setPrices(prev => ({ ...prev, [asset]: parseFloat(d.price) }));
      } catch { /* non-fatal */ }
    });

    // Combined Binance mini-ticker WebSocket
    const connect = () => {
      if (cleaned) return;
      try { ws = new WebSocket(BINANCE_COMBINED); } catch { schedRetry(); return; }

      ws.onopen = () => { retries = 0; };
      ws.onmessage = (ev: MessageEvent<string>) => {
        try {
          const msg = JSON.parse(ev.data) as { stream: string; data: MiniTicker };
          const sym   = msg.data?.s?.toUpperCase();
          const price = parseFloat(msg.data?.c ?? '');
          const asset = BN_SYM_TO_ASSET[sym];
          if (!asset || !Number.isFinite(price)) return;
          if (mountedRef.current)
            setPrices(prev => prev[asset] === price ? prev : { ...prev, [asset]: price });
        } catch { /* ignore */ }
      };
      ws.onclose = () => { if (!cleaned) schedRetry(); };
      ws.onerror = () => { /* onclose fires */ };
    };

    const schedRetry = () => {
      if (cleaned) return;
      retries++;
      retryTimer = setTimeout(connect, Math.min(1000 * Math.pow(2, Math.min(retries - 1, 3)), 10_000));
    };

    connect();

    // XAU/USD via backend proxy (OANDA = Yahoo Finance XAUUSD=X)
    const pollXau = async () => {
      if (cleaned) return;
      try {
        const r = await fetch('/api/market/xau-price/?source=oanda');
        const d = await r.json();
        if (d.success && d.price > 0 && mountedRef.current)
          setPrices(prev => ({ ...prev, XAUUSD: d.price as number }));
      } catch { /* non-fatal */ }
    };
    pollXau();
    xauTimer = setInterval(pollXau, 10_000);

    return () => {
      cleaned = true;
      if (retryTimer) clearTimeout(retryTimer);
      if (xauTimer)   clearInterval(xauTimer);
      try { ws?.close(); } catch { /* ignore */ }
    };
  }, [isAuthenticated, dataSource]);

  // ── Chart price update → keep watchlist in sync ───────────────────────────
  const handleChartPrice = useCallback((asset: WatchlistAsset, price: number) => {
    if (!mountedRef.current) return;
    setPrices(prev => prev[asset] === price ? prev : { ...prev, [asset]: price });
  }, []);

  // ── Loading / auth guards ─────────────────────────────────────────────────
  if (loading) return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="text-center">
        <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent" />
        <p className="mt-4 text-slate-400">Loading…</p>
      </div>
    </div>
  );
  if (!isAuthenticated) return null;

  // ── Render ────────────────────────────────────────────────────────────────
  const activeSource = SOURCE_OPTIONS.find(s => s.value === dataSource)!;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="mx-auto max-w-[1800px] px-4 py-6">

        {/* ── Data Source Switcher ── */}
        <div className="mb-5 rounded-2xl border border-slate-800 bg-slate-900/60 px-5 py-4">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Data Source</p>
              <p className="mt-0.5 text-xs text-slate-500">{activeSource.description}</p>
            </div>
            <div className="flex gap-2 ml-auto">
              {SOURCE_OPTIONS.map(opt => {
                const isActive = dataSource === opt.value;
                const cryptoLbl = opt.cryptoLabel;
                const xauLbl    = opt.xauLabel;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setDataSource(opt.value)}
                    className={`rounded-xl border px-4 py-2.5 text-left transition-all ${
                      isActive
                        ? 'border-cyan-500/60 bg-cyan-500/15 shadow-md shadow-cyan-500/20'
                        : 'border-slate-700 bg-slate-800/60 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {isActive && <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />}
                      <span className={`text-xs font-bold ${isActive ? 'text-cyan-300' : 'text-slate-300'}`}>
                        {cryptoLbl}
                      </span>
                      <span className="text-slate-600">·</span>
                      <span className={`text-xs font-bold ${isActive ? 'text-yellow-300' : 'text-slate-400'}`}>
                        {xauLbl}
                      </span>
                    </div>
                    <p className="mt-0.5 text-[10px] text-slate-500">
                      {opt.value === 'bitstamp' ? 'Default (matches TradingView)' : 'Alternative source'}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Source details row */}
          <div className="mt-3 flex flex-wrap gap-3 text-xs">
            {(['BTCUSD','ETHUSD','LTCUSD'] as WatchlistAsset[]).map(a => (
              <span key={a} className="rounded-lg bg-slate-800 px-2.5 py-1 text-slate-400">
                <span className="font-semibold text-white">{a}</span>
                {' → '}
                <span className="text-cyan-300">{activeSource.cryptoLabel}</span>
              </span>
            ))}
            <span className="rounded-lg bg-slate-800 px-2.5 py-1 text-slate-400">
              <span className="font-semibold text-white">XAUUSD</span>
              {' → '}
              <span className="text-yellow-300">{activeSource.xauLabel}</span>
            </span>
          </div>
        </div>

        {/* ── Main grid ── */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <aside className="lg:col-span-3">
            <Watchlist
              assets={ASSETS}
              prices={prices}
              selectedAsset={selectedAsset}
              onSelectAsset={setSelectedAsset}
              subscriptionActive={true}
            />
          </aside>

          <main className="lg:col-span-9">
            <ChartComponent
              asset={selectedAsset}
              aiSignals={[]}
              subscriptionActive={true}
              wsBaseUrl={wsBaseUrl}
              timeframe={selectedTimeframe}
              onTimeframeChange={setSelectedTimeframe}
              showFullDashboardButton={true}
              onPriceUpdate={handleChartPrice}
              dataSource={dataSource}
            />
          </main>
        </div>
      </div>
    </div>
  );
}