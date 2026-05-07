'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useAuth } from '@/lib/AuthContext';
import { useState, useEffect, useRef } from 'react';

function TrialCountdown({ trialEnd }: { trialEnd: string }) {
  const [timeLeft, setTimeLeft] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    const calculateTimeLeft = () => {
      const now = new Date().getTime();
      const end = new Date(trialEnd).getTime();
      const difference = end - now;

      if (difference <= 0) {
        setIsExpired(true);
        setTimeLeft({ days: 0, hours: 0, minutes: 0, seconds: 0 });
        return;
      }

      const days = Math.floor(difference / (1000 * 60 * 60 * 24));
      const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((difference % (1000 * 60)) / 1000);

      setTimeLeft({ days, hours, minutes, seconds });
    };

    calculateTimeLeft();
    const timer = setInterval(calculateTimeLeft, 1000);
    return () => clearInterval(timer);
  }, [trialEnd]);

  if (isExpired) {
    return (
      <div className="text-sm px-3 py-1 rounded-full bg-red-500/20 text-red-400 border border-red-500/50 animate-pulse">
        ⚠️ Trial Ended
      </div>
    );
  }

  const isLastDay = timeLeft.days === 0;
  const isWarning = timeLeft.days <= 1;

  return (
    <div className={`text-sm px-3 py-1.5 rounded-full font-medium ${
      isWarning 
        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50' 
        : 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
    }`}>
      <span className="mr-1">🎁</span>
      <span className="font-semibold">Trial:</span>
      {' '}
      {timeLeft.days > 0 && (
        <>
          <span className="font-bold">{timeLeft.days}</span>
          <span className="text-xs"> day{timeLeft.days !== 1 ? 's' : ''}</span>
          {' '}
        </>
      )}
      <span className="font-bold">{timeLeft.hours}</span>
      <span className="text-xs">h</span>
      {' '}
      <span className="font-bold">{timeLeft.minutes}</span>
      <span className="text-xs">m</span>
      {isLastDay && (
        <>
          {' '}
          <span className="font-bold">{timeLeft.seconds}</span>
          <span className="text-xs">s</span>
        </>
      )}
      <span className="text-xs ml-1">left</span>
    </div>
  );
}

