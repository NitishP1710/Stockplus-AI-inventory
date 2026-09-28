# ADR: StockPulse Approval-Driven Recommendation Workflow

## Status
Accepted

## Context
The project needed an inventory recommendation workflow where human operators review AI or rule-based suggestions before changing a real product price or reorder level. The workflow also needed asynchronous generation and a graceful fallback when the remote LLM endpoint is unavailable.

## Decision
We implemented a FastAPI modular monolith with:
- Product models in PostgreSQL with SQLAlchemy
- Pricing and reorder suggestion records separated to enforce approval before mutation
- Rule-based strategy classes for fast deterministic recommendations
- AI gateway fallback with a company-provided OpenAI-compatible endpoint and a mock mode for local development
- React dashboard polling every 3 seconds to review pending suggestions

## Consequences
- Product records remain immutable until an approved suggestion is accepted.
- Frontend UI remains decoupled from any secret credentials.
- Local development remains deterministic with `LLM_PROVIDER=mock`.
