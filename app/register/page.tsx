'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/AuthContext';
import { useDeviceFingerprint, checkDeviceEligibility } from '@/lib/useDeviceFingerprint';
import Link from 'next/link';

interface Toast {
  id: number;
  type: 'error' | 'success' | 'info';
  messages: string[];
}

function ToastNotification({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 7000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const styles = {
    error: {
      container: 'bg-slate-900 border border-red-500/60 shadow-2xl shadow-red-500/20',
      icon: '❌',
      title: 'text-red-400',
      titleText: 'Please fix the following:',
      dot: 'bg-red-400',
      bar: 'bg-red-500',
    },
    success: {
      container: 'bg-slate-900 border border-emerald-500/60 shadow-2xl shadow-emerald-500/20',
      icon: '✅',
      title: 'text-emerald-400',
      titleText: 'Success!',
      dot: 'bg-emerald-400',
      bar: 'bg-emerald-500',
    },
    info: {
      container: 'bg-slate-900 border border-cyan-500/60 shadow-2xl shadow-cyan-500/20',
      icon: 'ℹ️',
      title: 'text-cyan-400',
      titleText: 'Info',
      dot: 'bg-cyan-400',
      bar: 'bg-cyan-500',
    },
  };

  const s = styles[toast.type];

  return (
    <div className={`w-96 rounded-xl p-4 ${s.container}`} style={{ animation: 'slideIn 0.3s ease-out' }}>
      <div className="flex items-start gap-3">
        <span className="text-xl shrink-0 mt-0.5">{s.icon}</span>
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-bold mb-2 ${s.title}`}>{s.titleText}</p>
          <ul className="space-y-1.5">
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
          className="shrink-0 text-slate-500 hover:text-white transition text-xl leading-none ml-1"
        >
          ×
        </button>
      </div>
      <div className="mt-3 h-0.5 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${s.bar}`} style={{ animation: 'shrink 7s linear forwards' }} />
      </div>
    </div>
  );
}

// ── Validation helpers ────────────────────────────────────────────────────────

function validateEmail(email: string): string | null {
  const trimmed = email.trim();
  if (!trimmed) return 'Email address is required.';
  // Django EmailField max_length is 254 characters
  if (trimmed.length > 254) return 'Email address is too long (max 254 characters).';
  // Strict email regex
  const emailRegex = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
  if (!emailRegex.test(trimmed)) return 'Please enter a valid email address (e.g. john@gmail.com).';
  // Common typos in domain
  const typos: Record<string, string> = {
    'gmai.com': 'gmail.com', 'gmial.com': 'gmail.com', 'gamil.com': 'gmail.com',
    'yahooo.com': 'yahoo.com', 'yaho.com': 'yahoo.com',
    'hotmial.com': 'hotmail.com', 'hotmal.com': 'hotmail.com',
    'outlok.com': 'outlook.com',
  };
  const domain = trimmed.split('@')[1]?.toLowerCase();
  if (domain && typos[domain]) {
    return `Did you mean ${trimmed.split('@')[0]}@${typos[domain]}? Please check your email.`;
  }
  return null;
}

function validateUsername(username: string): string | null {
  const trimmed = username.trim();
  if (!trimmed) return 'Username is required.';
  if (trimmed.length < 3) return 'Username must be at least 3 characters long.';
  // Django AbstractUser username field max_length is 150 characters
  if (trimmed.length > 150) return 'Username is too long (max 150 characters).';
  if (!/^[a-zA-Z0-9_]+$/.test(trimmed)) return 'Username can only contain letters, numbers, and underscores (no spaces or special characters).';
  if (/^\d+$/.test(trimmed)) return 'Username cannot be all numbers — add some letters.';
  // Block placeholder-style values
  const blocked = ['username', 'user', 'test', 'admin', 'null', 'undefined'];
  if (blocked.includes(trimmed.toLowerCase())) return `"${trimmed}" is not allowed as a username. Please choose a unique one.`;
  return null;
}

