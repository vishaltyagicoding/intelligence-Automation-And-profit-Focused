'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import { getWebSocketUrl } from '@/lib/config';
import ChartComponent, { type Timeframe, type WatchlistAsset } from '../../components/ChartComponent';
import Watchlist from '../../components/Watchlist';

const WATCHLIST_ASSETS: WatchlistAsset[] = ['BTCUSD', 'ETHUSD', 'XAUUSD', 'LTCUSD'];

type WatchlistPriceMap = Record<WatchlistAsset, number | null>;
type MarketSocketMessage = { price?: number | string; type?: string };

// ── Asset → Binance symbol map (binance.com — same as the chart component) ──
// CRITICAL: Must use binance.com (not binance.us) to match the chart prices.
// The chart fetches history from api.binance.com so using binance.us here
// caused a permanent ~$8 price difference on BTCUSD between the two displays.
const ASSET_TO_BINANCE: Record<WatchlistAsset, string> = {
  BTCUSD: 'BTCUSDT',
  ETHUSD: 'ETHUSDT',
  XAUUSD: 'PAXGUSDT',
  LTCUSD: 'LTCUSDT',
};

export default function Page() {
  const router = useRouter();
  const { isAuthenticated, loading, user } = useAuth();

  const [selectedAsset, setSelectedAsset] = useState<WatchlistAsset>('BTCUSD');
  const [selectedTimeframe, setSelectedTimeframe] = useState<Timeframe>('15m');
  const [watchlistPrices, setWatchlistPrices] = useState<WatchlistPriceMap>({
    BTCUSD: null,
    ETHUSD: null,
    XAUUSD: null,
    LTCUSD: null,
  });
  const [marketConnected, setMarketConnected] = useState<boolean | null>(null);

  const wsBaseUrl = useMemo(() => getWebSocketUrl(), []);

  // ── ALL HOOKS BEFORE EARLY RETURNS ──────────────────────────────────────────

  // Protect route
  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, router]);

  // Check subscription status
  useEffect(() => {
    if (!loading && isAuthenticated && user) {
      const subscriptionStatus = user.subscription_status;
      if (subscriptionStatus && !subscriptionStatus.is_active && user.manual_subscription !== 'activated') {
        router.push('/subscription');
      }
    }
  }, [isAuthenticated, loading, user, router]);

  // ── Fetch initial prices via Binance.com REST (same source as the chart) ────
  // Using binance.com (not binance.us) ensures the initial price matches what
  // the chart will display — previously binance.us caused an ~$8 discrepancy.
  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchInitialPrices = async () => {
      for (const asset of WATCHLIST_ASSETS) {
        try {
          const symbol = ASSET_TO_BINANCE[asset];
          // binance.com — same exchange as ChartComponent's history fetch
          const res = await fetch(`https://api.binance.com/api/v3/ticker/price?symbol=${symbol}`);
          const data = await res.json();
          if (data.price) {
            setWatchlistPrices((prev) => ({ ...prev, [asset]: parseFloat(data.price) }));
          }
        } catch (error) {
          console.error(`Failed to fetch initial price for ${asset}:`, error);
        }
      }
    };

    fetchInitialPrices();
  }, [isAuthenticated]);

  // ── onPriceUpdate: called by ChartComponent on every new live price tick ───
  // This is how the watchlist price for the SELECTED asset always stays in sync
  // with the chart's "Price:" display — they now share the exact same value.
  const handleChartPriceUpdate = useCallback(
    (asset: WatchlistAsset, price: number) => {
      setWatchlistPrices((prev) => {
        // Only update if price actually changed (avoids unnecessary re-renders)
        if (prev[asset] === price) return prev;
        return { ...prev, [asset]: price };
      });
    },
    []
  );

  // ── WebSocket connections for all watchlist assets (1m candle feed) ─────────
  // All 4 assets get a live 1m price feed here.
  // For the selected asset, onPriceUpdate from ChartComponent fires on every
  // chart tick and overwrites this value — so the chart header and watchlist
  // always converge to the same number within milliseconds.
  useEffect(() => {
    if (!isAuthenticated) return;

    // Map of asset → { socket, reconnectAttempts, retryTimer }
    const connections: Map<WatchlistAsset, {
      socket: WebSocket | null;
      retryTimer: ReturnType<typeof setTimeout> | null;
    }> = new Map();

    let cleanedUp = false;

    const connectAsset = (asset: WatchlistAsset) => {
      if (cleanedUp) return;

      // Close any existing socket for this asset
      const existing = connections.get(asset);
      if (existing?.socket) {
        try { existing.socket.close(); } catch { /* ignore */ }
      }
      if (existing?.retryTimer) clearTimeout(existing.retryTimer);

      const conn = { socket: null as WebSocket | null, retryTimer: null as ReturnType<typeof setTimeout> | null };
      connections.set(asset, conn);

      let attempts = 0;

      const createSocket = () => {
        if (cleanedUp) return;

        const ws = new WebSocket(`${wsBaseUrl}/ws/market/${asset}/1m/`);
        conn.socket = ws;

        ws.onopen = () => {
          attempts = 0;
          setMarketConnected(true);
        };

        ws.onmessage = (event: MessageEvent<string>) => {
          try {
            const payload = JSON.parse(event.data) as MarketSocketMessage;
            if (payload.type === 'ping') {
              ws.send(JSON.stringify({ action: 'pong' }));
              return;
            }
            const priceValue =
              typeof payload.price === 'string'
                ? parseFloat(payload.price)
                : payload.price;
            if (typeof priceValue === 'number' && Number.isFinite(priceValue)) {
              setWatchlistPrices((prev) => {
                if (prev[asset] === priceValue) return prev;
                return { ...prev, [asset]: priceValue };
              });
            }
          } catch (error) {
            console.error(`Error parsing market data for ${asset}:`, error);
          }
        };

        ws.onclose = () => {
          if (cleanedUp) return;
          setMarketConnected(false);
          // Reconnect with exponential backoff — no maximum attempt cap
          attempts++;
          const delay = Math.min(1000 * Math.pow(2, Math.min(attempts - 1, 4)), 10_000);
          conn.retryTimer = setTimeout(createSocket, delay);
        };

        ws.onerror = () => {
          setMarketConnected(false);
        };
      };

      createSocket();
    };

    WATCHLIST_ASSETS.forEach(connectAsset);

    return () => {
      cleanedUp = true;
      connections.forEach(({ socket, retryTimer }) => {
        if (retryTimer) clearTimeout(retryTimer);
        if (socket) try { socket.close(); } catch { /* ignore */ }
      });
      connections.clear();
    };
  }, [wsBaseUrl, isAuthenticated]);

  // ── EARLY RETURNS AFTER ALL HOOKS ───────────────────────────────────────────

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent"></div>
          <p className="mt-4 text-slate-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  // ── RENDER ───────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="mx-auto max-w-[1800px] px-4 py-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Watchlist Sidebar */}
          <aside className="lg:col-span-3">
            <Watchlist
              assets={WATCHLIST_ASSETS}
              prices={watchlistPrices}
              selectedAsset={selectedAsset}
              onSelectAsset={setSelectedAsset}
              subscriptionActive={true}
            />
          </aside>

          {/* Chart */}
          <main className="lg:col-span-9">
            <ChartComponent
              asset={selectedAsset}
              aiSignals={[]}
              subscriptionActive={true}
              wsBaseUrl={wsBaseUrl}
              timeframe={selectedTimeframe}
              onTimeframeChange={setSelectedTimeframe}
              showFullDashboardButton={true}
              // KEY FIX: Every price tick from the chart updates the watchlist
              // price for that asset so "Price:" header and watchlist always match.
              onPriceUpdate={handleChartPriceUpdate}
            />
          </main>
        </div>
      </div>
    </div>
  );
}