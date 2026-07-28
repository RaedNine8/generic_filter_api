# Implementation Prompt: FilterX Copilot Agent Layer (Phase 1)

> **How to use this file:** Feed this entire document to your coding agent as its task specification. It is written to be self-contained — the agent should not need to guess conventions, since every convention referenced here was verified against the actual repository.

---

## 0. Role & Ground Rules

You are implementing a new capability inside the **FilterX** open-source repository (`generic_filter_api`). This is a real, existing, working project with real users — not a greenfield scaffold. Before writing any code:

1. Read `tools/filterx/filterx/core/scanner.py`, `tools/filterx/filterx/core/config.py`, `tools/filterx/filterx/core/patcher.py`, `tools/filterx/filterx/core/manifest.py`, `tools/filterx/filterx/core/conflicts.py`, `tools/filterx/filterx/commands/backend.py`, `tools/filterx/filterx/commands/scan.py`, and `app/filterx_generated/*.py`.
2. Match the existing style exactly: `from __future__ import annotations` at the top of every Python file, full type hints, `@dataclass` for value objects (see `PatchOp`, `ApplyResult`, `Conflict` in `patcher.py`/`conflicts.py`), plain functions over classes where the existing code already prefers that (e.g. `commands/*.py` are function-based, not class-based).
3. **Do not break any existing command.** `filterx scan`, `filterx backend install/validate/remove`, `filterx frontend install/validate/remove`, `filterx db install/validate`, `filterx install`, `filterx validate`, `filterx rollback` must all continue to work exactly as before. Run the full existing test suite (`tests/` at repo root and `tools/filterx/tests/`) before you start, and again after every major step, not just at the end.
4. **No dead code.** No unused imports, no placeholder methods that are never called, no `TODO: implement later` stubs left in the diff. If something isn't needed for Phase 1, don't scaffold it — just don't build it, and note it as a documented extension point instead (see §6).
5. This prompt covers **Phase 1 only**: the natural-language "Filter Copilot" feature. A second feature (an agentic setup/onboarding assistant) is intentionally **out of scope** for this task — do not build it, but the architecture you produce (provider abstraction, resilience layer, config schema) must be reusable by it later without rework. Where a design decision matters for that future reuse, a note is included below.

---

## 1. What You're Building (Functional Overview)

Today, a developer using a FilterX-generated app must either use the visual filter-builder UI or hand-construct a `FilterTreeNode` JSON payload (defined in `app/schema/filter_node.py` on the backend and `frontend/src/app/core/interfaces/filter-tree.interface.ts` on the frontend) to call the generated `/api/{entity}` filter endpoints.

**Filter Copilot** lets a user type a plain-English request — e.g. *"show me books published after 2015 with a rating above 4"* — against a specific entity, and get back:
1. A validated `FilterTreeNode` matching the exact schema the rest of FilterX already uses (no new query format is introduced),
2. A plain-English restatement of what that filter will do, shown to the user **before** anything runs,
3. Only after the user explicitly confirms, the query executes through the **existing, unmodified** `GenericQueryExecutor` (`app/generics/query_executor.py`) and results are returned with a short natural-language summary.

**The critical design constraint:** the LLM is never trusted to know what fields exist or what operations are valid on them. Every field name and operation the model proposes is checked against the entity's real, scanned metadata (already produced by `scanner.py` into `.filterx/scan.json`, and already exposed per-entity in `app/filterx_generated/entities.py` — which, importantly, **already lists the valid `ops` per field** for the demo entities). If the model gets it wrong, it is corrected through a bounded retry loop, not allowed to silently produce a wrong-but-plausible query.

---

## 2. Architecture & Where Code Lives

Mirror the separation that already exists in this repo between **generic library code** (`app/generics/*` — reusable logic other generated code depends on) and **generated glue code** (`app/filterx_generated/*` — thin files that just wire generics together for this specific project). Apply that same split to the agent layer:

