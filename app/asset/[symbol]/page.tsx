'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { useAuth } from '@/lib/AuthContext';
import { getWebSocketUrl } from '@/lib/config';
import ChartComponent, { type AISignal, type Timeframe, type WatchlistAsset } from '../../../components/ChartComponent';

type SignalSocketMessage = AISignal | { detail?: string; code?: string };
type MarketSocketMessage = { price?: number | string; type?: string };

function isAiSignal(payload: SignalSocketMessage): payload is AISignal {
  return (
    'asset' in payload &&
    'timestamp' in payload &&
    'price' in payload &&
    'action' in payload &&
    'message' in payload &&
    'color' in payload
  );
}

export default function AssetDashboardPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated, loading } = useAuth();
  const symbol = (params.symbol as string).toUpperCase() as WatchlistAsset;

  const [selectedTimeframe, setSelectedTimeframe] = useState<Timeframe>('5m');
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [signals, setSignals] = useState<AISignal[]>([]);
  const [marketConnected, setMarketConnected] = useState<boolean | null>(null);
  const [signalConnected, setSignalConnected] = useState<boolean | null>(null);
  const [subscriptionActive, setSubscriptionActive] = useState<boolean>(true);
  const [metrics] = useState({ trend: 'NEUTRAL', volatility: 'MEDIUM', momentum: 'NEUTRAL' });

  const wsBaseUrl = useMemo(() => getWebSocketUrl(), []);

  // ── ALL HOOKS MUST BE BEFORE ANY EARLY RETURNS ──────────────────────────────

  // Protect route - redirect to login if not authenticated
  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, router]);

  // Read subscription state from localStorage
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const saved = window.localStorage.getItem('subscription_active');
    if (saved !== null) setSubscriptionActive(saved === 'true');
  }, []);

  // WebSocket for market data - only connect when authenticated
  useEffect(() => {
    if (!isAuthenticated) return;

    const socket = new WebSocket(`${wsBaseUrl}/ws/market/${symbol}/5m/`);
    
    socket.onerror = (error) => {
      console.error('Market WebSocket error:', error);
      setMarketConnected(false);
    };
    
    socket.onopen = () => setMarketConnected(true);
    socket.onmessage = (event: MessageEvent<string>) => {
      try {
        const payload = JSON.parse(event.data) as MarketSocketMessage;
        if ('type' in payload && payload.type === 'ping') {
          socket.send(JSON.stringify({ action: 'pong' }));
          return;
        }
        const nextPrice = typeof payload.price === 'string' ? Number(payload.price) : payload.price;
        if (typeof nextPrice === 'number' && Number.isFinite(nextPrice) && nextPrice > 0) {
          setCurrentPrice(nextPrice);
        }
      } catch (error) {
        console.error('Error parsing market message:', error);
      }
    };
    socket.onclose = () => setMarketConnected(false);
    return () => socket.close();
  }, [symbol, wsBaseUrl, isAuthenticated]);

  // WebSocket for AI signals - only connect when authenticated
  useEffect(() => {
    if (!isAuthenticated) return;

    const token = typeof window !== 'undefined'
      ? (window.localStorage.getItem('auth_token') ?? 'dummy-token-for-testing')
      : 'dummy-token-for-testing';

    let signalSocket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout>;
    let destroyed = false;

    const connect = () => {
      if (destroyed) return;
      signalSocket = new WebSocket(`${wsBaseUrl}/ws/ai-signals/?token=${encodeURIComponent(token)}`);
      
      signalSocket.onerror = (error) => {
        console.error('Signal WebSocket error:', error);
        setSignalConnected(false);
      };
      
      signalSocket.onopen = () => setSignalConnected(true);
      signalSocket.onmessage = (event: MessageEvent<string>) => {
        try {
          const payload = JSON.parse(event.data) as SignalSocketMessage;
          if ('type' in payload) return;
          if (isAiSignal(payload) && payload.asset === symbol) {
            setSignals((current: AISignal[]) => {
              const withoutAsset = current.filter(s => s.asset !== payload.asset);
              return [payload, ...withoutAsset].slice(0, 50);
            });
          }
          if ('code' in payload && payload.code === 'subscription_inactive') {
            setSubscriptionActive(false);
          }
        } catch { return; }
      };
      signalSocket.onclose = (event: CloseEvent) => {
        setSignalConnected(false);
        if (event.code === 4003) { setSubscriptionActive(false); return; }
        if (!destroyed) reconnectTimer = setTimeout(connect, 3000);
      };
      signalSocket.onerror = () => setSignalConnected(false);
    };

    connect();
    return () => {
      destroyed = true;
      clearTimeout(reconnectTimer);
      signalSocket?.close();
    };
  }, [symbol, wsBaseUrl, isAuthenticated]);

  // ── EARLY RETURNS AFTER ALL HOOKS ───────────────────────────────────────────

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
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
    <div className="min-h-screen bg-[#0a0e1a]">
      {/* Navigation */}
      <nav className="border-b border-slate-800/50 bg-[#0f1419]">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex h-16 items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600">
                <span className="text-xl font-bold text-white">SR</span>
              </div>
              <span className="text-xl font-bold text-white">SmartRisk</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/dashboard" className="text-sm font-medium text-slate-400 hover:text-white transition">
                ← Back to Dashboard
              </Link>
              <Link href="/history" className="text-sm font-medium text-slate-300 hover:text-white transition">
                Signal History
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <div className="border-b border-slate-800/50 bg-[#0f1419]">
        <div className="mx-auto max-w-7xl px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-orange-500 to-orange-600">
                <span className="text-2xl">🤖</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">SmartRisk {symbol} Signal</h1>
                <p className="text-sm text-slate-400">Real-time SmartRisk analysis and trading signals</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="rounded-lg border border-slate-700/50 bg-slate-900/50 px-4 py-2 text-sm">
                <span className="text-slate-400">Market: </span>
                <span className={marketConnected === null ? 'text-amber-400' : marketConnected ? 'text-emerald-400' : 'text-rose-400'}>
                  {marketConnected === null ? 'Connecting...' : marketConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="rounded-lg border border-slate-700/50 bg-slate-900/50 px-4 py-2 text-sm">
                <span className="text-slate-400">Signals: </span>
                <span className={signalConnected === null ? 'text-amber-400' : signalConnected ? 'text-emerald-400' : 'text-rose-400'}>
                  {signalConnected === null ? 'Connecting...' : signalConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="mx-auto max-w-7xl px-6 py-8">
        {/* Metrics Grid */}
        <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
          <div className="rounded-xl border border-slate-800/50 bg-[#0f1419] p-4">
            <div className="mb-1 text-xs text-slate-500">CURRENT PRICE</div>
            <div className="text-2xl font-bold text-white">
              ${currentPrice ? currentPrice.toLocaleString() : '--'}
            </div>
          </div>
          <div className="rounded-xl border border-slate-800/50 bg-[#0f1419] p-4">
            <div className="mb-1 text-xs text-slate-500">TREND</div>
            <div className={`text-xl font-bold ${
              metrics.trend === 'BULLISH' ? 'text-emerald-400' :
              metrics.trend === 'BEARISH' ? 'text-rose-400' : 'text-slate-400'
            }`}>{metrics.trend}</div>
          </div>
          <div className="rounded-xl border border-slate-800/50 bg-[#0f1419] p-4">
            <div className="mb-1 text-xs text-slate-500">VOLATILITY</div>
            <div className="text-xl font-bold text-amber-400">{metrics.volatility}</div>
          </div>
          <div className="rounded-xl border border-slate-800/50 bg-[#0f1419] p-4">
            <div className="mb-1 text-xs text-slate-500">MOMENTUM</div>
            <div className="text-xl font-bold text-cyan-400">{metrics.momentum}</div>
          </div>
        </div>

        {/* Chart */}
        <div className="mb-6">
          <ChartComponent
            asset={symbol}
            aiSignals={signals}
            subscriptionActive={subscriptionActive}
            wsBaseUrl={wsBaseUrl}
            timeframe={selectedTimeframe}
            onTimeframeChange={setSelectedTimeframe}
          />
        </div>

        {/* Signal History Section */}
        <div className="rounded-xl border border-slate-800/50 bg-[#0f1419] p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white">Check Full Signal History</h2>
              <p className="text-sm text-slate-400">
                View the complete history of every signal, entry and exit prices, and full trade history
              </p>
            </div>
            <Link href="/history" className="rounded-lg bg-cyan-500 px-6 py-3 font-semibold text-white hover:bg-cyan-600 transition">
              Signal History →
            </Link>
          </div>
          <div className="space-y-3">
            <h3 className="font-semibold text-white">How to Use This {symbol} SmartRisk Dashboard</h3>
            <p className="text-sm text-slate-400">
              This page is a real-time {symbol} Scalper Dashboard built for short-term traders. It visualizes automated analysis so you can make better decisions.
            </p>
            <p className="text-sm text-slate-400">
              These are current market signals, not predictions. Signals refresh frequently as market context changes.
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-16 border-t border-slate-800/50 bg-[#0f1419] py-8">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <p className="text-sm text-slate-500">
            © 2026 SmartRisk. Powered by SmartRisk trading signals for crypto markets.
          </p>
        </div>
      </footer>
    </div>
  );
}