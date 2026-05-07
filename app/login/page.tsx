'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/AuthContext';
import Link from 'next/link';

interface Toast {
  id: number;
  type: 'error' | 'success' | 'info';
  messages: string[];
}

function ToastNotification({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 6000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const styles = {
    error: {
      container: 'bg-slate-900 border border-red-500/60 shadow-xl shadow-red-500/10',
      icon: '❌',
      title: 'text-red-400',
      titleText: 'Login failed',
      dot: 'bg-red-400',
      bar: 'bg-red-500',
    },
    success: {
      container: 'bg-slate-900 border border-emerald-500/60 shadow-xl shadow-emerald-500/10',
      icon: '✅',
      title: 'text-emerald-400',
      titleText: 'Success!',
      dot: 'bg-emerald-400',
      bar: 'bg-emerald-500',
    },
    info: {
      container: 'bg-slate-900 border border-cyan-500/60 shadow-xl shadow-cyan-500/10',
      icon: 'ℹ️',
      title: 'text-cyan-400',
      titleText: 'Info',
      dot: 'bg-cyan-400',
      bar: 'bg-cyan-500',
    },
  };

  const s = styles[toast.type];

  return (
    <div className={`w-80 rounded-xl p-4 ${s.container}`} style={{ animation: 'slideIn 0.3s ease-out' }}>
      <div className="flex items-start gap-3">
        <span className="text-xl shrink-0 mt-0.5">{s.icon}</span>
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-semibold mb-2 ${s.title}`}>{s.titleText}</p>
          <ul className="space-y-1">
            {toast.messages.map((msg, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${s.dot}`}></span>
                <span>{msg}</span>
              </li>
            ))}
          </ul>
        </div>
        <button
          onClick={onClose}
          className="shrink-0 text-slate-500 hover:text-slate-300 transition text-lg leading-none"
        >
          ×
        </button>
      </div>
      <div className="mt-3 h-0.5 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${s.bar}`} style={{ animation: 'shrink 6s linear forwards' }} />
      </div>
    </div>
  );
}

// Map technical backend errors to friendly messages
function friendlyLoginError(raw: string): string {
  const map: Record<string, string> = {
    'No active account found with the given credentials': 'Incorrect email or password. Please try again.',
    'Invalid credentials': 'Incorrect email or password. Please try again.',
    'Account is disabled': 'Your account has been disabled. Please contact support.',
    'This account is inactive': 'Your account is not active. Please check your email.',
    'Login failed': 'Unable to log in. Please check your email and password.',
  };
  return map[raw] ?? raw;
}

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [loading, setLoading] = useState(false);

  const addToast = (type: Toast['type'], messages: string[]) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, type, messages }]);
  };

  const removeToast = (id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await login(email, password);
    } catch (err: any) {
      const raw = err.message || 'Something went wrong. Please try again.';
      addToast('error', [friendlyLoginError(raw)]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Toast Container - fixed bottom-right */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 pointer-events-none">
        {toasts.map(toast => (
          <div key={toast.id} className="pointer-events-auto">
            <ToastNotification toast={toast} onClose={() => removeToast(toast.id)} />
          </div>
        ))}
      </div>

      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 py-12 px-4">
        <div className="max-w-md w-full">
          <div className="text-center mb-8">
            <h2 className="text-4xl font-bold text-white mb-2">Welcome Back</h2>
            <p className="text-slate-400">Login to access your trading dashboard</p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-cyan-500 focus:outline-none transition"
                  placeholder="your@email.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-cyan-500 focus:outline-none transition"
                  placeholder="••••••••"
                />
                <div className="mt-2 text-right">
                  <Link href="/forgot-password" className="text-sm text-cyan-400 hover:text-cyan-300">
                    Forgot Password?
                  </Link>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-white border-r-transparent"></span>
                    Logging in...
                  </span>
                ) : (
                  'Login'
                )}
              </button>
            </form>

            <div className="mt-6 text-center text-sm text-slate-400">
              Don't have an account?{' '}
              <Link href="/register" className="text-cyan-400 hover:text-cyan-300 font-semibold">
                Start your 3-day free trial
              </Link>
            </div>
          </div>
        </div>
      </div>

      <style jsx global>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </>
  );
}
