'use client';

import Link from 'next/link';

export default function LearnPage() {
  const courses = [
    {
      title: 'Crypto Trading Fundamentals',
      description: 'Master the basics of cryptocurrency trading, market analysis, and risk management strategies.',
      duration: '4 weeks',
      level: 'Beginner',
      icon: '📚',
      topics: ['Market Basics', 'Technical Analysis', 'Risk Management', 'Trading Psychology'],
    },
    {
      title: 'SmartRisk Trading Strategies',
      description: 'Learn how SmartRisk transforms trading decisions and signal generation.',
      duration: '3 weeks',
      level: 'Intermediate',
      icon: '🤖',
      topics: ['Machine Learning', 'Signal Analysis', 'Pattern Recognition', 'Automated Trading'],
    },
    {
      title: 'Advanced Chart Analysis',
      description: 'Deep dive into candlestick patterns, indicators, and multi-timeframe analysis techniques.',
      duration: '5 weeks',
      level: 'Advanced',
      icon: '📈',
      topics: ['Candlestick Patterns', 'Volume Analysis', 'Support & Resistance', 'Trend Following'],
    },
    {
      title: 'Portfolio Management',
      description: 'Build and manage a diversified crypto portfolio with proven allocation strategies.',
      duration: '3 weeks',
      level: 'Intermediate',
      icon: '💼',
      topics: ['Asset Allocation', 'Rebalancing', 'Risk Assessment', 'Performance Tracking'],
    },
  ];

  const resources = [
    {
      title: 'Market Psychology Guide',
      type: 'eBook',
      description: 'Understanding emotions and behavior in volatile markets',
    },
    {
      title: 'Technical Indicators Cheat Sheet',
      type: 'PDF',
      description: 'Quick reference for RSI, MACD, Bollinger Bands, and more',
    },
    {
      title: 'Live Trading Webinars',
      type: 'Video',
      description: 'Weekly sessions with professional traders',
    },
    {
      title: 'Community Trading Forum',
      type: 'Community',
      description: 'Connect with traders, share strategies, and learn together',
    },
  ];

  return (
    <div className="min-h-screen bg-[#0a0e1a]">
      {/* Navigation */}


      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-[#0f1419] via-[#0a0e1a] to-[#0f1419] py-20">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzIxMjEyMSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] bg-repeat"></div>
        </div>
        
        <div className="relative mx-auto max-w-7xl px-6 text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-4 py-2">
            <span className="text-2xl">🎓</span>
            <span className="text-sm font-semibold text-cyan-400">Trading Education Hub</span>
          </div>
          
          <h1 className="mb-6 text-5xl font-bold text-white md:text-6xl">
            Master Crypto Trading<br />
            <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              With SmartRisk Insights
            </span>
          </h1>
          
          <p className="mx-auto mb-8 max-w-2xl text-lg text-slate-400">
            From beginner fundamentals to advanced strategies — learn how professional traders combine technical analysis with SmartRisk signals to make confident trading decisions.
          </p>
          
          <div className="flex flex-wrap items-center justify-center gap-4">
            <button className="rounded-lg bg-cyan-500 px-8 py-3 font-semibold text-white hover:bg-cyan-600 transition">
              Start Learning Free
            </button>
            <button className="rounded-lg border border-slate-700 bg-slate-800/50 px-8 py-3 font-semibold text-white hover:bg-slate-700/50 transition">
              Browse Courses
            </button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="border-b border-slate-800/50 bg-[#0f1419] py-12">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            <div className="text-center">
              <div className="mb-2 text-4xl font-bold text-cyan-400">50+</div>
              <div className="text-sm text-slate-400">Video Lessons</div>
            </div>
            <div className="text-center">
              <div className="mb-2 text-4xl font-bold text-cyan-400">10K+</div>
              <div className="text-sm text-slate-400">Active Students</div>
            </div>
            <div className="text-center">
              <div className="mb-2 text-4xl font-bold text-cyan-400">4.8★</div>
              <div className="text-sm text-slate-400">Average Rating</div>
            </div>
            <div className="text-center">
              <div className="mb-2 text-4xl font-bold text-cyan-400">24/7</div>
              <div className="text-sm text-slate-400">Support Access</div>
            </div>
          </div>
        </div>
      </section>

      {/* Courses Section */}
      <section className="py-16">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold text-white">Featured Courses</h2>
            <p className="text-slate-400">Structured learning paths designed by professional traders</p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {courses.map((course, index) => (
              <div
                key={index}
                className="group rounded-xl border border-slate-800/50 bg-[#0f1419] p-6 transition hover:border-cyan-500/30 hover:shadow-lg hover:shadow-cyan-500/10"
              >
                <div className="mb-4 flex items-start justify-between">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-cyan-500/10 text-2xl">
                    {course.icon}
                  </div>
                  <span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-medium text-slate-300">
                    {course.level}
                  </span>
                </div>

                <h3 className="mb-2 text-xl font-bold text-white group-hover:text-cyan-400 transition">
                  {course.title}
                </h3>
                <p className="mb-4 text-sm text-slate-400">{course.description}</p>

                <div className="mb-4 flex flex-wrap gap-2">
                  {course.topics.map((topic, i) => (
                    <span
                      key={i}
                      className="rounded-full border border-slate-700/50 bg-slate-800/30 px-3 py-1 text-xs text-slate-400"
                    >
                      {topic}
                    </span>
                  ))}
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">⏱️ {course.duration}</span>
                  <button className="rounded-lg bg-cyan-500/10 px-4 py-2 text-sm font-semibold text-cyan-400 hover:bg-cyan-500/20 transition">
                    Enroll Now →
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Resources Section */}
      <section className="border-t border-slate-800/50 bg-[#0f1419] py-16">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold text-white">Free Learning Resources</h2>
            <p className="text-slate-400">Downloadable guides, webinars, and community access</p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {resources.map((resource, index) => (
              <div
                key={index}
                className="rounded-xl border border-slate-800/50 bg-[#0a0e1a] p-6 text-center transition hover:border-cyan-500/30"
              >
                <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-cyan-500/10">
                  <span className="text-2xl">
                    {resource.type === 'eBook' && '📖'}
                    {resource.type === 'PDF' && '📄'}
                    {resource.type === 'Video' && '🎥'}
                    {resource.type === 'Community' && '👥'}
                  </span>
                </div>
                <h3 className="mb-2 font-bold text-white">{resource.title}</h3>
                <p className="mb-4 text-sm text-slate-400">{resource.description}</p>
                <button className="text-sm font-semibold text-cyan-400 hover:text-cyan-300 transition">
                  Access Now →
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16">
        <div className="mx-auto max-w-4xl px-6">
          <div className="rounded-2xl border border-cyan-500/30 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 p-12 text-center">
            <h2 className="mb-4 text-3xl font-bold text-white">Ready to Start Your Trading Journey?</h2>
            <p className="mb-8 text-slate-400">
              Join thousands of traders who are mastering crypto markets with our SmartRisk platform.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/"
                className="rounded-lg bg-cyan-500 px-8 py-3 font-semibold text-white hover:bg-cyan-600 transition"
              >
                Create Free Account
              </Link>
              <Link
                href="/"
                className="rounded-lg border border-slate-700 bg-slate-800/50 px-8 py-3 font-semibold text-white hover:bg-slate-700/50 transition"
              >
                Try SmartRisk Dashboard
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800/50 bg-[#0f1419] py-8">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <p className="text-sm text-slate-500">
            © 2026 SmartRisk. Powered by SmartRisk trading education and signals.
          </p>
        </div>
      </footer>
    </div>
  );
}
