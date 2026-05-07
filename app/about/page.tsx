'use client';

import Link from 'next/link';

export default function AboutPage() {
  const stats = [
    { value: '50K+', label: 'Active Traders' },
    { value: '99.9%', label: 'Uptime' },
    { value: '$2B+', label: 'Trading Volume' },
    { value: '150+', label: 'Countries' },
  ];

  const values = [
    {
      icon: '🎯',
      title: 'Accuracy First',
      description: 'Our AI models are trained on millions of data points to deliver precise signals.',
    },
    {
      icon: '🔒',
      title: 'Security & Privacy',
      description: 'Bank-level encryption and zero-knowledge architecture protect your data.',
    },
    {
      icon: '⚡',
      title: 'Real-Time Speed',
      description: 'Sub-second latency ensures you never miss a trading opportunity.',
    },
    {
      icon: '🤝',
      title: 'Community Driven',
      description: 'Built with feedback from thousands of traders worldwide.',
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
          <h1 className="mb-6 text-5xl font-bold text-white md:text-6xl">
            Building the Future of<br />
            <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              Powered by SmartRisk Trading
            </span>
          </h1>
          
          <p className="mx-auto mb-8 max-w-2xl text-lg text-slate-400">
            SmartRisk combines cutting-edge technology with real-time market data to help traders make smarter, faster decisions in the volatile crypto markets.
          </p>
        </div>
      </section>

      {/* Stats Section */}
      <section className="border-b border-slate-800/50 bg-[#0f1419] py-16">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="mb-2 text-4xl font-bold text-cyan-400">{stat.value}</div>
                <div className="text-sm text-slate-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid gap-12 lg:grid-cols-2 lg:gap-16">
            <div>
              <h2 className="mb-6 text-3xl font-bold text-white">Our Mission</h2>
              <div className="space-y-4 text-slate-400">
                <p>
                  Founded in 2024, SmartRisk was born from a simple observation: traditional trading tools weren't keeping pace with the speed and complexity of modern crypto markets.
                </p>
                <p>
                  We set out to build a platform that combines institutional-grade AI technology with an interface that any trader can use — from complete beginners to seasoned professionals.
                </p>
                <p>
                  Today, we serve over 50,000 traders across 150+ countries, processing billions in trading volume and delivering real-time signals that help our users navigate volatile markets with confidence.
                </p>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800/50 bg-[#0f1419] p-8">
              <h3 className="mb-6 text-2xl font-bold text-white">What Sets Us Apart</h3>
              <div className="space-y-6">
                <div className="flex gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10">
                    <span className="text-2xl">🧠</span>
                  </div>
                  <div>
                    <h4 className="mb-1 font-semibold text-white">Advanced SmartRisk Models</h4>
                    <p className="text-sm text-slate-400">
                      Our systems analyze millions of data points per second
                    </p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10">
                    <span className="text-2xl">⚡</span>
                  </div>
                  <div>
                    <h4 className="mb-1 font-semibold text-white">Lightning Fast</h4>
                    <p className="text-sm text-slate-400">
                      Sub-second latency ensures you're always ahead of the market
                    </p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10">
                    <span className="text-2xl">🎯</span>
                  </div>
                  <div>
                    <h4 className="mb-1 font-semibold text-white">Proven Accuracy</h4>
                    <p className="text-sm text-slate-400">
                      Backtested on years of historical data with consistent results
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="border-t border-slate-800/50 bg-[#0f1419] py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold text-white">Our Core Values</h2>
            <p className="text-slate-400">The principles that guide everything we build</p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {values.map((value, index) => (
              <div
                key={index}
                className="rounded-xl border border-slate-800/50 bg-[#0a0e1a] p-6 text-center transition hover:border-cyan-500/30"
              >
                <div className="mb-4 text-4xl">{value.icon}</div>
                <h3 className="mb-2 font-bold text-white">{value.title}</h3>
                <p className="text-sm text-slate-400">{value.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="border-t border-slate-800/50 bg-[#0f1419] py-20">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white">Join Our Growing Community</h2>
          <p className="mb-8 text-slate-400">
            Start trading smarter with SmartRisk signals and real-time market analysis.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/"
              className="rounded-lg border border-slate-700 bg-slate-800/50 px-8 py-3 font-semibold text-white hover:bg-slate-700/50 transition"
            >
              View Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800/50 bg-[#0f1419] py-8">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <p className="text-sm text-slate-500">
            © 2026 SmartRisk. Powered by SmartRisk trading signals for crypto markets.
          </p>
        </div>
      </footer>
    </div>
  );
}
