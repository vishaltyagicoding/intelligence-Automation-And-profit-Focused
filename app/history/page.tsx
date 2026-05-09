'use client';

// Force dynamic rendering (disable static optimization)
export const dynamic = 'force-dynamic';

import Link from 'next/link';
import { useEffect, useState, useCallback } from 'react';
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

// ALL symbols and ALL timeframes — same as what reversal calculator uses
const SYMBOLS = ['BTCUSD', 'ETHUSD', 'XAUUSD', 'LTCUSD'] as const;
const TIMEFRAMES = ['5m', '15m', '30m', '1h', '2h', '4h', '1d'] as const;

export default function SignalHistoryPage() {
  const router = useRouter();
  const { isAuthenticated, loading, user } = useAuth();

  const [signals, setSignals]           = useState<SignalHistory[]>([]);
  const [loadingSignals, setLoadingSignals] = useState(true);
  const [lastUpdated, setLastUpdated]   = useState<Date | null>(null);
  const [filter, setFilter]             = useState<'ALL' | 'BUY' | 'SELL'>('ALL');
  const [symbolFilter, setSymbolFilter] = useState<'ALL' | 'BTCUSD' | 'ETHUSD' | 'XAUUSD' | 'LTCUSD'>('ALL');

  // Protect route
  useEffect(() => {
    if (!loading && !isAuthenticated) router.push('/login');
  }, [isAuthenticated, loading, router]);

  useEffect(() => {
    if (!loading && isAuthenticated && user) {
      const sub = user.subscription_status;
      if (sub && !sub.is_active && user.manual_subscription !== 'activated') {
        router.push('/subscription');
      }
    }
  }, [isAuthenticated, loading, user, router]);

  // ── Core fetch — ALL symbols × ALL timeframes in PARALLEL ──────────────────
  const fetchSignalHistory = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoadingSignals(true);

    try {
      // Build all fetch promises at once — parallel, not sequential
      const tasks = SYMBOLS.flatMap(symbol =>
        TIMEFRAMES.map(timeframe => ({
          symbol,
          timeframe,
          promise: fetch(
            `/api/trading/signal-history/${symbol}/?timeframe=${timeframe}`,
            {
              headers: { 'Content-Type': 'application/json' },
              signal: AbortSignal.timeout(8000),
            }
          )
            .then(r => r.ok ? r.json() : null)
            .catch(() => null),
        }))
      );

      // Execute ALL requests in parallel — 28 calls in ~1-2s instead of 18s
      const results = await Promise.all(tasks.map(t => t.promise));

      const allSignals: SignalHistory[] = [];

      results.forEach((data, i) => {
        const { symbol, timeframe } = tasks[i];
        if (!data?.success || !data.signals?.length) return;

        const converted = data.signals.map((signal: Record<string, unknown>, idx: number) => ({
          id:         `${symbol}-${timeframe}-${idx}-${signal.timestamp}`,
          timestamp:  signal.timestamp as string,
          symbol,
          action:     (signal.is_bullish ? 'BUY' : 'SELL') as 'BUY' | 'SELL',
          entryPrice: signal.center_price as number,
          stopLoss:   signal.is_bullish ? (signal.outer_bottom as number) : (signal.outer_top as number),
          target:     signal.is_bullish ? (signal.outer_top as number)    : (signal.outer_bottom as number),
          status:     'OPEN' as const,
          timeframe,
        }));

        allSignals.push(...converted);
      });

      // Sort newest first
      allSignals.sort((a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );

      // Keep last 5 months
      const fiveMonthsAgo = new Date();
      fiveMonthsAgo.setMonth(fiveMonthsAgo.getMonth() - 5);
      const finalSignals = allSignals.filter(
        s => new Date(s.timestamp) >= fiveMonthsAgo
      );

      setSignals(finalSignals);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching signal history:', error);
    } finally {
      setLoadingSignals(false);
    }
  }, [isAuthenticated]);

  // Initial fetch when auth is ready
  useEffect(() => {
    if (!loading && isAuthenticated) {
      fetchSignalHistory();
    }
  }, [isAuthenticated, loading, fetchSignalHistory]);

  // Auto-refresh every 60 seconds — picks up new signals automatically
  useEffect(() => {
    if (!isAuthenticated) return;
    const interval = setInterval(fetchSignalHistory, 60_000);
    return () => clearInterval(interval);
  }, [isAuthenticated, fetchSignalHistory]);

  // Refresh when tab gets focus (user coming back to page)
  useEffect(() => {
    if (!isAuthenticated) return;
    const onFocus = () => fetchSignalHistory();
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [isAuthenticated, fetchSignalHistory]);

  // Stats
  const stats = {
    total: signals.length,
    buy:   signals.filter(s => s.action === 'BUY').length,
    sell:  signals.filter(s => s.action === 'SELL').length,
  };

  // Filter
  const filteredSignals = signals.filter(s => {
    if (filter !== 'ALL' && s.action !== filter) return false;
    if (symbolFilter !== 'ALL' && s.symbol !== symbolFilter) return false;
    return true;
  });

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
              <button
                onClick={fetchSignalHistory}
                disabled={loadingSignals}
                className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-50 transition"
              >
                {loadingSignals ? 'Refreshing…' : '↻ Refresh'}
              </button>
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
          <div className="flex items-start justify-between">
            <div>
              <h1 className="mb-2 text-3xl font-bold text-white">SmartRisk Signal History</h1>
              <p className="text-slate-400">
                Complete history of all SmartRisk-generated trading signals from the last 5 months
              </p>
            </div>
            {lastUpdated && (
              <p className="text-xs text-slate-500 mt-1">
                Updated {lastUpdated.toLocaleTimeString()} UTC
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="border-b border-slate-800/50 bg-[#0f1419]">
        <div className="mx-auto max-w-7xl px-6 py-6">
          <div className="flex justify-center gap-6">
            <div className="rounded-xl border border-slate-800/50 bg-[#0a0e1a] p-6 text-center min-w-[140px]">
              {loadingSignals
                ? <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent mb-1" />
                : <div className="mb-1 text-4xl font-bold text-white">{stats.total}</div>
              }
              <div className="text-sm text-slate-500">TOTAL SIGNALS</div>
            </div>
            <div className="rounded-xl border border-slate-800/50 bg-[#0a0e1a] p-6 text-center min-w-[140px]">
              <div className="mb-1 text-4xl font-bold text-emerald-400">{stats.buy}</div>
              <div className="text-sm text-slate-500">BUY SIGNALS</div>
            </div>
            <div className="rounded-xl border border-slate-800/50 bg-[#0a0e1a] p-6 text-center min-w-[140px]">
              <div className="mb-1 text-4xl font-bold text-rose-400">{stats.sell}</div>
              <div className="text-sm text-slate-500">SELL SIGNALS</div>
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
              {(['ALL', 'BUY', 'SELL'] as const).map(action => (
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
            <div className="flex gap-2 flex-wrap">
              {(['ALL', 'BTCUSD', 'ETHUSD', 'XAUUSD', 'LTCUSD'] as const).map(sym => (
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

        {/* Table */}
        <div className="rounded-xl border border-slate-800/50 bg-[#0f1419] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-slate-800/50 bg-slate-950/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">Date & Time (UTC)</th>
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
                {loadingSignals && signals.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center">
                      <div className="flex flex-col items-center gap-3">
                        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent"></div>
                        <p className="text-slate-400">Loading signals from all timeframes in parallel…</p>
                      </div>
                    </td>
                  </tr>
                ) : filteredSignals.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center text-slate-400">
                      No signals found matching your filters
                    </td>
                  </tr>
                ) : (
                  filteredSignals.map(signal => (
                    <tr key={signal.id} className="hover:bg-slate-800/30 transition">
                      <td className="px-6 py-4 text-sm text-slate-300">
                        {/* Show UTC time — consistent with chart display */}
                        {new Date(signal.timestamp).toISOString().replace('T', ' ').slice(0, 19)} UTC
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
                        {signal.stopLoss ? `$${signal.stopLoss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                      </td>
                      <td className="px-6 py-4 text-right text-sm text-emerald-400">
                        {signal.target ? `$${signal.target.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
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

        {/* Info */}
        <div className="mt-8 rounded-xl border border-slate-800/50 bg-[#0f1419] p-6">
          <h3 className="mb-4 text-lg font-bold text-white">Understanding Signal History</h3>
          <div className="space-y-3 text-sm text-slate-400">
            <p><strong className="text-white">Entry Price:</strong> The price at which the SmartRisk reversal signal was generated</p>
            <p><strong className="text-white">Stop Loss:</strong> Recommended stop loss level (outer zone boundary)</p>
            <p><strong className="text-white">Target:</strong> Recommended take profit level (outer zone boundary)</p>
            <p><strong className="text-white">Timeframe:</strong> The chart timeframe on which the signal was detected</p>
            <p><strong className="text-white">Status:</strong> OPEN — historical signals shown for reference</p>
            <p className="mt-4 rounded-lg bg-cyan-500/10 border border-cyan-500/30 p-3 text-cyan-300">
              <strong>Note:</strong> History shows reversal signals from the last 5 months across all 4 assets
              and all timeframes (5m, 15m, 30m, 1h, 2h, 4h, 1d). Automatically refreshes every 60 seconds.
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