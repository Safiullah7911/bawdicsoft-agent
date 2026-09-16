# BawdicSoft AI Sales Agent

AI-powered sales agent for BawdicSoft website. Fine-tuned `google/flan-t5-small` model with visitor tracking, lead capture, and personalized greetings.

## Features

- 🤖 **Fine-tuned AI Model** — 80M params, trained on 5,000+ BawdicSoft-specific examples
- 📧 **Auto Lead Capture** — Email + Name detection on high engagement
- 👤 **Known User Detection** — Email + IP-based identification
- 🎯 **Smart Popups** — Page-specific proactive messages after 5s dwell time
- 🔒 **Persistent Storage** — User data survives server restarts
- 💰 **Zero Cost** — Runs on Render free tier

## Architecture

```
Website (tracker.js) 
    ↓ HTTP
FastAPI Server (app.py)
    ↓
Flan-T5 Model (model_out/)
    ↓
users.json + ip_index.json + anon_visitors.json
```

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat` | POST | Main conversation |
| `/track` | POST | Receive page dwell time |
| `/check-trigger` | GET | Check if popup should fire |
| `/admin/sessions` | GET | Debug view of all sessions |
| `/health` | GET | Uptime check |

## Local Development

```bash
pip install -r requirements.txt
python app.py
```

Server runs at `http://localhost:8000`. Test UI: `http://localhost:8000/docs`.

## Deployment

Deployed on Render free tier. Uses Git LFS for model files.

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MODEL_DIR` | `./model_out` | Path to trained model |
| `USERS_FILE` | `./users.json` | Known users storage |
| `IP_INDEX_FILE` | `./ip_index.json` | IP → email mapping |
| `ANON_FILE` | `./anon_visitors.json` | Anonymous visitor tracking |

## Frontend Integration

Add `tracker.js` to website `<head>`:

```html
<script>
  window.BAWDIC_API = 'https://your-app.onrender.com';
</script>
<script src="/tracker.js" defer></script>
```

## Model Training

Model was trained on Kaggle using:
- `generate_dataset.py` — creates ~12,000 synthetic examples
- `train.py` — fine-tunes flan-t5-small (4 epochs, ~10 min on T4 GPU)

To retrain: run both scripts on Kaggle with GPU enabled.

## License

Internal use — BawdicSoft.