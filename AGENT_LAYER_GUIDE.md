# FilterX Agent Layer

Filter Copilot converts plain-language requests into the same validated filter-tree JSON used by FilterX. The model never receives database credentials and never executes SQL. A request follows this flow:

1. Load the selected entity metadata from the FilterX scan.
2. Send only that metadata and the user's request to the configured model.
3. Parse and validate the model's proposed filter tree.
4. Return a preview and a short-lived confirmation token.
5. Confirm the token in a second request.
6. Apply the confirmed tree through the normal `/api/filterx/{entity}/filter` endpoint.

The last step deliberately uses the standard FilterX endpoint so existing permission hooks, row predicates, field visibility, query-cost limits, and response serialization remain authoritative.

## Current support

- Agent API: FastAPI + SQLAlchemy backend renderer.
- Generated copilot panel: Angular frontend renderer.
- Other frontends can call the two HTTP endpoints directly.
- Grounding source: `.filterx/scan.json` plus generated entity metadata.
- Providers: Groq, Gemini, and any OpenAI-compatible HTTP endpoint.
- Local/open-source servers: Ollama, LM Studio, LocalAI, and vLLM through `openai-compatible`.

The configuration validator rejects `agent.enabled: true` with unsupported backend renderers instead of generating broken imports.

## Install the agent dependencies

From a clone of this repository:

```powershell
python -m pip install -e ".\tools\filterx[agent]"
```

For a Git installation:

```powershell
python -m pip install "filterx-cli[agent] @ git+https://github.com/RaedNine8/generic_filter_api.git#subdirectory=tools/filterx"
```

The normal agent extra is lightweight. Experimental vector-store dependencies are separate:

```powershell
python -m pip install -e ".\tools\filterx[agent,agent-vector]"
```

Vector retrieval is not enabled in the current agent workflow; scan metadata remains the source of truth.

## Configure `filterx.yaml`

The existing FastAPI configuration and `# FILTERX:ROUTER_MOUNT` anchor are reused. No second copilot-specific anchor is required unless `agent.mount_anchor` is explicitly set.

### Free local option: Ollama, no API key

Install Ollama, then pull a tool-capable instruct model:

```powershell
ollama pull qwen2.5:7b
```

Use this configuration:

```yaml
agent:
  enabled: true
  providers:
    - name: openai-compatible
      model: qwen2.5:7b
      base_url: http://localhost:11434/v1
      api_key_env: ""
      require_api_key: false
      json_mode: true
      timeout_seconds: 60
      roles: [compile]
  safety:
    require_human_preview: true
    max_validation_retries: 3
    max_provider_retries: 2
    circuit_breaker_failure_threshold: 5
    circuit_breaker_reset_seconds: 60
    confirmation_ttl_seconds: 600
    max_pending_confirmations: 1000
```

If a local server or model rejects OpenAI JSON mode, set `json_mode: false`. FilterX still parses and validates the returned JSON.

### Free hosted option: Groq

Create a developer key in the Groq console and expose it only as an environment variable:

```powershell
$env:GROQ_API_KEY = "your-key"
```

```yaml
agent:
  enabled: true
  providers:
    - name: groq
      model: llama-3.3-70b-versatile
      api_key_env: GROQ_API_KEY
      timeout_seconds: 30
      roles: [compile]
  safety:
    require_human_preview: true
    max_validation_retries: 3
    max_provider_retries: 3
    circuit_breaker_failure_threshold: 5
    circuit_breaker_reset_seconds: 60
    confirmation_ttl_seconds: 600
    max_pending_confirmations: 1000
```

Groq's available model names and free-tier limits can change; use a currently available chat model if the example is retired.

### Free hosted option: Gemini

Create a key in Google AI Studio and expose it as an environment variable:

```powershell
$env:GEMINI_API_KEY = "your-key"
```

```yaml
agent:
  enabled: true
  providers:
    - name: gemini
      model: gemini-2.5-flash
      api_key_env: GEMINI_API_KEY
      timeout_seconds: 30
      roles: [compile]
  safety:
    require_human_preview: true
    max_validation_retries: 3
    max_provider_retries: 3
    circuit_breaker_failure_threshold: 5
    circuit_breaker_reset_seconds: 60
    confirmation_ttl_seconds: 600
    max_pending_confirmations: 1000
```

### Hosted OpenAI-compatible endpoint

