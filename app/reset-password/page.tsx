'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { apiEndpoint } from '@/lib/config';

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const resetId = searchParams.get('id');
  const email = searchParams.get('email');
  
  const [step, setStep] = useState<'otp' | 'password'>('otp');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState('');
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes
  
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Countdown timer
  useEffect(() => {
    if (timeLeft <= 0) return;
    
    const timer = setInterval(() => {
      setTimeLeft(prev => prev - 1);
    }, 1000);
    
    return () => clearInterval(timer);
  }, [timeLeft]);

  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);
    
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newOtp = [...otp];
    
    for (let i = 0; i < pastedData.length; i++) {
      newOtp[i] = pastedData[i];
    }
    
    setOtp(newOtp);
    const nextIndex = Math.min(pastedData.length, 5);
    inputRefs.current[nextIndex]?.focus();
  };

  const handleVerifyOtp = async () => {
    const otpCode = otp.join('');
    
    if (otpCode.length !== 6) {
      setError('Please enter all 6 digits');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(apiEndpoint('/api/users/verify-reset-otp/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reset_id: resetId,
          otp: otpCode
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setStep('password');
      } else {
        setError(data.error || 'Invalid OTP');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await fetch(apiEndpoint('/api/users/reset-password/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reset_id: resetId,
          otp: otp.join(''),
          new_password: newPassword,
          new_password2: confirmPassword
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Redirect to login
        setTimeout(() => {
          router.push('/login?reset=success');
        }, 2000);
      } else {
        setError(data.error || 'Failed to reset password');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    setError('');
    
    try {
      const response = await fetch(apiEndpoint('/api/users/resend-reset-otp/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reset_id: resetId })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setOtp(['', '', '', '', '', '']);
        setTimeLeft(600);
        inputRefs.current[0]?.focus();
      } else {
        setError(data.error || 'Failed to resend code');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setResending(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!resetId || !email) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="text-center">
          <p className="text-red-400 mb-4">Invalid reset link</p>
          <Link href="/forgot-password" className="text-cyan-400 hover:text-cyan-300">
            Request a new reset link
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 py-12 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-500/30 mb-4">
            <span className="text-3xl">{step === 'otp' ? '🔐' : '🔑'}</span>
          </div>
          <h2 className="text-4xl font-bold text-white mb-2">
            {step === 'otp' ? 'Enter Reset Code' : 'Create New Password'}
          </h2>
          <p className="text-slate-400">
            {step === 'otp' ? (
              <>Code sent to <span className="text-cyan-400 font-semibold">{email}</span></>
            ) : (
              'Choose a strong password for your account'
            )}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
          {step === 'otp' ? (
            <>
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-300 mb-4 text-center">
                  Enter 6-Digit Code
                </label>
                
                <div className="flex gap-2 justify-center" onPaste={handlePaste}>
                  {otp.map((digit, index) => (
                    <input
                      key={index}
                      ref={el => { inputRefs.current[index] = el; }}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={e => handleOtpChange(index, e.target.value)}
                      onKeyDown={e => handleKeyDown(index, e)}
                      className="w-12 h-14 text-center text-2xl font-bold rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-cyan-500 focus:outline-none transition"
                    />
                  ))}
                </div>
              </div>

              <div className="mb-6 text-center">
                {timeLeft > 0 ? (
                  <p className="text-sm text-slate-400">
                    Code expires in <span className="text-cyan-400 font-semibold">{formatTime(timeLeft)}</span>
                  </p>
                ) : (
                  <p className="text-sm text-red-400">Code expired. Please request a new one.</p>
                )}
              </div>

              {error && (
                <div className="mb-4 p-4 rounded-lg bg-red-500/10 border border-red-500/30">
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              )}

              <button
                onClick={handleVerifyOtp}
                disabled={loading || otp.join('').length !== 6}
                className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition disabled:opacity-50 disabled:cursor-not-allowed mb-4"
              >
                {loading ? 'Verifying...' : 'Verify Code'}
              </button>

              <button
                onClick={handleResend}
                disabled={resending || timeLeft > 540}
                className="w-full text-cyan-400 hover:text-cyan-300 py-2 text-sm font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {resending ? 'Sending...' : 'Resend Code'}
              </button>
            </>
          ) : (
            <form onSubmit={handleResetPassword} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  New Password
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-cyan-500 focus:outline-none transition"
                  placeholder="••••••••"
                />
                <p className="mt-1 text-xs text-slate-500">At least 8 characters</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Confirm Password
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-cyan-500 focus:outline-none transition"
                  placeholder="••••••••"
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
                {loading ? 'Resetting Password...' : 'Reset Password'}
              </button>
            </form>
          )}
        </div>

        <div className="mt-6 text-center text-sm text-slate-400">
          <Link href="/login" className="text-cyan-400 hover:text-cyan-300 font-semibold">
            Back to Login
          </Link>
        </div>
      </div>
    </div>
  );
}
