'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import { getWebSocketUrl } from '@/lib/config';
import ChartComponent, { type Timeframe, type WatchlistAsset } from '../../components/ChartComponent';
import Watchlist from '../../components/Watchlist';

const WATCHLIST_ASSETS: WatchlistAsset[] = ['BTCUSD', 'ETHUSD', 'XAUUSD', 'LTCUSD'];

type WatchlistPriceMap = Record<WatchlistAsset, number | null>;
type MarketSocketMessage = { price?: number | string; type?: string };

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

  // Protect route - redirect to login if not authenticated
  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, router]);

  // Check subscription status - redirect to subscription if expired
  useEffect(() => {
    if (!loading && isAuthenticated && user) {
      const subscriptionStatus = user.subscription_status;
      
      // If subscription exists and is not active, redirect to subscription page
      if (subscriptionStatus && !subscriptionStatus.is_active && user.manual_subscription !== 'activated') {
        router.push('/subscription');
      }
    }
  }, [isAuthenticated, loading, user, router]);

  // Fetch initial prices immediately via REST API (no waiting for WebSocket)
  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchInitialPrices = async () => {
      const ASSET_TO_BINANCE: Record<string, string> = {
        'XAUUSD': 'PAXGUSDT',
      };

      for (const asset of WATCHLIST_ASSETS) {
        try {
          const symbol = ASSET_TO_BINANCE[asset] ?? asset.replace('USD', 'USDT');
          const res = await fetch(`https://api.binance.us/api/v3/ticker/price?symbol=${symbol}`);
          const data = await res.json();
          if (data.price) {
            const price = parseFloat(data.price);
            setWatchlistPrices((prev) => ({ ...prev, [asset]: price }));
          }
        } catch (error) {
          console.error(`Failed to fetch initial price for ${asset}:`, error);
        }
      }
    };

    fetchInitialPrices();
  }, [isAuthenticated]);

  // WebSocket connections - only when authenticated
  useEffect(() => {
    if (!isAuthenticated) return;

    const sockets: WebSocket[] = [];
    let openConnections = 0;
    const reconnectTimers: ReturnType<typeof setTimeout>[] = [];
    const reconnectAttempts: Map<WatchlistAsset, number> = new Map();

    const connectAsset = (asset: WatchlistAsset) => {
      const attempts = reconnectAttempts.get(asset) || 0;
      const socket = new WebSocket(`${wsBaseUrl}/ws/market/${asset}/1m/`);

      socket.onerror = (error) => {
        console.error(`WebSocket error for ${asset}:`, error);
      };

      socket.onopen = () => {
        openConnections += 1;
        reconnectAttempts.set(asset, 0);
        if (openConnections === WATCHLIST_ASSETS.length) {
          setMarketConnected(true);
        }
      };

      socket.onmessage = (event: MessageEvent<string>) => {
        try {
          const payload = JSON.parse(event.data) as MarketSocketMessage;
          if (payload.type === 'ping') {
            socket.send(JSON.stringify({ action: 'pong' }));
            return;
          }
          const priceValue = typeof payload.price === 'string'
            ? parseFloat(payload.price)
            : payload.price;
          if (typeof priceValue === 'number' && Number.isFinite(priceValue)) {
            setWatchlistPrices((prev) => ({ ...prev, [asset]: priceValue }));
          }
        } catch (error) {
          console.error(`Error parsing market data for ${asset}:`, error);
        }
      };

      socket.onclose = () => {
        openConnections = Math.max(0, openConnections - 1);
        if (openConnections === 0) setMarketConnected(false);

        const newAttempts = attempts + 1;
        reconnectAttempts.set(asset, newAttempts);
        const delay = Math.min(1000 * Math.pow(2, newAttempts), 30000);
        const timer = setTimeout(() => {
          const newSocket = connectAsset(asset);
          const index = sockets.indexOf(socket);
          if (index !== -1) sockets[index] = newSocket;
        }, delay);
        reconnectTimers.push(timer);
      };

      socket.onerror = () => setMarketConnected(false);
      sockets.push(socket);
      return socket;
    };

    WATCHLIST_ASSETS.forEach(connectAsset);

    return () => {
      reconnectTimers.forEach(clearTimeout);
      sockets.forEach((s) => s.close());
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
            />
          </main>
        </div>
      </div>
    </div>
  );
}