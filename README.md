# NEXUS Supply Chain Intelligence Platform

NEXUS is an AI-driven procurement platform where buyer and supplier agents handle:
- intent parsing,
- supplier discovery,
- RFQ/quote collection,
- multi-round negotiation,
- contract generation,
- deal tracking,
- supplier performance updates.

This repo currently runs from the `backend-new` + `frontend new` implementation.

---

## 1) Project Structure (active paths)

- Backend API + orchestration: `backend-new/nexus/main.py`
- Buyer orchestration logic: `backend-new/nexus/buyer/negotiation.py`
- Supplier pricing/response logic: `backend-new/nexus/supplier/tools.py`
- RL-style score updater: `backend-new/nexus/rl/updater.py`
- Supplier seed dataset: `backend-new/nexus/scripts/seed_suppliers.py`
- Frontend dashboard: `frontend new/static/index.html`
- Data models: `backend-new/nexus/database.py`
- API schemas: `backend-new/nexus/protocols/schemas.py`

---

## 2) Prerequisites

- Python `>=3.11`
- `uv` installed
- OpenRouter API key (required for parsing + rationale generation)

Install dependencies from project root:

```bash
uv sync
```

---

## 3) Environment Setup (`.env`)

> Important: do **not** commit real keys. Use placeholders and rotate exposed secrets.

Minimal working `.env`:

```env
# App host/port
HOST=0.0.0.0
PORT=8010
DEBUG=false

# Database (SQLite default if omitted)
# DATABASE_URL=sqlite:///backend-new/nexus.db
# ADK session store
# ADK_DATABASE_URL=sqlite+aiosqlite:///backend-new/adk_sessions.db

# LLM
OPENROUTER_KEY=your_openrouter_key_here
OPENROUTER_MODEL=nvidia/nemotron-3-super-120b-a12b:free

# A2A endpoints (optional; defaults use same PORT)
# A2A_SUPPLIER_URL=http://127.0.0.1:8010/supplier/a2a/QuoteAgent
# A2A_BUYER_URL=http://127.0.0.1:8010/buyer/a2a/BuyerAgent
```

### Common variables found in this repo

- `DATABASE_URL`: Primary SQLAlchemy DB for suppliers/negotiations/contracts.
- `ADK_DATABASE_URL`: ADK session DB.
- `OPENROUTER_KEY`: Used by `nexus/buyer/tools.py` for parser + text generation.
- `OPENROUTER_MODEL`: Model name for OpenRouter chat completions.
- `HOST`, `PORT`, `DEBUG`: Server runtime options.
- `A2A_SUPPLIER_URL`, `A2A_BUYER_URL`: A2A JSON-RPC endpoints.

---

## 4) Run Locally

From project root:

```bash
cd backend-new
uv run python -m nexus.main
```

Then open:
- UI: `http://localhost:8010/`
- Health: `http://localhost:8010/health`

On startup, backend runs:
- DB init,
- supplier seeding,
- expired negotiation cleanup loop.

---

## 5) End-to-End Workflow (what happens)

## Buyer flow

1. User submits request in UI (`Launch Procurement`).
2. Frontend calls `POST /procure`.
3. `run_procurement()` in `buyer/negotiation.py` executes:
   - `parse_procurement_request()` → converts NL text to structured BOM.
   - `discover_suppliers()` → filters/scoring by capability, trust, lead-time, budget fit.
   - `broadcast_rfq()` → sends RFQ to suppliers via A2A.
   - `select_winner()` → chooses winner (with exploration chance, see RL section).
   - `compute_negotiation_params()` → open/counter/walkaway prices.
   - `negotiate()` → up to `MAX_ROUNDS=3` with supplier.
   - On success: contract is generated.
   - On fail: returns closest offer + alternatives + suggestion.
4. Frontend updates `Agent Workflow`, negotiation timeline, savings, and contract panel.

## Supplier flow (self-registration + product setup)

In `Catalog` tab, supplier can register/update in one save:
- Supplier identity (id/name/country/region)
- Capabilities (products)
- Certifications
- Trust score
- Lead time days
- Per-capability pricing:
  - base price,
  - max discount %,
  - auto floor price preview.

On save, frontend posts `POST /suppliers` with:
- `capabilities`
- `base_price_map`
- `discount_percent_map`
- `lead_time_days`

