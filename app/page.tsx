'use client';

import Link from 'next/link';
import { useState } from 'react';

export default function HomePage() {
  const [activeFeature, setActiveFeature] = useState(0);

  const features = [
    {
      title: 'SmartRisk Reversal Signals',
      description: 'Advanced TradingView Pine Script algorithm detects high-probability reversal zones in real-time.',
      icon: '🎯',
      color: 'from-cyan-500 to-blue-500',
    },
    {
      title: 'Real-Time Market Data',
      description: 'Live WebSocket connection to Binance for instant price updates and signal generation.',
      icon: '⚡',
      color: 'from-blue-500 to-purple-500',
    },
    {
      title: 'Multi-Timeframe Analysis',
      description: 'Track signals across 10 timeframes from 1-minute to daily charts for complete market view.',
      icon: '📊',
      color: 'from-purple-500 to-pink-500',
    },
    {
      title: 'Signal Alternation Protection',
      description: 'Intelligent filtering ensures signals always alternate BUY → SELL → BUY for quality trades.',
      icon: '🛡️',
      color: 'from-pink-500 to-red-500',
    },
  ];

  const cryptos = [
    { symbol: 'BTCUSD', name: 'Bitcoin', icon: '₿' },
    { symbol: 'ETHUSD', name: 'Ethereum', icon: 'Ξ' },
    { symbol: 'XAUUSD', name: 'Gold (XAU)', icon: '🪙' },
    { symbol: 'LTCUSD', name: 'Litecoin', icon: 'Ł' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-20 left-20 h-72 w-72 rounded-full bg-cyan-500 blur-[120px]"></div>
          <div className="absolute bottom-20 right-20 h-72 w-72 rounded-full bg-blue-500 blur-[120px]"></div>
        </div>

        <div className="relative mx-auto max-w-7xl px-6 py-24 sm:py-32">
          <div className="text-center">
            {/* Badge */}
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-4 py-3 text-sm font-semibold text-cyan-400">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-cyan-500"></span>
              </span>
              Live SmartRisk Trading Signals
            </div>

            {/* Main Heading */}
            <h1 className="mb-6 text-5xl font-bold tracking-tight text-white sm:text-6xl leading-relaxed pb-6">
              Trade Smarter with
              <span className="block bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent pb-6 overflow-visible" style={{ lineHeight: '1.3' }}>
                SmartRisk Signals
              </span>
            </h1>

            <p className="mx-auto mb-10 max-w-2xl text-lg leading-8 text-slate-400">
              Professional cryptocurrency trading platform powered by advanced reversal detection algorithms. 
              Get real-time BUY and SELL signals for Bitcoin, Ethereum, Ripple, and Litecoin across multiple timeframes.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/dashboard"
                className="group relative inline-flex items-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 px-8 py-4 text-lg font-bold text-white shadow-lg shadow-cyan-500/30 transition-all hover:shadow-cyan-500/50 hover:scale-105"
              >
                <span>Launch Dashboard</span>
                <svg className="h-5 w-5 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>

              <Link
                href="/history"
                className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800/50 px-8 py-4 text-lg font-semibold text-white backdrop-blur-sm transition-all hover:border-slate-600 hover:bg-slate-800"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                View Signal History
              </Link>
            </div>

            {/* Stats */}
            <div className="mt-16 grid grid-cols-2 gap-8 sm:grid-cols-4">
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 backdrop-blur-sm">
                <div className="text-3xl font-bold text-cyan-400">4</div>
                <div className="mt-1 text-sm text-slate-400">Cryptocurrencies</div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 backdrop-blur-sm">
                <div className="text-3xl font-bold text-blue-400">10</div>
                <div className="mt-1 text-sm text-slate-400">Timeframes</div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 backdrop-blur-sm">
                <div className="text-3xl font-bold text-purple-400">24/7</div>
                <div className="mt-1 text-sm text-slate-400">Live Monitoring</div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 backdrop-blur-sm">
                <div className="text-3xl font-bold text-pink-400">Real-Time</div>
                <div className="mt-1 text-sm text-slate-400">Signal Generation</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Supported Cryptocurrencies */}
      <section className="border-t border-slate-800 bg-slate-900/30 py-16">
        <div className="mx-auto max-w-7xl px-6">
          <h2 className="mb-12 text-center text-3xl font-bold text-white">
            Supported Cryptocurrencies
          </h2>
          <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
            {cryptos.map((crypto) => (
              <Link
                key={crypto.symbol}
                href={`/asset/${crypto.symbol.toLowerCase()}`}
                className="group rounded-xl border border-slate-800 bg-slate-900/50 p-6 text-center backdrop-blur-sm transition-all hover:border-cyan-500/50 hover:bg-slate-800/50 hover:shadow-lg hover:shadow-cyan-500/20"
              >
                <div className="mb-3 text-5xl">{crypto.icon}</div>
                <div className="text-lg font-bold text-white">{crypto.name}</div>
                <div className="mt-1 text-sm text-slate-400">{crypto.symbol}</div>
                <div className="mt-3 text-xs font-semibold text-cyan-400 opacity-0 transition-opacity group-hover:opacity-100">
                  View Live Chart →
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-4xl font-bold text-white">
              Powerful Features for Smart Trading
            </h2>
            <p className="mx-auto max-w-2xl text-lg text-slate-400">
              Advanced technology meets intuitive design to give you the edge in cryptocurrency trading
            </p>
          </div>

          <div className="grid gap-8 lg:grid-cols-2">
            {features.map((feature, index) => (
              <div
                key={index}
                onMouseEnter={() => setActiveFeature(index)}
                className={`group cursor-pointer rounded-2xl border p-8 transition-all ${
                  activeFeature === index
                    ? 'border-cyan-500/50 bg-gradient-to-br from-slate-900 to-slate-800 shadow-xl shadow-cyan-500/20'
                    : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'
                }`}
              >
                <div className={`mb-4 inline-flex h-16 w-16 items-center justify-center rounded-xl bg-gradient-to-br ${feature.color} text-3xl shadow-lg`}>
                  {feature.icon}
                </div>
                <h3 className="mb-3 text-2xl font-bold text-white">{feature.title}</h3>
                <p className="text-slate-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="border-t border-slate-800 bg-slate-900/30 py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-4xl font-bold text-white">How It Works</h2>
            <p className="mx-auto max-w-2xl text-lg text-slate-400">
              Simple, powerful, and automated trading signal generation
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-3">
            <div className="relative rounded-2xl border border-slate-800 bg-slate-900/50 p-8 text-center">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-cyan-500/20 text-2xl font-bold text-cyan-400">
                1
              </div>
              <h3 className="mb-3 text-xl font-bold text-white">Connect to Live Data</h3>
              <p className="text-slate-400">
                Real-time WebSocket connection to Binance streams live market data 24/7
              </p>
            </div>

            <div className="relative rounded-2xl border border-slate-800 bg-slate-900/50 p-8 text-center">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/20 text-2xl font-bold text-blue-400">
                2
              </div>
              <h3 className="mb-3 text-xl font-bold text-white">SmartRisk Analyzes Patterns</h3>
              <p className="text-slate-400">
                Advanced reversal detection algorithm identifies high-probability entry zones
              </p>
            </div>

            <div className="relative rounded-2xl border border-slate-800 bg-slate-900/50 p-8 text-center">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-purple-500/20 text-2xl font-bold text-purple-400">
                3
              </div>
              <h3 className="mb-3 text-xl font-bold text-white">Get Instant Signals</h3>
              <p className="text-slate-400">
                Receive BUY and SELL signals directly on your chart with entry and exit zones
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="mx-auto max-w-4xl px-6">
          <div className="relative overflow-hidden rounded-3xl border border-cyan-500/30 bg-gradient-to-br from-cyan-500/10 via-blue-500/10 to-purple-500/10 p-12 text-center backdrop-blur-sm">
            <div className="absolute inset-0 opacity-20">
              <div className="absolute -top-10 -left-10 h-40 w-40 rounded-full bg-cyan-500 blur-[80px]"></div>
              <div className="absolute -bottom-10 -right-10 h-40 w-40 rounded-full bg-blue-500 blur-[80px]"></div>
            </div>

            <div className="relative">
              <h2 className="mb-4 text-4xl font-bold text-white">
                Ready to Start Trading Smarter?
              </h2>
              <p className="mb-8 text-lg text-slate-300">
                Access professional-grade SmartRisk trading signals for free. No credit card required.
              </p>
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 px-8 py-4 text-lg font-bold text-white shadow-lg shadow-cyan-500/30 transition-all hover:shadow-cyan-500/50 hover:scale-105"
              >
                Launch Dashboard Now
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/50 py-12">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid gap-8 md:grid-cols-3">
            <div>
              <div className="mb-4 text-2xl font-bold text-white">SmartRisk</div>
              <p className="text-sm text-slate-400">
                Powered by SmartRisk cryptocurrency trading signals for Bitcoin, Ethereum, Ripple, and Litecoin.
              </p>
            </div>

            <div>
              <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
                Quick Links
              </h3>
              <div className="space-y-2">
                <Link href="/dashboard" className="block text-slate-300 hover:text-white transition">
                  Dashboard
                </Link>
                <Link href="/history" className="block text-slate-300 hover:text-white transition">
                  Signal History
                </Link>
                <Link href="/learn" className="block text-slate-300 hover:text-white transition">
                  Learn
                </Link>
                <Link href="/about" className="block text-slate-300 hover:text-white transition">
                  About
                </Link>
              </div>
            </div>

            <div>
              <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
                Supported Assets
              </h3>
              <div className="space-y-2">
                {cryptos.map((crypto) => (
                  <Link
                    key={crypto.symbol}
                    href={`/asset/${crypto.symbol.toLowerCase()}`}
                    className="block text-slate-300 hover:text-white transition"
                  >
                    {crypto.icon} {crypto.name} ({crypto.symbol})
                  </Link>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-12 border-t border-slate-800 pt-8 text-center text-sm text-slate-500">
            <p>© 2026 SmartRisk. Powered by SmartRisk trading signals for crypto markets.</p>
            <p className="mt-2">
              <strong className="text-amber-400">Disclaimer:</strong> Trading cryptocurrencies carries risk. 
              Signals are for informational purposes only and not financial advice.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}