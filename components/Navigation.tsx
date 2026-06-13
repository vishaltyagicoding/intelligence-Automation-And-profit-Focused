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
      <div className="text-xs sm:text-sm px-2 sm:px-3 py-1 rounded-full bg-red-500/20 text-red-400 border border-red-500/50 animate-pulse whitespace-nowrap">
        ⚠️ Trial Ended
      </div>
    );
  }

  const isLastDay = timeLeft.days === 0;
  const isWarning = timeLeft.days <= 1;

  return (
    <div className={`text-xs sm:text-sm px-2 sm:px-3 py-1 sm:py-1.5 rounded-full font-medium whitespace-nowrap ${
      isWarning 
        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50' 
        : 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
    }`}>
      <span className="mr-1">🎁</span>
      <span className="hidden xs:inline font-semibold">Trial:</span>
      {' '}
      {timeLeft.days > 0 && (
        <>
          <span className="font-bold">{timeLeft.days}</span>
          <span className="text-[10px] sm:text-xs">d</span>
          {' '}
        </>
      )}
      <span className="font-bold">{timeLeft.hours}</span>
      <span className="text-[10px] sm:text-xs">h</span>
      {' '}
      <span className="font-bold">{timeLeft.minutes}</span>
      <span className="text-[10px] sm:text-xs">m</span>
      {isLastDay && (
        <>
          <span className="hidden sm:inline">
            {' '}
            <span className="font-bold">{timeLeft.seconds}</span>
            <span className="text-xs">s</span>
          </span>
        </>
      )}
    </div>
  );
}

