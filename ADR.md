# StockPulse Architecture Decision Records (ADR)

> **Format**: Context $\rightarrow$ Options Considered $\rightarrow$ Decision & Rationale $\rightarrow$ Tradeoffs & Consequences  
> **Status**: Accepted

---

## 1. Where Does Commerce Logic Live?

### Context
StockPulse requires evaluating inventory thresholds, demand velocity, price adjustment calculations, and reorder quantities across both on-demand user endpoints and automated background loops. We needed a clean boundary to avoid bloated controller endpoints or models accumulating mixed responsibilities (persistence, HTTP, business logic, AI calls).

### Options Considered
- **Option A (Fat Active Record / Domain Models)**: Place pricing calculation and reorder logic directly on `Product` model instances.
- **Option B (Monolithic Service Layer)**: Implement all calculation, database querying, AI dispatch, and approval logic inside a single monolithic service function.
- **Option C (Dedicated Strategy Classes & Orchestrating Service)**: Separate the commerce logic into distinct strategy classes (`RuleBasedPricingStrategy`, `RuleBasedReorderStrategy`), isolated AI gateway (`AIGateway`), and an orchestration service (`suggestion_service.py`) handling database state transactions.

### Decision
We chose **Option C**. Commerce algorithms are isolated within standalone strategy classes under `app/strategies/`. The service layer (`suggestion_service.py`) coordinates evaluation, deduplication, and persistence, while FastAPI controllers exclusively handle HTTP routing and serialization.

### Tradeoffs & Consequences
- **Pros**: Clean separation of concerns, high testability of pricing/reorder calculations in isolation without requiring database mocks, easy addition of future strategies.
- **Cons**: Requires passing product attributes between the model and strategy objects.

---

## 2. Unified AI Call vs. Separate Pricing and Reorder Calls

### Context
When a product triggers recommendations, it often requires both a pricing adjustment and an inventory replenishment quantity (e.g., during low stock or viral demand). We evaluated whether to make separate LLM calls for pricing and reorder or execute a unified advisory call.

### Options Considered
- **Option A (Separate LLM Prompts)**: One dedicated prompt for dynamic pricing, and a completely separate prompt for replenishment quantity.
- **Option B (Unified Contextual Advisory Call)**: A single comprehensive prompt providing all telemetry (current stock, velocity, category average, trigger signal) and requesting structured JSON with both `suggested_price`, `suggested_quantity`, and reasoning.

### Decision
We chose **Option B (Unified Contextual Advisory Call)** with dedicated strategy fallbacks. Inventory level directly influences optimal pricing (e.g., scarcity pricing vs. clearance), and demand velocity directly influences replenishment urgency. Merging context into a unified prompt gives the LLM complete operational visibility.

### Tradeoffs & Consequences
- **Pros**: Cuts LLM latency and API token consumption in half; provides holistic reasoning where pricing and replenishment inform one another.
- **Cons**: If the response is unparseable, both recommendations fall back to their respective rule-based engines simultaneously.

---

## 3. How Does Runtime Strategy Switching Work?

### Context
The application must support switching between live AI advisory mode (`openai`) and deterministic local mock mode (`mock`) dynamically without requiring codebase refactoring or complex redeployments.

### Options Considered
- **Option A (Hardcoded Mode / Code Toggles)**: Use conditional branches scattered across functions.
- **Option B (Dependency Injection / Gateway Factory)**: A central `AIGateway` governed by declarative environment settings (`LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`).

### Decision
We chose **Option B**. The `AIGateway` inspects `settings.llm_provider`. When configured to `mock`, it bypasses external HTTP requests and returns deterministic, testable values. When configured to `openai`, it delegates to the OpenAI-compatible completions endpoint.

### Tradeoffs & Consequences
- **Pros**: Evaluators and developers can run the entire system offline with zero external dependencies; automated CI/CD can test full workflows deterministically.
- **Cons**: Runtime configuration changes require an environment reload or server restart.

