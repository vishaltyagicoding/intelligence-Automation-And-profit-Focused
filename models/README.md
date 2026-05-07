# 📦 Models Directory

## Where to Put Your Trained Model

### ✅ CORRECT PATH:
```
models/production/model.pth
```

**Full path on your system:**
```
D:\intelligence-Automation-And-profit-Focused\intelligence-Automation-And-profit-Focused\models\production\model.pth
```

---

## Step-by-Step Instructions

### Step 1: Download from Kaggle
1. Go to your Kaggle notebook
2. Click **"Output"** tab (top right)
3. Find `best_model.pth`
4. Click **Download**
5. File will be saved to your Downloads folder

### Step 2: Copy to Production Folder

**Option A: Using File Explorer (Easy)**
1. Open File Explorer
2. Go to your Downloads folder
3. Find `best_model.pth`
4. Copy the file (Ctrl+C)
5. Navigate to: `D:\intelligence-Automation-And-profit-Focused\intelligence-Automation-And-profit-Focused\models\production\`
6. Paste the file (Ctrl+V)
7. Rename it to `model.pth` (remove "best_" prefix)

**Option B: Using PowerShell**
```powershell
# Copy from Downloads to production folder
Copy-Item "$env:USERPROFILE\Downloads\best_model.pth" -Destination "models\production\model.pth"
```

**Option C: Using Command Prompt**
```cmd
copy "%USERPROFILE%\Downloads\best_model.pth" "models\production\model.pth"
```

---

## Directory Structure

After copying, your structure should look like this:

```
intelligence-Automation-And-profit-Focused/
├── models/
│   ├── production/
│   │   └── model.pth          ← YOUR MODEL GOES HERE!
│   ├── backups/
│   │   └── (automatic backups will be saved here)
│   └── README.md              ← This file
├── ai_agents/
├── market_data/
├── neuraltrade/
└── manage.py
```

---

## Verify Your Model is in the Right Place

### Check if file exists:

**PowerShell:**
```powershell
Test-Path models\production\model.pth
```
Should return: `True`

**Command Prompt:**
```cmd
dir models\production\model.pth
```
Should show the file details

**File Explorer:**
Navigate to: `models\production\` and you should see `model.pth`

---

## File Details

**File name:** `model.pth`
**Expected size:** 5-10 MB
**Format:** PyTorch model checkpoint
**Contains:**
- Model weights
- Training history
- Accuracy: 75%
- Configuration

---

## What Happens Next?

Once your model is at `models/production/model.pth`, you can load it:

```bash
# Load the model into Django
python manage.py load_model --checkpoint models/production/model.pth
```

**Expected output:**
```
✅ Loading model from: models/production/model.pth
✅ Model loaded successfully!
✅ Validation accuracy: 75.00%
✅ Model ready for production
```

---

## Troubleshooting

### Problem: "File not found"
**Solution:** Make sure you copied the file to the correct path:
```
models/production/model.pth
```
NOT:
- ❌ `models/model.pth`
- ❌ `production/model.pth`
- ❌ `models/production/best_model.pth`

### Problem: "Permission denied"
**Solution:** Run PowerShell as Administrator

### Problem: "Invalid model file"
**Solution:** Make sure you downloaded the complete file from Kaggle (should be 5-10 MB)

---

## Backup Your Model

The system automatically creates backups when you retrain, but you can manually backup:

```powershell
# Create manual backup
Copy-Item "models\production\model.pth" -Destination "models\backups\model_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').pth"
```

---

## Multiple Models

If you train multiple times and want to keep different versions:

```
models/
├── production/
│   └── model.pth              ← Currently active model
├── backups/
│   ├── model_75_percent.pth   ← Your 75% model
│   ├── model_70_percent.pth   ← Your 70% model
│   └── model_backup_20260413.pth
```

To switch models:
```powershell
# Use the 75% model
Copy-Item "models\backups\model_75_percent.pth" -Destination "models\production\model.pth"

# Reload
python manage.py load_model --checkpoint models/production/model.pth
```

---

## ✅ Quick Checklist

- [ ] Downloaded `best_model.pth` from Kaggle
- [ ] Copied to `models/production/`
- [ ] Renamed to `model.pth`
- [ ] Verified file exists (5-10 MB)
- [ ] Ready to load with `python manage.py load_model`

---

## 🚀 You're Ready!

Once your model is at `models/production/model.pth`, you can proceed with deployment!