function UserProfileDropdown({ user, logout }: { user: any; logout: () => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1 sm:gap-2 hover:bg-slate-800 rounded-lg px-2 sm:px-3 py-2 transition touch-target"
      >
        <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center text-white font-bold text-sm">
          {getInitials()}
        </div>
        <div className="hidden lg:block text-left">
          <div className="text-sm font-semibold text-white truncate max-w-[120px]">
            {user?.full_name || user?.username || 'User'}
          </div>
          <div className="text-xs text-slate-400 truncate max-w-[120px]">{user?.email}</div>
        </div>
        <svg
          className={`w-4 h-4 text-slate-400 transition-transform hidden sm:block ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-[calc(100vw-2rem)] max-w-[320px] sm:w-72 rounded-xl border border-slate-800 bg-slate-900 shadow-xl overflow-hidden z-50">
          <div className="p-3 sm:p-4 border-b border-slate-800 bg-gradient-to-br from-slate-800 to-slate-900">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center text-white font-bold text-base sm:text-lg flex-shrink-0">
                {getInitials()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-white truncate">
                  {user?.full_name || user?.username}
                </div>
                <div className="text-xs text-slate-400 truncate">{user?.email}</div>
                <div className="text-xs text-cyan-400 mt-1 truncate">
                  @{user?.username}
                </div>
              </div>
            </div>
          </div>

          <div className="py-1 sm:py-2">
            <Link
              href="/settings"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-3 sm:px-4 py-2 sm:py-3 hover:bg-slate-800 transition text-slate-300 hover:text-white touch-target"
            >
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <div>
                <div className="text-sm font-medium">Settings</div>
                <div className="text-xs text-slate-500 hidden sm:block">Manage your account</div>
              </div>
            </Link>

            <Link
              href="/dashboard"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-3 sm:px-4 py-2 sm:py-3 hover:bg-slate-800 transition text-slate-300 hover:text-white touch-target"
            >
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <div className="text-sm font-medium">Dashboard</div>
            </Link>

            <Link
              href="/history"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-3 sm:px-4 py-2 sm:py-3 hover:bg-slate-800 transition text-slate-300 hover:text-white touch-target"
            >
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-sm font-medium">Signal History</div>
            </Link>

            <Link
              href="/signal-alerts"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-3 sm:px-4 py-2 sm:py-3 hover:bg-slate-800 transition text-slate-300 hover:text-white touch-target"
            >
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <div className="text-sm font-medium">Signal Alerts</div>
            </Link>
          </div>

          <div className="border-t border-slate-800 p-2">
            <button
              onClick={() => {
                setIsOpen(false);
                logout();
              }}
              className="flex items-center gap-3 px-3 sm:px-4 py-2 sm:py-3 hover:bg-red-500/10 transition text-red-400 hover:text-red-300 w-full rounded-lg touch-target"
            >
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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

function MobileMenu({ isAuthenticated }: { isAuthenticated: boolean }) {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  return (
    <>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="md:hidden p-2 hover:bg-slate-800 rounded-lg transition touch-target"
        aria-label="Toggle menu"
      >
        <svg
          className="w-6 h-6 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          {isOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/60 z-40 md:hidden"
            onClick={() => setIsOpen(false)}
          />
          <div className="fixed top-16 left-0 right-0 bottom-0 bg-slate-900 z-50 md:hidden overflow-y-auto">
            <nav className="p-4 space-y-2">
              <Link
                href="/"
                onClick={() => setIsOpen(false)}
                className="block px-4 py-3 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition touch-target"
              >
                Home
              </Link>
              {isAuthenticated && (
                <>
                  <Link
                    href="/dashboard"
                    onClick={() => setIsOpen(false)}
                    className="block px-4 py-3 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition touch-target"
                  >
                    Dashboard
                  </Link>
                  <Link
                    href="/history"
                    onClick={() => setIsOpen(false)}
                    className="block px-4 py-3 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition touch-target"
                  >
                    History
                  </Link>
                  <Link
                    href="/signal-alerts"
                    onClick={() => setIsOpen(false)}
                    className="block px-4 py-3 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition touch-target"
                  >
                    Signal Alerts
                  </Link>
                </>
              )}
              <Link
                href="/about"
                onClick={() => setIsOpen(false)}
                className="block px-4 py-3 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition touch-target"
              >
                About
              </Link>
              <Link
                href="/learn"
                onClick={() => setIsOpen(false)}
                className="block px-4 py-3 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition touch-target"
              >
                Learn
              </Link>
            </nav>
          </div>
        </>
      )}
    </>
  );
}

export default function Navigation() {
  const { user, isAuthenticated, logout, loading } = useAuth();

  if (loading) {
    return (
      <nav className="border-b border-slate-800 bg-slate-900/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="text-lg sm:text-xl font-bold text-white">
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
      <div className="container mx-auto px-3 sm:px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-4 sm:gap-6 lg:gap-8 min-w-0">
            <Link href="/" className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
              <Image 
                src="/logo.jpeg" 
                alt="SmartRisk Logo" 
                width={32} 
                height={32}
                className="rounded-full object-cover sm:w-10 sm:h-10"
                priority
              />
              <span className="text-base sm:text-xl font-bold text-white hidden xs:inline">SmartRisk</span>
            </Link>
            
            <div className="hidden md:flex gap-4 lg:gap-6">
              <Link href="/" className="text-sm text-slate-300 hover:text-white transition whitespace-nowrap">
                Home
              </Link>
              {isAuthenticated && (
                <>
                  <Link href="/dashboard" className="text-sm text-slate-300 hover:text-white transition whitespace-nowrap">
                    Dashboard
                  </Link>
                  <Link href="/history" className="text-sm text-slate-300 hover:text-white transition whitespace-nowrap">
                    History
                  </Link>
                  <Link href="/signal-alerts" className="text-sm text-slate-300 hover:text-white transition whitespace-nowrap">
                    Alerts
                  </Link>
                </>
              )}
              <Link href="/about" className="text-sm text-slate-300 hover:text-white transition whitespace-nowrap">
                About
              </Link>
              <Link href="/learn" className="text-sm text-slate-300 hover:text-white transition whitespace-nowrap">
                Learn
              </Link>
            </div>
          </div>

          <div className="flex items-center gap-1 xs:gap-2 sm:gap-3 lg:gap-4">
            {isAuthenticated ? (
              <>
                {user?.manual_subscription === 'activated' && (
                  <div className="hidden sm:block text-xs sm:text-sm px-2 sm:px-3 py-1 sm:py-1.5 rounded-full bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-emerald-400 border border-emerald-500/50 font-semibold whitespace-nowrap">
                    <span className="mr-1">👑</span>
                    <span className="hidden lg:inline">Subscription </span>Active
                  </div>
                )}
                
                {user?.subscription_status?.status === 'trial' && user?.subscription_status?.trial_end && user?.manual_subscription !== 'activated' && (
                  <TrialCountdown trialEnd={user.subscription_status.trial_end} />
                )}
                
                {trialExpired && user?.manual_subscription !== 'activated' && (
                  <div className="text-xs sm:text-sm px-2 sm:px-3 py-1 rounded-full bg-red-500/20 text-red-400 border border-red-500/50 animate-pulse whitespace-nowrap">
                    ⚠️ <span className="hidden sm:inline">Trial </span>Ended
                  </div>
                )}
                
                {paidSubscriptionExpired && user?.manual_subscription !== 'activated' && (
                  <div className="text-xs sm:text-sm px-2 sm:px-3 py-1 rounded-full bg-red-500/20 text-red-400 border border-red-500/50 animate-pulse whitespace-nowrap">
                    ⚠️ <span className="hidden sm:inline">Subscription </span>Ended
                  </div>
                )}
                
                <Link 
                  href="/subscription" 
                  className="hidden sm:block text-xs sm:text-sm px-2 sm:px-3 lg:px-4 py-1.5 sm:py-2 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 hover:bg-emerald-500/30 transition font-semibold whitespace-nowrap touch-target"
                >
                  <span className="hidden lg:inline">Subscription</span>
                  <span className="lg:hidden">Sub</span>
                </Link>

                <UserProfileDropdown user={user} logout={logout} />
              </>
            ) : (
              <>
                <Link 
                  href="/login" 
                  className="text-xs sm:text-sm text-slate-300 hover:text-white transition whitespace-nowrap touch-target px-2 sm:px-3 py-2"
                >
                  Login
                </Link>
                <Link 
                  href="/register" 
                  className="bg-cyan-500 hover:bg-cyan-600 text-white text-xs sm:text-sm px-2 sm:px-3 lg:px-4 py-1.5 sm:py-2 rounded-lg transition font-semibold whitespace-nowrap touch-target"
                >
                  <span className="hidden sm:inline">Start Free Trial</span>
                  <span className="sm:hidden">Trial</span>
                </Link>
              </>
            )}

            <MobileMenu isAuthenticated={isAuthenticated} />
          </div>
        </div>
      </div>
    </nav>
  );
}
