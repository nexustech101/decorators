# Decorates

Decorator-driven tooling for Python:

- `decorates.cli` for ergonomic command-line apps
- `decorates.db` for Pydantic + SQLAlchemy persistence

The philosophy is simple: minimal setup, predictable behavior, and a fast path to shipping.

## Install

```bash
pip install decorates
```

## Quick Start Guide

1. Build one CLI command with a decorator.
2. Build one DB model with a decorator.
3. Use `Model.objects` for CRUD.

### CLI in 60 seconds

```python
import time
import decorates.cli as cli
import decorates.db as db
from decorates.db import db_field
from pydantic import BaseModel
from enum import Enum


DATABASE = "todos.db"
TABLE_NAME = "todos"

class TodoStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"

@db.database_registry(
    DATABASE,
    table_name=TABLE_NAME,
    key_field="id"
)
class TodoItem(BaseModel):
    id: int | None = None  # Required id=None for autoincrement
    title: str = db_field(index=True)
    description: str = db_field(default="")
    status: TodoStatus = db_field(default=TodoStatus.PENDING.value)
    created_at: str = db_field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = db_field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


@cli.register(description="Add a new todo item")
@cli.argument("title", type=str, help="Title of the todo item")
@cli.argument("description", type=str, help="Description of the todo item", default="")
@cli.option("--add", help="Add a new todo item")
@cli.option("-a", help="Add a new todo item")
def add_todo(title: str, description: str = "") -> str:
    todo = TodoItem(title=title, description=description)
    todo.save()
    return f"Added todo: {todo.title} (ID: {todo.id})"

@cli.register(description="List all todo items")
@cli.option("--list", help="List all todo items")
@cli.option("-l", help="List all todo items")
def list_todos() -> str:
    todos = TodoItem.objects.all()
    if not todos:
        return "No todo items found."
    return "\n".join([f"{todo.id}: {todo.title} - {todo.status}" for todo in todos])

@cli.register(description="Mark a todo item as completed")
@cli.argument("todo_id", type=int, help="ID of the todo item to mark as completed")
def complete_todo(todo_id: int) -> str:
    todo = TodoItem.objects.get(id=todo_id)

    if not todo:
        return f"Todo item with ID {todo_id} not found."
    
    todo.status = TodoStatus.COMPLETED.value
    todo.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
    todo.save()

    return f"Marked todo ID {todo_id} as completed."

@cli.register(description="Update a todo item")
@cli.argument("todo_id", type=int, help="ID of the todo item to update")
@cli.argument("title", type=str, help="New title of the todo item", default=None)
@cli.argument("description", type=str, help="New description of the todo item", default=None)
@cli.option("--update", help="Update a todo item")
@cli.option("-u", help="Update a todo item")
def update_todo(todo_id: int, title: str = None, description: str = None) -> str:
    todo = TodoItem.objects.get(id=todo_id)

    if not todo:
        return f"Todo item with ID {todo_id} not found."
    
    if title:
        todo.title = title
    if description:
        todo.description = description

    todo.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
    todo.save()

    return f"Updated todo ID {todo_id}."

if __name__ == "__main__":
    cli.run()
```

### Add Todo

```bash
python todo.py add "Buy groceries" "Milk, eggs, bread"
python todo.py --add "Buy groceries" "Milk, eggs, bread"
python todo.py -a "Buy groceries" "Milk, eggs, bread"

python todo.py add --title "Buy groceries" --description "Milk, eggs, bread"
python todo.py --add --title "Buy groceries" --description "Milk, eggs, bread"
```

### List Todos

```bash
python todo.py list
python todo.py --list
python todo.py -l
```

### Complete Todo

```bash
python todo.py complete_todo 1
python todo.py complete_todo --todo_id 1
python todo.py complete_todo --todo-id 1
```

### Update Todo

```bash
python todo.py update 1 "Read two books" "Finish both novels this week"
python todo.py update 1 --title "Read two books" --description "Finish both novels this week"

python todo.py update --todo_id 1 --title "Read two books"
python todo.py update --todo-id 1 --description "Finish both novels this week"
```

### Notes

