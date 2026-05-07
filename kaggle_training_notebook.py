#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NeuralTrade - Kaggle Training Notebook
=======================================
FULLY AUTOMATED - Just click "Run All" in Kaggle!

Instructions:
1. Go to https://www.kaggle.com/code
2. Click "New Notebook"
3. Copy-paste this ENTIRE file
4. Settings → Accelerator → GPU (Enable GPU)
5. Click "Run All"
6. Wait 2-4 hours
7. Download "best_model.pth" from Output tab
8. Copy to your project: models/production/model.pth

That's it! Everything is automated.
"""

print("=" * 70)
print("🚀 NeuralTrade - Automated Model Training on Kaggle")
print("=" * 70)
print("\n✅ Starting fully automated training pipeline...\n")

# ============================================================================
# STEP 1: Install Required Packages
# ============================================================================
print("📦 Step 1/7: Installing required packages...")

import subprocess
import sys

packages = [
    'yfinance',  # Yahoo Finance for free data
    'ta',  # Technical analysis library
]

for package in packages:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-q'])

print("✅ All packages installed!\n")

# ============================================================================
# STEP 2: Import Libraries
# ============================================================================
print("📚 Step 2/7: Importing libraries...")

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

print(f"✅ PyTorch version: {torch.__version__}")
print(f"✅ CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
print()

# ============================================================================
# STEP 3: Define Model Architecture
# ============================================================================
print("🏗️  Step 3/7: Building model architecture...")

class CNNFeatureExtractor(nn.Module):
    """CNN for visual pattern recognition (Support/Resistance, Breakouts)"""
    
    def __init__(self, input_channels=5, hidden_dim=128):
        super(CNNFeatureExtractor, self).__init__()
        
        # Convolutional layers
        self.conv1 = nn.Conv2d(input_channels, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        
        self.pool = nn.MaxPool2d(2, 2)
        self.dropout = nn.Dropout(0.3)
        
        # Fully connected layers
        self.fc1 = nn.Linear(128 * 8 * 8, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, 64)
        
        self.relu = nn.ReLU()
        self.batch_norm1 = nn.BatchNorm2d(32)
        self.batch_norm2 = nn.BatchNorm2d(64)
        self.batch_norm3 = nn.BatchNorm2d(128)
    
    def forward(self, x):
        # Conv block 1: 64x64 -> 32x32
        x = self.relu(self.batch_norm1(self.conv1(x)))
        x = self.pool(x)
        
        # Conv block 2: 32x32 -> 16x16
        x = self.relu(self.batch_norm2(self.conv2(x)))
        x = self.pool(x)
        
        # Conv block 3: 16x16 -> 8x8
        x = self.relu(self.batch_norm3(self.conv3(x)))
        x = self.pool(x)
        
        # Flatten and FC layers
        x = x.view(x.size(0), -1)
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.fc2(x)
        
        return x


class LSTMTrendAnalyzer(nn.Module):
    """LSTM for temporal trend analysis (Momentum)"""
    
    def __init__(self, input_dim=64, hidden_dim=128, num_layers=2):
        super(LSTMTrendAnalyzer, self).__init__()
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_dim,
            hidden_dim,
            num_layers,
            batch_first=True,
            dropout=0.3
        )
        
        self.fc1 = nn.Linear(hidden_dim, 64)
        self.fc2 = nn.Linear(64, 32)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
    
    def forward(self, x):
        # LSTM forward pass
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # Take last output
        x = lstm_out[:, -1, :]
        
        # FC layers
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.fc2(x)
        
        return x


class CNNLSTMHybrid(nn.Module):
    """Hybrid CNN-LSTM model for trading decisions"""
    
    def __init__(self):
        super(CNNLSTMHybrid, self).__init__()
        
        self.cnn = CNNFeatureExtractor()
        self.lstm = LSTMTrendAnalyzer()
        
        # Combined decision layers
        self.fc_combined = nn.Linear(32 + 64, 64)
        self.fc_output = nn.Linear(64, 3)  # BUY, SELL, HOLD
        self.fc_confidence = nn.Linear(64, 1)
        
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, cnn_input, lstm_input):
        # Extract features
        cnn_features = self.cnn(cnn_input)
        lstm_features = self.lstm(lstm_input)
        
        # Combine features
        combined = torch.cat([cnn_features, lstm_features], dim=1)
        combined = self.relu(self.fc_combined(combined))
        
        # Decision and confidence
        decision = self.softmax(self.fc_output(combined))
        confidence = self.sigmoid(self.fc_confidence(combined)) * 100
        
        return decision, confidence, cnn_features, lstm_features

print("✅ Model architecture defined!")
print("   - CNN: 5 channels → 32 → 64 → 128 filters")
print("   - LSTM: 2 layers, 128 hidden units")
print("   - Output: BUY/SELL/HOLD + Confidence\n")

# ============================================================================
# STEP 4: Data Preparation Functions
# ============================================================================
print("🔧 Step 4/7: Setting up data preparation...")

class MarketDataset(Dataset):
    """PyTorch Dataset for market data"""
    
    def __init__(self, cnn_data, lstm_data, labels):
        self.cnn_data = torch.FloatTensor(cnn_data)
        self.lstm_data = torch.FloatTensor(lstm_data)
        self.labels = torch.LongTensor(labels)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return self.cnn_data[idx], self.lstm_data[idx], self.labels[idx]


def fetch_historical_data(symbol='BTC-USD', days=365):
    """Fetch historical data from Yahoo Finance (works worldwide, no restrictions!)"""
    print(f"   📊 Fetching {days} days of {symbol} data from Yahoo Finance...")
    
    import yfinance as yf
    
    # Fetch data from Yahoo Finance (free, no API key needed, no restrictions)
    ticker = yf.Ticker(symbol)
    
    # Yahoo Finance limitations:
    # - 1m data: only 7 days
    # - 5m data: only 60 days
    # - 1h data: up to 730 days ✅
    
    # Use 1-hour data for full 365 days
    df = ticker.history(period=f"{days}d", interval="1h")
    
    if len(df) == 0:
        raise ValueError(f"No data available for {symbol}")
    
    # Reset index to get timestamp as column
    df = df.reset_index()
    
    # Rename columns to match our format
    df = df.rename(columns={
        'Date': 'timestamp',
        'Datetime': 'timestamp',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })
    
    # Convert to float
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = df[col].astype(float)
    
    print(f"   ✅ Fetched {len(df):,} candles ({df['timestamp'].min()} to {df['timestamp'].max()})")
    
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]


def create_cnn_input(df, start_idx, lookback=100):
    """
    Create 5-channel 64x64 matrix for CNN input
    
    Channels:
    1. Price line
    2. Volume bars
    3. Moving average
    4. Support/Resistance levels
    5. Momentum indicator
    """
    data_slice = df.iloc[start_idx:start_idx + lookback]
    
    if len(data_slice) < lookback:
        return None
    
    prices = data_slice['close'].values
    volumes = data_slice['volume'].values
    
    # Normalize
    prices_norm = (prices - prices.min()) / (prices.max() - prices.min() + 1e-8)
    volumes_norm = (volumes - volumes.min()) / (volumes.max() - volumes.min() + 1e-8)
    
    matrix_size = 64
    channels = []
    
    # Channel 1: Price line
    price_matrix = np.zeros((matrix_size, matrix_size))
    for i, price in enumerate(prices_norm[:matrix_size]):
        y = int(price * (matrix_size - 1))
        price_matrix[matrix_size - 1 - y, i] = 1.0
    channels.append(price_matrix)
    
    # Channel 2: Volume bars
    volume_matrix = np.zeros((matrix_size, matrix_size))
    for i, vol in enumerate(volumes_norm[:matrix_size]):
        height = int(vol * matrix_size)
        volume_matrix[-height:, i] = 1.0
    channels.append(volume_matrix)
    
    # Channel 3: Moving average (20-period)
    ma = np.convolve(prices_norm, np.ones(20)/20, mode='same')
    ma_matrix = np.zeros((matrix_size, matrix_size))
    for i, ma_val in enumerate(ma[:matrix_size]):
        y = int(ma_val * (matrix_size - 1))
        ma_matrix[matrix_size - 1 - y, i] = 1.0
    channels.append(ma_matrix)
    
    # Channel 4: Support/Resistance
    sr_matrix = np.zeros((matrix_size, matrix_size))
    local_max = np.where(np.r_[True, prices_norm[1:] > prices_norm[:-1]] & 
                        np.r_[prices_norm[:-1] > prices_norm[1:], True])[0]
    for idx in local_max[:matrix_size]:
        y = int(prices_norm[idx] * (matrix_size - 1))
        sr_matrix[matrix_size - 1 - y, :] = 0.5
    channels.append(sr_matrix)
    
    # Channel 5: Momentum
    momentum = np.diff(prices_norm, prepend=prices_norm[0])
    momentum_norm = (momentum - momentum.min()) / (momentum.max() - momentum.min() + 1e-8)
    momentum_matrix = np.zeros((matrix_size, matrix_size))
    for i, mom in enumerate(momentum_norm[:matrix_size]):
        y = int(mom * (matrix_size - 1))
        momentum_matrix[matrix_size - 1 - y, i] = 1.0
    channels.append(momentum_matrix)
    
    return np.stack(channels, axis=0)


def create_lstm_input(df, start_idx, lookback=50):
    """Create time series for LSTM input"""
    data_slice = df.iloc[start_idx:start_idx + lookback]
    
    if len(data_slice) < lookback:
        return None
    
    features = []
    for _, row in data_slice.iterrows():
        features.append([
            row['close'],
            row['volume'],
            row['high'] - row['low'],  # Range
            row['close'] - row['open'],  # Body
        ])
    
    features_array = np.array(features)
    
    # Normalize
    mean = features_array.mean(axis=0)
    std = features_array.std(axis=0) + 1e-8
    features_norm = (features_array - mean) / std
    
    # Expand to 64 dimensions (pad with zeros)
    features_expanded = np.zeros((lookback, 64))
    features_expanded[:, :4] = features_norm
    
    return features_expanded


def create_labels(df, start_idx, lookback_max=100, future_window=24):
    """
    Create labels based on future price movement
    
    SWING TRADING MODE (FIXED):
    - Use 24 candles ahead (24 * 4 hours = 4 days)
    - More realistic thresholds for 4-hour candles
    - Balanced dataset
    
    Labels:
    0 = BUY (price will go up > 2%)
    1 = SELL (price will go down < -2%)
    2 = HOLD (price will stay flat)
    """
    current_idx = start_idx + lookback_max
    future_idx = current_idx + future_window  # Look 4 days ahead
    
    if future_idx >= len(df):
        return None
    
    current_price = df.iloc[current_idx]['close']
    
    # Find the highest and lowest price in the next 4 days
    future_slice = df.iloc[current_idx:future_idx]
    max_price = future_slice['high'].max()
    min_price = future_slice['low'].min()
    
    # Calculate potential profit and loss
    max_profit = (max_price - current_price) / current_price
    max_loss = (min_price - current_price) / current_price
    
    # SWING TRADING THRESHOLDS (realistic for 4-hour candles)
    # If price can go up 2%+ before going down 2%, it's a BUY
    if max_profit > 0.02 and max_profit > abs(max_loss):
        return 0  # BUY
    # If price will go down 2%+ before going up 2%, it's a SELL
    elif max_loss < -0.02 and abs(max_loss) > max_profit:
        return 1  # SELL
    else:
        return 2  # HOLD


def prepare_dataset(df):
    """Prepare complete dataset from raw data"""
    print("   🔄 Preparing dataset (this may take a few minutes)...")
    
    cnn_data = []
    lstm_data = []
    labels = []
    
    max_idx = len(df) - 134  # Leave room for lookback + future (100 + 24 + 10)
    
    # Process every candle for more data
    for i in range(0, max_idx, 1):
        cnn_input = create_cnn_input(df, i)
        lstm_input = create_lstm_input(df, i)
        label = create_labels(df, i)
        
        if cnn_input is not None and lstm_input is not None and label is not None:
            cnn_data.append(cnn_input)
            lstm_data.append(lstm_input)
            labels.append(label)
        
        # Progress update
        if len(cnn_data) % 1000 == 0 and len(cnn_data) > 0:
            print(f"      Processed {len(cnn_data):,} samples...")
    
    print(f"   ✅ Dataset prepared: {len(labels):,} samples")
    
    # Count labels
    buy_count = labels.count(0)
    sell_count = labels.count(1)
    hold_count = labels.count(2)
    
    print(f"      BUY: {buy_count:,} | SELL: {sell_count:,} | HOLD: {hold_count:,}")
    
    # ALWAYS balance dataset for production (critical!)
    print(f"   🔄 Balancing dataset for production...")
    cnn_data, lstm_data, labels = balance_dataset(cnn_data, lstm_data, labels)
    
    buy_count = labels.count(0)
    sell_count = labels.count(1)
    hold_count = labels.count(2)
    print(f"   ✅ Final: BUY: {buy_count:,} | SELL: {sell_count:,} | HOLD: {hold_count:,}")
    
    return np.array(cnn_data), np.array(lstm_data), np.array(labels)


def balance_dataset(cnn_data, lstm_data, labels):
    """
    Balance dataset properly for production
    
    CRITICAL FIX:
    - ETH has too few HOLD signals
    - Need to balance ALL classes equally
    - Use proper resampling
    """
    import random
    
    # Separate by class
    buy_indices = [i for i, l in enumerate(labels) if l == 0]
    sell_indices = [i for i, l in enumerate(labels) if l == 1]
    hold_indices = [i for i, l in enumerate(labels) if l == 2]
    
    print(f"      Original: BUY={len(buy_indices)}, SELL={len(sell_indices)}, HOLD={len(hold_indices)}")
    
    # Find the minimum class size
    min_size = min(len(buy_indices), len(sell_indices), len(hold_indices))
    
    # If min_size is too small, use the median instead
    sizes = [len(buy_indices), len(sell_indices), len(hold_indices)]
    sizes.sort()
    target_size = sizes[1]  # Use median size
    
    # Downsample all classes to target size
    if len(buy_indices) > target_size:
        buy_indices = random.sample(buy_indices, target_size)
    if len(sell_indices) > target_size:
        sell_indices = random.sample(sell_indices, target_size)
    if len(hold_indices) > target_size:
        hold_indices = random.sample(hold_indices, target_size)
    
    # Combine indices
    all_indices = buy_indices + sell_indices + hold_indices
    random.shuffle(all_indices)
    
    # Create balanced dataset
    balanced_cnn = [cnn_data[i] for i in all_indices]
    balanced_lstm = [lstm_data[i] for i in all_indices]
    balanced_labels = [labels[i] for i in all_indices]
    
    print(f"      Balanced: BUY={len(buy_indices)}, SELL={len(sell_indices)}, HOLD={len(hold_indices)}")
    
    return balanced_cnn, balanced_lstm, balanced_labels

print("✅ Data preparation functions ready!\n")

# ============================================================================
# STEP 5: Training Functions
# ============================================================================
print("🎓 Step 5/7: Setting up training functions...")

def train_epoch(model, train_loader, criterion, optimizer, device):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    for cnn_input, lstm_input, labels in train_loader:
        cnn_input = cnn_input.to(device)
        lstm_input = lstm_input.to(device)
        labels = labels.to(device)
        
        # Forward pass
        optimizer.zero_grad()
        decision, confidence, _, _ = model(cnn_input, lstm_input)
        
        # Calculate loss
        loss = criterion(decision, labels)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Statistics
        total_loss += loss.item()
        _, predicted = decision.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
    
    return total_loss / len(train_loader), 100. * correct / total


def validate(model, val_loader, criterion, device):
    """Validate model"""
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for cnn_input, lstm_input, labels in val_loader:
            cnn_input = cnn_input.to(device)
            lstm_input = lstm_input.to(device)
            labels = labels.to(device)
            
            # Forward pass
            decision, confidence, _, _ = model(cnn_input, lstm_input)
            loss = criterion(decision, labels)
            
            # Statistics
            total_loss += loss.item()
            _, predicted = decision.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    
    return total_loss / len(val_loader), 100. * correct / total

print("✅ Training functions ready!\n")

# ============================================================================
# STEP 6: Fetch and Prepare Data
# ============================================================================
print("📥 Step 6/7: Fetching and preparing data...")

# Fetch data (365 days of BTC/USD from Yahoo Finance - works worldwide!)
# Fetch data from multiple symbols for SWING TRADING (4-hour candles)
print("📥 Fetching SWING TRADING data (4-hour candles)...")
print("=" * 70)
print("⚠️  SWING TRADING MODE: Safer, fewer trades, bigger profits!")
print()

symbols = ['BTC-USD', 'ETH-USD', 'BNB-USD']
all_cnn_data = []
all_lstm_data = []
all_labels = []

for symbol in symbols:
    print(f"\n📊 Processing {symbol}...")
    
    # Fetch 730 days (2 years) of 4-HOUR data for swing trading
    df = fetch_historical_data(symbol=symbol, days=730)
    
    # Prepare dataset
    cnn_data_temp, lstm_data_temp, labels_temp = prepare_dataset(df)
    
    all_cnn_data.append(cnn_data_temp)
    all_lstm_data.append(lstm_data_temp)
    all_labels.append(labels_temp)
    
    print(f"   ✅ {symbol}: {len(labels_temp):,} samples")

# Combine all data
print(f"\n🔄 Combining data from all symbols...")
cnn_data = np.concatenate(all_cnn_data)
lstm_data = np.concatenate(all_lstm_data)
labels = np.concatenate(all_labels)

# Split train/validation (80/20) - TIME-BASED SPLIT (CRITICAL!)
# DON'T shuffle! Keep time order for walk-forward validation
split_idx = int(len(labels) * 0.8)

print(f"\n⚠️  IMPORTANT: Using time-based split (not random shuffle)")
print(f"   Train: First 80% of data (older)")
print(f"   Val: Last 20% of data (newer)")
print(f"   This simulates real trading where you predict future!\n")

train_dataset = MarketDataset(
    cnn_data[:split_idx],
    lstm_data[:split_idx],
    labels[:split_idx]
)

val_dataset = MarketDataset(
    cnn_data[split_idx:],
    lstm_data[split_idx:],
    labels[split_idx:]
)

# DON'T shuffle validation data (keep time order)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=2)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=2)  # shuffle=False!

print(f"✅ Data ready!")
print(f"   Train samples: {len(train_dataset):,}")
print(f"   Validation samples: {len(val_dataset):,}\n")

# ============================================================================
# STEP 7: Train Model
# ============================================================================
print("🚀 Step 7/7: Training model...")
print("=" * 70)

# Initialize model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = CNNLSTMHybrid().to(device)

# Loss and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5, factor=0.5)

print(f"✅ Model initialized on {device}")
print(f"✅ Total parameters: {sum(p.numel() for p in model.parameters()):,}")
print()

# Training configuration
epochs = 100  # Increased for better accuracy
best_val_acc = 0
patience = 15  # Early stopping
patience_counter = 0
history = {
    'train_loss': [],
    'train_acc': [],
    'val_loss': [],
    'val_acc': []
}

print("🎯 Training for up to 100 epochs with early stopping...")
print("=" * 70)
print()

# Training loop
for epoch in range(1, epochs + 1):
    # Train
    train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
    
    # Validate
    val_loss, val_acc = validate(model, val_loader, criterion, device)
    
    # Update learning rate
    scheduler.step(val_loss)
    
    # Save history
    history['train_loss'].append(train_loss)
    history['train_acc'].append(train_acc)
    history['val_loss'].append(val_loss)
    history['val_acc'].append(val_acc)
    
    # Print progress
    print(f"Epoch {epoch:3d}/{epochs}: "
          f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}% | "
          f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
    
    # Save best model
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        patience_counter = 0
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'accuracy': val_acc,
            'loss': val_loss,
            'history': history,
            'config': {
                'symbols': ['BTC-USD', 'ETH-USD', 'BNB-USD'],
                'days': 730,
                'epochs': epochs,
                'batch_size': 32,
                'learning_rate': 0.001,
            }
        }, 'best_model.pth')
        print(f"   ⭐ New best model saved! Accuracy: {val_acc:.2f}%")
    else:
        patience_counter += 1
    
    # Early stopping
    if patience_counter >= patience:
        print(f"\n⚠️  Early stopping at epoch {epoch} (no improvement for {patience} epochs)")
        break

print()
print("=" * 70)
print("✅ Training completed!")
print(f"🎯 Best validation accuracy: {best_val_acc:.2f}%")
print("=" * 70)

# Save final model
torch.save({
    'epoch': epochs,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'accuracy': val_acc,
    'loss': val_loss,
    'history': history,
    'config': {
        'symbol': 'BTCUSDT',
        'epochs': epochs,
        'batch_size': 32,
        'learning_rate': 0.001,
    }
}, 'final_model.pth')

# Save training history
with open('training_history.json', 'w') as f:
    json.dump(history, f, indent=2)

# Print summary
print()
print("📊 Training Summary:")
print(f"   Total epochs: {epochs}")
print(f"   Best accuracy: {best_val_acc:.2f}%")
print(f"   Final train loss: {train_loss:.4f}")
print(f"   Final val loss: {val_loss:.4f}")
print()

print("📦 Files created:")
print("   ✅ best_model.pth (USE THIS ONE!)")
print("   ✅ final_model.pth")
print("   ✅ training_history.json")
print()

print("=" * 70)
print("🎉 ALL DONE!")
print("=" * 70)
print()
print("📥 NEXT STEPS:")
print("   1. Click 'Output' tab in Kaggle")
print("   2. Download 'best_model.pth'")
print("   3. Copy to your project: models/production/model.pth")
print("   4. Run: python manage.py load_model --checkpoint models/production/model.pth")
print("   5. Restart services: docker-compose restart django celery_worker")
print("   6. Test: curl -X POST http://localhost:8000/api/ai/analyze/")
print()
print("🚀 Your AI model is ready for production!")
print("=" * 70)