---

## 4. LLM Failure Handling & Resilience

### Context
Third-party LLM endpoints are prone to network timeouts, rate limiting (HTTP 429), server errors (HTTP 5xx), and occasional schema non-compliance (malformed JSON or hallucinated values). The agentic loop must never crash or silently drop suggestions when the AI provider experiences an outage.

### Options Considered
- **Option A (Fail-Fast & Retry)**: Throw exceptions up the stack and retry with exponential backoff.
- **Option B (Silent Drop)**: Log errors and skip suggestion generation for that cycle.
- **Option C (Multi-Tier Resilient Fallback to Deterministic Rules)**: Wrap AI gateway calls with strict timeout limits and a comprehensive try/except guard that automatically substitutes deterministic rule-based outputs.

### Decision
We chose **Option C**. The `AIGateway` sets a 25-second HTTP timeout and catches all exceptions. Upon any failure or unparseable JSON, it seamlessly returns the deterministic baseline from `RuleBasedPricingStrategy` and `RuleBasedReorderStrategy`, annotating the reasoning with *"LLM unavailable; fallback to deterministic rule-based output"*.

### Tradeoffs & Consequences
- **Pros**: 100% loop reliability and uptime; merchandising teams always receive valid recommendations even during complete upstream AI outages.
- **Cons**: The user receives a rule-based suggestion rather than deep generative reasoning during outages.

---

## 5. Agentic Loop Trigger & Decoupling

### Context
Catalog events (such as stock decrements from orders or telemetry polling) must evaluate recommendation triggers without blocking user requests or degrading transactional throughput.

### Options Considered
- **Option A (Synchronous In-Request Evaluation)**: Run evaluation and AI calls directly within the HTTP request handler of order/stock updates.
- **Option B (Decoupled Background Loop with Idempotent Deduplication)**: Run an asynchronous background loop (`app/events/background.py`) that monitors database state periodically (every 3 seconds), paired with idempotent deduplication queries (`_pending_duplicate_exists`).

### Decision
We chose **Option B**. The recommendation engine runs asynchronously outside the critical request path. If a product's telemetry triggers a recommendation, the system verifies whether a `PENDING` suggestion already exists for that product, trigger reason, and suggestion type before inserting a new record.

### Tradeoffs & Consequences
- **Pros**: HTTP endpoints return sub-millisecond responses without being blocked by LLM latency; the approval queue is never flooded with duplicate pending suggestions.
- **Cons**: Suggestions appear within the polling window (up to 3 seconds) rather than instantly in the database at the exact millisecond of the signal.

---

## 6. Extensibility Seams & Sprint 2/3 Roadmap Exclusions

### Context
To deliver a high-quality, focused solution within sprint constraints, non-core features (competitor price scraping, automated ERP purchase order dispatch, payment processing) were deliberately scoped out while preserving architectural extension points.

### Implemented Extensibility Seams
1. **Competitor-Aware Pricing (`CompetitorAwareStrategy`)**:
   - The strategy pattern allows introducing a competitor-aware class implementing `.generate(product, trigger_reason)` without altering database schema or controllers.
2. **Margin Floor Bounds (`cost_price`)**:
   - The `Product` model and schemas are structured to incorporate a `cost_price` column and constraint check to guarantee dynamic pricing never breaches minimum margin thresholds.
3. **Outbound Replenishment Webhooks**:
   - `approve_reorder_suggestion()` in `suggestion_service.py` provides a designated hook to publish purchase order events to supplier APIs or ERP message buses.

### Deliberate Exclusions
- **Direct Storefront Checkout & Payments**: The core deliverable is an intelligent reactive merchandising advisor and approval engine, not a consumer checkout cart.
- **Unsupervised Autonomous Price Mutation**: Dynamic pricing in commerce requires regulatory and brand safety governance; human approval before mutation was enforced by design.
