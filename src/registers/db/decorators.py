"""
Module-level decorator surface for registers.db.

This stays backward-compatible by delegating to a default registry coordinator.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, TypeVar

from pydantic import BaseModel

from registers.db.registry import DatabaseRegistry

ModelT = TypeVar("ModelT", bound=BaseModel)

_DEFAULT_DB_REGISTRY = DatabaseRegistry()


def database_registry(
    database_url: str | Path | None = None,
    *,
    table_name: str | None = None,
    key_field: str = "id",
    manager_attr: str = "objects",
    auto_create: bool = True,
    autoincrement: bool = False,
    unique_fields: list[str] | tuple[str, ...] = (),
) -> Callable[[type[ModelT]], type[ModelT]]:
    """
    Decorate a Pydantic model and attach persistence manager as ``Model.objects``.

    Backed by a module-level default ``DatabaseRegistry`` coordinator.
    """
    return _DEFAULT_DB_REGISTRY.database_registry(
        database_url=database_url,
        table_name=table_name,
        key_field=key_field,
        manager_attr=manager_attr,
        auto_create=auto_create,
        autoincrement=autoincrement,
        unique_fields=unique_fields,
    )