| Layer | Lives in | Role |
|---|---|---|
| Agent library (providers, resilience, validation, orchestration) | **`tools/filterx/filterx/agent/`** — new subpackage of the installable `filterx` pip package | Rich, reusable, project-agnostic logic. Ships as an optional extra so base FilterX installs stay lightweight. |
| CLI install/validate/remove commands | **`tools/filterx/filterx/commands/copilot.py`** — new file | Mirrors `commands/backend.py` exactly: scaffolds the thin generated file, patches the anchor, updates the manifest. |
| Generated glue (per consumer project) | **`app/filterx_generated/copilot_router.py`** — new generated file in the demo/consumer project | Thin. Imports from the installed `filterx.agent` package and wires it to this project's entities, DB session, and scan file — same spirit as the existing `router_factory.py`. |
| Frontend chat UI | **`frontend/src/app/shared/components/copilot-panel/`** — new component, same 3-file pattern as `advanced-search-panel/` (`.ts`, `.html`, `.scss`) | User-facing chat + preview/confirm UI. |
| Frontend template source | **`tools/filterx/filterx/reference_runtime/app/shared/components/copilot-panel/`** | The template FilterX copies into new projects during `frontend install`. **Verify first** whether `reference_runtime/app/**` and `frontend/src/app/**` are meant to be kept in sync (diff `reference_runtime/app/shared/components/advanced-search-panel/` against `frontend/src/app/shared/components/advanced-search-panel/` — if they match, apply every frontend change to both locations identically). |

Do not put agent logic directly inside `app/filterx_generated/` — that violates the thin-generated-code convention already established by every other file in that directory.

---

## 3. New Files to Create

### Backend — agent library (`tools/filterx/filterx/agent/`)

```
tools/filterx/filterx/agent/
├── __init__.py
├── providers/
│   ├── __init__.py
│   ├── base.py            # LLMProvider ABC, LLMRequest/LLMResponse dataclasses, error hierarchy
│   ├── registry.py         # register_provider() decorator + create_provider() factory
│   ├── groq_provider.py    # @register_provider("groq")
│   ├── gemini_provider.py  # @register_provider("gemini")
│   └── resilient.py        # ResilientLLMClient — retry + circuit breaker wrapper
├── grounding/
│   ├── __init__.py
│   └── schema_repository.py   # Reads .filterx/scan.json, exposes entity/field/ops lookups, caches + reloads
├── validation/
│   ├── __init__.py
│   ├── base.py             # Validator ABC, FilterValidationError, ValidationPipeline
│   └── validators.py       # SchemaShapeValidator, FieldExistsValidator, OperationAllowedValidator, ValueTypeValidator
├── pipeline/
│   ├── __init__.py
│   └── copilot_graph.py    # LangGraph StateGraph: resolve_entity → compile_filter → validate → (retry loop) → preview
└── api.py                  # create_copilot_router(...) — the FastAPI router factory imported by the generated glue file
```

### Backend — CLI command

```
tools/filterx/filterx/commands/copilot.py
```
Mirror `commands/backend.py`'s structure precisely: `run_install(args) -> int`, `run_validate(args) -> int`, `run_remove(args) -> int`.

### Backend — generated glue (demo/consumer project)

```
app/filterx_generated/copilot_router.py
```

### Frontend

```
frontend/src/app/shared/components/copilot-panel/
├── copilot-panel.component.ts
├── copilot-panel.component.html
└── copilot-panel.component.scss

frontend/src/app/core/interfaces/copilot.interface.ts
frontend/src/app/core/services/copilot.service.ts
```
Plus the mirrored copies under `tools/filterx/filterx/reference_runtime/app/...` per §2's instruction.

### Tests

```
tools/filterx/tests/test_agent_providers.py       # provider adapters, mocked HTTP, retryable vs fatal errors
tools/filterx/tests/test_agent_validators.py      # each validator, valid + invalid cases per field type
tools/filterx/tests/test_agent_pipeline.py        # full graph with a fake in-memory provider (no real API calls)
tools/filterx/tests/test_copilot_install.py       # mirrors test_backend_install.py — CLI install/validate/remove
tests/test_copilot_api.py                          # mounted endpoint, using the demo project's Book/Author entities
```

---

## 4. Files to Update