- Wrap multi-word values in quotes.
- `add` and `list` have aliases (`--add`/`-a`, `--list`/`-l`).
- The function name decorated with `@cli.register(...)` will be used as an option argument if no `@cli.option(...)` is specified.
```

### Database + FastAPI in 5 minutes

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from decorates.db import (
    RecordNotFoundError,
    UniqueConstraintError,
    database_registry,
)

DB_URL = "sqlite:///shop.db"


@database_registry(DB_URL, table_name="customers", unique_fields=["email"])
class Customer(BaseModel):
    id: int | None = None
    name: str
    email: str


@database_registry(DB_URL, table_name="products")
class Product(BaseModel):
    id: int | None = None
    name: str
    price: float


@database_registry(DB_URL, table_name="orders")
class Order(BaseModel):
    id: int | None = None
    customer_id: int
    product_id: int
    quantity: int
    total: float


class CreateCustomer(BaseModel):
    name: str
    email: str


class CreateProduct(BaseModel):
    name: str
    price: float


class CreateOrder(BaseModel):
    customer_id: int
    product_id: int
    quantity: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    for model in (Customer, Product, Order):
        model.create_schema()
    yield
    for model in (Customer, Product, Order):
        model.objects.dispose()


app = FastAPI(lifespan=lifespan)


@app.post("/customers", response_model=Customer, status_code=201)
def create_customer(payload: CreateCustomer):
    try:
        return Customer.objects.create(**payload.model_dump())
    except UniqueConstraintError:
        raise HTTPException(status_code=409, detail="Email already exists")


@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: int):
    try:
        return Customer.objects.require(customer_id)
    except RecordNotFoundError:
        raise HTTPException(status_code=404, detail="Customer not found")


@app.post("/products", response_model=Product, status_code=201)
def create_product(payload: CreateProduct):
    return Product.objects.create(**payload.model_dump())


@app.post("/orders", response_model=Order, status_code=201)
def create_order(payload: CreateOrder):
    customer = Customer.objects.get(payload.customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    product = Product.objects.get(payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return Order.objects.create(
        customer_id=customer.id,
        product_id=product.id,
        quantity=payload.quantity,
        total=product.price * payload.quantity,
    )


@app.get("/orders/desc", response_model=list[Order])
def list_orders_desc(limit: int = 20, offset: int = 0):  # Filter by oldest   (1, 2, 3...n)
    return Order.objects.filter(order_by="id", limit=limit, offset=offset)


@app.get("/orders/asc", response_model=list[Order])
def list_orders_asc(limit: int = 20, offset: int = 0):  # Filter by newest  (n...3, 2, 1)
    return Order.objects.filter(order_by="-id", limit=limit, offset=offset)
```

## Core Concepts

### `decorates.cli`

- Register functions with module-level decorators: `@register`, `@argument`, `@option`.
- Run command handlers through the module registry via `decorates.cli.run()`.
- Support positional + named argument forms (for non-bool args), with bool flags as `--flag`.
- Command aliases are declared with `@option("-x")` / `@option("--long")`.
- Built-in help command is always available: `help`, `--help`, and `-h`.
- Runtime wraps unexpected handler crashes as `CommandExecutionError` (with original exception chaining).
- Operational logs use standard Python logging namespaces under `decorates.cli.*`.

### `decorates.db`

- Register `BaseModel` classes with `@database_registry(...)`.
- Access all persistence through `Model.objects`.
- `id: int | None = None` gives database-managed autoincrement IDs.
- Schema helpers are available as class methods: `create_schema`, `drop_schema`, `schema_exists`, `truncate`.
- Unexpected SQLAlchemy runtime failures are normalized into `SchemaError` for cleaner, predictable error handling.
- Operational logs use standard Python logging namespaces under `decorates.db.*`.
- DB exceptions provide structured metadata (`exc.context`, `exc.to_dict()`) for production diagnostics.

## `decorates.db` Usage Snapshot

```python
# Filtering operators
Order.objects.filter(total__gte=100)
Customer.objects.filter(email__ilike="%@example.com")
Order.objects.filter(quantity__in=[1, 2, 3])

# Sorting and pagination
Order.objects.filter(order_by="-id", limit=20, offset=0)

# Bulk writes
Product.objects.bulk_create([...])
Product.objects.bulk_upsert([...])

# Additive migration helpers
Customer.objects.ensure_column("phone", str | None, nullable=True)
Customer.objects.rename_table("customers_archive")
```

After `rename_table(...)` succeeds, the same `Model.objects` manager and
schema helpers are immediately bound to the new table name.

If your model contains a field named `password`, password values are automatically hashed on write, and instances receive `verify_password(...)`.

## Documentation

- DB guide: `src/decorates/db/USAGE.md`
- CLI source API: `src/decorates/cli`
- DB source API: `src/decorates/db`

## Requirements

- Python 3.10+
- `pydantic>=2.0`
- `sqlalchemy>=2.0`

## Testing

- Default `pytest` includes SQLite plus PostgreSQL/MySQL rename-state integration tests.
- Start Docker Desktop (or another Docker engine) before running tests so
  `docker-compose.test-db.yml` services can boot.
- The decorates is backed by a rigorous, production-focused test suite (170+ tests) that covers unit, edge-case, and multi-dialect integration behavior.

## License

MIT

