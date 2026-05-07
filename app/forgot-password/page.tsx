'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiEndpoint } from '@/lib/config';

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(apiEndpoint('/api/users/forgot-password/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      const data = await response.json();

      if (data.success) {
        setSuccess(true);
        // Redirect to reset password page
        setTimeout(() => {
          router.push(`/reset-password?id=${data.reset_id}&email=${encodeURIComponent(email)}`);
        }, 2000);
      } else {
        setError(data.error || 'Failed to send reset code');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 py-12 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-500/30 mb-4">
            <span className="text-3xl">🔒</span>
          </div>
          <h2 className="text-4xl font-bold text-white mb-2">Forgot Password?</h2>
          <p className="text-slate-400">
            No worries! Enter your email and we'll send you a reset code.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
          {success ? (
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/30 mb-4">
                <span className="text-3xl">✅</span>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Check Your Email!</h3>
              <p className="text-slate-400 mb-4">
                We've sent a 6-digit code to <span className="text-cyan-400 font-semibold">{email}</span>
              </p>
              <p className="text-sm text-slate-500">Redirecting to reset page...</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Email Address
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

              {error && (
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30">
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-white border-r-transparent"></span>
                    Sending Code...
                  </span>
                ) : (
                  'Send Reset Code'
                )}
              </button>
            </form>
          )}

          <div className="mt-6 text-center text-sm text-slate-400">
            Remember your password?{' '}
            <Link href="/login" className="text-cyan-400 hover:text-cyan-300 font-semibold">
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
