'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import Link from 'next/link';
import { apiEndpoint } from '@/lib/config';

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
      titleText: 'Error',
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

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuthData } = useAuth();
  
  const verificationId = searchParams.get('id');
  const email = searchParams.get('email');
  
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes in seconds
  
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Countdown timer
  useEffect(() => {
    if (timeLeft <= 0) return;
    
    const timer = setInterval(() => {
      setTimeLeft(prev => prev - 1);
    }, 1000);
    
    return () => clearInterval(timer);
  }, [timeLeft]);

  const addToast = (type: Toast['type'], messages: string[]) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, type, messages }]);
  };

  const removeToast = (id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return; // Only digits
    
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1); // Only last digit
    setOtp(newOtp);
    
    // Auto-focus next input
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
    
    // Focus last filled input or first empty
    const nextIndex = Math.min(pastedData.length, 5);
    inputRefs.current[nextIndex]?.focus();
  };

  const handleVerify = async () => {
    const otpCode = otp.join('');
    
    if (otpCode.length !== 6) {
      addToast('error', ['Please enter all 6 digits']);
      return;
    }
    
    if (!verificationId) {
      addToast('error', ['Invalid verification link']);
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await fetch(apiEndpoint('/api/users/verify-otp/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          verification_id: verificationId,
          otp: otpCode
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Save auth data
        setAuthData(data.user, data.tokens.access);
        
        addToast('success', [data.message || 'Email verified successfully!']);
        
        // Redirect to dashboard after 1 second
        setTimeout(() => {
          router.push('/dashboard');
        }, 1000);
      } else {
        addToast('error', [data.error || 'Verification failed']);
      }
    } catch (error) {
      addToast('error', ['Network error. Please try again.']);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!verificationId) {
      addToast('error', ['Invalid verification link']);
      return;
    }
    
    setResending(true);
    
    try {
      const response = await fetch(apiEndpoint('/api/users/resend-otp/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ verification_id: verificationId })
      });
      
      const data = await response.json();
      
      if (data.success) {
        addToast('success', ['New code sent to your email']);
        setOtp(['', '', '', '', '', '']);
        setTimeLeft(600); // Reset timer
        inputRefs.current[0]?.focus();
      } else {
        addToast('error', [data.error || 'Failed to resend code']);
      }
    } catch (error) {
      addToast('error', ['Network error. Please try again.']);
    } finally {
      setResending(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!verificationId || !email) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="text-center">
          <p className="text-red-400 mb-4">Invalid verification link</p>
          <Link href="/register" className="text-cyan-400 hover:text-cyan-300">
            Go back to registration
          </Link>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Toast Container */}
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
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-500/30 mb-4">
              <span className="text-3xl">📧</span>
            </div>
            <h2 className="text-4xl font-bold text-white mb-2">Verify Your Email</h2>
            <p className="text-slate-400">
              We sent a 6-digit code to<br />
              <span className="text-cyan-400 font-semibold">{email}</span>
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-300 mb-4 text-center">
                Enter Verification Code
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
                    onChange={e => handleChange(index, e.target.value)}
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

            <button
              onClick={handleVerify}
              disabled={loading || otp.join('').length !== 6}
              className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition disabled:opacity-50 disabled:cursor-not-allowed mb-4"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-white border-r-transparent"></span>
                  Verifying...
                </span>
              ) : (
                'Verify Email'
              )}
            </button>

            <button
              onClick={handleResend}
              disabled={resending || timeLeft > 540} // Can resend after 1 minute
              className="w-full text-cyan-400 hover:text-cyan-300 py-2 text-sm font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {resending ? 'Sending...' : 'Resend Code'}
            </button>

            <div className="mt-6 p-4 rounded-lg bg-cyan-500/5 border border-cyan-500/20">
              <p className="text-xs text-slate-400 text-center">
                💡 <strong>Tip:</strong> Check your spam folder if you don't see the email<br />
                📧 <strong>Important:</strong> If you registered multiple times, use the code from the MOST RECENT email
              </p>
            </div>
          </div>

          <div className="mt-6 text-center text-sm text-slate-400">
            Wrong email?{' '}
            <Link href="/register" className="text-cyan-400 hover:text-cyan-300 font-semibold">
              Start over
            </Link>
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