| File | Change |
|---|---|
| `tools/filterx/filterx/cli.py` | Register a new `copilot` subparser mirroring the `backend`/`frontend` subparser blocks exactly (`install`, `validate`, `remove` subcommands, same global options). |
| `tools/filterx/filterx/core/config.py` | Add a new `agent:` section to `default_config()` (schema in §5) and extend `_validate()` to check it **only when `agent.enabled` is true** — do not make agent config mandatory for existing users. |
| `filterx.yaml` (demo project's config) | Add a commented-out or `enabled: false` example `agent:` block so the demo project documents the new option without turning it on by default. |
| `tools/filterx/pyproject.toml` | Add a new optional dependency group: `[project.optional-dependencies] agent = ["langgraph>=...", "chromadb>=...", "sentence-transformers>=...", "tenacity>=...", "httpx>=..."]`. Base `filterx-cli` install must remain dependency-light — agent extras are opt-in via `pip install filterx-cli[agent]`. |
| `app/main.py` | Add a new anchor comment, e.g. `# FILTERX:COPILOT_MOUNT`, placed near the existing `# FILTERX:ROUTER_MOUNT` anchor. This is what `commands/copilot.py`'s `run_install` patches via the existing `patcher.apply_patch_operations`. |
| `frontend/src/app/app.routes.ts` / `app.config.ts` | Only touch if the copilot panel needs a dedicated route or a new provider registration — prefer embedding the panel as a component inside existing entity list views over adding a new top-level route, to keep the footprint small. |
| `README.md` | Add a short new section describing the copilot feature and pointing to the (to-be-generated) beginner guide from §7. Keep this brief — the detailed explanation belongs in the separate file, not the README. |

---

## 5. Config Schema Addition (`core/config.py`)

Add to `default_config()`, following the existing dict-of-dicts style exactly:

```python
"agent": {
    "enabled": False,
    "providers": [
        {
            "name": "groq",
            "api_key_env": "GROQ_API_KEY",
            "model": "llama-3.3-70b-versatile",
            "roles": ["compile", "retry", "summarize"],
        },
        {
            "name": "gemini",
            "api_key_env": "GEMINI_API_KEY",
            "model": "gemini-2.5-flash",
            "roles": ["fallback"],
        },
    ],
    "vector_store": {
        "enabled": False,
        "backend": "chroma",
        "path": ".filterx/vector_store",
        "embedding_model": "all-MiniLM-L6-v2",
    },
    "safety": {
        "require_human_preview": True,
        "max_validation_retries": 3,
        "max_provider_retries": 3,
        "circuit_breaker_failure_threshold": 5,
        "circuit_breaker_reset_seconds": 60,
    },
    "mount_file": "app/main.py",
    "mount_anchor": "# FILTERX:COPILOT_MOUNT",
    "generated_file": "app/filterx_generated/copilot_router.py",
},
```

**Note the `providers` field is a list, not two hardcoded fields.** This is the extensibility mechanism — adding a third provider later is a config change plus one new provider file, never a change to the pipeline or factory code. `roles` lets different providers serve different pipeline steps (fast/cheap for the high-frequency compile/retry loop, larger-context for anything that needs it), decided by config, not hardcoded in Python.

Extend `_validate()` with an `agent`-specific check, gated behind `cfg.get("agent", {}).get("enabled", False)`:
- If enabled, `providers` must be a non-empty list, each entry must have `name`, `api_key_env`, `model`, `roles`.
- At least one provider must be registered for each of the roles actually used by the pipeline (`compile` is mandatory; `fallback` is optional).

---

## 6. Design Patterns — What to Use Where, and Why

Do not pick these arbitrarily — each is solving a specific problem this feature actually has:

### 6.1 Strategy + Factory/Registry — LLM Providers
**Problem:** you explicitly don't want to be locked to Groq/Gemini only.
**Pattern:** `LLMProvider` is an abstract base class (`providers/base.py`) defining one method, `async def complete(self, request: LLMRequest) -> LLMResponse`. Each concrete provider (`GroqProvider`, `GeminiProvider`) implements it. A `register_provider(name)` decorator (`providers/registry.py`) adds the class to a module-level dict; `create_provider(name, **kwargs)` looks it up. **Adding provider #3 in the future means: one new file with one new class and one decorator — zero changes to any existing file.** This is the Open/Closed Principle applied directly to your stated requirement.

### 6.2 Adapter — Request/Response Normalization
**Problem:** Groq's OpenAI-compatible chat-completions shape and Gemini's `contents`/`parts` shape are different wire formats.
**Pattern:** each provider's `complete()` method is itself the adapter — it takes the shared `LLMRequest` DTO, translates it into that provider's actual HTTP payload, and translates the raw response back into the shared `LLMResponse` DTO. Nothing outside `providers/` ever sees a provider-specific shape.

### 6.3 Decorator — Resilience Wrapper
**Problem:** network calls fail transiently (timeouts, 429 rate limits, 5xx) and need retry with backoff, but retry logic shouldn't be duplicated inside every provider.
**Pattern:** `ResilientLLMClient` (`providers/resilient.py`) wraps any `LLMProvider` and is itself an `LLMProvider` (same interface — this is the Decorator pattern, not inheritance). Use `tenacity` for exponential backoff with jitter, retrying only on a distinct `LLMRetryableError` subclass (429/timeout/5xx) and never on `LLMFatalError` (401/400/misconfiguration — retrying these wastes time and quota for no benefit). Cap at `agent.safety.max_provider_retries`.

### 6.4 Circuit Breaker — Provider Health
**Problem:** if a provider is fully down, retrying every single request for it wastes time and quota before falling through.
**Pattern:** implement a small, self-contained `CircuitBreaker` class (do not pull in an opaque third-party breaker library — this one is simple enough to own directly and explain in an interview). Track consecutive failures per provider name; once `circuit_breaker_failure_threshold` is hit, short-circuit new calls to that provider for `circuit_breaker_reset_seconds`, routing immediately to a configured `fallback`-role provider if one exists, or surfacing a clear error if not.

### 6.5 Chain of Responsibility — Validation
**Problem:** a generated filter can be wrong in several independent ways (bad shape, unknown field, disallowed operation, wrong value type), and the retry prompt is much more useful if it reports *all* problems at once rather than one round-trip per problem.
**Pattern:** `ValidationPipeline` (`validation/base.py`) runs an ordered list of `Validator` instances (`validation/validators.py`) and collects every `FilterValidationError` rather than stopping at the first. `SchemaShapeValidator` runs first (no point checking field names against garbage-shaped input); the rest can run independently after that.

### 6.6 Repository — Schema Grounding
**Problem:** agent code shouldn't scatter raw file reads of `.filterx/scan.json` everywhere, and re-parsing it on every request is wasteful.
**Pattern:** `SchemaRepository` (`grounding/schema_repository.py`) loads and caches `.filterx/scan.json` once, exposes `get_entity(name)` / `list_entities()`, and a `reload()` for cache invalidation (e.g. after a re-scan). This is also the single object the `FieldExistsValidator` and `OperationAllowedValidator` depend on — inject it, don't have validators read files themselves.

### 6.7 State Graph — Orchestration
**Problem:** this is a genuinely multi-step, conditionally-looping process (compile → validate → retry-on-failure → preview), not a single prompt call.
**Pattern:** use **LangGraph's `StateGraph`** directly (`pipeline/copilot_graph.py`) rather than hand-rolling control flow. Nodes: `resolve_entity`, `compile_filter`, `validate_filter`. A conditional edge from `validate_filter` routes back to `compile_filter` (with the collected validation errors appended to the prompt as feedback) if invalid and under the retry cap, or forward to a terminal `preview` state if valid or retries exhausted. This is the one place where "which design pattern" has an obvious, off-the-shelf answer — don't reinvent a graph engine.

### 6.8 Dependency Injection Throughout
Every class above takes its dependencies as constructor arguments (a `SchemaRepository`, a `LLMProvider`, a list of `Validator`s) rather than constructing them internally or reaching for globals. This matches the existing codebase's style (`commands/scan.py` passes `cfg` and `project_root` explicitly rather than using module state) and is what makes `test_agent_pipeline.py` possible without any real network calls — inject a fake in-memory provider that returns canned responses.

---

## 7. Error Handling & Resilience — Concrete Requirements

- Define a clear exception hierarchy in `providers/base.py`: `LLMProviderError` (base) → `LLMRetryableError` (429, timeouts, 5xx) and `LLMFatalError` (401, 400, missing API key, unknown model). This distinction is what lets the resilience decorator know what's worth retrying.
- Every HTTP call must have an explicit timeout (do not rely on library defaults).
- On final failure after all retries and fallback are exhausted, the API endpoint must return a clear, actionable error to the frontend (not a raw stack trace) — e.g. `{"error": "copilot_unavailable", "detail": "All configured LLM providers failed after retries."}` with an appropriate HTTP status (503).
- Log every retry attempt and circuit breaker state transition at `INFO` level minimum — this matters for anyone operating this in production, and it's also exactly the kind of detail worth pointing to in an interview.
- The validation retry loop (§6.5/6.7) and the network resilience retry (§6.3) are **two separate mechanisms** solving two different problems — do not conflate them into one retry counter.

---

## 8. API Surface

Two endpoints, mounted by `create_copilot_router()` in `agent/api.py`:

- `POST /api/filterx/copilot/query` — body: `{"entity": str, "prompt": str}`. Runs the graph through the `preview` state. Returns `{"filter_tree": {...}, "explanation": "Filtering books where...", "confirmation_token": "..."}`. **Does not execute the query.**
- `POST /api/filterx/copilot/execute` — body: `{"confirmation_token": str}`. Only after this explicit second call does the system execute the previously-previewed filter tree through the existing, unmodified `GenericQueryExecutor`, and return results plus a short natural-language summary.

The two-call split is intentional and is your human-approval gate — do not collapse it into one endpoint that executes immediately, even though that would be simpler. Store the pending filter tree behind the confirmation token with a short TTL (e.g. an in-memory dict with expiry is fine for Phase 1 — don't over-engineer persistent storage for this).

---

## 9. Testing Requirements

- **Provider tests**: mock HTTP responses (success, 429, timeout, 401) for both `GroqProvider` and `GeminiProvider`; assert `LLMRetryableError` vs `LLMFatalError` classification is correct in each case.
- **Validator tests**: for each validator, at least one passing case and one failing case per relevant field type (string, integer, boolean, datetime), using the actual `Author`/`Book` entity shapes already present in `app/filterx_generated/entities.py` as fixtures — don't invent a parallel fake schema.
- **Pipeline test**: build the graph with a fake `LLMProvider` (returns scripted responses, including one deliberately invalid response to prove the retry loop actually re-prompts) — no real network calls in this test.
- **CLI install test** (`test_copilot_install.py`): mirror `test_backend_install.py`'s approach — install into a temp project copy, assert the anchor was patched, the manifest was updated, and running install twice is idempotent (matches the existing idempotency guarantee the rest of the tool already provides).
- **API test** (`tests/test_copilot_api.py`): exercise the two-endpoint flow end-to-end against the demo project's real `Book`/`Author` data, with the LLM provider mocked out (do not make real API calls in CI).
- **Regression check**: run the entire existing test suite (both `tests/` and `tools/filterx/tests/`) and confirm 100% of previously-passing tests still pass. Do not consider this task done otherwise.

---

## 10. Definition of Done

- [ ] All files in §3 created, all files in §4 updated, exactly as specified.
- [ ] `pip install filterx-cli` (no extras) still works and has zero new required dependencies.
- [ ] `pip install filterx-cli[agent]` installs the new optional dependencies.
- [ ] `filterx copilot install` scaffolds `app/filterx_generated/copilot_router.py`, patches the `# FILTERX:COPILOT_MOUNT` anchor in `app/main.py`, and records the change in `.filterx/manifest.json` — running it twice is a no-op the second time (idempotent, matching every other `install` command in this tool).
- [ ] `filterx copilot remove` cleanly reverses the above, reusing the existing rollback/patch-bundle mechanism.
- [ ] Adding a hypothetical third provider requires touching only: one new file in `providers/`, one line in `agent.providers` config — nothing else. Verify this claim by actually writing a trivial dummy third provider in a test and confirming the pipeline picks it up with zero pipeline-code changes.
- [ ] Every test in §9 passes, and the full pre-existing test suite still passes with zero regressions.
- [ ] No dead code: search the diff for unused imports, unreferenced functions, and stub methods before considering this complete.

---

## 11. Final Deliverable: Beginner-Facing Explanation Document

**Only after** everything above is implemented, tested, and confirmed not to have broken anything: create a new file at the **repository root** named `AGENT_LAYER_GUIDE.md`. This is a separate deliverable from the code — do not skip it, and do not fold it into the README.

Structure it as one section per job-description requirement, in this exact format:

```markdown
## [JD Requirement, quoted or closely paraphrased]

**Implemented by:** [file path(s)]

**What it does (plain language):** [2-4 sentences, no jargon, as if explaining to someone who has
never touched LangGraph, vector databases, or agent architectures before — define any term you use]

**Key things to remember:**
- [The one or two design decisions that matter most for this piece, and *why* they were made this way]
- [Any gotcha, tradeoff, or thing that would break if changed carelessly]
```

Cover, at minimum, one section each for:
- LLM API integration (provider abstraction)
- Vector databases (even though vector search is a Phase-2/large-schema feature — document the `SchemaRepository` design as the current grounding mechanism and note where a vector store would plug in later)
- Agentic orchestration (the LangGraph pipeline)
- "Ensure the AI behaves correctly within the app" (the validation chain + human-approval gate — this is the most important section, write it carefully)
- Resilience/production-readiness (retry + circuit breaker)
- Extensibility (how to add a new provider, walked through concretely, step by step, as a mini-tutorial)

This file is what turns the implementation into something a beginner (including future-you, revisiting this in six months) can actually learn from — treat it as seriously as the code itself.
