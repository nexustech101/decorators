"""
Public module-level decorators for ``functionals.cli``.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from functionals.cli.registry import CommandRegistry, MISSING

_default_registry = CommandRegistry()


def argument(
    name: str,
    *,
    type: Any = str,
    help: str = "",
    default: Any = MISSING,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Declare an argument spec for a command function."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        _default_registry.stage_argument(
            fn,
            name,
            arg_type=type,
            help_text=help,
            default=default,
        )
        return fn

    return decorator


def option(
    flag: str,
    *,
    help: str = "",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Declare a command alias token, for example ``--add`` or ``-a``."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        _default_registry.stage_option(fn, flag, help_text=help)
        return fn

    return decorator


def register(
    name: str | None = None,
    *,
    description: str = "",
    help: str = "",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Finalize a staged command and register it in the default registry."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        _default_registry.finalize_command(
            fn,
            name=name,
            description=description,
            help_text=help,
        )
        return fn

    return decorator


def run(argv: Sequence[str] | None = None, *, print_result: bool = True) -> Any:
    """Run the module-level default registry."""

    return _default_registry.run(argv, print_result=print_result)


def run_shell(
    *,
    print_result: bool = True,
    prompt: str = "cli> ",
    program_name: str | None = None,
    input_fn: Callable[[str], str] | None = None,
) -> None:
    """Run the module-level default registry in interactive mode."""

    return _default_registry.run_shell(
        print_result=print_result,
        prompt=prompt,
        program_name=program_name,
        input_fn=input_fn,
    )


def list_commands() -> None:
    """Print commands registered on the module-level default registry."""

    _default_registry.list_commands()


def get_registry() -> CommandRegistry:
    """Return the module-level default registry instance."""

    return _default_registry


def reset_registry() -> None:
    """Clear the module-level default registry (useful for tests)."""

    _default_registry.clear()
