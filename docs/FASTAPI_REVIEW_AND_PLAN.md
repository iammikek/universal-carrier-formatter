# FastAPI structure review and improvement plan

Review of the Universal Carrier Formatter HTTP API against current FastAPI best practice, with a concrete plan to improve structure.

## Implementation status (last updated)

| Item | Status | Notes |
|------|--------|--------|
| API limits in `core/config` | Done | `MAX_UPLOAD_BYTES`, `MAX_EXTRACTED_TEXT_CHARS`, `MAX_CONVERT_BODY_BYTES` in `core/config.py`; controller imports from config. |
| `api.py` use config limits | Pending | `api.py` still defines limits locally; should import from `core.config` for single source. |
| `api/` package (deps, schemas, routers) | Done | `api/dependencies.py`, `api/api_responses.py`, `api/schemas/` (extract, convert), `api/routers/` (root, carriers, convert) exist. |
| Wire routers into app | Pending | No `api/main.py`; app still in `api.py`; routers are not included. Need `main.py` + `include_router()` and optionally retire `api.py`. |
| Normalize `HTTPException.detail` | Pending | Handler still uses `exc.detail or "Request failed"`; detail may be non-string. |
| Document `get_extract_job` responses | Pending | OpenAPI `responses={200, 202, 404}` not yet added. |
| Test coverage | Done | Unit: `test_api_responses`, `test_api_schemas`, `test_controller`. Integration: extract mock fix, 404/413/request-id tests. |

## Current state summary

| Area | Current | Notes |
|------|--------|--------|
| **App layout** | Single `api.py` + `controller.py` + `api_responses.py`; parallel `api/` package (not wired) | All routes still on `app` in `api.py`. `api/` has routers, dependencies, schemas ready. |
| **Routers** | Defined but not used | `api/routers/` (root, carriers, convert) exist; app does not `include_router()`. Extract router not yet added. |
| **Dependency injection** | Prepared, not used | `api/dependencies.py` has `get_settings`, `get_controller`; `api.py` still uses module-level `_controller`. |
| **Request/response** | Pydantic in `api.py`; copies in `api/schemas/` | Models in both places; extract uses manual content-type + validation in route. |
| **Exception handling** | Global handlers on `app` | Custom envelope; `HTTPException.detail` passed as message (can be non-str). |
| **Middleware** | Custom `RequestIdMiddleware`, `BodySizeLimitMiddleware` | Order: BodySizeLimit then RequestId (reverse of registration = RequestId runs first). |
| **OpenAPI** | Default `/openapi.json`, `/docs`, `/redoc` | Good. |
| **API limits** | In `core/config.py`; controller uses them | `api.py` still has local constants; should switch to config. |

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
- **Current:** `http_exception_handler` does `exc.detail or "Request failed"` and passes that as `message` to `_error_response`. If `detail` is a dict (e.g. from a library), the response may be inconsistent or the client may expect a string.

### 6. Middleware order and BaseHTTPMiddleware

- **Best practice:** Middleware is executed in reverse order of registration (last registered runs first). Request ID should run first (outermost) so every downstream layer sees it; body size limit should run before heavy processing. Also, `BaseHTTPMiddleware` is async but runs the path in a thread pool; for pure async apps, `Middleware` with a raw ASGI app can avoid that.
- **Current:** `app.add_middleware(BodySizeLimitMiddleware)` then `app.add_middleware(RequestIdMiddleware)` → RequestId runs first (good). No strong need to change unless optimizing for pure async.

### 7. Response model consistency for get_extract_job

- **Best practice:** Use `response_model=None` or a Union of response models and document status codes so OpenAPI reflects 200 vs 202 and the different shapes (result vs status).
- **Current:** `get_extract_job` returns either a dict or a `JSONResponse`; no `response_model` on the route. OpenAPI won’t describe the multiple response shapes clearly.

### 8. Centralized API limits

- **Best practice:** Limits (max body, timeout) are good; avoid duplicating magic numbers between `api.py` and `controller.py`.
- **Current:** Limits live in `core/config.py` and controller imports them. **Remaining:** `api.py` still defines the same constants locally; it should import from `core.config` so there is a single source of truth.

---

## Improvement plan

### Phase 1: Low-risk, high-clarity

1. **Normalize HTTPException.detail in exception handler** — *Pending*  
   In `http_exception_handler`, if `exc.detail` is not a string (e.g. dict/list), use a fixed string (e.g. `"Request failed"`) for `message` and put the raw `detail` in `details` so the envelope stays consistent.

2. **Single source of truth for API limits** — *Partial*  
   Done: `MAX_*` moved to `core/config.py`; controller imports from config.  
   Remaining: Update `api.py` to `from .core.config import MAX_UPLOAD_BYTES, MAX_EXTRACTED_TEXT_CHARS, MAX_CONVERT_BODY_BYTES` and remove local definitions.

3. **Document get_extract_job responses in OpenAPI** — *Pending*  
   Add `responses={200: {...}, 202: {...}, 404: {...}}` to the `GET /extract/jobs/{job_id}` route so OpenAPI describes all status codes and body shapes.

