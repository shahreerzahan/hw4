# Campus Customs

Homework 4 for AI Foundations for Managers (MGT 409). Vibe coded by Shahreer.

A Yale merch shop website with **Dan the Bulldog**, an AI shopping assistant:

- **Front end:** React + Vite + TypeScript. Home, Products (search and category filter), product pages with live stock, About, and create account / log in, plus a chat box.
- **Backend:** Python FastAPI, serving products, images, accounts, and the chat.
- **Agent:** a PydanticAI agent using GPT (`gpt-5.6-luna`) through Portkey. It looks up real products, prices, and per-size stock in the SQLite database, shows matching products as cards on the page, remembers logged-in shoppers' chats, and logs every step to `output/audit_trail.json`.

Full system documentation: [`output/harness.md`](output/harness.md).

## Repo layout

```
hw4/
├── AI_prompts.md            # the prompts I gave the AI for each problem
├── requirements.txt         # Python dependencies
├── .env.example             # copy to .env and fill in (placeholders only)
├── .gitignore
├── README.md
├── frontend/                # Vite React TypeScript app
├── backend/
│   ├── main.py              # FastAPI app: run with `uvicorn main:app --reload --port 8000`
│   ├── agent.py             # agent wiring: model, prompt, deps, tools, audit trail
│   ├── models.py            # Pydantic / PydanticAI structured types
│   ├── tools.py             # tools the agent can call (catalogue, price, stock)
│   ├── prompts/
│   │   └── prompt.md        # system prompt (voice, tool use, safety rules)
│   ├── auth.py              # create account / log in (hashed passwords, session cookie)
│   ├── chat_history.py      # saved chats for logged-in shoppers
│   ├── db.py                # database path, connection, image URLs
│   └── scripts/
│       └── remove_backgrounds.py   # optional: transparent product photos
└── output/
    ├── harness.md           # how the whole system works
    ├── design.md            # design choices
    ├── usability.md         # usability improvements
    ├── app_check.html       # testing screenshots (double-click to open)
    ├── app_check_images/    # screenshots linked from app_check.html
    └── audit_trail.json     # agent audit log (append-only)
```

## Setup

### 1. Put the data folder in place

The database and product images are **not** in this repo. Copy the course data pack into the repo root so it looks like this:

```
hw4/
└── data/
    ├── campus_customs.db
    └── products/            # images referenced by the catalogue
```

The backend reads `data/campus_customs.db` and serves photos from `data/products/`. On first start it adds one table, `chat_history`, to the database.

### 2. Create `.env`

```bash
cp .env.example .env
```

Then edit `.env`:

| Variable | Value |
|---|---|
| `PORTKEY_API_KEY` | Your Portkey API key (required) |
| `MODEL_NAME` | `gpt-5.6-luna` (the default) |
| `SESSION_SECRET` | Any long random string; signs login cookies. Make one with `python3 -c "import secrets; print(secrets.token_hex(32))"` |

`.env` is git-ignored. Never commit it.

### 3. Install

Requirements: Python 3.12+ and Node.js 20+.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

```bash
cd frontend
npm install
```

## Run

Use two terminals.

**Backend** (FastAPI on http://localhost:8000), from the `backend/` folder:

```bash
cd backend
../.venv/bin/uvicorn main:app --reload --port 8000
```

If the virtual environment is activated (`source .venv/bin/activate`), this is just `uvicorn main:app --reload --port 8000`.

**Front end** (Vite on http://localhost:5173), from the `frontend/` folder:

```bash
cd frontend
npm run dev
```

Open **http://localhost:5173**. The Vite dev server forwards `/api` and `/images` requests to the backend, so both must be running.

- **Test account:** `test@campuscustoms.yale.edu` / `password` (or create your own).
- **Try the chat** (Dan's face, bottom right): "What hoodies do you have?", or "Is this in stock in large?" on a product page.
- **Editing the prompt:** `--reload` only watches `.py` files, so restart the backend after editing `backend/prompts/prompt.md`.

## Optional: transparent product photos

The product photos come on black and white backgrounds. To serve clean cut-outs instead (written to `data/products_nobg/`; the originals are not changed):

```bash
.venv/bin/pip install pillow numpy scipy
.venv/bin/python backend/scripts/remove_backgrounds.py
```

The backend uses a cut-out when one exists and falls back to the original photo otherwise.

## What's not in the repo (on purpose)

- `.env`: secrets
- `data/`: the database and product images
- `.venv/`, `node_modules/`, `__pycache__/`: rebuilt by the install steps
