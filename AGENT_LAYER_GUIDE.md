## LLM API Integration (Provider Abstraction)

**Implemented by:** tools/filterx/filterx/agent/providers/base.py, tools/filterx/filterx/agent/providers/registry.py, tools/filterx/filterx/agent/providers/groq_provider.py, tools/filterx/filterx/agent/providers/gemini_provider.py

**What it does (plain language):** FilterX talks to language models through one small shared interface called `LLMProvider`. Groq and Gemini each translate that shared request into their own HTTP format, then translate the provider response back into the same `LLMResponse` shape. The rest of the copilot code never needs to know which provider produced the answer.

**Key things to remember:**

- Provider-specific JSON stays inside the provider adapter, so the pipeline can stay provider-neutral.
- Retryable failures such as timeouts and rate limits are different from fatal failures such as missing API keys; the distinction controls whether retry logic should run.

## Vector Databases (Grounding And Future Retrieval)

**Implemented by:** tools/filterx/filterx/agent/grounding/schema_repository.py, tools/filterx/filterx/core/config.py

**What it does (plain language):** Phase 1 grounds the copilot in `.filterx/scan.json`, which is the metadata FilterX already creates by scanning real SQLAlchemy models. `SchemaRepository` loads and caches that file, then answers questions such as which entities exist, which fields they have, and which operations each field allows. A vector database is configured but disabled for now; it would plug in beside this repository later to retrieve the most relevant schema facts for very large projects.

**Key things to remember:**

- The LLM is not trusted to invent fields; every proposed field and operation is checked against scanned metadata.
- Vector search is a later scaling tool, not the source of truth. The scanned schema remains the authority.

## Agentic Orchestration (LangGraph Pipeline)

**Implemented by:** tools/filterx/filterx/agent/pipeline/copilot_graph.py

**What it does (plain language):** The copilot request is handled as a small workflow: resolve the entity, ask the model to compile a filter, validate that filter, and retry with feedback when validation fails. LangGraph provides the workflow engine for that loop. If LangGraph is not importable in a lightweight environment, the code uses the same steps in a tiny fallback runner so tests and basic imports still work.

**Key things to remember:**

- Validation retries are about correcting the model's filter JSON; provider retries are about network or service failures. They are separate counters.
- The graph returns a preview result, not executed data, because execution requires an explicit second call.

## Ensure The AI Behaves Correctly Within The App

**Implemented by:** tools/filterx/filterx/agent/validation/base.py, tools/filterx/filterx/agent/validation/validators.py, tools/filterx/filterx/agent/api.py, app/filterx_generated/copilot_router.py

**What it does (plain language):** The validation chain checks the generated filter in layers: first the JSON shape, then whether fields exist, whether operations are allowed, and whether values match field types. If the filter passes, the API returns a plain-English preview and a confirmation token. The query only runs after the frontend sends that token back to `/api/filterx/copilot/execute`.

**Key things to remember:**

- The human preview is the safety gate. Collapsing preview and execution into one endpoint would remove the user approval step.
- Validators collect multiple problems at once so the retry prompt can give the model useful feedback in a single round trip.

## Resilience And Production Readiness

**Implemented by:** tools/filterx/filterx/agent/providers/resilient.py, tools/filterx/filterx/agent/api.py

**What it does (plain language):** `ResilientLLMClient` wraps any provider and adds retry behavior with backoff for temporary problems. It also has a circuit breaker, which means a provider that keeps failing is skipped for a short period instead of slowing down every request. The API turns exhausted provider failures into a clear 503 response for the frontend.

**Key things to remember:**

- Only `LLMRetryableError` is retried. `LLMFatalError` is surfaced quickly because retrying bad credentials or malformed requests wastes time.
- Circuit breaker state is tracked per provider name, so fallback providers can still serve requests when the primary provider is unhealthy.

## Extensibility (Adding A New Provider)

**Implemented by:** tools/filterx/filterx/agent/providers/registry.py, tools/filterx/tests/test_agent_providers.py, filterx.yaml

**What it does (plain language):** New providers are registered with a decorator instead of being hardcoded into the pipeline. To add one, create a new file in `tools/filterx/filterx/agent/providers/`, subclass `LLMProvider`, implement `complete()`, and decorate the class with `@register_provider("your-name")`. Then add a provider entry in `agent.providers` with its `name`, `api_key_env`, `model`, and `roles`.

**Key things to remember:**

- The pipeline asks the registry for providers by name, so adding provider number three does not require editing pipeline code.
- Keep each provider responsible for its own wire format. The shared DTOs are the boundary that keeps the rest of FilterX simple.
