# Quick Training Guide - Get Started in 5 Minutes

## Step-by-Step: Train Your Model

### 1. Setup (One-time)

```bash
# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p models/checkpoints models/production runs logs

# Configure Binance API (in .env file)
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

### 2. Train the Model

**Option A: Simple Command (Recommended)**

```bash
python manage.py train_model
```

This will:
- Fetch 365 days of BTC/USDT data from Binance
- Prepare ~100,000 training samples
- Train for 50 epochs (~2-4 hours on GPU)
- Save best model automatically

**Option B: Custom Parameters**

```bash
python manage.py train_model --epochs 100 --batch-size 64 --learning-rate 0.0001
```

### 3. Monitor Training

Open another terminal:

```bash
tensorboard --logdir=runs
```

Visit: http://localhost:6006

You'll see:
- Training/Validation Loss
- Training/Validation Accuracy
- Real-time graphs

### 4. Check Progress

Training output will show:

```
Epoch 1: Train Loss: 0.9234, Train Acc: 45.23% | Val Loss: 0.8765, Val Acc: 48.12%
New best model saved with accuracy: 48.12%
Epoch 2: Train Loss: 0.8123, Train Acc: 52.34% | Val Loss: 0.7654, Val Acc: 54.23%
New best model saved with accuracy: 54.23%
...
Epoch 50: Train Loss: 0.3456, Train Acc: 78.90% | Val Loss: 0.4123, Val Acc: 72.45%
Training completed. Best validation accuracy: 72.45%
```

### 5. Deploy to Production

```bash
# Load best model
python manage.py load_model --checkpoint models/checkpoints/best_model.pth

# Restart services
docker-compose restart django celery_worker
# OR
sudo supervisorctl restart neuraltrade:*
```

### 6. Test It

```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/token/ \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access')

# Trigger AI analysis
curl -X POST http://localhost:8000/api/ai/analyze/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"symbol":"BTCUSDT","market":"CRYPTO"}'
```

---

## What Happens During Training?

### Data Preparation (Automatic)
1. Fetches 365 days of 1-minute candles from Binance
2. Creates 5-channel images (64x64) for CNN
3. Creates time series (50 steps) for LSTM
4. Labels: BUY (0), SELL (1), HOLD (2)
5. Splits 80% train, 20% validation

### Training Loop
1. Forward pass through CNN-LSTM
2. Calculate loss (CrossEntropy)
3. Backward pass (gradient descent)
4. Update weights
5. Validate every epoch
6. Save best model

### Output Files
```
models/checkpoints/
├── best_model.pth              # Best accuracy (USE THIS!)
├── checkpoint_epoch_10.pth     # Backup every 10 epochs
├── checkpoint_epoch_20.pth
├── final_model.pth             # Last epoch
└── training_history.json       # Complete metrics

runs/
└── training_20240115_143022/   # TensorBoard logs
```

---

## After Training - What to Do?

### 1. Check Model Quality

```python
import json

# Read training history
with open('models/checkpoints/training_history.json', 'r') as f:
    history = json.load(f)

print(f"Best validation accuracy: {max(history['val_acc']):.2f}%")
print(f"Final training loss: {history['train_loss'][-1]:.4f}")
```

**Good Model**: Validation accuracy > 65%
**Great Model**: Validation accuracy > 75%

### 2. Deploy to Production

```bash
# Copy best model to production
python manage.py load_model

# Restart services
docker-compose restart django celery_worker
```

### 3. Monitor in Production

```bash
# Check AI decisions
curl http://localhost:8000/api/ai/audit-logs/ \
  -H "Authorization: Bearer $TOKEN"

# View logs
tail -f logs/neuraltrade.log | grep "Agent A"
```

### 4. Retrain Regularly

**Recommended**: Retrain monthly with new data

```bash
# Automated (add to cron)
0 2 1 * * cd /app && python manage.py train_model --epochs 50
```

---

## Troubleshooting

### "Out of Memory"
```bash
# Reduce batch size
python manage.py train_model --batch-size 16
```

### "Training Too Slow"
```bash
# Check if using GPU
python -c "import torch; print(torch.cuda.is_available())"

# If False, install CUDA or train on CPU (slower)
```

### "Low Accuracy"
```bash
# Train longer
python manage.py train_model --epochs 100

# Or adjust learning rate
python manage.py train_model --learning-rate 0.0001
```

### "Binance API Error"
```bash
# Check API keys in .env
# Ensure keys have read permissions
# Check rate limits
```

---

## Expected Results

### Training Time
- **CPU**: 8-12 hours for 50 epochs
- **GPU**: 2-4 hours for 50 epochs

### Accuracy
- **Epoch 1**: ~45-50%
- **Epoch 10**: ~55-60%
- **Epoch 30**: ~65-70%
- **Epoch 50**: ~70-75%

### Model Size
- **Checkpoint**: ~50 MB
- **Production**: ~25 MB

---

## Quick Commands Reference

```bash
# Train model
python manage.py train_model

# Monitor training
tensorboard --logdir=runs

# Load to production
python manage.py load_model

# Test AI
curl -X POST http://localhost:8000/api/ai/analyze/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"symbol":"BTCUSDT","market":"CRYPTO"}'

# Check logs
tail -f logs/neuraltrade.log

# Restart services
docker-compose restart django celery_worker
```

---

## That's It!

You now have a trained AI model making trading decisions! 🚀

**Next Steps**:
1. Monitor performance in production
2. Collect real trading data
3. Retrain monthly
4. Optimize parameters
5. Scale to more symbols

For detailed information, see: **MODEL_TRAINING_GUIDE.md**
