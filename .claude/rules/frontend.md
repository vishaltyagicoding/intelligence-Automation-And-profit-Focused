# Frontend Reference

## Stack
- Next.js 14 App Router, TypeScript 5.x, TailwindCSS 3.x
- lightweight-charts v4.2.1 (TradingView chart library)

## Key Pages
| Page | File | Purpose |
|---|---|---|
| Dashboard | `app/dashboard/page.tsx` | Main dashboard with watchlist + live chart |
| Asset View | `app/asset/[symbol]/page.tsx` | Full-screen asset chart |
| History | `app/history/page.tsx` | Signal history table |
| Settings | `app/settings/page.tsx` | User settings |
| Signal Alerts | `app/signal-alerts/page.tsx` | Email alert preferences |

## ChartComponent.tsx — Critical Architecture

### Refs (do not rename or repurpose)
```typescript
chartRef           // IChartApi — the chart instance
seriesRef          // ISeriesApi<Candlestick> — candlestick series
markersRef         // Map<time, SeriesMarker> — ONE BUY/SELL marker per candle time
persistentSignalsRef // Map<"asset:tf:time", SeriesMarker> — survives timeframe change
slTargetMapRef     // Map<time, {sl, target, entry, isBullish}> — for line rendering
slTargetMarkersRef // Map<time, SeriesMarker[]> — stub, no longer used actively
activePriceLines   // any[] — line series for SL/Target/Entry (cleaned up on reset)
hitMarkersRef      // Map (stub, not used)
```

### Signal Rendering Flow
```
fetchSignals()
  → STEP 1: GET /signal-history/ → dbRaw[]
  → STEP 2: GET /reversal-zones/ → filter source==='live_pending'
  → STEP 3: merge (DB first, pending if new time + alternates)
  → build slTargetMapRef entries
  → flushMarkers() → setMarkers() + renderSLTargetLines()

renderSLTargetLines()
  → for each entry in slTargetMapRef:
       addLineSeries() × 3 (Entry white, SL red, TP green)
       line spans: signal_time - 1 candle to signal_time + 8 candles
       lastValueVisible:true + title:"SL 70595.72"
  → cleanup: chartRef.current.removeSeries(ls) on reset
```

### SL/Target Line Colors
```
Entry: '#e2e8f0' (white)  lineWidth: 2
SL:    '#ef4444' (red)    lineWidth: 2
TP:    '#10b981' (green)  lineWidth: 2
```

### WebSocket applySignal — Critical Rules
- ONLY applies `newestZone = s.all_zones[s.all_zones.length - 1]`
- NEVER applies all zones (prevents repainting)
- `typeAlternates` check — rejects same-type as last marker

## Auth
- Token stored as `access_token` in localStorage (NOT `auth_token`)
- Header: `Authorization: Bearer <token>`
- AuthContext provides `isAuthenticated`, `user`, `loading`

## Environment Variables
```bash
# Inside Docker (internal)
NEXT_PUBLIC_API_URL=http://django:8000
NEXT_PUBLIC_WS_URL=ws://django:8000
```

## Build Commands
```bash
npm run dev       # development
npm run build     # production build
npm run lint      # lint check
npm run type-check # TypeScript check
```