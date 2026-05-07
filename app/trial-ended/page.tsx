'use client';

import { useAuth } from '@/lib/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function TrialEndedPage() {
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 py-12 px-4">
      <div className="max-w-2xl w-full text-center">
        <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-500/10 to-orange-500/10 p-12">
          <div className="mb-6">
            <div className="inline-flex h-20 w-20 items-center justify-center rounded-full bg-amber-500/20 text-5xl">
              ⏰
            </div>
          </div>

          <h1 className="text-4xl font-bold text-white mb-4">
            Your Free Trial Has Ended
          </h1>

          <p className="text-xl text-slate-300 mb-8">
            Thank you for trying SmartRisk, {user?.full_name || user?.email}!
          </p>

          <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-6 mb-8">
            <h3 className="text-lg font-semibold text-white mb-4">
              What happened during your 3-day trial:
            </h3>
            <div className="space-y-3 text-left">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-cyan-500/20">
                  <span className="text-cyan-400">✓</span>
                </div>
                <p className="text-slate-300">You had full access to all trading signals</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-cyan-500/20">
                  <span className="text-cyan-400">✓</span>
                </div>
                <p className="text-slate-300">Real-time market data for 4 cryptocurrencies</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-cyan-500/20">
                  <span className="text-cyan-400">✓</span>
                </div>
                <p className="text-slate-300">SmartRisk BUY/SELL signals across 10 timeframes</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 p-6 mb-8">
            <h3 className="text-lg font-semibold text-white mb-2">
              🎉 Thank You for Trying SmartRisk!
            </h3>
            <p className="text-slate-300">
              We hope you enjoyed exploring our SmartRisk trading platform.<br />
              Payment features are available now to continue your journey..
            </p>
          </div>

          <div className="space-y-4">
            <button
              onClick={() => router.push('/')}
              className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition"
            >
              Return to Home
            </button>

            <p className="text-sm text-slate-500">
              Questions? Contact us at alberttyagi123@gmail.com or smarttriskfx@gmail.com
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
