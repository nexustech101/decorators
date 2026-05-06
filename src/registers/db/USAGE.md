<div align="center">

# `registers.db`

**Pydantic-first persistence layer with registry/manager ergonomics, schema helpers, query operators, and application-ready integration patterns.**

[![Module](https://img.shields.io/badge/module-registers.db-5C6BC0?style=for-the-badge)](#) [![Type](https://img.shields.io/badge/type-Persistence%20Layer-1F2937?style=for-the-badge)](#) [![Modeling](https://img.shields.io/badge/modeling-Pydantic--First-0F766E?style=for-the-badge)](#) [![Engine](https://img.shields.io/badge/powered%20by-SQLAlchemy-7C3AED?style=for-the-badge)](#) [![Patterns](https://img.shields.io/badge/patterns-Registry%20%7C%20Manager-9333EA?style=for-the-badge)](#) [![Maturity](https://img.shields.io/badge/status-Production%20Guide-2563EB?style=for-the-badge)](#)

</div>

## Tags

`Pydantic Models` `Manager API` `CRUD` `Query Operators` `Bulk Operations` `Schema Evolution` `Relationships` `FastAPI Integration`

> **Positioning:** Use `registers.db` when you want a lightweight persistence abstraction that preserves Pydantic-centered development while still exposing operationally useful database primitives.

---

`registers.db` is a Pydantic-first persistence layer powered by SQLAlchemy engines and a registry/manager pattern. It lets you define data as Pydantic models and persist, query, evolve, and integrate those models without writing full ORM mapping boilerplate.

This refactored manual is designed for backend engineers, FastAPI developers, library maintainers, and AI coding agents that need complete usage guidance for the public API.

## Audience

Use this manual if you are:

- registering Pydantic models as database-backed records;
- building FastAPI services with a manager-style persistence API;
- using query operators, upserts, bulk writes, relationships, or schema helpers;
- designing test-isolated registries;
- documenting safe lifecycle, error, and security practices.

## Operating Model

`registers.db` centers on one concept: a registered Pydantic model receives a manager object, usually `Model.objects`, that owns persistence operations.

| Layer | Responsibility |
|---|---|
| Model | Pydantic schema and validation. |
| Registry | Model-to-table binding, engine ownership, metadata validation. |
| Manager | CRUD, queries, upserts, bulk operations, schema helpers, transactions. |
| Integration | FastAPI lifecycle, exception mapping, service-layer composition. |

## Production Contract

A production service should define:

- explicit `table_name`, `key_field`, and uniqueness rules;
- stable manager naming, usually `objects`;
- startup-safe schema lifecycle checks;
- exception handlers for user-facing HTTP boundaries;
- explicit disposal at shutdown/test teardown;
- service-layer invariants for multi-record writes;
- clear policy around automatic password hashing and response serialization.

---
## What Is registers.db?

`registers.db` is a persistence layer for **Pydantic models**, powered by SQLAlchemy engines and a registry/manager pattern. Define your data as Pydantic classes. Persist, query, and evolve them through a clean manager API — with zero ORM boilerplate.

```python
from pydantic import BaseModel
from registers import database_registry

@database_registry("sqlite:///app.db", table_name="users", unique_fields=["email"])
class User(BaseModel):
    id: int | None = None
    email: str
    name: str

user = User.objects.create(email="alice@example.com", name="Alice")
user.name = "Alicia"
user.save()
```

That's it. No base classes to inherit. No metaclass magic. No mappers to configure.

---

## Feature Highlights

| Capability | Details |
|---|---|
| 🏗 **Declarative registration** | `@database_registry(...)` decorator wires models to tables |
| 🔍 **Expressive query operators** | `field__gte`, `field__in`, `field__ilike`, `field__between`, and more |
| 🔄 **Upsert & bulk ops** | `bulk_create`, `bulk_upsert`, key/constraint-aware upserts |
| 🔒 **Password hashing** | Auto-hashes `password` fields on write; `verify_password()` injected on instances |
| 🔗 **Relationships** | `HasMany`, `BelongsTo`, `HasManyThrough` — lazy, safe, read-optimized |
| 📐 **Schema evolution** | `ensure_column`, `add_column`, `rename_table` — additive and startup-safe |
| 🚨 **Structured exceptions** | Every error carries `.context` and `.to_dict()` for observability |
| ⚡ **FastAPI-ready** | Lifespan hooks, exception handlers, and service-layer patterns included |

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
  - [Decorator Mode](#decorator-mode)
  - [Instance Registry Mode](#instance-registry-mode)
- [Model Registration](#model-registration)
- [Field Metadata with `db_field`](#field-metadata-with-db_field)
- [CRUD API](#crud-api)
- [Querying, Sorting & Pagination](#querying-sorting--pagination)
- [Upsert & Identity Rules](#upsert--identity-rules)
- [Bulk Operations](#bulk-operations)
- [Schema Lifecycle & Evolution](#schema-lifecycle--evolution)
- [Relationships](#relationships)
- [Password Security](#password-security)
- [Transactions & Engine Lifecycle](#transactions--engine-lifecycle)
- [FastAPI Integration](#fastapi-integration)
- [Exception Model](#exception-model)
- [Ecommerce Blueprint](#ecommerce-blueprint)
- [Public API Reference](#public-api-reference)

---

## Installation

```bash
pip install registers
```

**Core imports:**

```python
from pydantic import BaseModel
from registers import (
    database_registry,
    DatabaseRegistry,
    db_field,
    HasMany,
    BelongsTo,
    HasManyThrough,
    dispose_all,
)
```

---

## Quick Start

### Decorator Mode

The fastest path from model to database. Ideal for single-surface services with minimal wiring.

```python
from pydantic import BaseModel
from registers import database_registry

@database_registry(
    "sqlite:///app.db",
    table_name="users",
    key_field="id",
    unique_fields=["email"],
)
class User(BaseModel):
    id: int | None = None
    email: str
    name: str

# Create
created = User.objects.create(email="alice@example.com", name="Alice")

# Fetch — raises RecordNotFoundError if missing
fetched = User.objects.require(created.id)

# Update
fetched.name = "Alicia"
fetched.save()

# Delete
fetched.delete()
```

> `id` is DB-generated when `autoincrement` policy applies. `save()` uses upsert semantics.

---

### Instance Registry Mode

Preferred when you need explicit registry ownership, isolated model sets, or test scoping.

```python
from pydantic import BaseModel
from registers import DatabaseRegistry

db = DatabaseRegistry()

@db.database_registry(
    "sqlite:///app.db",
    table_name="users",
    key_field="id",
    autoincrement=True,
    unique_fields=["email"],
)
class User(BaseModel):
    id: int | None = None
    email: str
    name: str

user = User.objects.create(email="alice@example.com", name="Alice")
```

Create one `DatabaseRegistry()` per DB namespace. Behaviors are identical to module-level `@database_registry(...)`.

---

## Model Registration

### Decorator Signature

```python
@database_registry(
    database_url="sqlite:///app.db",   # bare path also accepted
    table_name="users",
    key_field="id",
    manager_attr="objects",            # default; must not collide with fields
    auto_create=True,
    autoincrement=False,               # auto-enables for id: int | None
    unique_fields=["email"],
)
class User(BaseModel):
    ...
```

### Defaults

| Option | Default |
|---|---|
| `table_name` | snake_case pluralized model name |
| `database_url` | SQLite file derived from table name |
| `manager_attr` | `"objects"` |
| `auto_create` | `True` (defers unresolved FK DDL) |

### Primary Key Policy

| Field Type | Behavior |
|---|---|
| `id: int \| None = None` + autoincrement | DB-managed; `None` on create |
| `id: int` | Caller-supplied; required on create |

> **Violations:** Assigning a DB-managed key on create raises `InvalidPrimaryKeyAssignmentError`. Mutating a persisted key then saving raises `ImmutableFieldError`.

### Validation Rules

- Class must be a `pydantic.BaseModel` subclass
- `key_field` must exist on the model
- `manager_attr` must not collide with model fields or attributes
- `unique_fields` must reference valid fields with no duplicates
- `autoincrement=True` requires an integer key field that allows `None`

---

## Field Metadata with `db_field`

Attach DB metadata directly at field definition for index, unique, and foreign key behavior.

```python
from pydantic import BaseModel
from registers import database_registry, db_field

@database_registry("sqlite:///app.db", table_name="accounts", key_field="id")
class Account(BaseModel):
    id: int | None = None
    email: str = db_field(unique=True, index=True)
    manager_id: int | None = db_field(foreign_key="users.id", default=None)
```

### Supported Metadata Flags

| Flag | Type | Notes |
|---|---|---|
| `primary_key` | `bool` | Must align with configured `key_field` |
| `autoincrement` | `bool` | Non-key usage is rejected |
| `unique` | `bool` | Merges into `unique_fields` config |
| `index` | `bool` | Creates a DB index |
| `foreign_key` | `str` | Must use `"table.column"` format |

---

## CRUD API

All persistence operations live on `Model.objects`. Instance methods are convenience wrappers only.

### Write Operations

```python
Model.objects.create(**data)
Model.objects.strict_create(**data)          # alias of create
Model.objects.upsert(instance | **data)
Model.objects.save(instance)
Model.objects.update_where(criteria, **updates)
Model.objects.delete(key_value)
Model.objects.delete_where(**criteria)
Model.objects.bulk_create(list[dict])
Model.objects.bulk_upsert(list[dict])
```

### Read Operations

```python
Model.objects.get(pk_or_criteria)
Model.objects.require(pk_or_criteria)        # raises RecordNotFoundError if missing
Model.objects.filter(...)
Model.objects.all(...)
Model.objects.get_all()
Model.objects.exists(**criteria)
Model.objects.count(**criteria)
Model.objects.first(...)
Model.objects.last(...)
Model.objects.refresh(instance)
```

### Instance Helpers

```python
instance.save()
instance.delete()
instance.refresh()
instance.verify_password(raw)               # only on models with a password field
```

### Schema Helpers (class-level)

```python
Model.create_schema()
Model.schema_exists()
Model.truncate()
Model.drop_schema()
```

---

## Querying, Sorting & Pagination

Filters use `field__operator=value` syntax and are strongly validated at query time.

### Operators

| Operator | Example |
|---|---|
| `eq` (default) | `status="active"` |
| `not` | `status__not="banned"` |
| `gt`, `gte`, `lt`, `lte` | `age__gte=18` |
| `like`, `ilike` | `name__ilike="ali%"` |
| `in`, `not_in` | `status__in=["active", "trial"]` |
| `is_null` | `deleted_at__is_null=True` |
| `between` | `score__between=(70, 100)` |
| `contains`, `startswith`, `endswith` | `name__startswith="Al"` |

```python
User.objects.filter(age__gte=18, age__lt=65)
User.objects.filter(status__in=["active", "trial"])
User.objects.filter(deleted_at__is_null=True)
User.objects.filter(score__between=(70, 100))
User.objects.filter(name__ilike="ali%")
```

### Sorting

```python
User.objects.filter(order_by="name")           # ascending
User.objects.filter(order_by="-created_at")    # descending
User.objects.all(order_by=["role", "-name"])   # multi-column
```

### Pagination

```python
User.objects.filter(order_by="id", limit=20, offset=40)
```

> **Validation:** Unknown fields/operators raise `InvalidQueryError`. Iterable equality values are rejected — use `id__in=[1, 2]` instead of `id=[1, 2]`. Both `limit` and `offset` must be `>= 0`.

---

## Upsert & Identity Rules

```python
@database_registry("sqlite:///app.db", table_name="users", unique_fields=["email"])
class User(BaseModel):
    id: int | None = None
    email: str
    name: str

User.objects.create(email="alice@example.com", name="Alice")

# Resolves by unique_fields when key is absent
updated = User.objects.upsert(email="alice@example.com", name="Alicia")
```

**Upsert resolution order:**

1. If key is present → upsert by key
2. If autoincrement key is absent and `unique_fields` is configured → upsert by unique conflict key
3. Otherwise → falls back to create path

Persisted primary keys are **immutable** after first write.

---

## Bulk Operations

Optimized for service-layer write batches with normalized error behavior.

```python
rows = User.objects.bulk_create([
    {"email": "a@example.com", "name": "A"},
    {"email": "b@example.com", "name": "B"},
])

rows = User.objects.bulk_upsert([
    {"id": 1, "email": "a@example.com", "name": "A+"},
    {"id": 3, "email": "c@example.com", "name": "C"},
])
```

- Empty list input returns `[]`
- Integrity violations raise normalized DB exceptions
- Operations execute inside engine transaction contexts

---

## Schema Lifecycle & Evolution

### Class-Level Schema Control

```python
User.create_schema()
User.schema_exists()
User.truncate()
User.drop_schema()
```

### Manager-Level Evolution Helpers

```python
# Idempotent — safe to call at every startup
created: bool = User.objects.ensure_column("timezone", str, nullable=True)

# Explicit — fails if column already exists
User.objects.add_column("timezone", str, nullable=True)

# Rebinds manager state; subsequent .objects calls use new table immediately
User.objects.rename_table("users_archive")

columns: list[str] = User.objects.column_names()
```

> **Prefer `ensure_column`** for startup-safe idempotent migrations. Use `add_column` when you explicitly want failure on pre-existing columns.

---

## Relationships

Define relationship descriptors **after** class decoration. All relationships are lazy-loaded and read-only.

```python
from pydantic import BaseModel
from registers import DatabaseRegistry, HasMany, BelongsTo, HasManyThrough

DB = "sqlite:///app.db"
db = DatabaseRegistry()

@db.database_registry(DB, table_name="authors")
class Author(BaseModel):
    id: int | None = None
    name: str

@db.database_registry(DB, table_name="posts")
class Post(BaseModel):
    id: int | None = None
    author_id: int | None = None
    title: str

@db.database_registry(DB, table_name="tags")
class Tag(BaseModel):
    id: int | None = None
    name: str

@database_registry(DB, table_name="post_tags")
class PostTag(BaseModel):
    id: int | None = None
    post_id: int
    tag_id: int

# Wire relationships after decoration
Author.posts = HasMany(Post, foreign_key="author_id")
Post.author  = BelongsTo(Author, local_key="author_id")
Post.tags    = HasManyThrough(Tag, through=PostTag, source_key="post_id", target_key="tag_id")
```

| Descriptor | Behavior |
|---|---|
| `HasMany` | Returns a list; null FK resolves to `[]` |
| `BelongsTo` | Returns a single instance; null FK resolves to `None` |
| `HasManyThrough` | Joins through a pivot model; deduplicates repeated IDs |

---

## Password Security

Models with a field literally named `password` get automatic hash-on-write behavior. No configuration required.

```python
@database_registry("sqlite:///app.db", table_name="accounts")
class Account(BaseModel):
    id: int | None = None
    email: str
    password: str

acct = Account.objects.create(email="alice@example.com", password="secret123")

assert acct.password != "secret123"    # stored as hash
assert acct.verify_password("secret123")
```

**Hashing applies automatically to:** `create`, `strict_create`, `upsert`, `save`, `update_where`

**Standalone helpers:**

```python
from registers import hash_password, is_password_hash, verify_password

hashed = hash_password("secret123")
is_password_hash(hashed)               # True
verify_password("secret123", hashed)   # True
```

---

## Transactions & Engine Lifecycle

### Explicit Transactions

Use `transaction()` for low-level grouped SQL work that needs explicit control. Standard manager methods open their own transaction contexts and do not need wrapping.

```python
from sqlalchemy import text

with User.objects.transaction() as conn:
    conn.execute(
        text("UPDATE users SET name = :name WHERE id = :id"),
        {"name": "Alicia", "id": 1}
    )
```

### Engine Notes

- Engines are cached per database URL
- SQLite file engines enable WAL mode and enforce foreign keys automatically
- In-memory SQLite uses a shared static pool for process-local visibility

### Disposal

```python
User.objects.dispose()    # dispose one manager's engine

from registers import dispose_all
dispose_all()             # global cleanup — use at app shutdown / test teardown
```

---

## FastAPI Integration

### Lifespan Pattern

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not User.schema_exists():
        User.create_schema()
    yield
    User.objects.dispose()

app = FastAPI(lifespan=lifespan)
```

### Exception Mapping

```python
from fastapi.responses import JSONResponse
from registers import RecordNotFoundError, UniqueConstraintError, RegistryError

@app.exception_handler(UniqueConstraintError)
async def unique_error(_req, _exc):
    return JSONResponse(status_code=409, content={"detail": "Unique constraint violation"})

@app.exception_handler(RecordNotFoundError)
async def not_found_error(_req, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(RegistryError)
async def registry_error(_req, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
```

### Route Pattern

```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return User.objects.require(user_id)          # auto-raises 404 on miss

@app.patch("/users/{user_id}")
async def update_user(user_id: int, payload: UserUpdate):
    user = User.objects.require(user_id)
    user.name = payload.name
    user.save()
    return user
```

---

## Exception Model

Every exception inherits from `RegistryError` and carries `.context` and `.to_dict()` for structured observability.

```python
try:
    User.objects.require(email="missing@example.com")
except RecordNotFoundError as exc:
    payload = exc.to_dict()
    logger.error("record_not_found", extra=payload)
```

### Exception Reference

| Exception | Trigger |
|---|---|
| `ConfigurationError` | Invalid registry/model configuration |
| `ModelRegistrationError` | Registration contract violation |
| `SchemaError` | DDL failure |
| `MigrationError` | Column evolution failure |
| `RelationshipError` | Invalid relationship definition |
| `DuplicateKeyError` | Primary key collision |
| `InvalidPrimaryKeyAssignmentError` | Assigning a DB-managed key on create |
| `ImmutableFieldError` | Mutating a persisted primary key |
| `UniqueConstraintError` | Unique constraint violation |
| `RecordNotFoundError` | `require(...)` finds no match |
| `InvalidQueryError` | Unknown field, operator, or invalid value shape |

---

## Ecommerce Blueprint

A reference architecture for multi-entity API services.

### `models.py`

```python
from pydantic import BaseModel
from registers import DatabaseRegistry

DB = "sqlite:///ecommerce.db"
db = DatabaseRegistry()

@db.database_registry(DB, table_name="customers", key_field="id", unique_fields=["email"])
class Customer(BaseModel):
    id: int | None = None
    name: str
    email: str
    password: str
    created_at: str
    updated_at: str

@db.database_registry(DB, table_name="products", key_field="id")
class Product(BaseModel):
    id: int | None = None
    name: str
    price: float
    stock: int
    created_at: str
    updated_at: str

@db.database_registry(DB, table_name="orders", key_field="id")
class Order(BaseModel):
    id: int | None = None
    customer_id: int
    total_amount: float
    created_at: str
    updated_at: str
```

### `api.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from registers import RecordNotFoundError, UniqueConstraintError, RegistryError
from .models import Customer, Product, Order

MODEL_REGISTRY = [Customer, Product, Order]

@asynccontextmanager
async def lifespan(app: FastAPI):
    for model in MODEL_REGISTRY:
        if not model.schema_exists():
            model.create_schema()
    yield
    for model in MODEL_REGISTRY:
        model.objects.dispose()

app = FastAPI(lifespan=lifespan)
```

### `services/orders.py` — Write Invariants & Compensation

```python
from fastapi import HTTPException
from ..models import Order, Product

def create_order(customer_id: int, items: list[dict], now: str) -> Order:
    snapshots: dict[int, Product] = {}
    total = 0.0

    for item in items:
        product = Product.objects.require(item["product_id"])
        if product.stock < item["quantity"]:
            raise HTTPException(
                status_code=409,
                detail=f"Insufficient stock for product {product.id}"
            )
        snapshots[product.id] = product
        total += product.price * item["quantity"]

    created: Order | None = None
    try:
        created = Order.objects.create(
            customer_id=customer_id,
            total_amount=round(total, 2),
            created_at=now,
            updated_at=now,
        )
        for item in items:
            product = snapshots[item["product_id"]]
            Product.objects.update_where(
                {"id": product.id},
                stock=product.stock - item["quantity"]
            )
        return created
    except Exception as exc:
        if created is not None:
            Order.objects.delete(created.id)
        for product_id, snapshot in snapshots.items():
            Product.objects.update_where({"id": product_id}, stock=snapshot.stock)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

### Endpoint-to-Manager Mapping

| HTTP Operation | Manager Call |
|---|---|
| `POST /customers` | `Customer.objects.create(...)` |
| `GET /customers/{id}` | `Customer.objects.require(id)` |
| `PATCH /customers/{id}` | mutate instance → `instance.save()` |
| `DELETE /customers/{id}` | `instance.delete()` |
| `GET /products` | `Product.objects.filter(order_by="-id", limit=..., offset=..., **filters)` |
| `POST /orders/checkout` | service layer: `require` + `create` + `update_where` + compensation |
| `GET /orders/{id}` | `Order.objects.require(id)` + child collections via `filter(...)` |

**Building filter dicts for optional criteria:**

```python
filters = {}
if min_price is not None:
    filters["price__gte"] = min_price
if category is not None:
    filters["category__eq"] = category

rows = Product.objects.filter(
    order_by="-id",
    limit=limit,
    offset=offset,
    **filters,
)
```

> Always build a `filters` dict before spreading — never pass `None` values as operator arguments.

### Smoke Test Runbook

```bash
# Start the server
uvicorn app.api:app --host 127.0.0.1 --port 8000 --reload

# Health check
curl http://127.0.0.1:8000/health

# Create a customer
curl -X POST http://127.0.0.1:8000/customers \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"secret123"}'

# Paginated product list
curl "http://127.0.0.1:8000/products?limit=20&offset=0"
```

**Expected outcomes:** health returns a success payload · customer create returns the record without a raw password · product list respects pagination and optional filters.

---

## Architecture Decision Guide

| Scenario | Recommended Pattern |
|---|---|
| Single service, minimal boilerplate | `@database_registry(...)` decorator mode |
| Explicit registry ownership, test isolation | `db = DatabaseRegistry()` instance mode |
| Multi-entity API with lifecycle hooks | Instance registry + lifespan + exception handlers |
| Schema evolution at startup | `ensure_column(...)` in lifespan hook |
| Low-level SQL batching | `Model.objects.transaction()` context manager |

---

## Migration from Legacy Imports

Legacy package names (`functionals`, `decorates`) should be migrated to `registers`. Use the canonical import style consistently:

```python
# ✅ Correct
from registers import database_registry, DatabaseRegistry, db_field

# ❌ Legacy — migrate away
from functionals import ...
from decorates import ...
```

---

<div align="center">

Built with [Pydantic](https://docs.pydantic.dev/) · Powered by [SQLAlchemy](https://www.sqlalchemy.org/)

</div>

---

## Public API Reference

### Top-Level Imports

```python
from registers import (
    database_registry,
    DatabaseRegistry,
    db_field,
    HasMany,
    BelongsTo,
    HasManyThrough,
    dispose_all,
    hash_password,
    is_password_hash,
    verify_password,
)
```

### Registry APIs

| API | Purpose |
|---|---|
| `database_registry(...)` | Module-level decorator for binding a Pydantic model to a table. |
| `DatabaseRegistry()` | Explicit registry object for isolated model sets. |
| `db.database_registry(...)` | Instance-level decorator equivalent to the module-level API. |
| `dispose_all()` | Dispose globally cached engines; useful during shutdown or test teardown. |

### Manager APIs

| Category | Methods |
|---|---|
| Create/update | `create`, `strict_create`, `upsert`, `save`, `update_where` |
| Delete | `delete`, `delete_where` |
| Read | `get`, `require`, `filter`, `all`, `get_all`, `exists`, `count`, `first`, `last`, `refresh` |
| Bulk | `bulk_create`, `bulk_upsert` |
| Schema | `ensure_column`, `add_column`, `rename_table`, `column_names` |
| Transaction/lifecycle | `transaction`, `dispose` |

### Model Helpers

| Helper | Purpose |
|---|---|
| `instance.save()` | Persist changed instance state through manager upsert semantics. |
| `instance.delete()` | Delete the persisted record by primary key. |
| `instance.refresh()` | Reload the persisted record state. |
| `instance.verify_password(raw)` | Verify raw password against stored hash when a model has a `password` field. |
| `Model.create_schema()` | Create the registered table. |
| `Model.schema_exists()` | Check whether the table exists. |
| `Model.truncate()` | Remove table data. |
| `Model.drop_schema()` | Drop the registered table. |

## Production Readiness Checklist

Before deploying a `registers.db` model layer, verify the following:

- [ ] Every registered model has an intentional `table_name`.
- [ ] Primary key behavior is explicit and tested.
- [ ] `unique_fields` or `db_field(unique=True)` is defined for natural identity where upsert is expected.
- [ ] Query filters are validated at service boundaries before being spread into manager calls.
- [ ] Optional filters are built in a dict and omit `None` values.
- [ ] Multi-record business invariants live in a service layer.
- [ ] FastAPI exception handlers map registry errors to stable HTTP responses.
- [ ] Shutdown hooks call `dispose()` or `dispose_all()`.
- [ ] Password hashing behavior is documented in the API layer and raw passwords are never returned in responses.
- [ ] Schema evolution uses idempotent helpers such as `ensure_column(...)` unless failure-on-existing is desired.

## Recommended Positioning

Use `registers.db` as a lightweight persistence layer for Pydantic-centric services, prototypes that need real persistence, internal tools, and FastAPI backends where manager-style CRUD is preferred over direct ORM mapping. For complex transactional domains, highly customized SQL, or advanced migration workflows, keep service-layer boundaries explicit and use lower-level SQLAlchemy transactions where needed.