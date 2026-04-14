# Context Snapshot (Working Memory)

Last updated: 2026-04-14

## Active Projects

1. `C:\Users\charl\Documents\Python\cli_framework`
2. `C:\Users\charl\Documents\Python\ecommerce-backend-example`

## `cli_framework` Summary

### Intent
- Lightweight, ergonomic decorator-based tooling library.
- Two modules:
  - `registers.cli`: command registration, parsing, DI, middleware.
  - `registers.db`: Pydantic + SQLAlchemy persistence manager.

### Current DB Architecture (kept intact)
- Manager pattern via `Model.objects`.
- Decorator: `@database_registry(...)`.
- Schema helpers on model class: `create_schema`, `drop_schema`, `schema_exists`, `truncate`.
- Core files:
  - `src/registers/db/decorators.py`
  - `src/registers/db/registry.py`
  - `src/registers/db/schema.py`
  - `src/registers/db/engine.py`
  - `src/registers/db/operators.py`

### Implemented Feature State
- Primary key contract stabilized:
  - `id: int | None = None` => DB-managed autoincrement.
  - `id: int` => manual key.
  - explicit id rejected on DB-managed create.
  - persisted PK immutability enforced.
- Password handling:
  - `password` field auto-hashed on write paths.
  - `verify_password(...)` injected on models with `password`.
- Query/ordering:
  - operators (`__gt`, `__gte`, `__lt`, `__lte`, `__like`, `__ilike`, `__in`, `__not_in`, `__is_null`, `__between`, `__contains`, `__startswith`, `__endswith`).
  - `order_by` support for `filter`, `all`, `first`, `last`.
- Bulk APIs:
  - `bulk_create`, `bulk_upsert`.
- Migration helpers:
  - `add_column`, `ensure_column`, `rename_table`, `column_names`.
- SQLAlchemy delegation improvements:
  - dialect-aware insert/upsert plumbing.
  - `RETURNING`-based update/bulk hydration where supported.
  - fallback paths preserved for compatibility.

### Test Coverage Status
- Full suite currently green in `cli_framework`.
- Command used: `pytest -q`
- Result: `150 passed`.
- Notable DB test files:
  - `tests/test_db_registry.py`
  - `tests/test_db_registry_edge_cases.py`
  - `tests/test_db_registry_spec_features.py`
  - `tests/test_db_registry_migration.py`
  - `tests/test_db_registry_fastapi_integration.py`

### Docs State
- Root README rewritten for quick-start usage style.
- DB usage guide rewritten:
  - `src/registers/db/USAGE.md`
- Package naming drift normalized (`decorators` -> `registers`) in active docs/code.

## `ecommerce-backend-example` Summary

### Scope Used
- Ignored `test.py` and `command.py` intentionally.
- Used:
  - `app.py`
  - `models.py`
  - `db/ecommerce.sql`
  - `config.py`

### Implemented Changes
- Replaced `app.py` with a more robust FastAPI API layer using existing model schema.
- Added stronger request/response contracts and endpoint validation.
- Added richer ecommerce workflows:
  - customers, addresses, payment methods, products, categories, tags, product attachments, reviews.
  - checkout flow that creates `orders`, `order_items`, `order_payments` with stock checks.
  - list/detail endpoints with pagination/sorting.
  - admin schema/status/truncate endpoints.
- Improved lifecycle behavior:
  - create schemas on startup.
  - dispose engines on shutdown.
  - no destructive drop-on-shutdown.

### Critical Fix
- `config.py` now normalizes DB values to SQLite URLs and resolves relative paths against project directory.
- This fixed `sqlite3.OperationalError: unable to open database file` during app import/boot.

### Verification Performed
- Syntax compile:
  - `python -m py_compile app.py models.py config.py`
- Import smoke test:
  - `import app` succeeded with title `Ecommerce API (registers.db)`.

## Next High-Value Steps

1. Add integration tests for ecommerce checkout consistency:
   - stock decrement correctness
   - partial-failure compensation behavior
   - payment/order/item coherence
2. Add explicit relation ownership checks in more routes (customer-scoped list/detail patterns).
3. Add API pagination metadata envelope (`total`, `limit`, `offset`) where useful.
4. Add OpenAPI tags/examples for endpoint discoverability.

## Quick Restart Commands

### `cli_framework`
- `cd C:\Users\charl\Documents\Python\cli_framework`
- `pytest -q`

### `ecommerce-backend-example`
- `cd C:\Users\charl\Documents\Python\ecommerce-backend-example`
- `python main.py`

