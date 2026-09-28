# StockPulse: AI Inventory & Dynamic Pricing Engine

> **Autonomous Commerce Signals · AI Recommendations with Deterministic Fallbacks · Human-in-the-Loop Governance**

StockPulse solves the critical lag between real-time inventory changes and merchandising decision-making. In standard online retail operations, when products sell rapidly or demand suddenly spikes, prices stay flat and replenishment requests sit in backlog. StockPulse continuously monitors catalog telemetry, autonomously generates dynamic pricing and reorder suggestions using an AI commerce advisor with deterministic rule-based fallbacks, and surfaces them to a reactive merchandising approval queue where human operators review, accept, or reject recommendations before any product records mutate.

---

## Table of Contents

- [Overview & Problem Context](#overview--problem-context)
- [System Architecture](#system-architecture)
  - [High-Level Dataflow](#high-level-dataflow)
  - [State Machine & Approval Governance](#state-machine--approval-governance)
  - [Hybrid Strategy: Rules + AI Gateway Fallback](#hybrid-strategy-rules--ai-gateway-fallback)
- [Prerequisites](#prerequisites)
- [Quickstart: Running on Localhost](#quickstart-running-on-localhost)
  - [1. Database Setup (PostgreSQL)](#1-database-setup-postgresql)
  - [2. Backend Setup (.env & Python venv)](#2-backend-setup-env--python-venv)
  - [3. Run Migrations & Auto-Seeding](#3-run-migrations--auto-seeding)
  - [4. Launch the Backend Server](#4-launch-the-backend-server)
  - [5. Launch the React Frontend](#5-launch-the-react-frontend)
- [Evaluator Demo Walkthrough](#evaluator-demo-walkthrough)
  - [Scenario 1: Live Telemetry & Automated Signal Badges](#scenario-1-live-telemetry--automated-signal-badges)
  - [Scenario 2: Asynchronous Recommendation Loop](#scenario-2-asynchronous-recommendation-loop)
  - [Scenario 3: Human Approval for Dynamic Pricing](#scenario-3-human-approval-for-dynamic-pricing)
  - [Scenario 4: Human Approval for Inventory Replenishment](#scenario-4-human-approval-for-inventory-replenishment)
  - [Scenario 5: On-Demand Manual Evaluation](#scenario-5-on-demand-manual-evaluation)
  - [Scenario 6: Testing Deterministic Mock vs Remote LLM](#scenario-6-testing-deterministic-mock-vs-remote-llm)
- [API Reference & Testing](#api-reference--testing)
- [Configuration Reference (.env)](#configuration-reference-env)
- [Resilience, Idempotency & Security](#resilience-idempotency--security)
- [Troubleshooting & Windows Tips](#troubleshooting--windows-tips)
- [Sprint 2/3 Extensibility Seams](#sprint-23-extensibility-seams)

---

## Overview & Problem Context

E-commerce operations struggle with two common failure modes:
1. **Low Stock with Frozen Pricing**: A high-velocity SKU drops below safety stock, leading to costly stock-outs instead of raising prices to preserve margins and inventory or initiating timely replenishment.
2. **Uncaptured Demand Spikes**: Trending items experience rapid surges in demand velocity compared to category peers, but price adjustments wait days for manual merchandising reviews.

StockPulse automates this entire loop while strictly maintaining human oversight:
- **Observe**: Continuously watches inventory levels against safety thresholds and velocity ratios against category averages.
- **Reason**: Evaluates market context through a pluggable strategy pattern (deterministic rule baseline plus OpenAI-compatible LLM advisory).
- **Propose**: Dispatches `PricingSuggestion` and `ReorderSuggestion` records to the approval queue with plain-language reasoning.
- **Act (Human Gate)**: Product price and stock levels remain strictly immutable until an authorized human merchandiser approves the recommendation.

---

## System Architecture

### High-Level Dataflow

```mermaid
flowchart LR
    A[Catalog Telemetry / Events] --> B[Background Recommendation Loop]
    B --> C{Trigger Signal?}
    C -->|stock < reorder_threshold| D[INVENTORY_LOW Signal]
    C -->|demand_velocity >= 1.5x avg| E[DEMAND_SPIKE Signal]
    D & E --> F[Strategy Engine]
    F --> G[Deterministic Rule Baseline]
    F --> H[AI Gateway / LLM with Fallback]
    G & H --> I[Pending Suggestions Queue]
    I --> J[React Merchandising Console]
    J -->|Human Review: Accept / Reject| K{Approved?}
    K -->|Accepted Price| L[Mutate Product current_price]
    K -->|Accepted Reorder| M[Increment Product stock_level]
    K -->|Rejected| N[Mark Suggestion REJECTED]
```

### State Machine & Approval Governance

Suggestions follow a strict one-way state transition lifecycle:

```
[ PENDING ] ─── Accept ───> [ ACCEPTED ] ──> Mutates Product (Price / Stock)
     │
     └──────── Reject ───> [ REJECTED ] ──> No mutation (Preserves History)
```

- Products can never be mutated directly by recommendation engines or AI models.
- Duplicate pending suggestions for the same product and trigger reason are idempotently deduplicated.
- Every decision captures timestamps (`accepted_at`, `rejected_at`) for auditability.

### Hybrid Strategy: Rules + AI Gateway Fallback

The recommendation engine implements a resilient multi-tier design:
1. **Rule-Based Engine**:
   - `RuleBasedPricingStrategy`: Detects demand spikes ($\ge 1.5\times$ category average) and applies a 12% price lift; otherwise preserves conversion.
   - `RuleBasedReorderStrategy`: Calculates required safety replenishment based on current deficit and reorder thresholds.
2. **AI Commerce Advisor (`AIGateway`)**:
   - Sends enriched retail context (SKU, category, current price, stock level, velocity vs. category peers, trigger reason) to the LLM.
   - Parses structured recommendations (`suggested_price`, `suggested_quantity`, `reasoning`).
3. **Graceful Fallback**:
   - If the remote LLM endpoint times out, returns unparseable output, or encounters quota/network limits, the system catches the exception and transparently applies the deterministic rule-based output.
   - Setting `LLM_PROVIDER=mock` provides an entirely offline, deterministic execution path suitable for testing without external API dependencies.

---

## Prerequisites

Ensure the following tools are installed on your machine:

- **Python 3.10+** (Python **3.11** is strongly recommended, especially on Windows for pre-compiled `psycopg` C-binaries)
- **Node.js** (v18.0.0 or higher) and `npm`
- **PostgreSQL** (v14 or higher) running locally on port `5432`

---

## Quickstart: Running on Localhost

### 1. Database Setup (PostgreSQL)

Ensure PostgreSQL is running on port `5432`. Connect to PostgreSQL and verify or create the `stockpulse` database:

**Using psql (Linux / macOS / Windows):**
```bash
psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE stockpulse;"
```

**Using PowerShell:**
```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "CREATE DATABASE stockpulse;"
```
*(Default user and password expected in standard config is `postgres` / `postgres`).*

---

### 2. Backend Setup (.env & Python venv)

From the project root:

```bash
# Navigate to backend directory
cd backend

# Create .env from example (or verify existing .env)
cp .env.example .env
```

Ensure `backend/.env` contains:
```ini
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/stockpulse
APP_NAME=StockPulse
ENVIRONMENT=development
LLM_PROVIDER=openai
LLM_API_KEY=sk-SfyNGxhcv7RnQKbZFWX2LQ
LLM_BASE_URL=https://litellm-qc.zycus.net/v1
LLM_MODEL=qwen-cursor
CORS_ORIGINS=http://localhost:5173
DEMAND_SPIKE_MULTIPLIER=1.5
AUTO_INIT_DB=true
```
*(Tip: Set `LLM_PROVIDER=mock` if you prefer offline deterministic testing without external API calls).*

Create and activate the Python virtual environment:

**On Windows (PowerShell):**
```powershell
# From project root:
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

**On macOS / Linux (bash/zsh):**
```bash
# From project root:
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

---

### 3. Run Migrations & Auto-Seeding

Apply the schema migrations using Alembic:

```bash
cd backend
alembic upgrade head
```

With `AUTO_INIT_DB=true`, starting the server will automatically verify tables, seed the 8 demo catalog products, and start the asynchronous recommendation loop.

---

### 4. Launch the Backend Server

Start the FastAPI application with Uvicorn:

**Option A (Using the platform-optimized run script):**
```bash
cd backend
python run.py
```

**Option B (Direct Uvicorn command):**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify backend health at:
- Health check: [http://localhost:8000/health](http://localhost:8000/health) -> `{"status":"ok","service":"StockPulse","database_ready":"true"}`
- Interactive OpenAPI Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 5. Launch the React Frontend

Open a new terminal window:

```bash
cd frontend
npm install
```

Start the Vite development server:

**On Windows:**
```powershell
npm.cmd run dev
```

**On macOS / Linux:**
```bash
npm run dev
```

Open your browser at:
👉 **[http://localhost:5173](http://localhost:5173)**

---

## Evaluator Demo Walkthrough

Follow this step-by-step guide to evaluate all core features of the engine:

### Scenario 1: Live Telemetry & Automated Signal Badges
1. Open [http://localhost:5173](http://localhost:5173).
2. The top telemetry bar shows total metrics: **Products**, **Low Stock**, **Demand Spike**, and **Pending Suggestions**.
3. Inspect the Catalog table:
   - Notice **Pulse Water Bottle (`PRD-003`)** has stock level `12` vs threshold `40` $\rightarrow$ flagged with an amber **Low Stock** badge.
   - Notice **Velocity Running Shoe (`PRD-008`)** has demand velocity `17.7` vs category average `9.8` ($1.8\times$ ratio) $\rightarrow$ flagged with a blue **Demand Spike** badge.

### Scenario 2: Asynchronous Recommendation Loop
1. StockPulse runs a background cycle every 3 seconds (`app/events/background.py`).
2. Without clicking any buttons, observe the **Approval Queue** on the right side populate with pending suggestions:
   - **Reorder Suggestion** for `PRD-003` (`inventory_low` trigger) with proposed replenishment quantity and reasoning.
   - **Pricing Suggestion** for `PRD-008` (`demand_spike` trigger) with proposed price increase and reasoning.

### Scenario 3: Human Approval for Dynamic Pricing
1. Locate the pending pricing suggestion for **Velocity Running Shoe (`PRD-008`)** (e.g., current price `$118.00`, suggested price `$132.16`).
2. Click the green **Accept** button.
3. Observe:
   - The suggestion is resolved from the pending queue.
   - The product row in the Catalog updates immediately to **`$132.16`**.
   - No direct SQL mutation occurred until human approval was granted.

### Scenario 4: Human Approval for Inventory Replenishment
1. Locate the pending reorder suggestion for **Pulse Water Bottle (`PRD-003`)** (e.g., stock `12`, threshold `40`, suggested quantity `40`).
2. Click the green **Accept** button.
3. Observe:
   - The suggestion is resolved.
   - The product's stock count immediately increases from `12` to `52` (simulating inbound shipment fulfillment).
   - If stock now exceeds threshold, the **Low Stock** signal badge automatically clears.

### Scenario 5: On-Demand Manual Evaluation
1. Choose any product in the Catalog (e.g., `PRD-001` Alpha Headphones).
2. Click the **Evaluate** button in its table row.
3. The server immediately runs the strategy evaluation on demand (`POST /api/products/PRD-001/evaluate`) and updates the approval queue.

### Scenario 6: Testing Deterministic Mock vs Remote LLM
1. Open `backend/.env` and toggle:
   ```ini
   LLM_PROVIDER=mock
   ```
2. Restart the backend (`python run.py`).
3. Trigger an evaluation on any product:
   - The suggestion rationale will clearly reflect: *"Mock LLM: deterministic fallback recommended for local development."*
4. Toggle back to `LLM_PROVIDER=openai` to test live LLM reasoning via the configured gateway.

---

## API Reference & Testing

All endpoints are prefixed with `/api` (except `/health`). You can test them using `curl` or PowerShell:

### Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status & database readiness |
| `GET` | `/api/products` | Retrieve all catalog products with current price, stock, and velocity |
| `GET` | `/api/products/summary` | Aggregated dashboard KPI counters (low stock, spikes, totals) |
| `GET` | `/api/products/{id}` | Retrieve single product details |
| `POST` | `/api/products/{id}/evaluate` | Manually trigger pricing & replenishment evaluation for product |
| `GET` | `/api/suggestions/pending` | Fetch pending pricing and reorder suggestions with AI reasoning |
| `POST` | `/api/suggestions/pricing/{id}/accept` | Approve a pricing suggestion and update product `current_price` |
| `POST` | `/api/suggestions/pricing/{id}/reject` | Reject a pricing suggestion |
| `POST` | `/api/suggestions/reorder/{id}/accept` | Approve a reorder suggestion and increment product `stock_level` |
| `POST` | `/api/suggestions/reorder/{id}/reject` | Reject a reorder suggestion |

### Sample Commands

**Check Health:**
```bash
curl -X GET http://localhost:8000/health
```

**List Catalog Products:**
```bash
curl -X GET http://localhost:8000/api/products
```

**Trigger Product Evaluation (PRD-003):**
```bash
curl -X POST http://localhost:8000/api/products/PRD-003/evaluate
```

**Fetch Pending Suggestions:**
```bash
curl -X GET http://localhost:8000/api/suggestions/pending
```

**Accept Pricing Suggestion:**
```bash
curl -X POST http://localhost:8000/api/suggestions/pricing/PR-78519de7/accept
```

---

## Configuration Reference (.env)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/stockpulse` | PostgreSQL connection string using psycopg3 |
| `APP_NAME` | `StockPulse` | Display title for OpenAPI and service logs |
| `ENVIRONMENT` | `development` | Deployment environment identifier |
| `LLM_PROVIDER` | `openai` | AI mode: `openai` (calls gateway) or `mock` (deterministic fallback) |
| `LLM_API_KEY` | *(Secret)* | Bearer token for LLM endpoint |
| `LLM_BASE_URL` | `https://litellm-qc.zycus.net/v1` | Base URL for OpenAI-compatible completions API |
| `LLM_MODEL` | `qwen-cursor` | Target model name |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins for Vite frontend |
| `DEMAND_SPIKE_MULTIPLIER` | `1.5` | Ratio threshold above category average triggering demand spike |
| `AUTO_INIT_DB` | `true` | Automatically initializes schema, seeds products, and starts loop |

---

## Resilience, Idempotency & Security

- **Zero Client Credential Exposure**: LLM credentials and database connection strings reside strictly on the backend; the React client communicates exclusively with `/api/*`.
- **Deduplication / Idempotency**: `_pending_duplicate_exists()` ensures that continuous signal monitoring does not spam duplicate suggestions for the same product, trigger type, and pending state.
- **Fail-Safe Fallback**: Any HTTP error, timeout, or malformed JSON returned by the AI provider is caught safely by `AIGateway`, falling back to deterministic calculations without crashing or dropping recommendations.
- **Strict State Guards**: Approving or rejecting an already resolved suggestion returns HTTP `409 Conflict`, enforcing immutable decision history.

---

## Troubleshooting & Windows Tips

- **`uvicorn` or `python` not recognized in PowerShell**:
  Ensure the virtual environment is activated:
  ```powershell
  .\.venv\Scripts\activate
  ```
  Or run directly via `.\.venv\Scripts\python run.py`.
- **`npm.ps1 cannot be loaded because running scripts is disabled`**:
  On Windows PowerShell with restricted execution policies, run:
  ```powershell
  npm.cmd run dev
  ```
- **PostgreSQL Connection Refused (`port 5432`)**:
  Verify PostgreSQL is started:
  ```powershell
  Get-Service *postgres*
  # If running manually from installation directory:
  & "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" status -D "C:\Program Files\PostgreSQL\17\data"
  ```
- **Python Version Note**:
  Python 3.11 is strongly recommended. Very new Python versions (such as 3.14 pre-releases) may lack pre-compiled C-extensions for `psycopg[binary]`.

---

## Sprint 2/3 Extensibility Seams

StockPulse is designed with clean seams for future roadmap extensions (documented in [ADR.md](file:///c:/Users/poweroot/Desktop/hackathon/stockpulse/ADR.md)):
1. **Competitor-Aware Pricing (`CompetitorAwareStrategy`)**: The pluggable `Strategy` interface allows plugging in competitor pricing scrapers without changing controller or database contracts.
2. **Margin Floor Safeguards**: Product models and schemas include extension points for `cost_price` to prevent pricing recommendations below profit threshold.
3. **Automated Supplier Purchase Orders**: The reorder approval endpoint (`POST /api/suggestions/reorder/{id}/accept`) is structured to dispatch webhook events to external ERP/supplier endpoints.
