# FastAPI structure review and improvement plan

Review of the Universal Carrier Formatter HTTP API against current FastAPI best practice, with a concrete plan to improve structure.

## Implementation status (last updated)

| Item | Status | Notes |
|------|--------|--------|
| API limits in `core/config` | Done | `MAX_UPLOAD_BYTES`, `MAX_EXTRACTED_TEXT_CHARS`, `MAX_CONVERT_BODY_BYTES` in `core/config.py`; controller imports from config. |
| `api.py` use config limits | Done | `api.py` imports limits from `core.config`; single source of truth. |
| `api/` package (deps, schemas, routers) | Done | `api/dependencies.py`, `api/api_responses.py`, `api/schemas/` (extract, convert), `api/routers/` (root, carriers, convert) exist. |
| Wire routers into app | Done | `api/main.py` creates app, registers exception handlers and middleware, `include_router()` for root, carriers, extract, convert. `api.py` removed; `api/__init__.py` exports `app`. |
| Normalize `HTTPException.detail` | Done | `_normalize_http_exception_detail()` ensures message is always string; non-string detail in envelope `details`. |
| Document `get_extract_job` responses | Done | OpenAPI `responses={200, 202, 404}` added to GET /extract/jobs/{job_id}. |
| Test coverage | Done | Unit: `test_api_responses`, `test_api_schemas`, `test_controller`, `test_extract_parsing`. Integration: `test_api` (endpoints, OpenAPI, 404/413/request-id, extract job + response schemas in spec). |
| Controller domain split | Done | `src/controller/` package: `ApiController` (facade), `ExtractController`, `ConvertController`, `CarrierController`; routers unchanged, tests patch domain modules. |

## Current state summary

| Area | Current | Notes |
|------|--------|--------|
| **App layout** | `api/` package with `main.py`, routers, dependencies, schemas | `api/__init__.py` exports `app` from `main`. No `api.py`; app built in `api/main.py` with `include_router()`. |
| **Routers** | In use | `api/routers/` (root, carriers, extract, convert); all included in `main.py`. |
| **Dependency injection** | In use | Routes use `Depends(get_controller)` from `api/dependencies.py`. |
| **Request/response** | Pydantic in `api/schemas/` | Extract and convert routers use schemas from `api/schemas`; no duplicate models. |
| **Exception handling** | Global handlers on `app` | Custom envelope; `_normalize_http_exception_detail()` ensures message is always string; non-string detail in `details`. |
| **Middleware** | Custom `RequestIdMiddleware`, `BodySizeLimitMiddleware` | Order: BodySizeLimit then RequestId (reverse of registration = RequestId runs first). |
| **OpenAPI** | Default `/openapi.json`, `/docs`, `/redoc` | Good. |
| **API limits** | Single source in `core/config.py` | Both `api.py` and controller import from config. |
| **Controller** | Domain-driven `src/controller/` package | `ApiController` facade delegates to `ExtractController`, `ConvertController`, `CarrierController`; single `get_controller()` for routers. |

---

## Controller layout (domain-driven)

| Component | Role |
|-----------|------|
| **ApiController** (`controller/api_controller.py`) | Facade used by routers via `Depends(get_controller)`. Exposes `root()`, `health()`, and delegates `extract` / `get_extract_job` → ExtractController, `convert` → ConvertController, `list_carriers` / `carrier_openapi_yaml` → CarrierController. |
| **ExtractController** (`controller/extract.py`) | Extract domain: PDF/text → UCF schema, in-memory job store, sync/async execution. |
| **ConvertController** (`controller/convert.py`) | Convert domain: carrier response → universal JSON via CarrierRegistry. |
| **CarrierController** (`controller/carriers.py`) | Carriers domain: list carrier slugs, serve carrier OpenAPI YAML from schema files. |

Routers and `api/dependencies.get_controller()` are unchanged; only the internal structure of the controller is split by domain.

---

## Gaps vs best practice

### 1. No APIRouter split (bigger applications)

- **Best practice:** Use `APIRouter` with prefixes/tags so the app scales by domain (e.g. `/carriers`, `/extract`, `/convert`, health).
- **Current:** All path operations are declared directly on `app` in one file. Adding more endpoints will keep bloating `api.py`.

### 2. No FastAPI dependency injection

- **Best practice:** Use `Depends()` for reusable pieces (settings, logger, controller, job store). This improves testability and keeps route handlers thin.
- **Current:** `get_settings()` and `_controller` are used as module-level singletons. No way to override them per-request or in tests without patching.

### 3. Controller as singleton, not injected

