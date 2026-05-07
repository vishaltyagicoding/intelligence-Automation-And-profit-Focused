'use client';

// Force dynamic rendering (disable static optimization)
export const dynamic = 'force-dynamic';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';

interface SignalHistory {
  id: string;
  timestamp: string;
  symbol: string;
  action: 'BUY' | 'SELL';
  entryPrice: number;
  stopLoss: number | null;
  target: number | null;
  status: 'OPEN';
  timeframe: string;
}

export default function SignalHistoryPage() {
  const router = useRouter();
  const { isAuthenticated, loading, user } = useAuth();

  const [signals, setSignals] = useState<SignalHistory[]>([]);
  const [loadingSignals, setLoadingSignals] = useState(true);
  const [filter, setFilter] = useState<'ALL' | 'BUY' | 'SELL'>('ALL');
  const [symbolFilter, setSymbolFilter] = useState<'ALL' | 'BTCUSD' | 'ETHUSD' | 'XAUUSD' | 'LTCUSD'>('ALL');

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

  // Fetch signals only when authenticated
  useEffect(() => {
    if (!loading && isAuthenticated) {
      fetchSignalHistory();
    }
  }, [isAuthenticated, loading]);

  const fetchSignalHistory = async () => {
    try {
      const symbols = ['BTCUSD', 'ETHUSD', 'XAUUSD', 'LTCUSD'];
      const timeframes = ['1h', '4h', '1d'];
      const allSignals: SignalHistory[] = [];
      const apiBaseUrl = '/api';

      for (const symbol of symbols) {
        for (const timeframe of timeframes) {
          try {
            const url = `${apiBaseUrl}/trading/signal-history/${symbol}/?timeframe=${timeframe}`;
            const response = await fetch(url, {
              headers: { 'Content-Type': 'application/json' },
              signal: AbortSignal.timeout(5000),
            });

            if (response.ok) {
              const data = await response.json();
              if (data.success && data.signals && data.signals.length > 0) {
                const convertedSignals = data.signals.map((signal: any, index: number) => ({
                  id: `${symbol}-${timeframe}-${index}-${signal.timestamp}`,
                  timestamp: signal.timestamp,
                  symbol: symbol,
                  action: signal.is_bullish ? 'BUY' as const : 'SELL' as const,
                  entryPrice: signal.center_price,
                  stopLoss: signal.is_bullish ? signal.outer_bottom : signal.outer_top,
                  target: signal.is_bullish ? signal.outer_top : signal.outer_bottom,
                  status: 'OPEN' as const,
                  timeframe: timeframe,
                }));
                allSignals.push(...convertedSignals);
              }
            }
          } catch (err) {
            continue;
          }
        }
      }

      allSignals.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

      const fiveMonthsAgo = new Date();
      fiveMonthsAgo.setMonth(fiveMonthsAgo.getMonth() - 5);
      const filteredSignals = allSignals.filter(
        signal => new Date(signal.timestamp) >= fiveMonthsAgo
      );

      setSignals(filteredSignals);
    } catch (error) {
      console.error('Error fetching signal history:', error);
    } finally {
      setLoadingSignals(false);
    }
  };

  // Calculate stats
  const stats = {
    total: signals.length,
    buy: signals.filter(s => s.action === 'BUY').length,
    sell: signals.filter(s => s.action === 'SELL').length,
  };

  // Filter signals
  const filteredSignals = signals.filter(signal => {
    if (filter !== 'ALL' && signal.action !== filter) return false;
    if (symbolFilter !== 'ALL' && signal.symbol !== symbolFilter) return false;
    return true;
  });

  // Show loading while checking authentication
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

  // Don't render if not authenticated (redirect is already triggered)
  if (!isAuthenticated) {
    return null;
  }

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
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <div className="border-b border-slate-800/50 bg-[#0f1419]">
        <div className="mx-auto max-w-7xl px-6 py-8">
          <h1 className="mb-2 text-3xl font-bold text-white">SmartRisk Signal History</h1>
          <p className="text-slate-400">
            Complete history of all SmartRisk-generated trading signals from the last 5 months
          </p>
        </div>
      </div>

      {/* Stats Section */}
      <div className="border-b border-slate-800/50 bg-[#0f1419]">
        <div className="mx-auto max-w-7xl px-6 py-6">
          <div className="flex justify-center">
            <div className="rounded-xl border border-slate-800/50 bg-[#0a0e1a] p-6 text-center min-w-[200px]">
              <div className="mb-1 text-4xl font-bold text-white">{stats.total}</div>
              <div className="text-sm text-slate-500">TOTAL SIGNALS</div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="mx-auto max-w-7xl px-6 py-6">
        <div className="mb-6 flex flex-wrap items-center gap-4">
          <div>
            <label className="mb-2 block text-xs font-medium text-slate-400">FILTER BY ACTION</label>
            <div className="flex gap-2">
              {(['ALL', 'BUY', 'SELL'] as const).map((action) => (
                <button
                  key={action}
                  onClick={() => setFilter(action)}
                  className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                    filter === action
                      ? 'bg-cyan-500 text-white'
                      : 'border border-slate-700 bg-slate-800/50 text-slate-300 hover:bg-slate-700/50'
                  }`}
                >
                  {action}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-2 block text-xs font-medium text-slate-400">FILTER BY SYMBOL</label>
            <div className="flex gap-2">
              {(['ALL', 'BTCUSD', 'ETHUSD', 'XAUUSD', 'LTCUSD'] as const).map((sym) => (
                <button
                  key={sym}
                  onClick={() => setSymbolFilter(sym)}
                  className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                    symbolFilter === sym
                      ? 'bg-cyan-500 text-white'
                      : 'border border-slate-700 bg-slate-800/50 text-slate-300 hover:bg-slate-700/50'
                  }`}
                >
                  {sym}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Signal Table */}
        <div className="rounded-xl border border-slate-800/50 bg-[#0f1419] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-slate-800/50 bg-slate-950/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">Date & Time</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">Symbol</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">Timeframe</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">Action</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider text-slate-400">Entry Price</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider text-slate-400">Stop Loss</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider text-slate-400">Target</th>
                  <th className="px-6 py-4 text-center text-xs font-semibold uppercase tracking-wider text-slate-400">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {loadingSignals ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center text-slate-400">
                      Loading signal history from last 5 months...
                    </td>
                  </tr>
                ) : filteredSignals.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center text-slate-400">
                      No signals found matching your filters
                    </td>
                  </tr>
                ) : (
                  filteredSignals.map((signal) => (
                    <tr key={signal.id} className="hover:bg-slate-800/30 transition">
                      <td className="px-6 py-4 text-sm text-slate-300">
                        {new Date(signal.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-semibold text-white">
                          {signal.symbol}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-blue-500/20 px-3 py-1 text-xs font-semibold text-blue-400">
                          {signal.timeframe.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
                          signal.action === 'BUY'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-rose-500/20 text-rose-400'
                        }`}>
                          {signal.action}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right text-sm font-medium text-white">
                        ${signal.entryPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="px-6 py-4 text-right text-sm text-rose-400">
                        {signal.stopLoss ? signal.stopLoss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'}
                      </td>
                      <td className="px-6 py-4 text-right text-sm text-emerald-400">
                        {signal.target ? signal.target.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className="rounded-full bg-cyan-500/20 px-3 py-1 text-xs font-semibold text-cyan-400">
                          {signal.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-8 rounded-xl border border-slate-800/50 bg-[#0f1419] p-6">
          <h3 className="mb-4 text-lg font-bold text-white">Understanding Signal History</h3>
          <div className="space-y-3 text-sm text-slate-400">
            <p><strong className="text-white">Entry Price:</strong> The price at which the SmartRisk reversal signal was generated</p>
            <p><strong className="text-white">Stop Loss:</strong> Recommended stop loss level to limit downside risk (outer zone boundary)</p>
            <p><strong className="text-white">Target:</strong> Recommended take profit level (outer zone boundary)</p>
            <p><strong className="text-white">Timeframe:</strong> The chart timeframe on which the signal was detected (1h, 4h, 1d)</p>
            <p><strong className="text-white">Status:</strong> All signals shown are OPEN (historical signals for reference)</p>
            <p className="mt-4 rounded-lg bg-cyan-500/10 border border-cyan-500/30 p-3 text-cyan-300">
              <strong>Note:</strong> This history shows reversal signals from the last 5 months across all 4 cryptocurrencies on major timeframes (1h, 4h, 1d).
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