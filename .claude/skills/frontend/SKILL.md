# Frontend Development Skill

## Overview
Next.js 14 frontend with TypeScript, TailwindCSS, and real-time WebSocket integration.

## Core Technologies
- Next.js 14 (App Router)
- TypeScript 5.x
- TailwindCSS 3.x
- Lightweight Charts (TradingView)
- React Context API

## Project Structure
```
app/
├── page.tsx              # Landing page
├── layout.tsx            # Root layout
├── dashboard/            # Main trading dashboard
├── history/              # Signal history
├── login/                # Authentication
├── register/             # User registration
├── settings/             # User settings
├── subscription/         # Subscription management
└── signal-alerts/        # Alert preferences

components/
├── Navigation.tsx        # Main navigation
├── ChartComponent.tsx    # Trading chart
└── WatchlistPanel.tsx    # Price watchlist

lib/
├── config.ts             # API/WebSocket URLs
├── AuthContext.tsx       # Authentication context
└── utils.ts              # Utility functions
```

## Key Features

### Real-Time Price Updates
- WebSocket connection per symbol+timeframe
- Automatic reconnection on disconnect
- Fallback to REST API if WebSocket stale
- Instant price display on page load

### Interactive Charts
- TradingView Lightweight Charts
- Candlestick data from Binance.US
- Reversal zone overlays
- BUY/SELL signal markers
- Multiple timeframes (5m, 15m, 30m, 1h, 2h, 4h, 1d)

### Signal History
- Parallel API calls for all symbols+timeframes
- Live WebSocket updates (no polling)
- Filtering by symbol and action
- Last 5 months of data
- Auto-refresh every 60 seconds

### Authentication
- Token-based auth with AuthContext
- Protected routes with redirect
- Subscription status check
- Trial period management

## Component Patterns

### Page Component
```typescript
'use client';

export default function Page() {
  const { isAuthenticated, loading, user } = useAuth();
  const [data, setData] = useState([]);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading]);

  // Component logic...

  if (loading) return <LoadingSpinner />;
  if (!isAuthenticated) return null;

  return <div>...</div>;
}
```

### WebSocket Hook
```typescript
useEffect(() => {
  if (!isAuthenticated) return;

  const ws = new WebSocket(url);
  
  ws.onopen = () => console.log('Connected');
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleMessage(data);
  };
  ws.onerror = (error) => console.error('WS Error:', error);
  ws.onclose = () => console.log('Disconnected');

  return () => ws.close(); // Cleanup
}, [isAuthenticated]);
```

### API Call Pattern
```typescript
const fetchData = async () => {
  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch('/api/endpoint/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) throw new Error('API Error');
    const data = await response.json();
    setData(data);
  } catch (error) {
    console.error('Error:', error);
  }
};
```

## Chart Integration

### Setup
```typescript
import { createChart } from 'lightweight-charts';

const chart = createChart(containerRef.current, {
  layout: {
    background: { color: '#0a0e1a' },
    textColor: '#d1d5db',
  },
  grid: {
    vertLines: { color: '#1e293b' },
    horzLines: { color: '#1e293b' },
  },
  timeScale: {
    timeVisible: true,
    secondsVisible: false,
  },
});
```

### Add Candlestick Data
```typescript
const candlestickSeries = chart.addCandlestickSeries({
  upColor: '#10b981',
  downColor: '#ef4444',
  borderVisible: false,
  wickUpColor: '#10b981',
  wickDownColor: '#ef4444',
});

candlestickSeries.setData(klineData);
```

### Add Reversal Zones
```typescript
// Outer zone boundaries
const outerTopLine = chart.addLineSeries({
  color: zone.is_bullish ? '#10b981' : '#ef4444',
  lineWidth: 2,
  lineStyle: 2, // Dashed
});

outerTopLine.setData([
  { time: zone.timestamp, value: zone.outer_top },
  { time: endTime, value: zone.outer_top },
]);
```

### Add Signal Markers
```typescript
candlestickSeries.setMarkers([{
  time: signal.timestamp,
  position: signal.is_bullish ? 'belowBar' : 'aboveBar',
  color: signal.is_bullish ? '#10b981' : '#ef4444',
  shape: signal.is_bullish ? 'arrowUp' : 'arrowDown',
  text: signal.label,
}]);
```

## Styling Guidelines

### Color Palette
```typescript
const colors = {
  bg: {
    primary: '#0a0e1a',
    secondary: '#0f1419',
    tertiary: '#1e293b',
  },
  text: {
    primary: '#ffffff',
    secondary: '#d1d5db',
    tertiary: '#94a3b8',
  },
  accent: {
    primary: '#06b6d4',  // cyan-500
    secondary: '#2563eb', // blue-600
  },
  status: {
    success: '#34d399',  // emerald-400
    error: '#f87171',    // rose-400
    warning: '#fbbf24',  // amber-400
  },
};
```

### Responsive Classes
```typescript
<div className="
  px-4 md:px-6 lg:px-8
  text-sm md:text-base lg:text-lg
  grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3
">
```

## State Management

### AuthContext
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
- Use `useState` for component state
- Use `useRef` for mutable values
- Use `useCallback` for memoized functions
- Use `useMemo` for expensive computations

## Performance Optimization

### Code Splitting
```typescript
import dynamic from 'next/dynamic';

const ChartComponent = dynamic(() => import('@/components/ChartComponent'), {
  ssr: false,
  loading: () => <LoadingSpinner />,
});
```

### Memoization
```typescript
const filteredSignals = useMemo(() => {
  return signals.filter(s => 
    (filter === 'ALL' || s.action === filter) &&
    (symbolFilter === 'ALL' || s.symbol === symbolFilter)
  );
}, [signals, filter, symbolFilter]);
```

### WebSocket Optimization
- Reuse connections across components
- Close on unmount
- Throttle high-frequency updates
- Batch state updates

## Error Handling

### API Errors
```typescript
try {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
} catch (error) {
  console.error('API Error:', error);
  setError('Failed to load data');
}
```

### WebSocket Errors
```typescript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  // Attempt reconnection after delay
  setTimeout(() => connectWebSocket(), 5000);
};
```

## Loading States
```typescript
{loading ? (
  <div className="flex items-center justify-center">
    <div className="h-12 w-12 animate-spin rounded-full border-4 border-cyan-500 border-r-transparent" />
  </div>
) : (
  <Content />
)}
```

## Common Tasks

### Add New Page
1. Create `app/page-name/page.tsx`
2. Add to navigation if needed
3. Implement auth protection
4. Add to routing

### Add New Component
1. Create `components/ComponentName.tsx`
2. Export from component
3. Import where needed
4. Add TypeScript types

### Connect to API
1. Get token from localStorage
2. Add Authorization header
3. Handle response
4. Update state

### Add WebSocket Connection
1. Create WebSocket instance
2. Handle onmessage events
3. Cleanup on unmount
4. Handle reconnection

## Debugging

### Browser DevTools
- Console: View logs and errors
- Network: Monitor API calls
- Application: Check localStorage
- WebSocket: Monitor WS frames

### React DevTools
- Component tree
- Props and state
- Performance profiling

## Build and Deploy
```bash
# Development
npm run dev

# Production build
npm run build
npm start

# Type check
npm run type-check

# Lint
npm run lint
```