function UserProfileDropdown({ user, logout }: { user: any; logout: () => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Get user initials
  const getInitials = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    if (user?.username) {
      return user.username.substring(0, 2).toUpperCase();
    }
    if (user?.email) {
      return user.email.substring(0, 2).toUpperCase();
    }
    return 'U';
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* User Avatar Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 hover:bg-slate-800 rounded-lg px-3 py-2 transition"
      >
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center text-white font-bold text-sm">
          {getInitials()}
        </div>
        <div className="hidden md:block text-left">
          <div className="text-sm font-semibold text-white">
            {user?.full_name || user?.username || 'User'}
          </div>
          <div className="text-xs text-slate-400">{user?.email}</div>
        </div>
        <svg
          className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 rounded-xl border border-slate-800 bg-slate-900 shadow-xl overflow-hidden z-50">
          {/* User Info Header */}
          <div className="p-4 border-b border-slate-800 bg-gradient-to-br from-slate-800 to-slate-900">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center text-white font-bold text-lg">
                {getInitials()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-white truncate">
                  {user?.full_name || user?.username}
                </div>
                <div className="text-xs text-slate-400 truncate">{user?.email}</div>
                <div className="text-xs text-cyan-400 mt-1">
                  @{user?.username}
                </div>
              </div>
            </div>
          </div>

          {/* Menu Items */}
          <div className="py-2">
            <Link
              href="/settings"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-4 py-3 hover:bg-slate-800 transition text-slate-300 hover:text-white"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <div>
                <div className="text-sm font-medium">Settings</div>
                <div className="text-xs text-slate-500">Manage your account</div>
              </div>
            </Link>

            <Link
              href="/dashboard"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-4 py-3 hover:bg-slate-800 transition text-slate-300 hover:text-white"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <div className="text-sm font-medium">Dashboard</div>
            </Link>

            <Link
              href="/history"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-4 py-3 hover:bg-slate-800 transition text-slate-300 hover:text-white"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-sm font-medium">Signal History</div>
            </Link>

            <Link
              href="/signal-alerts"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-4 py-3 hover:bg-slate-800 transition text-slate-300 hover:text-white"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <div className="text-sm font-medium">Signal Alerts</div>
            </Link>
          </div>

          {/* Logout */}
          <div className="border-t border-slate-800 p-2">
            <button
              onClick={() => {
                setIsOpen(false);
                logout();
              }}
              className="flex items-center gap-3 px-4 py-3 hover:bg-red-500/10 transition text-red-400 hover:text-red-300 w-full rounded-lg"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <div className="text-sm font-medium">Logout</div>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Navigation() {
  const { user, isAuthenticated, logout, loading } = useAuth();

  if (loading) {
    return (
      <nav className="border-b border-slate-800 bg-slate-900/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="text-xl font-bold text-white">
              SmartRisk
            </Link>
          </div>
        </div>
      </nav>
    );
  }

  const trialExpired = user?.subscription_status?.status === 'expired' || 
                       (user?.subscription_status?.status === 'trial' && !user?.subscription_status?.is_active);
  
  const paidSubscriptionExpired = user?.subscription_status?.status === 'paid' && !user?.subscription_status?.is_active;

  return (
    <nav className="border-b border-slate-800 bg-slate-900/95 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link href="/" className="flex items-center gap-2">
              <Image 
                src="/logo.jpeg" 
                alt="SmartRisk Logo" 
                width={40} 
                height={40}
                className="rounded-full object-cover"
                priority
              />
              <span className="text-xl font-bold text-white">SmartRisk</span>
            </Link>
            <div className="hidden md:flex space-x-6">
              <Link href="/" className="text-slate-300 hover:text-white transition">
                Home
              </Link>
              {isAuthenticated && (
                <>
                  <Link href="/dashboard" className="text-slate-300 hover:text-white transition">
                    Dashboard
                  </Link>
                  <Link href="/history" className="text-slate-300 hover:text-white transition">
                    History
                  </Link>
                  <Link href="/signal-alerts" className="text-slate-300 hover:text-white transition">
                    Signal Alerts
                  </Link>
                </>
              )}
              <Link href="/about" className="text-slate-300 hover:text-white transition">
                About
              </Link>
              <Link href="/learn" className="text-slate-300 hover:text-white transition">
                Learn
              </Link>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                {/* Manual Subscription Active Badge */}
                {user?.manual_subscription === 'activated' && (
                  <div className="text-sm px-3 py-1.5 rounded-full bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-emerald-400 border border-emerald-500/50 font-semibold">
                    <span className="mr-1">👑</span>
                    Subscription Active
                  </div>
                )}
                
                {/* Real-time Trial Countdown */}
                {user?.subscription_status?.status === 'trial' && user?.subscription_status?.trial_end && user?.manual_subscription !== 'activated' && (
                  <TrialCountdown trialEnd={user.subscription_status.trial_end} />
                )}
                
                {/* Trial Ended Badge */}
                {trialExpired && user?.manual_subscription !== 'activated' && (
                  <div className="text-sm px-3 py-1 rounded-full bg-red-500/20 text-red-400 border border-red-500/50 animate-pulse">
                    ⚠️ Trial Ended
                  </div>
                )}
                
                {/* Paid Subscription Ended Badge */}
                {paidSubscriptionExpired && user?.manual_subscription !== 'activated' && (
                  <div className="text-sm px-3 py-1 rounded-full bg-red-500/20 text-red-400 border border-red-500/50 animate-pulse">
                    ⚠️ Subscription Ended
                  </div>
                )}
                
                {/* Subscription Link */}
                <Link 
                  href="/subscription" 
                  className="text-sm px-4 py-2 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 hover:bg-emerald-500/30 transition font-semibold"
                >
                  Subscription
                </Link>

                {/* User Profile Dropdown */}
                <UserProfileDropdown user={user} logout={logout} />
              </>
            ) : (
              <>
                <Link href="/login" className="text-slate-300 hover:text-white transition">
                  Login
                </Link>
                <Link href="/register" className="bg-cyan-500 hover:bg-cyan-600 text-white px-4 py-2 rounded-lg transition font-semibold">
                  Start Free Trial
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
