/**
 * Application Configuration
 * Works with localhost, ngrok, and any production deployment
 */

/**
 * Get the base API URL
 * Returns empty string for relative URLs (works with any domain)
 * This ensures API calls work whether user accesses via IP, domain, or localhost
 */
export function getApiUrl(): string {
  // Always use relative URL for maximum compatibility
  // Nginx will proxy /api/ requests to Django backend
  return '';
}

/**
 * Get the WebSocket base URL
 * Auto-detects protocol and host from browser location
 * Works with any domain, IP, or localhost
 */
export function getWebSocketUrl(): string {
  if (typeof window === 'undefined') {
    // Server-side: return placeholder
    return 'ws://localhost';
  }

  // Always auto-detect from browser location for maximum compatibility
  // This ensures WebSocket works whether user accesses via:
  // - IP address (http://54.183.178.141)
  // - Domain (http://smartriskfx.com)
  // - Localhost (http://localhost)
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