The generic adapter also supports services such as OpenRouter or an organization-hosted vLLM endpoint:

```powershell
$env:MY_LLM_API_KEY = "your-key"
```

```yaml
agent:
  enabled: true
  providers:
    - name: openai-compatible
      model: your-model-name
      base_url: https://your-provider.example/v1
      api_key_env: MY_LLM_API_KEY
      require_api_key: true
      json_mode: true
      timeout_seconds: 30
      roles: [compile]
```

FilterX appends `/chat/completions` unless `base_url` already ends with that path.

## Configure fallback providers

Exactly one provider must have the `compile` role. Any number can have the `fallback` role. For example, use local Ollama first and Groq only when the local service is unavailable:

```yaml
agent:
  enabled: true
  providers:
    - name: openai-compatible
      model: qwen2.5:7b
      base_url: http://localhost:11434/v1
      api_key_env: ""
      roles: [compile]
    - name: groq
      model: llama-3.3-70b-versatile
      api_key_env: GROQ_API_KEY
      roles: [fallback]
```

Retryable timeouts, rate limits, and server errors use exponential backoff and then fall through. Missing credentials and invalid requests are fatal for that provider but may still use a configured fallback. Circuit breakers are tracked by provider and model.

## Generate and validate

Run the normal all-in-one flow. When `agent.enabled` is true, it now installs the backend, copilot router, frontend, and optional database integration in order:

```powershell
filterx install --project-root . --config filterx.yaml --dry-run --json
filterx install --project-root . --config filterx.yaml --no-dry-run --yes --json
filterx validate --project-root . --config filterx.yaml --json
filterx copilot validate --project-root . --config filterx.yaml --json
```

Or run the agent step separately after scanning and installing the backend:

```powershell
filterx scan --project-root . --config filterx.yaml --no-dry-run --json
filterx backend install --project-root . --config filterx.yaml --no-dry-run --yes --json
filterx copilot install --project-root . --config filterx.yaml --no-dry-run --yes --json
```

By default the generated router is written beside the generated FastAPI router and mounted at the backend router anchor. Override `agent.generated_file`, `agent.mount_file`, or `agent.mount_anchor` only when necessary.

## Test the API directly

Start the host FastAPI app using its normal command, then request a preview:

```powershell
$preview = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/filterx/copilot/query" `
  -ContentType "application/json" `
  -Body '{"entity":"Book","prompt":"available books rated above 4"}'
$preview
```

Confirm it:

```powershell
$body = @{ confirmation_token = $preview.confirmation_token } | ConvertTo-Json
$confirmed = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/filterx/copilot/execute" `
  -ContentType "application/json" `
  -Body $body
$confirmed
```

Then submit `$confirmed.filter_tree` to the standard filtering endpoint. This is the request that reads data and enforces the normal FilterX authorization and row-security pipeline:

```powershell
$filterBody = @{ filter_tree = $confirmed.filter_tree } | ConvertTo-Json -Depth 20
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/filterx/Book/filter?page=1&size=20" `
  -ContentType "application/json" `
  -Body $filterBody
```

If the host uses authentication, include the same authorization headers in all three requests. Confirmation tokens are short-lived, single-use, and bound to the authenticated principal.

## Security behavior

- User prompts are treated as untrusted data.
- Only scanned fields and declared operations are accepted.
- Values are type-checked, including enum members.
- Filter trees are limited by node count and depth.
- Field-visibility hooks remove hidden schema fields before metadata is sent to the model.
- Permission hooks receive `copilot.preview` and `copilot.confirm` actions.
- The model never receives API keys; adapters read keys from environment variables.
- Upstream error bodies are not returned to clients.
- In-memory confirmation state is bounded and expired automatically.

The built-in confirmation store is process-local. Multi-process or multi-instance production deployments should replace it with a shared TTL store before relying on cross-instance confirmations.

## Run contributor tests

From the repository root with the project environment active:

```powershell
$env:PYTHONPATH = ".\tools\filterx"
python -m pytest tools/filterx/tests/test_agent_providers.py `
  tools/filterx/tests/test_agent_pipeline.py `
  tools/filterx/tests/test_agent_validators.py `
  tools/filterx/tests/test_copilot_api.py `
  tools/filterx/tests/test_copilot_install.py -q
python -m pytest tools/filterx/tests -q
```

The provider tests use fake HTTP clients and do not consume API quota.
