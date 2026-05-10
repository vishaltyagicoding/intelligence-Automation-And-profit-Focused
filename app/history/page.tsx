'use client';

export const dynamic = 'force-dynamic';

import Link from 'next/link';
import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import { getWebSocketUrl } from '@/lib/config';

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

const SYMBOLS    = ['BTCUSD', 'ETHUSD', 'XAUUSD', 'LTCUSD'] as const;
const TIMEFRAMES = ['5m', '15m', '30m', '1h', '2h', '4h', '1d'] as const;
type SymbolType = typeof SYMBOLS[number];
type FilterType = 'ALL' | 'BUY' | 'SELL';

function fmt(n: number | null): string {
  if (n === null || n === undefined) return '—';
  return '$' + n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function SignalHistoryPage() {
  const router = useRouter();
  const { isAuthenticated, loading, user } = useAuth();

  const [signals,       setSignals]       = useState<SignalHistory[]>([]);
  const [loadingData,   setLoadingData]   = useState(true);
  const [lastUpdated,   setLastUpdated]   = useState<Date | null>(null);
  const [filter,        setFilter]        = useState<FilterType>('ALL');
  const [symbolFilter,  setSymbolFilter]  = useState<'ALL' | SymbolType>('ALL');
  const [liveCount,     setLiveCount]     = useState(0);  // count of live WS signals received

  const wsRefs = useRef<WebSocket[]>([]);
  const signalsRef = useRef<Map<string, SignalHistory>>(new Map());

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

  // ── Fetch ALL historical signals in parallel ───────────────────────────────
  const fetchAll = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoadingData(true);
    try {
      const tasks = SYMBOLS.flatMap(symbol =>
        TIMEFRAMES.map(timeframe => ({
          symbol, timeframe,
          p: fetch(
            `/api/trading/signal-history/${symbol}/?timeframe=${timeframe}`,
            { signal: AbortSignal.timeout(8000) }
          ).then(r => r.ok ? r.json() : null).catch(() => null),
        }))
      );
      const results = await Promise.all(tasks.map(t => t.p));

      const fresh = new Map<string, SignalHistory>();
      results.forEach((data, i) => {
        const { symbol, timeframe } = tasks[i];
        if (!data?.success || !data.signals?.length) return;
        (data.signals as Record<string, unknown>[]).forEach((s, idx) => {
          const ts   = s.timestamp as string;
          const bull = s.is_bullish as boolean;
          const id   = `${symbol}-${timeframe}-${ts}-${idx}`;
          const oTop = s.outer_top as number;
          const oBot = s.outer_bottom as number;
          fresh.set(id, {
            id, timestamp: ts, symbol, timeframe,
            action:     bull ? 'BUY' : 'SELL',
            entryPrice: s.center_price as number,
            stopLoss:   bull ? oBot : oTop,
            target:     bull ? oTop : oBot,
            status:     'OPEN',
          });
        });
      });

      // Merge with any live signals already received via WebSocket
      for (const [k, v] of signalsRef.current) fresh.set(k, v);

      signalsRef.current = fresh;
      setSignals(
        [...fresh.values()].sort(
          (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        )
      );
      setLastUpdated(new Date());
    } catch (e) {
      console.error('History fetch error:', e);
    } finally {
      setLoadingData(false);
    }
  }, [isAuthenticated]);

  // ── Connect WebSocket for each symbol+timeframe to get INSTANT updates ────
  // When a new signal fires on the live chart it broadcasts a 'signal' event.
  // We intercept it here and prepend the new row immediately — no polling delay.
  const connectLiveWS = useCallback(() => {
    if (!isAuthenticated) return;

    // Close any existing connections first
    wsRefs.current.forEach(ws => ws.close());
    wsRefs.current = [];

    const wsBase = getWebSocketUrl();

    SYMBOLS.forEach(symbol => {
      TIMEFRAMES.forEach(timeframe => {
        const url = `${wsBase}/ws/market/${symbol}/${timeframe}/`;
        const ws  = new WebSocket(url);

        ws.onmessage = (ev) => {
          try {
            const data = JSON.parse(ev.data as string) as Record<string, unknown>;

            // Only handle signal events (not kline tick updates)
            if (data.type !== 'signal') return;

            const bull    = data.is_bullish as boolean;
            const ts      = data.timestamp as string;
            const asset   = data.asset as string;
            const tf      = data.timeframe as string;
            const entry   = data.price as number;
            const sl      = data.stop_loss as number;
            const tgt     = data.target as number;
            const id      = `${asset}-${tf}-${ts}-live`;

            const newSig: SignalHistory = {
              id, timestamp: ts, symbol: asset, timeframe: tf,
              action:     bull ? 'BUY' : 'SELL',
              entryPrice: entry,
              stopLoss:   sl   ?? null,
              target:     tgt  ?? null,
              status:     'OPEN',
            };

            signalsRef.current.set(id, newSig);

            // Prepend to top of list — instant update, no delay
            setSignals(prev => {
              const exists = prev.find(s => s.id === id);
              if (exists) return prev;
              return [newSig, ...prev];
            });
            setLiveCount(c => c + 1);
            setLastUpdated(new Date());
          } catch { /* ignore parse errors */ }
        };

        ws.onerror   = () => {};  // silent — expected for closed streams
        ws.onclose   = () => {};

        wsRefs.current.push(ws);
      });
    });
  }, [isAuthenticated]);

  // Initial fetch
  useEffect(() => {
    if (!loading && isAuthenticated) {
      fetchAll();
    }
  }, [isAuthenticated, loading, fetchAll]);

  // Connect live WebSocket after initial data loads
  useEffect(() => {
    if (!isAuthenticated) return;
    connectLiveWS();
    return () => {
      wsRefs.current.forEach(ws => ws.close());
      wsRefs.current = [];
    };
  }, [isAuthenticated, connectLiveWS]);

  // Auto-refresh historical data every 60 seconds
  useEffect(() => {
    if (!isAuthenticated) return;
    const iv = setInterval(fetchAll, 60_000);
    return () => clearInterval(iv);
  }, [isAuthenticated, fetchAll]);

  // Refresh on tab focus
  useEffect(() => {
    if (!isAuthenticated) return;
    const onFocus = () => fetchAll();
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [isAuthenticated, fetchAll]);

  // Stats
  const total = signals.length;
  const buys  = signals.filter(s => s.action === 'BUY').length;
  const sells = signals.filter(s => s.action === 'SELL').length;

  // Filtered list
  const filtered = signals.filter(s => {
    if (filter !== 'ALL' && s.action !== filter) return false;
    if (symbolFilter !== 'ALL' && s.symbol !== symbolFilter) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent" />
      </div>
    );
  }
  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-[#0a0e1a]">
      {/* Nav */}
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
              {liveCount > 0 && (
                <span className="rounded-full bg-cyan-500/20 px-3 py-1 text-xs font-semibold text-cyan-400 animate-pulse">
                  ● {liveCount} live update{liveCount !== 1 ? 's' : ''}
                </span>
              )}
              <button
                onClick={fetchAll}
                disabled={loadingData}
                className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-50 transition"
              >
                {loadingData ? 'Loading…' : '↻ Refresh'}
              </button>
              <Link href="/dashboard" className="text-sm font-medium text-slate-400 hover:text-white transition">
                ← Dashboard
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <div className="border-b border-slate-800/50 bg-[#0f1419]">
        <div className="mx-auto max-w-7xl px-6 py-8 flex items-start justify-between">
          <div>
            <h1 className="mb-2 text-3xl font-bold text-white">SmartRisk Signal History</h1>
            <p className="text-slate-400">Last 5 months — all assets and timeframes — live updates via WebSocket</p>
          </div>
          {lastUpdated && (
            <p className="text-xs text-slate-500 mt-1 whitespace-nowrap">
              Updated {lastUpdated.toISOString().replace('T', ' ').slice(0, 19)} UTC
            </p>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="border-b border-slate-800/50 bg-[#0f1419]">
        <div className="mx-auto max-w-7xl px-6 py-6 flex justify-center gap-6">
          {[
            { label: 'TOTAL SIGNALS', value: total, color: 'text-white' },
            { label: 'BUY SIGNALS',   value: buys,  color: 'text-emerald-400' },
            { label: 'SELL SIGNALS',  value: sells, color: 'text-rose-400' },
          ].map(({ label, value, color }) => (
            <div key={label} className="rounded-xl border border-slate-800/50 bg-[#0a0e1a] p-6 text-center min-w-[140px]">
              {loadingData && value === 0
                ? <div className="inline-block h-8 w-8 mb-1 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent" />
                : <div className={`mb-1 text-4xl font-bold ${color}`}>{value}</div>
              }
              <div className="text-sm text-slate-500">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="mx-auto max-w-7xl px-6 py-6">
        <div className="mb-6 flex flex-wrap items-center gap-6">
          <div>
            <label className="mb-2 block text-xs font-medium text-slate-400">FILTER BY ACTION</label>
            <div className="flex gap-2">
              {(['ALL', 'BUY', 'SELL'] as const).map(f => (
                <button key={f} onClick={() => setFilter(f)}
                  className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${filter === f ? 'bg-cyan-500 text-white' : 'border border-slate-700 bg-slate-800/50 text-slate-300 hover:bg-slate-700/50'}`}>
                  {f}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="mb-2 block text-xs font-medium text-slate-400">FILTER BY SYMBOL</label>
            <div className="flex gap-2 flex-wrap">
              {(['ALL', ...SYMBOLS] as const).map(s => (
                <button key={s} onClick={() => setSymbolFilter(s as 'ALL' | SymbolType)}
                  className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${symbolFilter === s ? 'bg-cyan-500 text-white' : 'border border-slate-700 bg-slate-800/50 text-slate-300 hover:bg-slate-700/50'}`}>
                  {s}
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
                  {['DATE & TIME (UTC)', 'SYMBOL', 'TIMEFRAME', 'ACTION', 'ENTRY PRICE', 'STOP LOSS', 'TARGET', 'STATUS'].map(h => (
                    <th key={h} className={`px-6 py-4 text-xs font-semibold uppercase tracking-wider text-slate-400 ${h === 'ENTRY PRICE' || h === 'STOP LOSS' || h === 'TARGET' ? 'text-right' : h === 'STATUS' ? 'text-center' : 'text-left'}`}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {loadingData && signals.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center">
                      <div className="flex flex-col items-center gap-3">
                        <div className="h-8 w-8 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent" />
                        <p className="text-slate-400">Loading all signals in parallel…</p>
                      </div>
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center text-slate-400">No signals found</td>
                  </tr>
                ) : filtered.map(signal => (
                  <tr key={signal.id} className="hover:bg-slate-800/30 transition">
                    <td className="px-6 py-4 text-sm text-slate-300 whitespace-nowrap">
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
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${signal.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                        {signal.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right text-sm font-medium text-white">{fmt(signal.entryPrice)}</td>
                    <td className="px-6 py-4 text-right text-sm text-rose-400">{fmt(signal.stopLoss)}</td>
                    <td className="px-6 py-4 text-right text-sm text-emerald-400">{fmt(signal.target)}</td>
                    <td className="px-6 py-4 text-center">
                      <span className="rounded-full bg-cyan-500/20 px-3 py-1 text-xs font-semibold text-cyan-400">OPEN</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-8 rounded-xl border border-slate-800/50 bg-[#0f1419] p-6">
          <h3 className="mb-4 text-lg font-bold text-white">Understanding Signal History</h3>
          <div className="space-y-2 text-sm text-slate-400">
            <p><strong className="text-white">Entry Price:</strong> Center price of the reversal zone when signal fired</p>
            <p><strong className="text-white">Stop Loss:</strong> Outer zone bottom (BUY) or outer zone top (SELL) — your risk boundary</p>
            <p><strong className="text-white">Target:</strong> Outer zone top (BUY) or outer zone bottom (SELL) — your profit target</p>
            <p><strong className="text-white">Live Updates:</strong> New signals appear instantly via WebSocket — no page refresh needed</p>
            <p className="mt-4 rounded-lg bg-cyan-500/10 border border-cyan-500/30 p-3 text-cyan-300">
              Showing last 5 months · {SYMBOLS.length} assets · {TIMEFRAMES.length} timeframes · Auto-refreshes every 60s
            </p>
          </div>
        </div>
      </div>

      <footer className="mt-16 border-t border-slate-800/50 bg-[#0f1419] py-8">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <p className="text-sm text-slate-500">© 2026 SmartRisk. Reversal signals for crypto markets.</p>
        </div>
      </footer>
    </div>
  );
}