# Campus Customs

Homework 4 for AI Foundations for Managers (MGT 409).

A shop website for Campus Customs: a React + Vite + TypeScript front end and a Python FastAPI backend with a PydanticAI chatbot (GPT via Portkey).

## Run locally

Put the course `data/` folder (with `campus_customs.db` and `products/`) in the project root, and copy `.env.example` to `.env` (set `PORTKEY_API_KEY` and a random `SESSION_SECRET`).

Backend (http://localhost:8000):

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cd backend && ../.venv/bin/uvicorn main:app --reload --port 8000
```

Front end (http://localhost:5173), in a second terminal:

```bash
cd frontend && npm install && npm run dev
```

The Vite dev server forwards `/api` and `/images` requests to the backend.

### Product photo cut-outs (optional)

The product photos come on black or white backgrounds. To serve transparent cut-outs instead, run this once (it writes `data/products_nobg/` and never changes the originals):

```bash
.venv/bin/pip install pillow numpy scipy
.venv/bin/python backend/scripts/remove_backgrounds.py
```

The backend uses a cut-out when one exists and falls back to the original photo otherwise.
