# FastAPI structure review and improvement plan

Review of the Universal Carrier Formatter HTTP API against current FastAPI best practice, with a concrete plan to improve structure.

## Current state summary

| Area | Current | Notes |
|------|--------|--------|
| **App layout** | Single `api.py` + `controller.py` + `api_responses.py` | All routes on one app; controller holds business logic. |
| **Routers** | None | No `APIRouter`; every route registered on `app` in `api.py`. |
| **Dependency injection** | None | Settings and controller are module-level singletons; no `Depends()`. |
| **Request/response** | Pydantic in `api.py` | Models live with app; extract uses manual content-type + validation in route. |
| **Exception handling** | Global handlers on `app` | Custom envelope; `HTTPException.detail` passed as message (can be non-str). |
| **Middleware** | Custom `RequestIdMiddleware`, `BodySizeLimitMiddleware` | Order: BodySizeLimit then RequestId (reverse of registration = RequestId runs first). |
| **OpenAPI** | Default `/openapi.json`, `/docs`, `/redoc` | Good. |

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
- **Current:** `MAX_UPLOAD_BYTES` and `MAX_EXTRACTED_TEXT_CHARS` exist in both; they’re kept in sync by comment. Should live in one place (e.g. config/settings or a single `api_limits` module).

---

## Improvement plan

### Phase 1: Low-risk, high-clarity (recommended first)

1. **Normalize HTTPException.detail in exception handler**  
   In `http_exception_handler`, if `exc.detail` is not a string (e.g. dict/list), serialize it for logging and pass a fixed string (e.g. `"Request failed"`) or a short summary as `message` in the error envelope. Put the raw `detail` in `details` if useful for clients.

2. **Single source of truth for API limits**  
   Move `MAX_UPLOAD_BYTES`, `MAX_EXTRACTED_TEXT_CHARS`, `MAX_CONVERT_BODY_BYTES` into `core/config.py` or a small `api/limits.py`. Import in both `api.py` and `controller.py`. Optionally read from settings/env for overrides.

3. **Document get_extract_job responses in OpenAPI**  
   Add `responses={200: {...}, 202: {...}, 404: {...}}` to the route and, if desired, use a Union response model or leave as-is but document the status codes and body shapes in the description.

### Phase 2: Structure with APIRouter and dependencies

4. **Introduce APIRouters**  
   - `src/api/routers/root.py` – `GET /`, `GET /health`  
   - `src/api/routers/carriers.py` – `GET /carriers`, `GET /carriers/{name}/openapi.yaml`  
   - `src/api/routers/extract.py` – `POST /extract`, `GET /extract/jobs/{job_id}`  
   - `src/api/routers/convert.py` – `POST /convert`  

   Each router uses a `prefix` and `tags` where it helps. `api/main.py` (or keep `api.py` as app entry) creates `FastAPI()` and `include_router()` for each.

5. **Add a dependencies module**  
   - `src/api/dependencies.py` (or `src/dependencies.py`):  
     - `get_settings() -> Settings` – return `get_settings()` from core (or wrap for future overrides).  
     - `get_controller() -> ApiController` – return a singleton or a request-scoped instance so tests can override via `app.dependency_overrides`.  
   - Use `Depends(get_controller)` (and optionally `Depends(get_settings)`) in route handlers so the controller (and settings) are injected instead of imported globals.

6. **Move request/response models**  
   Keep Pydantic models close to the routes that use them: e.g. put extract-related models in `routers/extract.py` or in `api/schemas/extract.py`, convert models in `api/schemas/convert.py`. This keeps `api.py` / `main.py` minimal and groups contract with behavior.

### Phase 3: Optional refinements

7. **Extract input abstraction**  
   Create an `ExtractInput` (or similar) built from either JSON body or multipart (e.g. in a dependency or a small helper). The route receives `ExtractInput` and calls `controller.extract(extract_input)`. Reduces branching and validation inside the route.

8. **Explicit response models for get_extract_job**  
   Define Pydantic models for “completed result”, “pending”, “failed” and use a Union or `responses=` so OpenAPI and clients have a clear contract.

9. **Middleware**  
   If you need more control or pure async, replace `BaseHTTPMiddleware` with a plain ASGI middleware that sets request-id and checks content-length. Keep current order (request-id outer, body limit inner relative to request handling).

---

## Suggested file layout (after Phase 2)

```
src/
├── api/
│   ├── __init__.py          # optional: re-export app
│   ├── main.py              # FastAPI app, middleware, exception handlers, include_router
│   ├── dependencies.py      # get_settings, get_controller
│   ├── api_responses.py     # error envelope (unchanged)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── root.py          # GET /, GET /health
│   │   ├── carriers.py      # GET /carriers, GET /carriers/{name}/openapi.yaml
│   │   ├── extract.py       # POST /extract, GET /extract/jobs/{job_id}
│   │   └── convert.py       # POST /convert
│   └── schemas/             # optional: extract.py, convert.py for Pydantic models
├── controller.py            # ApiController (unchanged or moved under api/)
├── ...
```

If you prefer to avoid a large `api/` package, you can keep `src/api.py` as the app entry and add `src/api_routers/` (or `src/routers/`) plus `src/api_dependencies.py` with the same ideas: routers + dependency injection.

---

## Priority summary

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| P1 | Normalize `HTTPException.detail` in handler | Low | Correctness, consistency |
| P1 | Single source for API limits | Low | Maintainability |
| P2 | APIRouters + dependencies (get_controller, get_settings) | Medium | Structure, testability |
| P2 | Move schemas next to routers | Low | Clarity |
| P3 | Extract input abstraction + explicit get_extract_job responses | Medium | Cleaner routes, better OpenAPI |

Implementing Phase 1 and Phase 2 will align the app with FastAPI’s recommended structure for “bigger applications” and make it easier to add endpoints and tests without touching a single large file.
