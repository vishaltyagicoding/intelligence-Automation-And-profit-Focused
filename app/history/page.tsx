'use client';

export const dynamic = 'force-dynamic';

import Link from 'next/link';
import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import { getWebSocketUrl } from '@/lib/config';

interface SignalHistory {
  id: string; timestamp: string; symbol: string;
  action: 'BUY' | 'SELL'; entryPrice: number;
  stopLoss: number | null; target: number | null;
  status: 'OPEN'; timeframe: string;
  isNew?: boolean; // flash highlight for live arrivals
}

const SYMBOLS    = ['BTCUSD', 'ETHUSD', 'XAUUSD', 'LTCUSD'] as const;
const TIMEFRAMES = ['5m', '15m', '30m', '1h', '2h', '4h', '1d'] as const;
type SymbolType  = typeof SYMBOLS[number];
type FilterType  = 'ALL' | 'BUY' | 'SELL';

function fmt(n: number | null): string {
  if (n === null || n === undefined) return '—';
  return '$' + n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ─── Toast notification for new signal ────────────────────────────────────────
interface Toast { id: string; msg: string; action: 'BUY' | 'SELL'; }

export default function SignalHistoryPage() {
  const router = useRouter();
  const { isAuthenticated, loading, user } = useAuth();

  const [signals,      setSignals]      = useState<SignalHistory[]>([]);
  const [loadingData,  setLoadingData]  = useState(true);
  const [lastUpdated,  setLastUpdated]  = useState<Date | null>(null);
  const [filter,       setFilter]       = useState<FilterType>('ALL');
  const [symbolFilter, setSymbolFilter] = useState<'ALL' | SymbolType>('ALL');
  const [liveCount,    setLiveCount]    = useState(0);
  const [toasts,       setToasts]       = useState<Toast[]>([]);

  const signalsRef  = useRef<Map<string, SignalHistory>>(new Map());
  // Tracks active WS connections: Map<"SYMBOL-TF", {ws, retries, timer}>
  const connsRef    = useRef<Map<string, { ws: WebSocket; retries: number; timer: ReturnType<typeof setTimeout> | null }>>(new Map());
  const cleanedRef  = useRef(false);

  // ── Auth guards ────────────────────────────────────────────────────────────
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

  // ── Toast helpers ──────────────────────────────────────────────────────────
  const addToast = useCallback((msg: string, action: 'BUY' | 'SELL') => {
    const id = Math.random().toString(36).slice(2);
    setToasts(prev => [...prev.slice(-4), { id, msg, action }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 8000);
  }, []);

  // ── Fetch all historical signals ───────────────────────────────────────────
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
          // Preserve isNew flag if already in signalsRef
          const existing = signalsRef.current.get(id);
          fresh.set(id, {
            id, timestamp: ts, symbol, timeframe,
            action:     bull ? 'BUY' : 'SELL',
            entryPrice: s.center_price as number,
            stopLoss:   bull ? oBot : oTop,
            target:     bull ? oTop : oBot,
            status:     'OPEN',
            isNew:      existing?.isNew ?? false,
          });
        });
      });

      // Preserve any live signals already prepended via WS
      for (const [k, v] of signalsRef.current) {
        if (v.isNew) fresh.set(k, v); // keep live signals at top
      }

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

  // ── Live WebSocket for each symbol+timeframe ──────────────────────────────
  // Proper reconnect with exponential backoff — never gives up.
  // When a new signal arrives:
  //   1. Instantly prepend the new row (zero delay)
  //   2. Show a toast notification
  //   3. Trigger fetchAll after 2 s so the DB row (with SL/Target) is loaded
  const connectLiveWS = useCallback(() => {
    if (!isAuthenticated || cleanedRef.current) return;
    const wsBase = getWebSocketUrl();

    // Close and clear all existing connections
    connsRef.current.forEach(({ ws, timer }) => {
      if (timer) clearTimeout(timer);
      try { ws.close(); } catch { /* ignore */ }
    });
    connsRef.current.clear();

    SYMBOLS.forEach(symbol => {
      TIMEFRAMES.forEach(timeframe => {
        const key = `${symbol}-${timeframe}`;
        let retries = 0;

        const connect = () => {
          if (cleanedRef.current) return;
          const url = `${wsBase}/ws/market/${symbol}/${timeframe}/`;
          let ws: WebSocket;
          try { ws = new WebSocket(url); } catch { scheduleRetry(); return; }

          connsRef.current.set(key, { ws, retries, timer: null });

          ws.onopen = () => { retries = 0; };

          ws.onmessage = (ev: MessageEvent<string>) => {
            try {
              const data = JSON.parse(ev.data as string) as Record<string, unknown>;
              if (data.type !== 'signal') return;

              const bull  = data.is_bullish as boolean;
              const ts    = data.timestamp as string;
              const asset = data.asset as string;
              const tf    = data.timeframe as string;
              const entry = data.price as number;
              const sl    = data.stop_loss as number | undefined;
              const tgt   = data.target as number | undefined;
              const id    = `${asset}-${tf}-${ts}-live`;

              const newSig: SignalHistory = {
                id, timestamp: ts, symbol: asset, timeframe: tf,
                action:     bull ? 'BUY' : 'SELL',
                entryPrice: entry,
                stopLoss:   sl   ?? null,
                target:     tgt  ?? null,
                status:     'OPEN',
                isNew:      true,
              };

              signalsRef.current.set(id, newSig);

              // ── STEP 1: Instant UI update — zero delay ──────────────────────
              setSignals(prev => {
                if (prev.find(s => s.id === id)) return prev;
                return [newSig, ...prev];
              });
              setLiveCount(c => c + 1);
              setLastUpdated(new Date());

              // ── STEP 2: Toast notification ──────────────────────────────────
              addToast(
                `${bull ? '▲ BUY' : '▼ SELL'} signal on ${asset} ${tf.toUpperCase()} @ $${entry.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
                bull ? 'BUY' : 'SELL'
              );

              // ── STEP 3: Refresh history from DB after backend writes ─────────
              // 2 s delay gives Django time to commit the DB row with SL/Target
              setTimeout(fetchAll, 2000);

              // Remove isNew flag after highlight duration
              setTimeout(() => {
                signalsRef.current.set(id, { ...newSig, isNew: false });
              }, 5000);

            } catch { /* ignore parse errors */ }
          };

          ws.onclose = () => {
            if (cleanedRef.current) return;
            scheduleRetry();
          };
          ws.onerror = () => { /* onclose fires next */ };
        };

        const scheduleRetry = () => {
          if (cleanedRef.current) return;
          retries++;
          const delay = Math.min(1000 * Math.pow(2, Math.min(retries - 1, 4)), 30_000);
          const timer = setTimeout(connect, delay);
          const existing = connsRef.current.get(key);
          if (existing) connsRef.current.set(key, { ...existing, timer });
        };

        connect();
      });
    });
  }, [isAuthenticated, fetchAll, addToast]);

  // Initial fetch + connect WS
  useEffect(() => {
    if (!loading && isAuthenticated) fetchAll();
  }, [isAuthenticated, loading, fetchAll]);

  useEffect(() => {
    if (!isAuthenticated) return;
    cleanedRef.current = false;
    connectLiveWS();
    return () => {
      cleanedRef.current = true;
      connsRef.current.forEach(({ ws, timer }) => {
        if (timer) clearTimeout(timer);
        try { ws.close(); } catch { /* ignore */ }
      });
      connsRef.current.clear();
    };
  }, [isAuthenticated, connectLiveWS]);

  // Auto-refresh every 60 s + on tab focus
  useEffect(() => {
    if (!isAuthenticated) return;
    const iv = setInterval(fetchAll, 60_000);
    const onFocus = () => fetchAll();
    window.addEventListener('focus', onFocus);
    return () => { clearInterval(iv); window.removeEventListener('focus', onFocus); };
  }, [isAuthenticated, fetchAll]);

  // ── Stats ──────────────────────────────────────────────────────────────────
  const total = signals.length;
  const buys  = signals.filter(s => s.action === 'BUY').length;
  const sells = signals.filter(s => s.action === 'SELL').length;

  const filtered = signals.filter(s => {
    if (filter !== 'ALL' && s.action !== filter) return false;
    if (symbolFilter !== 'ALL' && s.symbol !== symbolFilter) return false;
    return true;
  });

  if (loading) return (
    <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
      <div className="h-12 w-12 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent" />
    </div>
  );
  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-[#0a0e1a]">

      {/* ── Toast Notifications ── */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map(t => (
          <div key={t.id}
            className={`pointer-events-auto flex items-center gap-3 rounded-xl border px-4 py-3 shadow-2xl backdrop-blur-sm transition-all animate-in slide-in-from-right-4 ${
              t.action === 'BUY'
                ? 'border-emerald-500/50 bg-emerald-950/90 shadow-emerald-500/20'
                : 'border-rose-500/50 bg-rose-950/90 shadow-rose-500/20'
            }`}>
            <span className={`text-lg font-bold ${t.action === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}`}>
              {t.action === 'BUY' ? '▲' : '▼'}
            </span>
            <div>
              <p className="text-xs font-bold text-white">New {t.action} Signal</p>
              <p className="text-xs text-slate-400">{t.msg}</p>
            </div>
            <button
              onClick={() => setToasts(prev => prev.filter(x => x.id !== t.id))}
              className="ml-2 text-slate-500 hover:text-white transition pointer-events-auto">✕</button>
          </div>
        ))}
      </div>

      {/* ── Nav ── */}
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
                  ● {liveCount} live signal{liveCount !== 1 ? 's' : ''}
                </span>
              )}
              <button
                onClick={fetchAll} disabled={loadingData}
                className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-50 transition">
                {loadingData ? 'Loading…' : '↻ Refresh'}
              </button>
              <Link href="/dashboard" className="text-sm font-medium text-slate-400 hover:text-white transition">
                ← Dashboard
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* ── Header ── */}
      <div className="border-b border-slate-800/50 bg-[#0f1419]">
        <div className="mx-auto max-w-7xl px-6 py-8 flex items-start justify-between">
          <div>
            <h1 className="mb-2 text-3xl font-bold text-white">SmartRisk Signal History</h1>
            <p className="text-slate-400">Last 5 months — all assets and timeframes — instant live updates</p>
          </div>
          {lastUpdated && (
            <p className="text-xs text-slate-500 mt-1 whitespace-nowrap">
              Updated {lastUpdated.toISOString().replace('T',' ').slice(0,19)} UTC
            </p>
          )}
        </div>
      </div>

      {/* ── Stats ── */}
      <div className="border-b border-slate-800/50 bg-[#0f1419]">
        <div className="mx-auto max-w-7xl px-6 py-6 flex justify-center gap-6">
          {[
            { label: 'TOTAL SIGNALS', value: total, color: 'text-white' },
            { label: 'BUY SIGNALS',   value: buys,  color: 'text-emerald-400' },
            { label: 'SELL SIGNALS',  value: sells, color: 'text-rose-400' },
          ].map(({ label, value, color }) => (
            <div key={label} className="rounded-xl border border-slate-800/50 bg-[#0a0e1a] p-6 text-center min-w-[140px]">
              {loadingData && value === 0
                ? <div className="inline-block h-8 w-8 mb-1 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent"/>
                : <div className={`mb-1 text-4xl font-bold ${color}`}>{value}</div>
              }
              <div className="text-sm text-slate-500">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Filters ── */}
      <div className="mx-auto max-w-7xl px-6 py-6">
        <div className="mb-6 flex flex-wrap items-center gap-6">
          <div>
            <label className="mb-2 block text-xs font-medium text-slate-400">FILTER BY ACTION</label>
            <div className="flex gap-2">
              {(['ALL','BUY','SELL'] as const).map(f => (
                <button key={f} onClick={() => setFilter(f)}
                  className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                    filter===f?'bg-cyan-500 text-white':'border border-slate-700 bg-slate-800/50 text-slate-300 hover:bg-slate-700/50'}`}>
                  {f}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="mb-2 block text-xs font-medium text-slate-400">FILTER BY SYMBOL</label>
            <div className="flex gap-2 flex-wrap">
              {(['ALL',...SYMBOLS] as const).map(s => (
                <button key={s} onClick={() => setSymbolFilter(s as 'ALL'|SymbolType)}
                  className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                    symbolFilter===s?'bg-cyan-500 text-white':'border border-slate-700 bg-slate-800/50 text-slate-300 hover:bg-slate-700/50'}`}>
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
                  {['DATE & TIME (UTC)','SYMBOL','TIMEFRAME','ACTION','ENTRY PRICE','STOP LOSS','TARGET','STATUS'].map(h=>(
                    <th key={h} className={`px-6 py-4 text-xs font-semibold uppercase tracking-wider text-slate-400 ${
                      ['ENTRY PRICE','STOP LOSS','TARGET'].includes(h)?'text-right':h==='STATUS'?'text-center':'text-left'}`}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {loadingData && signals.length===0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center">
                      <div className="flex flex-col items-center gap-3">
                        <div className="h-8 w-8 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent"/>
                        <p className="text-slate-400">Loading all signals in parallel…</p>
                      </div>
                    </td>
                  </tr>
                ) : filtered.length===0 ? (
                  <tr><td colSpan={8} className="px-6 py-12 text-center text-slate-400">No signals found</td></tr>
                ) : filtered.map(signal => (
                  <tr key={signal.id}
                    className={`transition-colors ${
                      signal.isNew
                        ? signal.action==='BUY'
                          ? 'bg-emerald-500/10 hover:bg-emerald-500/15 border-l-2 border-emerald-400'
                          : 'bg-rose-500/10 hover:bg-rose-500/15 border-l-2 border-rose-400'
                        : 'hover:bg-slate-800/30'
                    }`}>
                    <td className="px-6 py-4 text-sm text-slate-300 whitespace-nowrap">
                      {signal.isNew && <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse"/>}
                      {new Date(signal.timestamp).toISOString().replace('T',' ').slice(0,19)} UTC
                    </td>
                    <td className="px-6 py-4">
                      <span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-semibold text-white">{signal.symbol}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="rounded-full bg-blue-500/20 px-3 py-1 text-xs font-semibold text-blue-400">{signal.timeframe.toUpperCase()}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
                        signal.action==='BUY'?'bg-emerald-500/20 text-emerald-400':'bg-rose-500/20 text-rose-400'}`}>
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
            <p><strong className="text-white">Stop Loss:</strong> Outer zone bottom (BUY) or outer zone top (SELL) — risk boundary</p>
            <p><strong className="text-white">Target:</strong> Outer zone top (BUY) or outer zone bottom (SELL) — profit target</p>
            <p><strong className="text-white">Live Updates:</strong> New signals appear instantly at the top with a highlight — no page refresh needed</p>
            <p className="mt-4 rounded-lg bg-cyan-500/10 border border-cyan-500/30 p-3 text-cyan-300">
              Showing last 5 months · {SYMBOLS.length} assets · {TIMEFRAMES.length} timeframes · Auto-refreshes every 60 s · WebSocket reconnects automatically
            </p>
          </div>
        </div>
      </div>

      <footer className="mt-16 border-t border-slate-800/50 bg-[#0f1419] py-8">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <p className="text-sm text-slate-500">© 2026 SmartRisk. Reversal signals for crypto and gold markets.</p>
        </div>
      </footer>
    </div>
  );
}