- **Best practice:** Inject the “service” or “controller” via `Depends(get_controller)` so tests can inject a mock.
- **Current:** `_controller = ApiController()` in `api.py`; routes call `_controller.*` directly. Unit tests for routes would require patching the global.

### 4. Extract endpoint: dual body (JSON vs multipart) and manual validation

- **Best practice:** Prefer a single body model per content type, or use a discriminated union / dependency that returns a validated “extract input” so the route stays thin.
- **Current:** The route manually checks `content-type`, reads `request.json()` or `request.form()`, validates `ExtractFromTextRequest` for JSON, and then calls the controller. Validation errors are handled with a custom `_error_response` return instead of raising so the global validation handler doesn’t run. Works but mixes HTTP and validation concerns in the route.

### 5. HTTPException.detail type

- **Best practice:** Error envelope `message` should be a string. FastAPI allows `HTTPException(detail=...)` to be any JSON-serializable value (e.g. dict for 422 details).
- **Current:** Done. `_normalize_http_exception_detail()` ensures `message` is always a string; non-string `detail` (e.g. dict) is passed in envelope `details`.

### 6. Middleware order and BaseHTTPMiddleware

- **Best practice:** Middleware is executed in reverse order of registration (last registered runs first). Request ID should run first (outermost) so every downstream layer sees it; body size limit should run before heavy processing. Also, `BaseHTTPMiddleware` is async but runs the path in a thread pool; for pure async apps, `Middleware` with a raw ASGI app can avoid that.
- **Current:** `app.add_middleware(BodySizeLimitMiddleware)` then `app.add_middleware(RequestIdMiddleware)` → RequestId runs first (good). No strong need to change unless optimizing for pure async.

### 7. Response model consistency for get_extract_job

- **Best practice:** Use `response_model=None` or a Union of response models and document status codes so OpenAPI reflects 200 vs 202 and the different shapes (result vs status).
- **Current:** Done. Route has `responses={200, 202, 404}` so OpenAPI describes completed, pending, and not-found responses.

### 8. Centralized API limits

- **Best practice:** Limits (max body, timeout) are good; avoid duplicating magic numbers between `api.py` and `controller.py`.
- **Current:** Done. Limits live in `core/config.py`; both `api.py` and controller import from config (single source of truth).

---

## Improvement plan

### Phase 1: Low-risk, high-clarity

1. **Normalize HTTPException.detail in exception handler** — *Done*  
   `_normalize_http_exception_detail()` ensures `message` is always a string; non-string `detail` is passed in envelope `details`.

2. **Single source of truth for API limits** — *Done*  
   `MAX_*` in `core/config.py`; both `api.py` and controller import from config.

3. **Document get_extract_job responses in OpenAPI** — *Done*  
   `GET /extract/jobs/{job_id}` has `responses={200, 202, 404}` with descriptions and optional schema hints.

### Phase 2: Structure with APIRouter and dependencies

4. **Introduce APIRouters** — *Done*  
   `api/routers/` (root, carriers, extract, convert) exist and are included in `api/main.py`. `api.py` removed; `api/__init__.py` exports `app` from `main`.

5. **Add a dependencies module** — *Done*  
   `api/dependencies.py` provides `get_settings()` and `get_controller()`. All routers use `Depends(get_controller)`; app is built in `main.py`.

6. **Move request/response models** — *Done*  
   Routes import from `api/schemas`; no duplicate models. `api/__init__.py` re-exports schemas for backwards compatibility (`from src.api import ConvertRequest`, etc.).

### Phase 3: Optional refinements

7. **Extract input abstraction** — *Done*  
   `ExtractInput` (dataclass) and `parse_extract_request(request)` in `api/extract_parsing.py` build input from JSON or multipart. The extract route calls `parse_extract_request`, then `controller.extract(**extract_input)`.

8. **Explicit response models for get_extract_job** — *Done*  
   `ExtractJobPendingResponse` (202) and `ExtractJobFailedResponse` (200 failed) in `api/schemas/extract.py`; route uses `responses={200: {model: ExtractJobFailedResponse}, 202: {model: ExtractJobPendingResponse}, 404: ...}` so OpenAPI documents the shapes.

9. **Middleware**  
   If you need more control or pure async, replace `BaseHTTPMiddleware` with a plain ASGI middleware that sets request-id and checks content-length. Keep current order (request-id outer, body limit inner relative to request handling).

---

## File layout

### Current

- **App entry:** `src/api/__init__.py` exports `app` from `api/main.py`. No `src/api.py`.
- **Package:** `src/api/` contains `main.py`, `dependencies.py`, `api_responses.py`, `middleware.py`, `extract_parsing.py` (ExtractInput + parse_extract_request), `schemas/` (extract, convert), `routers/` (root, carriers, extract, convert). All routers wired.
- **Shared:** `src/controller.py`, `src/core/config.py` (API limits). Top-level `src/api_responses.py` still exists; `api` package uses `api/api_responses.py`.

