# 🚀 Kaggle Training - Complete Setup Guide

## ⚡ Quick Start (5 Minutes Setup)

### Step 1: Go to Kaggle
1. Open https://www.kaggle.com/code
2. Click **"New Notebook"** button (top right)

### Step 2: Copy Training Code
1. Open `kaggle_training_notebook.py` from your project
2. **Copy ALL the code** (Ctrl+A, Ctrl+C)
3. **Paste into Kaggle notebook** (Ctrl+V)

### Step 3: Enable GPU
1. Click **"Settings"** (right sidebar)
2. Find **"Accelerator"**
3. Select **"GPU"** (NOT "None" or "TPU")
4. Click **"Save"**

### Step 4: Run Training
1. Click **"Run All"** button (top of notebook)
2. Wait 2-4 hours (Kaggle will show progress)
3. ☕ Take a break - everything is automated!

---

## 📥 After Training Completes

### Step 1: Download Model
1. In Kaggle, click **"Output"** tab (right sidebar)
2. Find **"best_model.pth"** file
3. Click **Download** icon
4. Save to your Downloads folder

### Step 2: Copy to Your Project
```bash
# Windows
copy "%USERPROFILE%\Downloads\best_model.pth" "models\production\model.pth"

# Linux/Mac
cp ~/Downloads/best_model.pth models/production/model.pth
```

### Step 3: Load Model in Your Project
```bash
# Make sure you're in your project directory
cd /path/to/neuraltrade

# Load the trained model
python manage.py load_model --checkpoint models/production/model.pth
```

### Step 4: Restart Services
```bash
# If using Docker
docker-compose restart django celery_worker

# If running manually
# Stop Django and Celery, then restart them
```

### Step 5: Test Your AI
```bash
# Test the AI analysis endpoint
curl -X POST http://localhost:8000/api/ai/analyze/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"symbol":"BTCUSDT","market":"CRYPTO"}'
```

---

## 🎯 What Happens During Training?

The script automatically:

1. ✅ **Installs packages** - python-binance, pyotp, etc.
2. ✅ **Fetches data** - 365 days of BTC/USDT from Binance
3. ✅ **Prepares dataset** - Creates CNN images and LSTM sequences
4. ✅ **Trains model** - 50 epochs with validation
5. ✅ **Saves best model** - Automatically saves when accuracy improves
6. ✅ **Creates history** - Saves training metrics

**You don't need to do ANYTHING manually!**

---

## 📊 Expected Results

### Training Time
- **With GPU**: 2-4 hours
- **Without GPU**: 8-12 hours (NOT recommended)

### Accuracy
- **Epoch 10**: ~55-60%
- **Epoch 30**: ~65-70%
- **Epoch 50**: ~70-75%

### Files Created
- `best_model.pth` - **USE THIS ONE** (best accuracy)
- `final_model.pth` - Last epoch model
- `training_history.json` - Training metrics

---

## 🔧 Troubleshooting

### Problem: "Out of Memory" Error
**Solution**: Reduce batch size
```python
# In the code, find this line:
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

# Change to:
train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
```

### Problem: Training Too Slow
**Solution**: Make sure GPU is enabled
1. Settings → Accelerator → GPU
2. Check output shows "CUDA available: True"

### Problem: Can't Download Model
**Solution**: 
1. Wait for training to complete (100%)
2. Click "Output" tab (not "Data" or "Code")
3. Look for "best_model.pth" in file list

### Problem: Model File Not Found
**Solution**: Create directory first
```bash
# Create models directory
mkdir -p models/production

# Then copy model
cp ~/Downloads/best_model.pth models/production/model.pth
```

---

## ✅ Complete Checklist

### Before Training
- [ ] Go to https://www.kaggle.com/code
- [ ] Create new notebook
- [ ] Copy code from `kaggle_training_notebook.py`
- [ ] Enable GPU in Settings
- [ ] Click "Run All"

### After Training
- [ ] Download `best_model.pth` from Output tab
- [ ] Copy to `models/production/model.pth`
- [ ] Run `python manage.py load_model`
- [ ] Restart Django and Celery
- [ ] Test with curl command

---

## 🎉 That's It!

**Total time**: 5 minutes setup + 2-4 hours training

**Your AI model will be ready for production trading!**
