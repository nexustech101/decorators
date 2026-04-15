# Building CLI Tools With `decorates.cli`

`decorates.cli` is now module-first: you define commands with module-level
decorators (`register`, `argument`, `option`) and execute them with `run()`.

## Quick Start

```python
import decorates.cli as cli


@cli.register(description="Greet someone")
@cli.argument("name", type=str, help="Person to greet")
@cli.option("--greet")
@cli.option("-g")
def greet(name: str) -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    cli.run()
```

## Example 2

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

Run it like:

```bash
python app.py greet Alice
python app.py --greet Alice
python app.py -g Alice
python app.py help
python app.py help greet
python app.py --help
python app.py -h
```

## Command Decorators

### `@register(...)`

Finalizes a function as a command.

```python
@cli.register(name="add", description="Add a todo")
```

- `name` is optional.
- If `name` is omitted, the command name is inferred from the first long option
  (`--add` -> `add`).
- If no long option exists, it falls back to the function name.

### `@argument(...)`

Defines command argument metadata.

```python
@cli.argument("title", type=str, help="Todo title")
@cli.argument("description", type=str, default="")
```

- Explicit `@argument` declarations are authoritative for ordering/type/help.
- Any function params without `@argument` still work via annotation/default
  inference.

### `@option(...)`

Adds command aliases.

```python
@cli.option("--add")
@cli.option("-a")
```

These aliases are valid for the command token:

```bash
python todo.py add "Buy groceries"
python todo.py --add "Buy groceries"
python todo.py -a "Buy groceries"
```

## Parsing Behavior

For non-boolean arguments, both positional and named forms are supported:

```bash
python todo.py add "Read a book" "Start to finish"
python todo.py add --title "Read a book" --description "Start to finish"
python todo.py add "Read a book" --description "Start to finish"
```

Boolean arguments are flag-style:

```bash
python app.py run --verbose
```

If the same argument is passed twice with different values, parsing fails.

## Runtime Helpers

- `cli.run(argv=None, print_result=True)` executes the default module registry.
- `cli.list_commands()` prints registered commands and aliases.
- `cli.reset_registry()` clears registry state (useful in tests).
- Built-in help command is always available: `help`, `--help`, and `-h`.

## Error Handling

- Unknown command: prints suggestion when available and exits with status `2`.
- Parse errors: prints a specific error + command usage and exits with status `2`.
- Handler crashes: wrapped as `CommandExecutionError` with exception chaining.
