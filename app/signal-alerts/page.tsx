'use client';

import { useAuth } from '@/lib/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';

type CryptoOption = 'BTCUSD' | 'ETHUSD' | 'LTCUSD' | 'XAUUSD';
type TimeframeOption = '5m' | '15m' | '30m' | '1h' | '2h' | '4h' | '1d';

export default function SignalAlertsPage() {
  const { user, isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const [selectedCrypto, setSelectedCrypto] = useState<CryptoOption>('BTCUSD');
  const [selectedTimeframe, setSelectedTimeframe] = useState<TimeframeOption>('1h');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, router]);

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

  // Check if user has PAID subscription (manual_subscription = 'activated')
  const isPaidSubscriber = user?.manual_subscription === 'activated';
  const isTrialUser = user?.subscription_status?.status === 'trial' || false;

  const cryptoOptions: { value: CryptoOption; label: string; icon: string }[] = [
    { value: 'BTCUSD', label: 'Bitcoin', icon: '₿' },
    { value: 'ETHUSD', label: 'Ethereum', icon: 'Ξ' },
    { value: 'LTCUSD', label: 'Litecoin', icon: 'Ł' },
    { value: 'XAUUSD', label: 'Gold (XAU)', icon: '🪙' },
  ];

  const timeframeOptions: { value: TimeframeOption; label: string }[] = [
    { value: '5m', label: '5 Minutes' },
    { value: '15m', label: '15 Minutes' },
    { value: '30m', label: '30 Minutes' },
    { value: '1h', label: '1 Hour' },
    { value: '2h', label: '2 Hours' },
    { value: '4h', label: '4 Hours' },
    { value: '1d', label: '1 Day' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isPaidSubscriber) {
      setErrorMessage('Signal alerts are only available for paid subscribers');
      setSubmitStatus('error');
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus('idle');
    setErrorMessage('');

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/signal-alerts/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          crypto: selectedCrypto,
          timeframe: selectedTimeframe,
          email: user?.email,
        }),
      });

      if (response.ok) {
        setSubmitStatus('success');
        setTimeout(() => setSubmitStatus('idle'), 5000);
      } else {
        const data = await response.json();
        setErrorMessage(data.error || 'Failed to set up signal alert');
        setSubmitStatus('error');
      }
    } catch (error) {
      setErrorMessage('Network error. Please try again.');
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

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
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 mb-6">
            <span className="text-4xl">🔔</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-4">
            Signal Alerts
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Stay informed without constantly monitoring charts. Get instant email notifications when new trading signals are generated for your selected cryptocurrency and timeframe.
          </p>
        </div>

        {/* Subscription Status Banner */}
        {!isPaidSubscriber && (
          <div className={`rounded-xl border p-6 mb-8 ${
            isTrialUser 
              ? 'border-amber-500/30 bg-gradient-to-br from-amber-500/10 to-orange-500/10'
              : 'border-red-500/30 bg-gradient-to-br from-red-500/10 to-pink-500/10'
          }`}>
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                <span className="text-2xl">{isTrialUser ? '⏰' : '🔒'}</span>
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-white mb-2">
                  {isTrialUser ? 'Premium Feature - Upgrade Required' : 'Subscription Required'}
                </h3>
                <p className="text-slate-300 mb-4">
                  {isTrialUser 
                    ? 'Signal alerts are available exclusively for paid subscribers. Upgrade your account to receive instant email notifications for new trading signals.'
                    : 'This feature requires an active paid subscription. Please activate your subscription to set up signal alerts.'
                  }
                </p>
                <Link
                  href="/subscription"
                  className="inline-flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white px-6 py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-emerald-500/50 transition"
                >
                  {isTrialUser ? 'Upgrade to Paid Plan' : 'View Subscription Plans'}
                  <span>→</span>
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Alert Setup Form */}
        <div className="rounded-2xl border border-slate-800/50 bg-[#0f1419] p-8 mb-8">
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Info Message */}
            <div className="rounded-lg bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 p-6">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-cyan-500/20 flex items-center justify-center">
                  <span className="text-xl">💡</span>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">How Signal Alerts Work</h3>
                  <p className="text-slate-300 text-sm leading-relaxed">
                    Configure your preferred cryptocurrency and timeframe below. When a new SmartRisk trading signal is generated matching your criteria, you'll receive an instant email notification with complete signal details including entry price, stop loss, and target levels. No need to monitor charts 24/7 - we'll keep you informed.
                  </p>
                </div>
              </div>
            </div>

            {/* Cryptocurrency Selection */}
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-3">
                Select Cryptocurrency
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {cryptoOptions.map((crypto) => (
                  <button
                    key={crypto.value}
                    type="button"
                    onClick={() => setSelectedCrypto(crypto.value)}
                    disabled={!isPaidSubscriber}
                    className={`relative p-4 rounded-xl border-2 transition-all ${
                      selectedCrypto === crypto.value
                        ? 'border-cyan-500 bg-cyan-500/10'
                        : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'
                    } ${!isPaidSubscriber ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                  >
                    <div className="text-3xl mb-2">{crypto.icon}</div>
                    <div className="text-sm font-semibold text-white">{crypto.label}</div>
                    <div className="text-xs text-slate-400">{crypto.value}</div>
                    {selectedCrypto === crypto.value && (
                      <div className="absolute top-2 right-2 w-6 h-6 rounded-full bg-cyan-500 flex items-center justify-center">
                        <span className="text-white text-xs">✓</span>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Timeframe Selection */}
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-3">
                Select Timeframe
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {timeframeOptions.map((tf) => (
                  <button
                    key={tf.value}
                    type="button"
                    onClick={() => setSelectedTimeframe(tf.value)}
                    disabled={!isPaidSubscriber}
                    className={`relative p-4 rounded-lg border-2 transition-all ${
                      selectedTimeframe === tf.value
                        ? 'border-purple-500 bg-purple-500/10'
                        : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'
                    } ${!isPaidSubscriber ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                  >
                    <div className="text-sm font-semibold text-white">{tf.label}</div>
                    <div className="text-xs text-slate-400 uppercase">{tf.value}</div>
                    {selectedTimeframe === tf.value && (
                      <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-purple-500 flex items-center justify-center">
                        <span className="text-white text-xs">✓</span>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Current Selection Summary */}
            <div className="rounded-lg bg-slate-800/50 border border-slate-700 p-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-3">Your Alert Configuration</h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Cryptocurrency:</span>
                  <span className="text-white font-semibold">
                    {cryptoOptions.find(c => c.value === selectedCrypto)?.label} ({selectedCrypto})
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Timeframe:</span>
                  <span className="text-white font-semibold">
                    {timeframeOptions.find(t => t.value === selectedTimeframe)?.label}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Email:</span>
                  <span className="text-white font-semibold">{user?.email}</span>
                </div>
              </div>
            </div>

            {/* Status Messages */}
            {submitStatus === 'success' && (
              <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/30 p-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">✅</span>
                  <div>
                    <p className="text-emerald-400 font-semibold">Alert Activated Successfully!</p>
                    <p className="text-sm text-slate-300">You'll receive email notifications for new signals.</p>
                  </div>
                </div>
              </div>
            )}

            {submitStatus === 'error' && (
              <div className="rounded-lg bg-red-500/10 border border-red-500/30 p-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">❌</span>
                  <div>
                    <p className="text-red-400 font-semibold">Error</p>
                    <p className="text-sm text-slate-300">{errorMessage}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!isPaidSubscriber || isSubmitting}
              className={`w-full py-4 rounded-xl font-bold text-lg transition-all ${
                isPaidSubscriber
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:shadow-lg hover:shadow-purple-500/50'
                  : 'bg-slate-700 text-slate-400 cursor-not-allowed'
              }`}
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Setting up alert...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  🔔 Activate Signal Alert
                </span>
              )}
            </button>
          </form>
        </div>

        {/* Features Section */}
        <div className="grid md:grid-cols-3 gap-6">
          <div className="rounded-xl border border-slate-800/50 bg-[#0f1419] p-6">
            <div className="w-12 h-12 rounded-lg bg-cyan-500/20 flex items-center justify-center mb-4">
              <span className="text-2xl">⚡</span>
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Instant Notifications</h3>
            <p className="text-sm text-slate-400">
              Receive alerts within seconds of signal generation
            </p>
          </div>

          <div className="rounded-xl border border-slate-800/50 bg-[#0f1419] p-6">
            <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center mb-4">
              <span className="text-2xl">📊</span>
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Complete Details</h3>
            <p className="text-sm text-slate-400">
              Get entry price, stop loss, and target levels in every alert
            </p>
          </div>

          <div className="rounded-xl border border-slate-800/50 bg-[#0f1419] p-6">
            <div className="w-12 h-12 rounded-lg bg-pink-500/20 flex items-center justify-center mb-4">
              <span className="text-2xl">🎯</span>
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Customizable</h3>
            <p className="text-sm text-slate-400">
              Choose your preferred crypto and timeframe combination
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}