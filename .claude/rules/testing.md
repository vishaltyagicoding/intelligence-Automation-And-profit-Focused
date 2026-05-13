# Testing Guidelines

## Testing Strategy
- Unit tests for business logic
- Integration tests for API endpoints
- Manual testing for UI/UX
- Load testing for WebSocket connections

## Backend Testing (Django)

### Test Structure
```
app_name/
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_serializers.py
│   └── test_tasks.py
```

### Running Tests
```bash
# All tests
python manage.py test

# Specific app
python manage.py test trading

# Specific test file
python manage.py test trading.tests.test_views

# With coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Example
```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import ReversalZone

User = get_user_model()

class ReversalZoneTestCase(TestCase):
    def setUp(self):
        self.zone = ReversalZone.objects.create(
            symbol='BTCUSDT',
            timeframe='15m',
            center_price=50000.00,
            is_bullish=True,
        )
    
    def test_zone_creation(self):
        self.assertEqual(self.zone.symbol, 'BTCUSDT')
        self.assertTrue(self.zone.is_bullish)
```

## Frontend Testing (Next.js)

### Test Structure
```
__tests__/
├── components/
│   ├── Navigation.test.tsx
│   └── ChartComponent.test.tsx
├── pages/
│   └── dashboard.test.tsx
└── lib/
    └── utils.test.ts
```

### Running Tests
```bash
# All tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

### Test Example (Jest + React Testing Library)
```typescript
import { render, screen } from '@testing-library/react';
import Navigation from '@/components/Navigation';

describe('Navigation', () => {
  it('renders logo', () => {
    render(<Navigation />);
    expect(screen.getByText('SmartRisk')).toBeInTheDocument();
  });
});
```

## API Testing

### Manual Testing with curl
```bash
# Login
curl -X POST https://smartriskfx.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# Get reversal zones
curl https://smartriskfx.com/api/trading/reversal-zones/BTCUSD/?timeframe=15m \
  -H "Authorization: Bearer <token>"
```

### Postman Collection
Create collection with:
- Authentication endpoints
- Trading signal endpoints
- Signal alert endpoints
- Subscription endpoints

## WebSocket Testing

### Manual Testing
```javascript
// Browser console
const ws = new WebSocket('wss://smartriskfx.com/ws/market/BTCUSD/15m/');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

### Load Testing
```bash
# Using wscat
npm install -g wscat
wscat -c wss://smartriskfx.com/ws/market/BTCUSD/15m/
```

## Email Testing

### Test Email Sending
```bash
# Django shell
python manage.py shell

from django.core.mail import send_mail
send_mail(
    'Test Subject',
    'Test message',
    'smarttriskfx@gmail.com',
    ['recipient@example.com'],
)
```

### Test Signal Alert Email
```bash
python manage.py test_live_signal_email
```

## Database Testing

### Test Migrations
```bash
# Create test database
python manage.py migrate --database=test

# Run migrations
python manage.py migrate

# Rollback
python manage.py migrate app_name 0001
```

### Test Data Seeding
```python
# Create test fixtures
python manage.py dumpdata app_name > fixtures/test_data.json

# Load fixtures
python manage.py loaddata fixtures/test_data.json
```

## Performance Testing

### Load Testing (Backend)
```bash
# Using Apache Bench
ab -n 1000 -c 10 https://smartriskfx.com/api/trading/reversal-zones/BTCUSD/?timeframe=15m

# Using wrk
wrk -t4 -c100 -d30s https://smartriskfx.com/api/trading/reversal-zones/BTCUSD/?timeframe=15m
```

### Frontend Performance
- Use Lighthouse in Chrome DevTools
- Check Core Web Vitals
- Monitor bundle size with `npm run build`

## Security Testing

### SQL Injection
- Django ORM prevents SQL injection by default
- Never use raw SQL without parameterization

### XSS Prevention
- React escapes content by default
- Never use `dangerouslySetInnerHTML` without sanitization

### CSRF Protection
- Django CSRF middleware enabled
- Include CSRF token in forms

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run backend tests
        run: python manage.py test
      - name: Run frontend tests
        run: npm test
```

## Test Coverage Goals
- Backend: 80%+ coverage
- Frontend: 70%+ coverage
- Critical paths: 100% coverage

## Manual Testing Checklist

### Authentication Flow
- [ ] User registration
- [ ] Email verification
- [ ] Login/logout
- [ ] Password reset
- [ ] Token refresh

### Trading Features
- [ ] View reversal zones
- [ ] Signal history loading
- [ ] WebSocket price updates
- [ ] Chart rendering
- [ ] Timeframe switching

### Subscription
- [ ] Trial activation
- [ ] Subscription status check
- [ ] Manual activation by admin

### Signal Alerts
- [ ] Create alert preferences
- [ ] Receive email notifications
- [ ] Test email functionality

### Edge Cases
- [ ] Network disconnection
- [ ] WebSocket reconnection
- [ ] API timeout handling
- [ ] Invalid token handling
- [ ] Empty data states
