# StockPulse

StockPulse is a FastAPI + PostgreSQL + React/Vite demo for product pricing and reorder decisioning with a human approval gate.

## Stack
- Backend: FastAPI, SQLAlchemy 2, PostgreSQL, Alembic
- Frontend: React + Vite + JavaScript
- AI layer: OpenAI-compatible endpoint with deterministic mock fallback

## Quickstart

1. Create a Python virtual environment and install backend dependencies:
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r backend/requirements.txt
2. Configure environment:
   copy backend/.env.example backend/.env
3. Start PostgreSQL locally and create the `stockpulse` database.
4. Run migrations:
   cd backend
   alembic upgrade head
5. Start the backend:
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
6. In a separate terminal, install frontend dependencies and run the UI:
   cd frontend
   npm install
   npm run dev

## Demo flow
- The app seeds catalog products, including inventory-low and demand-spike scenarios such as PRD-003 and PRD-008.
- Pending suggestions are generated asynchronously and polled from the dashboard every 3 seconds.
- Human approval is required before product mutation occurs.

## Security
- LLM credentials live only in local `.env` files.
- Frontend code never reads the LLM key directly.
- Product mutations only occur after a suggestion is accepted.
