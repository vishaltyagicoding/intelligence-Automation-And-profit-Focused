# 🚀 Kaggle Training - Quick Reference Card

## 📋 5-Minute Setup

```bash
1. Go to: https://www.kaggle.com/code
2. Click: "New Notebook"
3. Copy: kaggle_training_notebook.py (ALL code)
4. Paste: Into Kaggle notebook
5. Settings → Accelerator → GPU
6. Click: "Run All"
7. Wait: 2-4 hours
```

---

## 📥 After Training (5 Minutes)

```bash
# 1. Download from Kaggle
Output tab → best_model.pth → Download

# 2. Copy to project
mkdir -p models/production
cp ~/Downloads/best_model.pth models/production/

# 3. Load model
python manage.py load_model --checkpoint models/production/model.pth

# 4. Restart services
docker-compose restart django celery_worker

# 5. Test AI
curl -X POST http://localhost:8000/api/ai/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","market":"CRYPTO"}'
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `kaggle_training_notebook.py` | Complete training code (copy-paste ready) |
| `KAGGLE_SETUP_GUIDE.md` | Detailed setup instructions |
| `KAGGLE_VISUAL_GUIDE.md` | Visual flowcharts and diagrams |
| `AFTER_KAGGLE_TRAINING.md` | Post-training deployment steps |
| `KAGGLE_QUICK_REFERENCE.md` | This file - quick commands |

---

## ⚡ One-Line Commands

```bash
# Copy model (Windows)
copy "%USERPROFILE%\Downloads\best_model.pth" "models\production\model.pth"

# Copy model (Linux/Mac)
cp ~/Downloads/best_model.pth models/production/model.pth

# Load model
python manage.py load_model --checkpoint models/production/model.pth

# Restart Docker
docker-compose restart django celery_worker

# Test AI
curl -X POST http://localhost:8000/api/ai/analyze/ -H "Content-Type: application/json" -d '{"symbol":"BTCUSDT","market":"CRYPTO"}'
```

---

## 🎯 Expected Results

| Metric | Value |
|--------|-------|
| Training Time (GPU) | 2-4 hours |
| Training Time (CPU) | 8-12 hours |
| Final Accuracy | 70-75% |
| Model Size | ~50 MB |
| Setup Time | 5 minutes |
| Deployment Time | 5 minutes |

---

## ✅ Success Checklist

### Before Training
- [ ] Kaggle account created
- [ ] New notebook created
- [ ] Code pasted
- [ ] GPU enabled
- [ ] Training started

### After Training
- [ ] Model downloaded
- [ ] Copied to project
- [ ] Model loaded
- [ ] Services restarted
- [ ] AI tested

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Out of Memory | Reduce batch_size to 16 |
| Training slow | Enable GPU in Settings |
| Can't download | Wait for 100% completion |
| Model not found | Create models/production/ first |
| AI not responding | Check logs: `docker-compose logs django` |

---

## 📞 Quick Help

**Setup Issues**: See `KAGGLE_SETUP_GUIDE.md`
**Visual Guide**: See `KAGGLE_VISUAL_GUIDE.md`
**After Training**: See `AFTER_KAGGLE_TRAINING.md`
**Full Guide**: See `KAGGLE_TRAINING_GUIDE.md`

---

## 🎉 That's It!

**Total Time**: 10 minutes active + 2-4 hours waiting

**Your AI will be production-ready!**
