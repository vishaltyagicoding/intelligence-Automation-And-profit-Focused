# Frontend Architecture and Conventions

## Technology Stack
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.x
- **Styling**: TailwindCSS 3.x
- **Charts**: Lightweight Charts (TradingView)
- **State Management**: React Context API
- **HTTP Client**: Fetch API
- **WebSocket**: Native WebSocket API

## Project Structure
```
app/
├── page.tsx                    # Landing page
├── layout.tsx                  # Root layout
├── globals.css                 # Global styles
├── dashboard/page.tsx          # Main dashboard
├── history/page.tsx            # Signal history
├── login/page.tsx              # Login page
├── register/page.tsx           # Registration
├── settings/page.tsx           # User settings
├── subscription/page.tsx       # Subscription management
├── signal-alerts/page.tsx      # Alert preferences
└── api/health/route.ts         # Health check endpoint

components/
├── Navigation.tsx              # Main navigation
├── ChartComponent.tsx          # Trading chart
├── WatchlistPanel.tsx          # Price watchlist
└── ProtectedRoute.tsx          # Auth guard

lib/
├── config.ts                   # API/WS URLs
├── AuthContext.tsx             # Authentication
└── utils.ts                    # Utilities
```

## Routing
- Uses Next.js App Router (file-based routing)
- Dynamic routes: `[symbol]` for asset pages
- Protected routes: Check auth in `useEffect`

## Authentication Flow
1. User logs in → receives `access_token`
2. Token stored in `localStorage`
3. `AuthContext` provides auth state globally
4. Protected pages redirect to `/login` if not authenticated
5. Subscription check redirects to `/subscription` if inactive

## State Management

### Global State (AuthContext)
```typescript
interface AuthContextType {
  isAuthenticated: boolean;
  loading: boolean;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (data: RegisterData) => Promise<void>;
}
```

### Local State
- Use `useState` for component-specific state
- Use `useRef` for mutable values that don't trigger re-renders
- Use `useCallback` for memoized functions
- Use `useMemo` for expensive computations

## API Integration

### REST API Calls
```typescript
const response = await fetch('/api/endpoint/', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
});
const data = await response.json();
```

### WebSocket Connection
```typescript
const ws = new WebSocket(`${wsUrl}/ws/market/${symbol}/${timeframe}/`);

ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle message
};
ws.onerror = (error) => console.error('WS Error:', error);
ws.onclose = () => console.log('Disconnected');
```

## Chart Integration

### Lightweight Charts Setup
```typescript
import { createChart } from 'lightweight-charts';

const chart = createChart(container, {
  layout: {
    background: { color: '#0a0e1a' },
    textColor: '#d1d5db',
  },
  grid: {
    vertLines: { color: '#1e293b' },
    horzLines: { color: '#1e293b' },
  },
});

const candlestickSeries = chart.addCandlestickSeries();
```

### Reversal Zone Rendering
- Use `addLineSeries()` for zone boundaries
- Use `createPriceLine()` for horizontal levels
- Use markers for BUY/SELL labels

## Styling Guidelines

### Color Scheme
```css
/* Backgrounds */
--bg-primary: #0a0e1a
--bg-secondary: #0f1419
--bg-tertiary: #1e293b

/* Text */
--text-primary: #ffffff
--text-secondary: #d1d5db
--text-tertiary: #94a3b8

/* Accent */
--accent-primary: #06b6d4 (cyan-500)
--accent-secondary: #2563eb (blue-600)

/* Status */
--success: #34d399 (emerald-400)
--error: #f87171 (rose-400)
--warning: #fbbf24 (amber-400)
```

### Responsive Design
- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Use Tailwind responsive prefixes: `md:`, `lg:`, etc.

## Performance Optimization

### Code Splitting
- Use dynamic imports for heavy components
- Lazy load charts and non-critical components

### Memoization
```typescript
const memoizedValue = useMemo(() => expensiveComputation(), [deps]);
const memoizedCallback = useCallback(() => { /* ... */ }, [deps]);
```

### WebSocket Optimization
- Reuse connections across components
- Close connections on unmount
- Implement reconnection logic
- Throttle high-frequency updates

### Image Optimization
- Use Next.js `<Image>` component
- Provide width and height
- Use appropriate formats (WebP)

## Error Handling

### API Errors
```typescript
try {
  const response = await fetch('/api/endpoint/');
  if (!response.ok) throw new Error('API Error');
  const data = await response.json();
} catch (error) {
  console.error('Error:', error);
  // Show user-friendly message
}
```

### WebSocket Errors
```typescript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  // Attempt reconnection
};
```

## Loading States
- Show spinners for async operations
- Use skeleton screens for content loading
- Disable buttons during submission
- Show loading overlays for chart transitions

## Accessibility
- Use semantic HTML elements
- Provide alt text for images
- Ensure keyboard navigation
- Use ARIA labels where needed
- Maintain color contrast ratios

## SEO Optimization
- Use Next.js metadata API
- Provide page titles and descriptions
- Use semantic HTML structure
- Implement Open Graph tags

## Environment Variables
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Build and Deployment
- Build command: `npm run build`
- Start command: `npm start`
- Dev command: `npm run dev`
- Lint command: `npm run lint`
