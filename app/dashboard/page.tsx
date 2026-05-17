'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import { getWebSocketUrl } from '@/lib/config';
import ChartComponent, { type Timeframe, type WatchlistAsset } from '../../components/ChartComponent';
import Watchlist from '../../components/Watchlist';

const WATCHLIST_ASSETS: WatchlistAsset[] = ['BTCUSD', 'ETHUSD', 'XAUUSD', 'LTCUSD'];

type WatchlistPriceMap = Record<WatchlistAsset, number | null>;

// Lowercase Binance stream names for each asset
const ASSET_TO_BINANCE_WS: Record<WatchlistAsset, string> = {
  BTCUSD: 'btcusdt',
  ETHUSD: 'ethusdt',
  XAUUSD: 'paxgusdt',
  LTCUSD: 'ltcusdt',
};

// Map Binance uppercase symbol back to our asset key
const BINANCE_SYMBOL_TO_ASSET: Record<string, WatchlistAsset> = {
  BTCUSDT:  'BTCUSD',
  ETHUSDT:  'ETHUSD',
  PAXGUSDT: 'XAUUSD',
  LTCUSDT:  'LTCUSD',
};

// REST symbols for initial price fetch
const ASSET_TO_BINANCE_REST: Record<WatchlistAsset, string> = {
  BTCUSD: 'BTCUSDT',
  ETHUSD: 'ETHUSDT',
  XAUUSD: 'PAXGUSDT',
  LTCUSD: 'LTCUSDT',
};

// ─── Combined mini-ticker stream URL ─────────────────────────────────────────
// One WebSocket → all 4 asset prices simultaneously.
// Binance sends a tick every ~1 second per symbol → prices can never get stuck.
// Completely bypasses backend / nginx / Redis / Django for price data.
const COMBINED_TICKER_URL =
  `wss://stream.binance.com:9443/stream?streams=${
    WATCHLIST_ASSETS.map(a => `${ASSET_TO_BINANCE_WS[a]}@miniTicker`).join('/')
  }`;

interface MiniTickerData {
  e: string;   // "24hrMiniTicker"
  s: string;   // "BTCUSDT"
  c: string;   // current/close price
}

interface CombinedStreamMsg {
  stream: string;
  data: MiniTickerData;
}

export default function Page() {
  const router                = useRouter();
  const { isAuthenticated, loading, user } = useAuth();

  const [selectedAsset,    setSelectedAsset]    = useState<WatchlistAsset>('BTCUSD');
  const [selectedTimeframe, setSelectedTimeframe] = useState<Timeframe>('15m');
  const [watchlistPrices,  setWatchlistPrices]  = useState<WatchlistPriceMap>({
    BTCUSD: null, ETHUSD: null, XAUUSD: null, LTCUSD: null,
  });
  const [marketConnected, setMarketConnected] = useState<boolean | null>(null);

  const wsBaseUrl = useMemo(() => getWebSocketUrl(), []);

  // Track whether cleanup has run so async callbacks don't set state after unmount
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

  useEffect(() => {
    return () => { mountedRef.current = false; };
  }, []);

  // ── Fetch initial prices from Binance REST (instant first paint) ────────────
  useEffect(() => {
    if (!isAuthenticated) return;

    (async () => {
      for (const asset of WATCHLIST_ASSETS) {
        try {
          const symbol = ASSET_TO_BINANCE_REST[asset];
          const res    = await fetch(`https://api.binance.com/api/v3/ticker/price?symbol=${symbol}`);
          const data   = await res.json();
          if (data.price && mountedRef.current) {
            setWatchlistPrices(prev => ({ ...prev, [asset]: parseFloat(data.price) }));
          }
        } catch { /* non-fatal */ }
      }
    })();
  }, [isAuthenticated]);

  // ════════════════════════════════════════════════════════════════════════════
  // BINANCE COMBINED MINI-TICKER — single WebSocket for all 4 watchlist prices
  //
  // One connection delivers all 4 prices every ~1 second directly from Binance.
  // No backend, no nginx, no Redis in the path — prices can NEVER get stuck.
  //
  // If this connection drops, it reconnects with exponential backoff (no cap on
  // attempts) and restores all 4 prices automatically without a page refresh.
  // ════════════════════════════════════════════════════════════════════════════
  useEffect(() => {
    if (!isAuthenticated) return;

    let ws:         WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let retryCount  = 0;
    let cleanedUp   = false;

    const connect = () => {
      if (cleanedUp) return;

      try { ws = new WebSocket(COMBINED_TICKER_URL); }
      catch { scheduleRetry(); return; }

      ws.onopen = () => {
        retryCount = 0;
        if (mountedRef.current) setMarketConnected(true);
        console.log('✅ Binance combined ticker WS connected');
      };

      ws.onmessage = (ev: MessageEvent<string>) => {
        try {
          const msg    = JSON.parse(ev.data) as CombinedStreamMsg;
          const symbol = msg.data?.s?.toUpperCase();     // e.g. "BTCUSDT"
          const price  = parseFloat(msg.data?.c ?? '');  // current price

          if (!symbol || !Number.isFinite(price)) return;

          const asset = BINANCE_SYMBOL_TO_ASSET[symbol];
          if (!asset) return;

          if (mountedRef.current) {
            setWatchlistPrices(prev => {
              if (prev[asset] === price) return prev;  // skip no-op updates
              return { ...prev, [asset]: price };
            });
          }
        } catch { /* ignore bad frames */ }
      };

      ws.onclose = () => {
        if (mountedRef.current) setMarketConnected(false);
        scheduleRetry();
      };

      ws.onerror = () => {
        if (mountedRef.current) setMarketConnected(false);
        // onclose fires next
      };
    };

    const scheduleRetry = () => {
      if (cleanedUp) return;
      retryCount++;
      // Backoff: 1s → 2s → 4s → 8s → 10s (cap) — retries forever, no attempt limit
      const delay = Math.min(1000 * Math.pow(2, Math.min(retryCount - 1, 3)), 10_000);
      console.log(`Binance ticker WS retry in ${delay}ms (#${retryCount})`);
      retryTimer = setTimeout(connect, delay);
    };

    connect();

    return () => {
      cleanedUp = true;
      if (retryTimer) clearTimeout(retryTimer);
      try { ws?.close(); } catch { /* ignore */ }
    };
  }, [isAuthenticated]);

  // ── onPriceUpdate from ChartComponent ─────────────────────────────────────
  // The chart connects directly to Binance for candle data and fires this on
  // every tick. For the selected asset, this slightly overrides the mini-ticker
  // price to use the exact kline close — ensures "Price:" header and watchlist
  // always display the identical number.
  const handleChartPriceUpdate = useCallback(
    (asset: WatchlistAsset, price: number) => {
      if (!mountedRef.current) return;
      setWatchlistPrices(prev => {
        if (prev[asset] === price) return prev;
        return { ...prev, [asset]: price };
      });
    },
    []
  );

  // ── Loading / auth guards ───────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent" />
          <p className="mt-4 text-slate-400">Loading…</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="mx-auto max-w-[1800px] px-4 py-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">

          <aside className="lg:col-span-3">
            <Watchlist
              assets={WATCHLIST_ASSETS}
              prices={watchlistPrices}
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
              onPriceUpdate={handleChartPriceUpdate}
            />
          </main>

        </div>
      </div>
    </div>
  );
}