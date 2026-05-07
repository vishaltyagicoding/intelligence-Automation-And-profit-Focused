import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/lib/AuthContext';
import Navigation from '@/components/Navigation';

export const metadata: Metadata = {
  title: 'SmartRisk - Powered by SmartRisk Trading Platform',
  description: 'Advanced cryptocurrency trading platform with SmartRisk signals and real-time market data',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📈</text></svg>" />
      </head>
      <body className="bg-slate-950 text-white min-h-screen">
        <AuthProvider>
          <Navigation />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
