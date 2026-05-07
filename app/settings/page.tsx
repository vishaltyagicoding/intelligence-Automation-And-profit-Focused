'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import { apiEndpoint } from '@/lib/config';

interface Toast {
  id: number;
  type: 'error' | 'success' | 'info';
  message: string;
}

function ToastNotification({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const styles = {
    error: { bg: 'bg-red-500/10', border: 'border-red-500/50', text: 'text-red-400', icon: '❌' },
    success: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/50', text: 'text-emerald-400', icon: '✅' },
    info: { bg: 'bg-cyan-500/10', border: 'border-cyan-500/50', text: 'text-cyan-400', icon: 'ℹ️' },
  };

  const s = styles[toast.type];

  return (
    <div className={`${s.bg} border ${s.border} rounded-lg p-4 shadow-lg`}>
      <div className="flex items-center gap-3">
        <span className="text-xl">{s.icon}</span>
        <p className={`text-sm ${s.text}`}>{toast.message}</p>
        <button onClick={onClose} className="ml-auto text-slate-500 hover:text-white">×</button>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const router = useRouter();
  const { user, isAuthenticated, loading, setAuthData } = useAuth();
  
  const [activeTab, setActiveTab] = useState<'profile' | 'password'>('profile');
  const [toasts, setToasts] = useState<Toast[]>([]);
  
  // Profile form
  const [profileData, setProfileData] = useState({
    username: '',
    first_name: '',
    last_name: '',
    email: ''
  });
  const [profileLoading, setProfileLoading] = useState(false);
  
  // Password change form
  const [passwordStep, setPasswordStep] = useState<'request' | 'verify'>('request');
  const [resetId, setResetId] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, router]);

  useEffect(() => {
    if (user) {
      setProfileData({
        username: user.username || '',
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || ''
      });
    }
  }, [user]);

  const addToast = (type: Toast['type'], message: string) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, type, message }]);
  };

  const removeToast = (id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiEndpoint('/api/users/profile/update/'), {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(profileData)
      });

      const data = await response.json();

      if (data.success) {
        // Update auth context with new user data
        setAuthData(data.user, token!);
        addToast('success', 'Profile updated successfully!');
      } else {
        addToast('error', data.error || 'Failed to update profile');
      }
    } catch (error) {
      addToast('error', 'Network error. Please try again.');
    } finally {
      setProfileLoading(false);
    }
  };

  const handleRequestPasswordChange = async () => {
    if (!user?.email) return;
    
    setPasswordLoading(true);

    try {
      const response = await fetch(apiEndpoint('/api/users/forgot-password/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: user.email })
      });

      const data = await response.json();

      if (data.success) {
        setResetId(data.reset_id);
        setPasswordStep('verify');
        addToast('success', 'OTP sent to your email!');
      } else {
        addToast('error', data.error || 'Failed to send OTP');
      }
    } catch (error) {
      addToast('error', 'Network error. Please try again.');
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      addToast('error', 'Passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      addToast('error', 'Password must be at least 8 characters');
      return;
    }

    setPasswordLoading(true);

    try {
      const response = await fetch(apiEndpoint('/api/users/reset-password/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reset_id: resetId,
          otp: otp,
          new_password: newPassword,
          new_password2: confirmPassword
        })
      });

      const data = await response.json();

      if (data.success) {
        addToast('success', 'Password changed successfully!');
        // Reset form
        setPasswordStep('request');
        setOtp('');
        setNewPassword('');
        setConfirmPassword('');
        setResetId('');
      } else {
        addToast('error', data.error || 'Failed to change password');
      }
    } catch (error) {
      addToast('error', 'Network error. Please try again.');
    } finally {
      setPasswordLoading(false);
    }
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

      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 py-12 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-2">Settings</h1>
            <p className="text-slate-400">Manage your account settings and preferences</p>
          </div>

          {/* Tabs */}
          <div className="flex gap-4 mb-6 border-b border-slate-800">
            <button
              onClick={() => setActiveTab('profile')}
              className={`px-6 py-3 font-semibold transition ${
                activeTab === 'profile'
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              👤 Profile
            </button>
            <button
              onClick={() => setActiveTab('password')}
              className={`px-6 py-3 font-semibold transition ${
                activeTab === 'password'
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              🔒 Password
            </button>
          </div>

          {/* Content */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
            {activeTab === 'profile' ? (
              <form onSubmit={handleProfileUpdate} className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-6">Profile Information</h2>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Username
                      </label>
                      <input
                        type="text"
                        value={profileData.username}
                        onChange={(e) => setProfileData({ ...profileData, username: e.target.value })}
                        className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-cyan-500 focus:outline-none transition"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Email
                      </label>
                      <input
                        type="email"
                        value={profileData.email}
                        disabled
                        className="w-full px-4 py-3 rounded-lg bg-slate-800/50 border border-slate-700 text-slate-500 cursor-not-allowed"
                      />
                      <p className="mt-1 text-xs text-slate-500">Email cannot be changed</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        First Name
                      </label>
                      <input
                        type="text"
                        value={profileData.first_name}
                        onChange={(e) => setProfileData({ ...profileData, first_name: e.target.value })}
                        className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-cyan-500 focus:outline-none transition"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Last Name
                      </label>
                      <input
                        type="text"
                        value={profileData.last_name}
                        onChange={(e) => setProfileData({ ...profileData, last_name: e.target.value })}
                        className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-cyan-500 focus:outline-none transition"
                      />
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={profileLoading}
                  className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {profileLoading ? 'Saving...' : 'Save Changes'}
                </button>
              </form>
            ) : (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-white mb-6">Change Password</h2>

                {passwordStep === 'request' ? (
                  <div className="space-y-6">
                    <div className="p-6 rounded-lg bg-cyan-500/10 border border-cyan-500/30">
                      <p className="text-slate-300 mb-4">
                        To change your password, we'll send a verification code to your email:
                      </p>
                      <p className="text-cyan-400 font-semibold">{user?.email}</p>
                    </div>

                    <button
                      onClick={handleRequestPasswordChange}
                      disabled={passwordLoading}
                      className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {passwordLoading ? 'Sending OTP...' : 'Send Verification Code'}
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleChangePassword} className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Verification Code (OTP)
                      </label>
                      <input
                        type="text"
                        value={otp}
                        onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        placeholder="Enter 6-digit code"
                        className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-cyan-500 focus:outline-none transition"
                        maxLength={6}
                      />
                      <p className="mt-1 text-xs text-slate-500">Check your email for the code</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        New Password
                      </label>
                      <input
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-cyan-500 focus:outline-none transition"
                      />
                      <p className="mt-1 text-xs text-slate-500">At least 8 characters</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-cyan-500 focus:outline-none transition"
                      />
                    </div>

                    <div className="flex gap-4">
                      <button
                        type="button"
                        onClick={() => {
                          setPasswordStep('request');
                          setOtp('');
                          setNewPassword('');
                          setConfirmPassword('');
                        }}
                        className="flex-1 px-6 py-3 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 transition"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={passwordLoading || !otp || !newPassword || !confirmPassword}
                        className="flex-1 bg-gradient-to-r from-cyan-500 to-blue-500 text-white py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {passwordLoading ? 'Changing Password...' : 'Change Password'}
                      </button>
                    </div>
                  </form>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
