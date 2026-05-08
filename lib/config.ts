/**
 * Application Configuration
 * Works with localhost, ngrok, and any production deployment
 */

/**
 * Get the base API URL
 * Returns relative URL by default (works with any domain)
 */
export function getApiUrl(): string {
  // Use environment variable if set, otherwise use relative URL
  return process.env.NEXT_PUBLIC_API_URL || '';
}

/**
 * Get the WebSocket base URL
 * Auto-detects protocol and host from browser location
 */
export function getWebSocketUrl(): string {
  if (typeof window === 'undefined') {
    // Server-side: return placeholder
    return 'ws://localhost';
  }

  // Use environment variable if set
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }

  // Auto-detect from browser location
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host; // includes port if present
  
  return `${protocol}//${host}`;
}

/**
 * Build full API endpoint URL
 */
export function apiEndpoint(path: string): string {
  const base = getApiUrl();
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${cleanPath}`;
}

/**
 * Build full WebSocket endpoint URL
 */
export function wsEndpoint(path: string): string {
  const base = getWebSocketUrl();
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${cleanPath}`;
}
