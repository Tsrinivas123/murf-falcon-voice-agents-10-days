# Day 2 — Coffee Shop Barista Agent

**Project:** Brew & Bean Cafe — Barista Voice Agent

**Purpose:**
An AI barista agent that takes coffee orders through voice interaction, validates order completeness, persists orders as timestamped JSON files, and provides real-time logging for staff.

---

## Table of Contents

1. Overview
2. Features
3. Order Data Structure
4. Function Tools (signatures)
5. Quick Start

   * Backend
   * Frontend
6. Environment Variables
7. Running Locally
8. Order Management & Storage
9. Example Order Flow
10. Validation Rules
11. Real-time Logging
12. Project Structure
13. Troubleshooting
14. Contribution
15. License

---

## 1. Overview

This Day 2 project implements a voice-first barista agent for *Brew & Bean Cafe*. The agent interacts with customers, gathers all required order fields (drink, size, milk, extras, customer name), validates completeness, and writes each finalized order as a timestamped JSON file under `backend/orders/`.

Built to be integrated with LiveKit Agents for voice sessions, Deepgram for STT, Google Gemini for NLU/dialogue, and Murf Falcon for TTS (voice responses). The frontend provides a minimal React/Next.js UI for monitoring active orders and logs.

---

## 2. Features

* Voice-driven ordering flow (STT + NLU + TTS)
* Incremental order collection & state management
* Validation to ensure all required fields are present
* Function tools to enforce structured data collection
* Persistence of completed orders to `backend/orders/` as timestamped JSON
* Real-time logging of agent state and order progress

---

## 3. Order Data Structure

```json
{
  "drinkType": "latte",
  "size": "large",
  "milk": "oat",
  "extras": ["extra shot"],
  "name": "John",
  "timestamp": "2025-11-26T15:30:00+05:30"
}
```

Required fields: `drinkType`, `size`, `milk`, `name`. `extras` is optional (array).

---

## 4. Function Tools (signatures)

These are the function tools the agent exposes and uses to collect structured data. Implement them in `backend/src/agent_tools.py` (or similar).

* `set_drink_type(drink_type: str) -> dict`
* `set_size(size: str) -> dict`
* `set_milk(milk: str) -> dict`
* `set_extras(extras: List[str]) -> dict`
* `set_name(name: str) -> dict`
* `complete_order() -> dict`  — validates and writes JSON file

Each function should update the current `order` state and return the updated state (or a validation error object).

---

## 5. Quick Start

### Backend

```bash
cd Day_2/backend
uv sync
cp .env.example .env.local
# Edit .env.local with API keys
uv run python src/agent.py dev
```

**Notes:** `uv` is the project's task runner (keeps dev commands consistent). If you don't have it, run the Python module directly with `python -m src.agent` or `python src/agent.py`.

### Frontend

```bash
cd Day_2/frontend
pnpm install
cp .env.example .env.local
# Edit .env.local if needed
pnpm dev
```

Open `http://localhost:3000` (or the port printed by the dev server).

---

## 6. Environment Variables

Populate `backend/.env.local` (example keys):

```
DEEPGRAM_API_KEY=your_deepgram_api_key
GEMINI_API_KEY=your_google_gemini_api_key
MURF_API_KEY=your_murf_api_key
LIVEKIT_API_URL=https://livekit.example
LIVEKIT_API_KEY=xxx
LIVEKIT_API_SECRET=yyy
ORDERS_DIR=./orders
LOG_LEVEL=info
```

Frontend `.env.local` may include LiveKit connection info and public keys.

---

## 7. Running Locally

* Start backend agent (dev mode) — this opens LiveKit session handlers and the function tools.
* Start frontend to monitor real-time order logs.
* Use a test voice client or the front-end UI to start voice sessions.

---

## 8. Order Management & Storage

* Completed orders are saved as `{timestamp_iso}_{name or id}.json` in `backend/orders/`.
* Example file name: `2025-11-26T15-30-00+05-30_john.json`.
* The backend should create the `orders/` directory if missing and handle concurrent writes safely (file lock or atomic write to temporary filename + rename).

---

## 9. Example Order Flow

**Customer:** "I'd like a coffee"

**Agent:** "What type of coffee would you like?"

**Customer:** "A large latte with oat milk"

Agent calls `set_drink_type('latte')`, `set_size('large')`, `set_milk('oat')`.

**Agent:** "Any extras like sugar or whipped cream?"

**Customer:** "Extra shot please, and my name is John"

Agent calls `set_extras(['extra shot'])`, `set_name('John')` then `complete_order()` which validates and saves.

**Agent:** "Perfect! Your large latte with oat milk and extra shot is ready, John!"

---

## 10. Validation Rules

* `drinkType` must be one of: `latte, cappuccino, americano, espresso, mocha, coffee`.
* `size` must be one of: `small, medium, large`.
* `milk` must be one of: `whole, skim, almond, oat`.
* `extras` if present must be array with items from: `sugar, whipped cream, caramel, extra shot`.
* `name` must be a non-empty string.

If validation fails, `complete_order()` should return an error response listing missing/invalid fields and the agent should ask follow-up questions.

---

## 11. Real-time Logging

* Log each state transition (e.g., `asked_for_drink`, `set_drink`, `asked_for_extras`, `completed`) to console and to a simple rotating log file in `backend/logs/` for staff monitoring.
* Optionally stream logs to frontend over WebSocket or LiveKit data channels for live UI updates.

---

## 12. Project Structure (suggested)

```
Day_2/
├─ backend/
│  ├─ src/
│  │  ├─ agent.py            # main LiveKit agent entrypoint
│  │  ├─ agent_tools.py      # function tool implementations
│  │  ├─ order_store.py      # persistence helpers
│  │  └─ config.py
│  ├─ orders/                # saved JSON orders
│  ├─ logs/
│  └─ .env.example
├─ frontend/
│  ├─ src/
│  ├─ pages/
│  └─ .env.example
└─ README.md
```

---

## 13. Troubleshooting

* **No audio / STT not working:** Check `DEEPGRAM_API_KEY`, ensure the microphone stream is reaching the backend and LiveKit sessions are connected.
* **Orders not saved:** Confirm `ORDERS_DIR` exists or agent has permission to create it. Check logs for exceptions during `complete_order()`.
* **Concurrent write errors:** Implement atomic writes (write to temp file then `os.replace()` on success) and ensure unique filenames.

---

## 14. Contribution

* Fork the repo, create a feature branch (`feat/day2-improve-validation`), make changes, and open a PR.
* Write unit tests for validation logic in `backend/tests/`.

---

## 15. License

MIT License — see `LICENSE` file.

---

If you'd like, I can also:

* generate example `agent_tools.py` with the function tool implementations,
* create sample unit tests for validation,
* produce a minimal frontend monitoring page.

Tell me which of the above you'd like next.
