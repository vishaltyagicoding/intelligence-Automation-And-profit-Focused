# 🚀 Quick Model Setup Guide

## Where to Put Your Model - SIMPLE VERSION

### 📍 EXACT FILE PATH:

```
models/production/model.pth
```

---

## 3 Simple Steps

### Step 1: Download from Kaggle ⬇️

1. Open your Kaggle notebook
2. Click **"Output"** tab
3. Download `best_model.pth`
4. It goes to your Downloads folder

### Step 2: Copy to Project 📁

**Easy Way (File Explorer):**

1. Open File Explorer
2. Go to Downloads folder
3. Find `best_model.pth`
4. Copy it (Ctrl+C)
5. Go to your project folder:
   ```
   D:\intelligence-Automation-And-profit-Focused\intelligence-Automation-And-profit-Focused\models\production\
   ```
6. Paste it (Ctrl+V)
7. Rename to `model.pth` (remove "best_")

**Fast Way (PowerShell):**

Open PowerShell in your project folder and run:
```powershell
Copy-Item "$env:USERPROFILE\Downloads\best_model.pth" -Destination "models\production\model.pth"
```

### Step 3: Load into Django ⚙️

```bash
python manage.py load_model --checkpoint models/production/model.pth
```

**You should see:**
```
✅ Model loaded successfully!
✅ Accuracy: 75.00%
✅ Ready for production
```

---

## Visual Guide

```
Your Computer
│
├── Downloads/
│   └── best_model.pth          ← Downloaded from Kaggle
│
└── Your Project/
    └── intelligence-Automation-And-profit-Focused/
        └── models/
            └── production/
                └── model.pth    ← COPY IT HERE!
```

---

## Check if It Worked

Run this command:
```powershell
Test-Path models\production\model.pth
```

If it says `True` → ✅ Success!
If it says `False` → ❌ File not in the right place

---

## That's It!

Once the file is at `models/production/model.pth`, you're ready to deploy!

Next step: Follow `DEPLOYMENT_CHECKLIST.md`
