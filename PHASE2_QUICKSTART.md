# Phase 2 Quick Start Guide

## What's New in Phase 2

Phase 2 adds the **3-Agent AI Intelligence Engine** to NeuralTrade:

1. **Agent A (Analyst)**: CNN-LSTM hybrid for technical analysis
2. **Agent B (Oracle)**: Sentiment analysis with veto power
3. **Agent C (Disciplinarian)**: Risk management and execution

---

## Installation

### 1. Update Dependencies

```bash
pip install -r requirements.txt
```

New packages added:
- `torch` - PyTorch for CNN-LSTM models
- `transformers` - For sentiment analysis
- `beautifulsoup4` - Web scraping
- `feedparser` - News feed parsing

### 2. Run Migrations

```bash
# Create migrations for AI agents
python manage.py makemigrations ai_agents

# Apply migrations
python manage.py migrate
```

This creates:
- `AuditLog` table (immutable)
- `AgentState` table (state recovery)
- `ModelPrediction` table (debugging)

### 3. Update Docker (if using)

```bash
# Rebuild containers
docker-compose down
docker-compose up --build -d

# Run migrations in container
docker-compose exec django python manage.py migrate
```

---

## Quick Test

### 1. Start Services

```bash
# Option A: Docker
docker-compose up -d

# Option B: Manual
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A neuraltrade worker -l info

# Terminal 3: Celery Beat
celery -A neuraltrade beat -l info
```

### 2. Test AI Analysis

```bash
# Get JWT token first
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Trigger AI analysis
curl -X POST http://localhost:8000/api/ai/analyze/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","market":"CRYPTO"}'
```

### 3. Check Results

```bash
# View audit logs
curl http://localhost:8000/api/ai/audit-logs/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check agent status
curl http://localhost:8000/api/ai/agent-status/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Python Usage

### Manual Trigger

```python
from ai_agents.orchestrator import orchestrator
from decimal import Decimal
import asyncio

# Run analysis
result = asyncio.run(
    orchestrator.make_trading_decision(
        symbol='BTCUSDT',
        market='CRYPTO',
        user_id=1,
        user_balance=Decimal('10000')
    )
)

print(f"Decision: {result['decision']}")
print(f"Confidence: {result['agent_b']['confidence']}%")
print(f"Executed: {result['success']}")
```

### Continuous Monitoring

```python
# Define symbols to monitor
symbols = [
    {
        'symbol': 'BTCUSDT',
        'market': 'CRYPTO',
        'user_id': 1,
        'balance': 10000
    },
    {
        'symbol': 'ETHUSDT',
        'market': 'CRYPTO',
        'user_id': 1,
        'balance': 10000
    }
]

# Start monitoring (runs in background)
await orchestrator.continuous_monitoring_loop(
    symbols,
    interval=60  # Check every 60 seconds
)
```

### Via Celery Task

```python
from ai_agents.tasks import ai_decision_task

# Trigger async task
task = ai_decision_task.delay(
    symbol='BTCUSDT',
    market='CRYPTO',
    user_id=1,
    balance=10000.0
)

# Get result
result = task.get(timeout=30)
```

---

## Configuration

### Environment Variables

Add to `.env`:

```bash
# AI Configuration
AI_CONFIDENCE_THRESHOLD=70
AI_SENTIMENT_VETO_THRESHOLD=30
AI_MAX_TRADES_PER_DAY=4
AI_RISK_PER_TRADE=0.02
AI_ATR_PERIOD=14
AI_MIN_RISK_REWARD=1.5
```

### Agent Parameters

Edit in code if needed:

```python
# ai_agents/agent_a_analyst.py
CNN_INPUT_SIZE = 64
LSTM_SEQUENCE_LENGTH = 50

# ai_agents/agent_b_oracle.py
VETO_THRESHOLD = 30
STRONG_SIGNAL_THRESHOLD = 70