### Target (after completing Phase 2)

```
src/
├── api/
│   ├── __init__.py          # re-export app from main (so "from src.api import app" still works)
│   ├── main.py              # FastAPI app, middleware, exception handlers, include_router
│   ├── dependencies.py      # get_settings, get_controller ✅
│   ├── api_responses.py     # error envelope ✅
│   ├── routers/
│   │   ├── __init__.py      ✅
│   │   ├── root.py          ✅ GET /, GET /health
│   │   ├── carriers.py      ✅ GET /carriers, GET /carriers/{name}/openapi.yaml
│   │   ├── extract.py       ✅ POST /extract, GET /extract/jobs/{job_id}
│   │   └── convert.py       ✅ POST /convert
│   └── schemas/             ✅ extract.py, convert.py
├── controller.py
├── api_responses.py         # can remove once api/main.py uses api/api_responses.py
├── ...
```

If you prefer to avoid a full `api/` package, you can keep `src/api.py` as the app entry and have it `include_router()` from `src/api/routers/*` and use `api/dependencies.py` for `Depends(get_controller)` in a hybrid setup.

---

## Priority summary

| Priority | Action | Status | Effort | Impact |
|----------|--------|--------|--------|--------|
| P1 | Normalize `HTTPException.detail` in handler | Done | Low | Correctness, consistency |
| P1 | Single source for API limits (api.py → config) | Done | Low | Maintainability |
| P2 | Wire APIRouters into app (main.py + include_router) | Done | Medium | Structure, testability |
| P2 | Add extract router; use Depends(get_controller) in app | Done | Medium | Structure |
| P2 | Use api/schemas in app (remove duplicates from api.py) | Done | Low | Clarity |
| P2 | Document get_extract_job responses in OpenAPI | Done | Low | API contract |
| P3 | Extract input abstraction + explicit get_extract_job response models | Done | Medium | Cleaner routes, better OpenAPI |

Completing the remaining Phase 1 and Phase 2 items will align the app with FastAPI’s recommended structure for “bigger applications” and make it easier to add endpoints and tests without touching a single large file.

---

## Next steps (recommended order)

1. ~~**api.py uses config limits**~~ — Done. `api.py` imports from `core.config`.
2. ~~**Normalize HTTPException.detail**~~ — Done. `_normalize_http_exception_detail()` in use.
3. ~~**Add get_extract_job responses**~~ — Done. Route documents 200, 202, 404.
4. ~~**Create api/main.py**~~ — Done. `api/main.py` builds app, registers handlers and middleware, includes all four routers. `api/routers/extract.py` added.
5. ~~**Export app from package**~~ — Done. `api/__init__.py` exports `app` from `main`; `api.py` removed. `from src.api import app` unchanged.

---

## Test coverage

| Area | Tests | What's covered |
|------|--------|----------------|
| **Error envelope** | `tests/unit/api/test_responses.py` | `ErrorDetail`, `ErrorEnvelope`, `error_response()` status and body shape. |
| **API schemas** | `tests/unit/api/schemas/test_schemas.py` | `ConvertRequest`, `ExtractFromTextRequest`, `ExtractResponse` validation; `ExtractInput`, `ExtractJobPendingResponse`, `ExtractJobFailedResponse`. |
| **Extract parsing** | `tests/unit/api/test_extract_parsing.py` | `parse_extract_request()`: JSON valid → `ExtractInput`, JSON invalid/empty → 422 `JSONResponse`, bad content-type → 400, async query param. |
| **Controller** | `tests/unit/api/controller/test_controller.py` | `ApiController` facade: root, health, list_carriers, convert, get_extract_job, carrier_openapi_yaml. Unit tests patch domain modules (`src.api.controller.carriers`, `src.api.controller.convert`, `src.api.controller.extract`). Integration: `src.api.controller.extract.ExtractionPipeline`. |
| **API endpoints** | `tests/integration/api/test_api.py` | GET /, /health, /openapi.json; POST /convert (success, validation, 404); POST /extract (validation, mocked pipeline); GET /extract/jobs/{id} 404; GET /carriers/expected/openapi.yaml; request-id; 413; OpenAPI schemas include `ExtractJobPendingResponse`, `ExtractJobFailedResponse`. |

Run unit tests (in Docker): `make test` or `docker-compose run --rm app pytest tests/unit/api/ -v -m unit`.  
Run API integration tests (in Docker): `docker-compose run --rm app pytest tests/integration/api/test_api.py -v -m integration`.