### Phase 2: Structure with APIRouter and dependencies

4. **Introduce APIRouters** — *Partial*  
   Done: `api/routers/root.py`, `carriers.py`, `convert.py` exist (with prefix and tags).  
   Remaining: Add `api/routers/extract.py` for `POST /extract` and `GET /extract/jobs/{job_id}`. Create `api/main.py` that builds the `FastAPI` app, registers exception handlers and middleware, and calls `app.include_router()` for each router. Then either retire `api.py` and have `api/__init__.py` export `app` from `main`, or keep `api.py` as a thin wrapper that imports and includes the routers.

5. **Add a dependencies module** — *Done*  
   `api/dependencies.py` provides `get_settings()` and `get_controller()`.  
   Remaining: Use them in the app by including the routers (which already use `Depends(get_controller)`) and ensuring the app is built in `main.py` so dependency overrides work in tests.

6. **Move request/response models** — *Partial*  
   Done: `api/schemas/extract.py` and `api/schemas/convert.py` contain the Pydantic models.  
   Remaining: When switching to routers, have routes import from `api.schemas` and remove duplicate model definitions from `api.py` (or have `api.py` import from `api.schemas` once routers are wired).

### Phase 3: Optional refinements

7. **Extract input abstraction**  
   Create an `ExtractInput` (or similar) built from either JSON body or multipart (e.g. in a dependency or a small helper). The route receives `ExtractInput` and calls `controller.extract(extract_input)`. Reduces branching and validation inside the route.

8. **Explicit response models for get_extract_job**  
   Define Pydantic models for “completed result”, “pending”, “failed” and use a Union or `responses=` so OpenAPI and clients have a clear contract.

9. **Middleware**  
   If you need more control or pure async, replace `BaseHTTPMiddleware` with a plain ASGI middleware that sets request-id and checks content-length. Keep current order (request-id outer, body limit inner relative to request handling).

---

## File layout

### Current

- **App entry:** `src/api.py` — defines `app`, all routes, middleware, exception handlers, and request/response models.
- **Package (not wired):** `src/api/` contains `dependencies.py`, `api_responses.py`, `schemas/` (extract, convert), `routers/` (root, carriers, convert). No `main.py` or `__init__.py`; app does not include these routers.
- **Shared:** `src/controller.py`, `src/api_responses.py` (used by `api.py`), `core/config.py` (includes API limits; controller uses them).

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
│   │   ├── extract.py       ❌ to add: POST /extract, GET /extract/jobs/{job_id}
│   │   └── convert.py       ✅ POST /convert
│   └── schemas/             ✅ extract.py, convert.py
├── api.py                   # optional: remove after main.py is the entry, or keep as thin wrapper
├── controller.py
├── api_responses.py         # can remove once api/main.py uses api/api_responses.py
├── ...
```

If you prefer to avoid a full `api/` package, you can keep `src/api.py` as the app entry and have it `include_router()` from `src/api/routers/*` and use `api/dependencies.py` for `Depends(get_controller)` in a hybrid setup.

---

## Priority summary

| Priority | Action | Status | Effort | Impact |
|----------|--------|--------|--------|--------|
| P1 | Normalize `HTTPException.detail` in handler | Pending | Low | Correctness, consistency |
| P1 | Single source for API limits (api.py → config) | Partial (config + controller done) | Low | Maintainability |
| P2 | Wire APIRouters into app (main.py + include_router) | Pending | Medium | Structure, testability |
| P2 | Add extract router; use Depends(get_controller) in app | Partial (routers exist, not included) | Medium | Structure |
| P2 | Use api/schemas in app (remove duplicates from api.py) | Pending | Low | Clarity |
| P2 | Document get_extract_job responses in OpenAPI | Pending | Low | API contract |
| P3 | Extract input abstraction + explicit get_extract_job response models | Pending | Medium | Cleaner routes, better OpenAPI |

Completing the remaining Phase 1 and Phase 2 items will align the app with FastAPI’s recommended structure for “bigger applications” and make it easier to add endpoints and tests without touching a single large file.

---

## Next steps (recommended order)

1. **api.py uses config limits** — In `api.py`, replace local `MAX_*` with `from .core.config import MAX_UPLOAD_BYTES, MAX_EXTRACTED_TEXT_CHARS, MAX_CONVERT_BODY_BYTES`.
2. **Normalize HTTPException.detail** — In `http_exception_handler`, set `message = exc.detail if isinstance(exc.detail, str) else "Request failed"` (and optionally put non-string `detail` in `details`).
3. **Add get_extract_job responses** — On the route, add `responses={200: {...}, 202: {...}, 404: {...}}`.
4. **Create api/main.py** — Build `FastAPI()`, register exception handlers and middleware, `include_router()` for root, carriers, convert; add `api/routers/extract.py` and include it.
5. **Export app from package** — Add `api/__init__.py` with `from .main import app` so `from src.api import app` still works; then remove or slim down `api.py`.