function validateName(value: string, field: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return `${field} is required.`;
  if (trimmed.length < 2) return `${field} must be at least 2 characters long.`;
  // Django AbstractUser first_name/last_name fields max_length is 150 characters
  if (trimmed.length > 150) return `${field} is too long (max 150 characters).`;
  if (!/^[a-zA-Z\s'\-]+$/.test(trimmed)) return `${field} can only contain letters, spaces, hyphens, or apostrophes — no numbers or symbols.`;
  if (/^\s+$/.test(trimmed)) return `${field} cannot be blank spaces.`;
  // Block placeholder-style values
  const blocked = ['first name', 'last name', 'firstname', 'lastname', 'name', 'test', 'null'];
  if (blocked.includes(trimmed.toLowerCase())) return `Please enter your real ${field.toLowerCase()}.`;
  return null;
}

function validatePassword(password: string): string | null {
  if (!password) return 'Password is required.';
  if (password.length < 8) return 'Password must be at least 8 characters long.';
  if (password.length > 128) return 'Password is too long (max 128 characters).';
  if (/^\d+$/.test(password)) return 'Password cannot be all numbers — add some letters to make it stronger.';
  if (/^[a-zA-Z]+$/.test(password)) return 'Password is too weak — add at least one number or symbol.';
  // Common weak passwords
  const weak = ['password', 'password1', '12345678', '123456789', 'qwerty123', 'abc12345', 'iloveyou', 'welcome1'];
  if (weak.includes(password.toLowerCase())) return 'This password is too common. Please choose something more unique.';
  return null;
}

function validateConfirmPassword(password: string, confirm: string): string | null {
  if (!confirm) return 'Please confirm your password.';
  if (password !== confirm) return 'Passwords do not match — please re-enter both passwords carefully.';
  return null;
}

// Run all validations and return list of error messages
function validateAll(formData: {
  email: string; username: string; first_name: string;
  last_name: string; password: string; password2: string;
}): string[] {
  const errors: string[] = [];
  const checks = [
    validateEmail(formData.email),
    validateUsername(formData.username),
    validateName(formData.first_name, 'First Name'),
    validateName(formData.last_name, 'Last Name'),
    validatePassword(formData.password),
    validateConfirmPassword(formData.password, formData.password2),
  ];
  checks.forEach(e => { if (e) errors.push(e); });
  return errors;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function RegisterPage() {
  const { register } = useAuth();
  const { deviceId, loading: fingerprintLoading, error: fingerprintError } = useDeviceFingerprint();
  
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
  });
  // Per-field touched state so we only show errors after user interacts
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [loading, setLoading] = useState(false);
  const [trialInfo, setTrialInfo] = useState<{
    trial_allowed: boolean;
    reason: string;
  } | null>(null);

  const addToast = useCallback((type: Toast['type'], messages: string[]) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, type, messages }]);
  }, []);

  const removeToast = (id: number) => setToasts(prev => prev.filter(t => t.id !== id));

  // Check device eligibility when fingerprint is ready
  useEffect(() => {
    if (deviceId && deviceId !== 'unknown') {
      checkDeviceEligibility(deviceId).then(result => {
        if (result.success) {
          setTrialInfo({
            trial_allowed: result.trial_allowed,
            reason: result.reason
          });
          
          // Show warning if trial not allowed
          if (!result.trial_allowed) {
            addToast('info', [
              'Free trial not available on this device',
              result.reason,
              'You can still create an account with full access after trial period'
            ]);
          }
        }
      });
    }
  }, [deviceId, addToast]);

  // Validate a single field on blur
  const validateField = (name: string, value: string) => {
    let error: string | null = null;
    switch (name) {
      case 'email':    error = validateEmail(value); break;
      case 'username': error = validateUsername(value); break;
      case 'first_name': error = validateName(value, 'First Name'); break;
      case 'last_name':  error = validateName(value, 'Last Name'); break;
      case 'password':   error = validatePassword(value); break;
      case 'password2':  error = validateConfirmPassword(formData.password, value); break;
    }
    setFieldErrors(prev => ({ ...prev, [name]: error ?? '' }));
  };

  const handleChange = (name: string, value: string) => {
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error as user types (after field was touched)
    if (touched[name]) {
      validateField(name, value);
    }
  };

  const handleBlur = (name: string, value: string) => {
    setTouched(prev => ({ ...prev, [name]: true }));
    validateField(name, value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Check if device fingerprint is ready
    if (fingerprintLoading) {
      addToast('info', ['Please wait while we verify your device...']);
      return;
    }

    if (!deviceId) {
      addToast('error', ['Device verification failed. Please refresh the page and try again.']);
      return;
    }

    // Mark all fields as touched
    const allTouched = Object.keys(formData).reduce((acc, k) => ({ ...acc, [k]: true }), {});
    setTouched(allTouched);

    // Run full validation
    const errors = validateAll(formData);
    if (errors.length > 0) {
      addToast('error', errors);
      // Also set per-field errors
      const newFieldErrors: Record<string, string> = {};
      if (validateEmail(formData.email)) newFieldErrors.email = validateEmail(formData.email)!;
      if (validateUsername(formData.username)) newFieldErrors.username = validateUsername(formData.username)!;
      if (validateName(formData.first_name, 'First Name')) newFieldErrors.first_name = validateName(formData.first_name, 'First Name')!;
      if (validateName(formData.last_name, 'Last Name')) newFieldErrors.last_name = validateName(formData.last_name, 'Last Name')!;
      if (validatePassword(formData.password)) newFieldErrors.password = validatePassword(formData.password)!;
      if (validateConfirmPassword(formData.password, formData.password2)) newFieldErrors.password2 = validateConfirmPassword(formData.password, formData.password2)!;
      setFieldErrors(newFieldErrors);
      return; // ← STOP — do NOT call API
    }

    setLoading(true);
    try {
      // Call the new registration endpoint that sends OTP with device_id
      const res = await fetch('/api/users/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          device_id: deviceId // Include device fingerprint
        }),
      });

      const data = await res.json();

      if (!data.success) {
        // Parse backend validation errors
        if (data.errors && typeof data.errors === 'object') {
          const messages: string[] = [];
          for (const [field, errors] of Object.entries(data.errors)) {
            const errorList = Array.isArray(errors) ? errors : [errors];
            errorList.forEach((err: any) => messages.push(String(err)));
          }
          addToast('error', messages);
        } else {
          addToast('error', [data.error || 'Registration failed. Please try again.']);
        }
        return;
      }

      // Show trial info if available
      if (data.trial_info && !data.trial_info.trial_allowed) {
        addToast('info', [
          '📧 Verification code sent to your email!',
          `Note: ${data.trial_info.reason}`
        ]);
      } else {
        addToast('success', ['📧 Verification code sent to your email! Check your inbox.']);
      }
      
      // Redirect to verify-email page after 1 second
      setTimeout(() => {
        window.location.href = `/verify-email?id=${data.verification_id}&email=${encodeURIComponent(data.email)}`;
      }, 1000);
      
    } catch (err: any) {
      const raw: string = err.message || 'Something went wrong. Please try again.';
      const messages = raw.split('\n').filter(Boolean);
      addToast('error', messages);
    } finally {
      setLoading(false);
    }
  };

  // Helper: input class based on field error state
  const inputClass = (name: string) =>
    `w-full px-4 py-3 rounded-lg bg-slate-800 border text-white focus:outline-none transition ${
      touched[name] && fieldErrors[name]
        ? 'border-red-500 focus:border-red-400'
        : touched[name] && !fieldErrors[name]
        ? 'border-emerald-500 focus:border-emerald-400'
        : 'border-slate-700 focus:border-cyan-500'
    }`;

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
            <h2 className="text-4xl font-bold text-white mb-2">Start Free Trial</h2>
            <p className="text-xl text-slate-400 mb-4">3 days free access to all features</p>
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-4 py-2 text-sm font-semibold text-cyan-400">
              <span>🎁</span>
              <span>No credit card required</span>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
            {/* Device Verification Status */}
            {fingerprintLoading && (
              <div className="mb-6 p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
                <p className="text-sm text-blue-400 flex items-center gap-2">
                  <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-blue-400 border-r-transparent"></span>
                  Verifying your device...
                </p>
              </div>
            )}
            
            {!fingerprintLoading && deviceId && trialInfo && !trialInfo.trial_allowed && (
              <div className="mb-6 p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
                <p className="text-sm text-yellow-400 font-semibold mb-1">⚠️ Trial Not Available</p>
                <p className="text-xs text-yellow-300">{trialInfo.reason}</p>
                <p className="text-xs text-slate-400 mt-2">You can create an account, but you'll need a subscription to access features.</p>
              </div>
            )}
            
            {!fingerprintLoading && deviceId && trialInfo && trialInfo.trial_allowed && (
              <div className="mb-6 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                <p className="text-sm text-emerald-400 flex items-center gap-2">
                  <span>✅</span>
                  Device verified - 3-day free trial available!
                </p>
              </div>
            )}
            
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Email Address *
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={e => handleChange('email', e.target.value)}
                  onBlur={e => handleBlur('email', e.target.value)}
                  className={inputClass('email')}
                  placeholder="john@gmail.com"
                  autoComplete="email"
                />
                {touched.email && fieldErrors.email && (
                  <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
                    <span>⚠</span> {fieldErrors.email}
                  </p>
                )}
                {touched.email && !fieldErrors.email && formData.email && (
                  <p className="mt-1.5 text-xs text-emerald-400 flex items-center gap-1">
                    <span>✓</span> Looks good!
                  </p>
                )}
              </div>

              {/* Username */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Username *
                </label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={e => handleChange('username', e.target.value)}
                  onBlur={e => handleBlur('username', e.target.value)}
                  className={inputClass('username')}
                  placeholder="johndoe123"
                  autoComplete="username"
                />
                <p className="mt-1 text-xs text-slate-500">Letters, numbers, and underscores only</p>
                {touched.username && fieldErrors.username && (
                  <p className="mt-1 text-xs text-red-400 flex items-center gap-1">
                    <span>⚠</span> {fieldErrors.username}
                  </p>
                )}
                {touched.username && !fieldErrors.username && formData.username && (
                  <p className="mt-1 text-xs text-emerald-400 flex items-center gap-1">
                    <span>✓</span> Username looks good!
                  </p>
                )}
              </div>

              {/* First & Last Name */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    First Name *
                  </label>
                  <input
                    type="text"
                    value={formData.first_name}
                    onChange={e => handleChange('first_name', e.target.value)}
                    onBlur={e => handleBlur('first_name', e.target.value)}
                    className={inputClass('first_name')}
                    placeholder="John"
                    autoComplete="given-name"
                  />
                  {touched.first_name && fieldErrors.first_name && (
                    <p className="mt-1 text-xs text-red-400 flex items-start gap-1">
                      <span className="shrink-0">⚠</span> {fieldErrors.first_name}
                    </p>
                  )}
                  {touched.first_name && !fieldErrors.first_name && formData.first_name && (
                    <p className="mt-1 text-xs text-emerald-400">✓ Valid</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Last Name *
                  </label>
                  <input
                    type="text"
                    value={formData.last_name}
                    onChange={e => handleChange('last_name', e.target.value)}
                    onBlur={e => handleBlur('last_name', e.target.value)}
                    className={inputClass('last_name')}
                    placeholder="Doe"
                    autoComplete="family-name"
                  />
                  {touched.last_name && fieldErrors.last_name && (
                    <p className="mt-1 text-xs text-red-400 flex items-start gap-1">
                      <span className="shrink-0">⚠</span> {fieldErrors.last_name}
                    </p>
                  )}
                  {touched.last_name && !fieldErrors.last_name && formData.last_name && (
                    <p className="mt-1 text-xs text-emerald-400">✓ Valid</p>
                  )}
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Password *
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={e => handleChange('password', e.target.value)}
                  onBlur={e => handleBlur('password', e.target.value)}
                  className={inputClass('password')}
                  placeholder="••••••••"
                  autoComplete="new-password"
                />
                <p className="mt-1 text-xs text-slate-500">
                  At least 8 characters — mix letters and numbers for a strong password
                </p>
                {touched.password && fieldErrors.password && (
                  <p className="mt-1 text-xs text-red-400 flex items-center gap-1">
                    <span>⚠</span> {fieldErrors.password}
                  </p>
                )}
                {touched.password && !fieldErrors.password && formData.password && (
                  <p className="mt-1 text-xs text-emerald-400 flex items-center gap-1">
                    <span>✓</span> Strong password!
                  </p>
                )}
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Confirm Password *
                </label>
                <input
                  type="password"
                  value={formData.password2}
                  onChange={e => handleChange('password2', e.target.value)}
                  onBlur={e => handleBlur('password2', e.target.value)}
                  className={inputClass('password2')}
                  placeholder="••••••••"
                  autoComplete="new-password"
                />
                {touched.password2 && fieldErrors.password2 && (
                  <p className="mt-1 text-xs text-red-400 flex items-center gap-1">
                    <span>⚠</span> {fieldErrors.password2}
                  </p>
                )}
                {touched.password2 && !fieldErrors.password2 && formData.password2 && (
                  <p className="mt-1 text-xs text-emerald-400 flex items-center gap-1">
                    <span>✓</span> Passwords match!
                  </p>
                )}
              </div>

              <button
                type="submit"
                disabled={loading || fingerprintLoading}
                className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition disabled:opacity-50 disabled:cursor-not-allowed mt-2"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-white border-r-transparent"></span>
                    Creating your account...
                  </span>
                ) : fingerprintLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-white border-r-transparent"></span>
                    Verifying device...
                  </span>
                ) : trialInfo && !trialInfo.trial_allowed ? (
                  'Create Account (Subscription Required)'
                ) : (
                  'Start 3-Day Free Trial'
                )}
              </button>
              
              {trialInfo && !trialInfo.trial_allowed && (
                <p className="mt-3 text-xs text-center text-yellow-400">
                  ⚠️ Free trial not available. You'll need a subscription to access features.
                </p>
              )}
            </form>

            <div className="mt-6 text-center text-sm text-slate-400">
              Already have an account?{' '}
              <Link href="/login" className="text-cyan-400 hover:text-cyan-300 font-semibold">
                Login
              </Link>
            </div>

            <div className="mt-6 p-4 rounded-lg bg-cyan-500/5 border border-cyan-500/20">
              <p className="text-xs text-slate-400 text-center">
                ✨ Get instant access to all features for 3 days<br />
                📊 No payment required during trial<br />
                🔒 Your data is secure and private
              </p>
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
          from { transform: translateX(110%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </>
  );
}