Backend computes/stores:
- `base_price_map`
- `price_floor_map = base * (1 - discount/100)`

So self-registered suppliers behave like seeded suppliers in negotiation and RFQ.

### Default deal acceptance thresholds (current behavior)

File: `backend-new/nexus/buyer/negotiation.py`

- `MAX_ROUNDS = 3`
- Buyer offer ladder (per-unit):
  - `open_offer = 85%` of budget-per-unit (or 85% of supplier ask if no budget)
  - `counter_offer = 95%` of budget-per-unit (or 92% of supplier ask if no budget)
  - `walkaway_price = 100%` of budget-per-unit (or 100% of supplier ask if no budget)
- Immediate accept rule:
  - If initial supplier ask `<= open_offer`, deal is accepted immediately (round 0).
- Round accept rules:
  - If supplier explicitly accepts buyer offer, deal is accepted.
  - If supplier counter-offer `<= walkaway_price`, deal is accepted.
- Failure default:
  - If no acceptable counter by round 3, negotiation fails.

Important: there is **no hard trust-score cutoff** enforced in backend by default (trust is part of weighted scoring/ranking, not a strict reject threshold).

---

## 6) RL: where it is used (explicit)

The project currently uses an **RL-inspired scoring update**, not a full Q-table agent.

### 6.1 Exploration during winner selection

File: `backend-new/nexus/buyer/negotiation.py`
- `EPSILON = 0.10`
- In `select_winner()`:
  - with 10% probability: random quote is selected (exploration),
  - otherwise: best scored quote is selected (exploitation).

### 6.2 Reward + trust/fit updates after negotiation

Files:
- `backend-new/nexus/buyer/negotiation.py` (`_finalize_negotiation()`)
- `backend-new/nexus/rl/updater.py` (`compute_reward()`, `update_scores()`)

Flow:
1. On accepted/failed outcome, `_finalize_negotiation()` computes:
   - `discount_given = initial_ask - final_price`
   - `reward = compute_reward(...)`
2. `update_scores(...)` updates supplier metrics:
   - `new_trust = (1 - alpha)*old_trust + alpha*reward`, with `alpha=0.15`
   - `new_fit = 0.5*new_trust + 0.5*success_rate`
3. Supplier `trust_score`, `fit_score`, `total_deals`, `successful_deals` are persisted.
4. System stores an `rl_update` message in transcript payload.

### 6.3 What it means practically

- Suppliers with better negotiation outcomes improve future ranking.
- Faster/efficient accepted deals generally earn higher reward.
- This is **adaptive scoring**, not policy-gradient or deep RL.

---

## 7) API Endpoints (core)

- `POST /procure` → run full procurement
- `POST /procure/retry` → retry with chosen supplier and updated budget/deadline
- `GET /suppliers` → list suppliers
- `POST /suppliers` → create/update supplier (supports capability pricing maps)
- `GET /negotiations/{id}` → negotiation metadata
- `GET /negotiations/{id}/transcript` → transcript + summary
- `GET /negotiations/{id}/contract` → plain text contract
- `GET /contracts` → contract list
- `GET /health` → health check

---

## 8) Frontend Behavior Notes

- Workflow steps are animated step-by-step in `Agent Workflow` (active → done).
- Buyer sees unavailable-item notice when procurement fails.
- Supplier sees "Deals Done With You" filtered by active supplier profile.
- Contract draft can be downloaded as `.txt`.
- Sidebar/header has quick "Back to Home" behavior (no hard reload needed).

---

## 9) Troubleshooting

- `OPENROUTER_KEY not set`: add key in `.env`.
- No quotes returned: check supplier capabilities, A2A endpoint, and supplier agent availability.
- Supplier not appearing in negotiations: verify capability matches BOM category (`sensors|motors|cables|connectors|displays|batteries|other`).
- Pricing seems off: inspect saved `base_price_map` + `price_floor_map` in `/suppliers` response.

---

## 10) Security / Ops Notes

- Do not store production secrets in repo.
- Rotate any accidentally exposed keys immediately.
- Keep `.env` local; use secret manager in production.

---

If you want, next step can be adding an `ENV.example` file with safe placeholders and a startup validation check that fails fast when required env keys are missing.