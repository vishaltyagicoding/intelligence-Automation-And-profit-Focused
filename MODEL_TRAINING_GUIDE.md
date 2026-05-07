# NeuralTrade - Model Training & Deployment Guide

## Overview

This guide explains how to train the CNN-LSTM model and deploy it to production.

---

## 📚 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Data Preparation](#data-preparation)
3. [Training the Model](#training-the-model)
4. [Monitoring Training](#monitoring-training)
5. [Evaluating the Model](#evaluating-the-model)
6. [Deploying to Production](#deploying-to-production)
7. [Continuous Improvement](#continuous-improvement)

---

## Prerequisites

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Additional packages for training:
```bash
pip install tensorboard
```

### 2. Configure API Keys

Ensure your `.env` file has Binance API credentials:

```bash
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
```

### 3. Create Directories

```bash
mkdir -p models/checkpoints
mkdir -p models/production
mkdir -p runs
mkdir -p logs
```

---

## Data Preparation

### Automatic Data Fetching

The training script automatically fetches historical data from Binance:

```python
# Fetches 365 days of 1-minute candles
# Approximately 525,600 data points
# Processes into ~100,000 training samples
```

### Manual Data Preparation (Optional)

If you want to prepare data separately:

```python
from ai_agents.training.data_preparation import DataPreparation

# Initialize
data_prep = DataPreparation(symbol='BTCUSDT')

# Fetch historical data
df = data_prep.fetch_historical_data(days=365)

# Prepare dataset
cnn_data, lstm_data, labels = data_prep.prepare_dataset(df)

# Create dataloaders
train_loader, val_loader = data_prep.create_dataloaders(batch_size=32)
```

### Data Format

**CNN Input**: 5-channel 64x64 matrix
- Channel 1: Price line visualization
- Channel 2: Volume bars
- Channel 3: Moving average overlay
- Channel 4: Support/Resistance zones
- Channel 5: Momentum indicator

**LSTM Input**: 50 timesteps × 64 features
- Close price
- Volume
- High-Low range
- Open-Close change
- (Padded to 64 features)

**Labels**: 3 classes
- 0: BUY (price increases > 0.2%)
- 1: SELL (price decreases > 0.2%)
- 2: HOLD (no significant movement)

---

## Training the Model

### Method 1: Django Management Command (Recommended)

```bash
# Basic training (50 epochs, default settings)
python manage.py train_model

# Custom parameters
python manage.py train_model --epochs 100 --batch-size 64 --learning-rate 0.0001
```

### Method 2: Direct Python Script

```bash
cd ai_agents/training
python train_model.py
```

### Method 3: Programmatic Training

```python
from ai_agents.training.train_model import ModelTrainer
from ai_agents.training.data_preparation import DataPreparation
from ai_agents.agent_a_analyst import CNNLSTMHybrid

# Prepare data
data_prep = DataPreparation(symbol='BTCUSDT')
train_loader, val_loader = data_prep.create_dataloaders(batch_size=32)

# Initialize model
model = CNNLSTMHybrid()

# Initialize trainer
trainer = ModelTrainer(
    model=model,
    learning_rate=0.001,
    save_dir='models/checkpoints'
)

# Train
history = trainer.train(
    train_loader=train_loader,
    val_loader=val_loader,
    epochs=50
)
```

### Training Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `epochs` | 50 | Number of training epochs |
| `batch_size` | 32 | Batch size for training |
| `learning_rate` | 0.001 | Initial learning rate |
| `device` | auto | 'cuda' or 'cpu' (auto-detected) |

### Expected Training Time

- **CPU**: ~8-12 hours for 50 epochs
- **GPU (CUDA)**: ~2-4 hours for 50 epochs

---

## Monitoring Training

### TensorBoard

Start TensorBoard to monitor training in real-time:

```bash
tensorboard --logdir=runs
```

Open browser: `http://localhost:6006`

**Metrics Available**:
- Training loss
- Validation loss
- Training accuracy
- Validation accuracy
- Learning rate

### Training Logs

Check console output for progress:

```
Epoch: 1 [0/100000 (0%)] Loss: 1.098612
Epoch: 1 [3200/100000 (3%)] Loss: 1.045231
...
Epoch 1: Train Loss: 0.9234, Train Acc: 45.23% | Val Loss: 0.8765, Val Acc: 48.12%
New best model saved with accuracy: 48.12%
```

### Checkpoints

Models are automatically saved:

```
models/checkpoints/
├── best_model.pth              # Best validation accuracy
├── checkpoint_epoch_10.pth     # Every 10 epochs
├── checkpoint_epoch_20.pth
├── final_model.pth             # Final epoch
└── training_history.json       # Complete history
```

---

## Evaluating the Model

### Check Training History

```python
import json

with open('models/checkpoints/training_history.json', 'r') as f:
    history = json.load(f)

print(f"Best validation accuracy: {max(history['val_acc']):.2f}%")
print(f"Final training loss: {history['train_loss'][-1]:.4f}")
```

### Test on New Data

```python
import torch
from ai_agents.agent_a_analyst import CNNLSTMHybrid

# Load model
model = CNNLSTMHybrid()
checkpoint = torch.load('models/checkpoints/best_model.pth')
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Test on sample
# (Prepare cnn_input and lstm_input as shown in data preparation)
with torch.no_grad():
    decision, confidence, _, _ = model(cnn_input, lstm_input)
    predicted = decision.argmax(dim=1)
    print(f"Prediction: {predicted.item()} (0=BUY, 1=SELL, 2=HOLD)")
    print(f"Confidence: {confidence.item():.2f}%")
```

### Backtesting

```python
# Test on historical data
from ai_agents.training.data_preparation import DataPreparation

data_prep = DataPreparation(symbol='BTCUSDT')
df = data_prep.fetch_historical_data(days=30)  # Last 30 days

# Run predictions
# Calculate accuracy, precision, recall
# Simulate trades and calculate P&L
```

---

## Deploying to Production

### Step 1: Load Best Model

```bash
# Load the best checkpoint into production
python manage.py load_model --checkpoint models/checkpoints/best_model.pth
```

This copies the model to `models/production/model.pth`

### Step 2: Update Agent A

Modify `ai_agents/agent_a_analyst.py` to load production model:

```python
class AgentAnalyst:
    def __init__(self):
        self.model = CNNLSTMHybrid()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load production model
        production_model = 'models/production/model.pth'
        if Path(production_model).exists():
            self.model.load_state_dict(torch.load(production_model, map_location=self.device))
            logger.info("Production model loaded")
        else:
            logger.warning("No production model found, using untrained model")
        
        self.model.to(self.device)
        self.model.eval()
```

### Step 3: Restart Services

```bash
# If using Docker
docker-compose restart django celery_worker

# If using Supervisord
sudo supervisorctl restart neuraltrade:*

# If running manually
# Restart Django and Celery workers
```

### Step 4: Verify Deployment

```bash
# Test AI analysis
curl -X POST http://localhost:8000/api/ai/analyze/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"symbol":"BTCUSDT","market":"CRYPTO"}'

# Check logs
tail -f logs/neuraltrade.log | grep "Agent A"
```

### Step 5: Monitor Performance

```python
# Check audit logs for AI decisions
from ai_agents.models import AuditLog

recent_decisions = AuditLog.objects.filter(
    agent='ORCHESTRATOR'
).order_by('-timestamp')[:100]

# Calculate accuracy
correct = 0
total = 0
for log in recent_decisions:
    # Compare prediction with actual outcome
    # (Implement based on your metrics)
    pass

accuracy = (correct / total) * 100
print(f"Production accuracy: {accuracy:.2f}%")
```

---

## Continuous Improvement

### Retraining Schedule

**Recommended**: Retrain model monthly or when accuracy drops

```bash
# Automated retraining (add to cron)
0 2 1 * * cd /app && python manage.py train_model --epochs 50
```

### A/B Testing

Deploy new model alongside old model:

```python
# models/production/model_v1.pth  # Current
# models/production/model_v2.pth  # New

# Route 50% of traffic to each
# Compare performance
# Deploy winner
```

### Hyperparameter Tuning

Try different configurations:

```python
# Learning rates
for lr in [0.0001, 0.001, 0.01]:
    trainer = ModelTrainer(model, learning_rate=lr)
    trainer.train(train_loader, val_loader, epochs=50)

# Batch sizes
for batch_size in [16, 32, 64]:
    train_loader, val_loader = data_prep.create_dataloaders(batch_size=batch_size)
    trainer.train(train_loader, val_loader, epochs=50)
```

### Data Augmentation

Improve model robustness:

```python
# Add noise to training data
# Flip/rotate price charts
# Mix different timeframes
# Use multiple symbols
```

---

## Troubleshooting

### Issue: Low Accuracy

**Solutions**:
- Increase training epochs (100+)
- Adjust label thresholds (0.2% → 0.5%)
- Add more features to LSTM input
- Use larger dataset (2+ years)
- Try different architectures

### Issue: Overfitting

**Symptoms**: High train accuracy, low validation accuracy

**Solutions**:
- Increase dropout (0.3 → 0.5)
- Add more regularization
- Reduce model complexity
- Use more training data
- Early stopping

### Issue: Out of Memory

**Solutions**:
- Reduce batch size (32 → 16)
- Use gradient accumulation
- Train on CPU (slower but works)
- Use mixed precision training

### Issue: Slow Training

**Solutions**:
- Use GPU (CUDA)
- Reduce data preprocessing
- Use DataLoader num_workers
- Cache preprocessed data

---

## Best Practices

1. **Always validate** on unseen data
2. **Save checkpoints** regularly
3. **Monitor TensorBoard** during training
4. **Test thoroughly** before production
5. **Keep old models** for rollback
6. **Document changes** in model versions
7. **Track performance** in production
8. **Retrain regularly** with new data

---

## Next Steps

After successful training and deployment:

1. ✅ **Monitor Production Performance**
   - Track accuracy in audit logs
   - Monitor P&L from AI trades
   - Check decision distribution

2. ✅ **Collect Feedback**
   - Analyze failed predictions
   - Identify edge cases
   - Gather user feedback

3. ✅ **Iterate and Improve**
   - Retrain with new data
   - Adjust hyperparameters
   - Add new features

4. ✅ **Scale Up**
   - Train on multiple symbols
   - Add more timeframes
   - Ensemble multiple models

---

## Summary

```bash
# Complete workflow
1. python manage.py train_model --epochs 50
2. # Monitor with TensorBoard
3. python manage.py load_model --checkpoint models/checkpoints/best_model.pth
4. # Restart services
5. # Monitor production performance
6. # Retrain monthly
```

**Your model is now ready for production!** 🚀
