'use client';

import { useAuth } from '@/lib/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';

export default function SubscriptionPage() {
  const { user, isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const [copied, setCopied] = useState(false);
  const [timeLeft, setTimeLeft] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, router]);

  // Real-time countdown timer
  useEffect(() => {
    if (!user?.subscription_status?.trial_end) return;

    const updateCountdown = () => {
      if (!user?.subscription_status?.trial_end) return;
      
      const trialEnd = new Date(user.subscription_status!.trial_end!);
      const now = new Date();
      const diff = trialEnd.getTime() - now.getTime();

      if (diff <= 0) {
        setTimeLeft({ days: 0, hours: 0, minutes: 0, seconds: 0 });
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      setTimeLeft({ days, hours, minutes, seconds });
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);

    return () => clearInterval(interval);
  }, [user?.subscription_status?.trial_end]);

  const copyEmailToClipboard = () => {
    navigator.clipboard.writeText('smarttriskfx@gmail.com');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

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

  const isSubscriptionActive = user?.subscription_status?.is_active || false;
  const isTrialActive = user?.trial_status === 'active' || user?.subscription_status?.trial_status === 'active';
  const isPaidSubscription = user?.manual_subscription === 'activated';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
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

      {/* Main Content */}
      <div className="mx-auto max-w-4xl px-6 py-12">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 mb-6">
            <span className="text-4xl">{isPaidSubscription ? '👑' : isTrialActive ? '🎁' : '🔒'}</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-4">
            {isPaidSubscription 
              ? 'Your Subscription' 
              : isTrialActive 
                ? 'Free Trial Active' 
                : 'Activate Your Subscription'
            }
          </h1>
          <p className="text-xl text-slate-400">
            {isPaidSubscription 
              ? 'You have full access to all premium features'
              : isTrialActive
                ? 'Enjoy your 3-day free trial with full access'
                : 'Get unlimited access to SmartRisk trading signals'
            }
          </p>
        </div>

        {isPaidSubscription ? (
          // Paid Subscription View
          <div className="rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 p-8 mb-8">
            <div className="flex items-center justify-center gap-3 mb-6">
              <span className="text-3xl">✅</span>
              <h2 className="text-2xl font-bold text-white">Subscription Active</h2>
            </div>
            
            <div className="space-y-4 text-center">
              <p className="text-lg text-slate-300">
                You have full access to all premium features including:
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-4">
                  <div className="text-2xl mb-2">📊</div>
                  <p className="text-white font-semibold">Real-time Trading Signals</p>
                  <p className="text-sm text-slate-400">SmartRisk BUY/SELL signals</p>
                </div>
                
                <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-4">
                  <div className="text-2xl mb-2">💹</div>
                  <p className="text-white font-semibold">4 Cryptocurrencies</p>
                  <p className="text-sm text-slate-400">BTC, ETH, XAU, LTC</p>
                </div>
                
                <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-4">
                  <div className="text-2xl mb-2">⏰</div>
                  <p className="text-white font-semibold">10 Timeframes</p>
                  <p className="text-sm text-slate-400">From 1m to 1 month</p>
                </div>
                
                <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-4">
                  <div className="text-2xl mb-2">📈</div>
                  <p className="text-white font-semibold">Signal History</p>
                  <p className="text-sm text-slate-400">Last 5 months of data</p>
                </div>
              </div>
            </div>
          </div>
        ) : isTrialActive ? (
          // Trial Active View with Countdown
          <div className="rounded-2xl border border-cyan-500/30 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 p-8 mb-8">
            <div className="flex items-center justify-center gap-3 mb-6">
              <span className="text-3xl">🎁</span>
              <h2 className="text-2xl font-bold text-white">Free Trial Active</h2>
            </div>
            
            {/* Countdown Timer */}
            <div className="mb-8">
              <p className="text-center text-slate-300 mb-4">Your trial ends in:</p>
              <div className="grid grid-cols-4 gap-4 max-w-2xl mx-auto">
                <div className="rounded-lg bg-slate-900/50 border border-cyan-500/30 p-4 text-center">
                  <div className="text-4xl font-bold text-cyan-400">{timeLeft.days}</div>
                  <div className="text-sm text-slate-400 mt-1">Days</div>
                </div>
                <div className="rounded-lg bg-slate-900/50 border border-cyan-500/30 p-4 text-center">
                  <div className="text-4xl font-bold text-cyan-400">{timeLeft.hours}</div>
                  <div className="text-sm text-slate-400 mt-1">Hours</div>
                </div>
                <div className="rounded-lg bg-slate-900/50 border border-cyan-500/30 p-4 text-center">
                  <div className="text-4xl font-bold text-cyan-400">{timeLeft.minutes}</div>
                  <div className="text-sm text-slate-400 mt-1">Minutes</div>
                </div>
                <div className="rounded-lg bg-slate-900/50 border border-cyan-500/30 p-4 text-center">
                  <div className="text-4xl font-bold text-cyan-400">{timeLeft.seconds}</div>
                  <div className="text-sm text-slate-400 mt-1">Seconds</div>
                </div>
              </div>
            </div>
            
            <div className="space-y-4 text-center">
              <p className="text-lg text-slate-300">
                You currently have full access to all premium features:
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-4">
                  <div className="text-2xl mb-2">📊</div>
                  <p className="text-white font-semibold">Real-time Trading Signals</p>
                  <p className="text-sm text-slate-400">SmartRisk BUY/SELL signals</p>
                </div>
                
                <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-4">
                  <div className="text-2xl mb-2">💹</div>
                  <p className="text-white font-semibold">4 Cryptocurrencies</p>
                  <p className="text-sm text-slate-400">BTC, ETH, XAU, LTC</p>
                </div>
                
                <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-4">
                  <div className="text-2xl mb-2">⏰</div>
                  <p className="text-white font-semibold">10 Timeframes</p>
                  <p className="text-sm text-slate-400">From 1m to 1 month</p>
                </div>
                
                <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-4">
                  <div className="text-2xl mb-2">📈</div>
                  <p className="text-white font-semibold">Signal History</p>
                  <p className="text-sm text-slate-400">Last 5 months of data</p>
                </div>
              </div>

              {/* Upgrade CTA */}
              <div className="mt-8 p-6 rounded-xl bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-emerald-500/30">
                <h3 className="text-xl font-bold text-white mb-2">🚀 Upgrade to Premium</h3>
                <p className="text-slate-300 mb-4">
                  Don't lose access! Contact us to activate your paid subscription before your trial ends.
                </p>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                  <a
                    href="mailto:smarttriskfx@gmail.com?subject=Subscription%20Activation%20Request&body=Hello,%20I%20would%20like%20to%20activate%20my%20subscription%20for%20SmartRisk.%0D%0A%0D%0AMy%20account%20email:%20"
                    className="inline-block bg-gradient-to-r from-emerald-500 to-cyan-500 text-white px-6 py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-emerald-500/50 transition"
                  >
                    📧 Contact Support
                  </a>
                </div>
              </div>
            </div>
          </div>
        ) : (
          // Inactive Subscription View
          <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-500/10 to-orange-500/10 p-8 mb-8">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-amber-500/20 mb-4">
                <span className="text-3xl">🔒</span>
              </div>
              <h2 className="text-2xl font-bold text-white mb-4">Subscription Required</h2>
              <p className="text-lg text-slate-300 mb-6">
                To access premium features and SmartRisk trading signals, please activate your subscription.
              </p>
            </div>

            {/* Contact Information */}
            <div className="rounded-xl bg-slate-900/50 border border-slate-800 p-6 mb-6">
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span>📧</span>
                Get Your Subscription Activated
              </h3>
              
              <div className="space-y-4">
                <p className="text-slate-300">
                  Contact our support team to activate your subscription and unlock all premium features:
                </p>
                
                <div className="rounded-lg bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 p-4">
                  <p className="text-sm text-slate-400 mb-2">Email Support</p>
                  <div className="space-y-1">
                    <a 
                      href="mailto:alberttyagi123@gmail.com" 
                      className="block text-lg font-semibold text-cyan-400 hover:text-cyan-300 transition"
                    >
                      alberttyagi123@gmail.com
                    </a>
                    <a 
                      href="mailto:smarttriskfx@gmail.com" 
                      className="block text-lg font-semibold text-cyan-400 hover:text-cyan-300 transition"
                    >
                      smarttriskfx@gmail.com
                    </a>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                      <span className="text-xl">⚡</span>
                    </div>
                    <div>
                      <p className="font-semibold text-white">Fast Response</p>
                      <p className="text-sm text-slate-400">Get reply within 24 hours</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                      <span className="text-xl">🛡️</span>
                    </div>
                    <div>
                      <p className="font-semibold text-white">Secure & Trusted</p>
                      <p className="text-sm text-slate-400">Your data is safe with us</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                      <span className="text-xl">🎯</span>
                    </div>
                    <div>
                      <p className="font-semibold text-white">Dedicated Support</p>
                      <p className="text-sm text-slate-400">Personal assistance for setup</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                      <span className="text-xl">💎</span>
                    </div>
                    <div>
                      <p className="font-semibold text-white">Premium Access</p>
                      <p className="text-sm text-slate-400">Instant activation available</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* What You'll Get */}
            <div className="rounded-xl bg-slate-900/50 border border-slate-800 p-6">
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span>✨</span>
                What's Included
              </h3>
              
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <span className="text-emerald-400 text-sm">✓</span>
                  </div>
                  <p className="text-slate-300">Real-time SmartRisk trading signals for 4 cryptocurrencies</p>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <span className="text-emerald-400 text-sm">✓</span>
                  </div>
                  <p className="text-slate-300">Access to 10 different timeframes (1m to 1 month)</p>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <span className="text-emerald-400 text-sm">✓</span>
                  </div>
                  <p className="text-slate-300">Complete signal history for the last 5 months</p>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <span className="text-emerald-400 text-sm">✓</span>
                  </div>
                  <p className="text-slate-300">Live market data and price updates</p>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <span className="text-emerald-400 text-sm">✓</span>
                  </div>
                  <p className="text-slate-300">Priority customer support</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* CTA Button */}
        <div className="text-center space-y-4">
          {isPaidSubscription ? (
            <Link
              href="/dashboard"
              className="inline-block bg-gradient-to-r from-cyan-500 to-blue-500 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:shadow-lg hover:shadow-cyan-500/50 transition"
            >
              Go to Dashboard →
            </Link>
          ) : isTrialActive ? (
            <div className="space-y-4">
              <Link
                href="/dashboard"
                className="inline-block bg-gradient-to-r from-cyan-500 to-blue-500 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:shadow-lg hover:shadow-cyan-500/50 transition"
              >
                Continue to Dashboard →
              </Link>
              <p className="text-sm text-slate-400">
                Enjoying your trial? Contact us to upgrade:{' '}
                <a href="mailto:smarttriskfx@gmail.com" className="text-cyan-400 hover:text-cyan-300">
                  smarttriskfx@gmail.com
                </a>
              </p>
            </div>
          ) : (
            <>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <a
                  href="mailto:smarttriskfx@gmail.com?subject=Subscription%20Activation%20Request&body=Hello,%20I%20would%20like%20to%20activate%20my%20subscription%20for%20SmartRisk.%0D%0A%0D%0AMy%20account%20email:%20"
                  className="inline-block bg-gradient-to-r from-emerald-500 to-cyan-500 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:shadow-lg hover:shadow-emerald-500/50 transition"
                >
                  📧 Email Support
                </a>
                <button
                  onClick={copyEmailToClipboard}
                  className="inline-block bg-gradient-to-r from-blue-500 to-purple-500 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:shadow-lg hover:shadow-blue-500/50 transition"
                >
                  {copied ? '✓ Copied!' : '📋 Copy Email Address'}
                </button>
              </div>
              <p className="text-sm text-slate-400">
                Email: <span className="text-cyan-400 font-semibold">smarttriskfx@gmail.com</span>
              </p>
            </>
          )}
        </div>

        {/* Help Text */}
        <p className="text-center text-sm text-slate-500 mt-6">
          Questions? Email us at{' '}
          <a href="mailto:alberttyagi123@gmail.com" className="text-cyan-400 hover:text-cyan-300">
            alberttyagi123@gmail.com
          </a>
          {' '}or{' '}
          <a href="mailto:smarttriskfx@gmail.com" className="text-cyan-400 hover:text-cyan-300">
            smarttriskfx@gmail.com
          </a>
        </p>
      </div>
    </div>
  );
}