# ai_agents/agent_c_disciplinarian.py
RISK_PER_TRADE = 0.02
ATR_MULTIPLIER_SL = 2.0
ATR_MULTIPLIER_TP = 3.0
```

---

## Verify Installation

### 1. Check Database Tables

```bash
python manage.py shell
>>> from ai_agents.models import AuditLog, AgentState
>>> AuditLog.objects.count()
0
>>> AgentState.objects.count()
0
```

### 2. Check Celery Tasks

```bash
celery -A neuraltrade inspect registered | grep ai_agents
```

Should show:
- `ai_agents.tasks.ai_decision_task`
- `ai_agents.tasks.recover_agent_state`
- `ai_agents.tasks.update_agent_heartbeat`

### 3. Test Agents Individually

```python
# Test Agent A
from ai_agents.agent_a_analyst import AgentAnalyst
agent_a = AgentAnalyst()
result = await agent_a.analyze('BTCUSDT')
print(result)

# Test Agent B
from ai_agents.agent_b_oracle import AgentOracle
agent_b = AgentOracle()
result = await agent_b.evaluate_decision(
    {'decision': 'BUY', 'confidence': 80},
    'BTCUSDT',
    'CRYPTO'
)
print(result)

# Test Agent C
from ai_agents.agent_c_disciplinarian import AgentDisciplinarian
agent_c = AgentDisciplinarian()
result = await agent_c.validate_and_prepare_trade(
    user_id=1,
    user_balance=Decimal('10000'),
    decision={'decision': 'BUY'},
    symbol='BTCUSDT',
    current_price=Decimal('45000')
)
print(result)
```

---

## Common Issues

### Issue: "Insufficient data for analysis"

**Solution**: Ensure WebSocket is streaming data to Redis

```bash
# Check Redis data
redis-cli LLEN market:ticks:BTCUSDT
# Should be > 100

# If empty, start WebSocket consumer
# Connect to: ws://localhost:8000/ws/market/BTCUSDT/
```

### Issue: "Agent state not found"

**Solution**: Create initial agent states

```python
from ai_agents.models import AgentState

AgentState.objects.create(
    agent_name='Agent-A-Analyst',
    is_active=True
)
AgentState.objects.create(
    agent_name='Agent-B-Oracle',
    is_active=True
)
AgentState.objects.create(
    agent_name='Agent-C-Disciplinarian',
    is_active=True
)
```

### Issue: "Daily trade limit reached"

**Solution**: Reset counter or wait for next day

```bash
# Check current count
redis-cli GET trades:count:1:2024-01-15

# Reset (for testing only)
redis-cli DEL trades:count:1:2024-01-15
```

---

## Monitoring

### View Audit Logs

```bash
# Django admin
http://localhost:8000/admin/ai_agents/auditlog/

# API
curl http://localhost:8000/api/ai/audit-logs/?limit=50 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Check Agent Status

```bash
# API
curl http://localhost:8000/api/ai/agent-status/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Django shell
python manage.py shell
>>> from ai_agents.models import AgentState
>>> for agent in AgentState.objects.all():
...     print(f"{agent.agent_name}: {agent.is_active}")
```

### Monitor Performance

```python
# Check decision time
import time
start = time.time()
result = await orchestrator.make_trading_decision(...)
print(f"Decision time: {time.time() - start:.2f}s")
# Should be < 2 seconds
```

---

## Next Steps

1. **Populate Redis with market data** (WebSocket streaming)
2. **Create user accounts** with balances
3. **Configure API credentials** in `.env`
4. **Start continuous monitoring** for your symbols
5. **Monitor audit logs** for decisions
6. **Adjust parameters** based on performance

---

## Documentation

- **AI_AGENTS_GUIDE.md** - Complete guide to the 3-agent system
- **PHASE2_COMPLETE.md** - Phase 2 completion report
- **API_DOCUMENTATION.md** - API reference (updated)
- **ARCHITECTURE.md** - System architecture (updated)

---

## Support

For issues:
1. Check logs: `docker-compose logs -f django`
2. Verify Redis data: `redis-cli LLEN market:ticks:BTCUSDT`
3. Test agents individually (see above)
4. Review audit logs for decision details

---

**Phase 2 is ready! Start trading with AI!** 🚀
