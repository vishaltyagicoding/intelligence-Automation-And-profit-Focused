/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  
  // Environment variables for client-side
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || '',
  },
  
  // Disable rewrites in production (nginx handles routing)
  async rewrites() {
    // Only use rewrites in development
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ];
    }
    return [];
  },
  
  // Production optimizations
  swcMinify: true,
  compress: true,
  
  // Image optimization
  images: {
    unoptimized: true, // Disable Next.js image optimization (use CDN in production)
  },
  
  // Disable telemetry
  telemetry: {
    enabled: false,
  },
  
  // Skip static generation for pages that use search params
  experimental: {
    missingSuspenseWithCSRBailout: false,
  },
};

module.exports = nextConfig;
