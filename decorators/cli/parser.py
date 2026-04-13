"""
cli_registry.cli.parser
~~~~~~~~~~~~~~~~~~~~
Builds an ``argparse.ArgumentParser`` from a :class:`CommandRegistry`.

All knowledge of argparse lives here. The rest of the framework never
imports argparse directly. This keeps the parser easily swappable and
the dispatcher clean.
"""

from __future__ import annotations

import argparse
import inspect
from typing import TYPE_CHECKING, Any

from decorators.cli.registry import CommandRegistry
from decorators.cli.utils.reflection import get_params
from decorators.cli.utils.typing import is_bool_flag, is_optional, resolve_argparse_type

if TYPE_CHECKING:
    from decorators.cli.container import DIContainer


def build_parser(
    registry: CommandRegistry,
    container: "DIContainer | None" = None,
) -> argparse.ArgumentParser:
    """
    Construct a top-level ArgumentParser with one subparser per command.

    Parameters whose type is registered in *container* are skipped —
    they are DI-injected at dispatch time and must not appear on the CLI.

    Argument behaviour for everything else:
    * bool              → --flag  (store_true)
    * Optional[X] / default → --arg (optional keyword)
    * required primitive    → positional argument
    """
    parser = argparse.ArgumentParser(
        description="Built with cli_registry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    for name, entry in registry.all().items():
        sub = subparsers.add_parser(
            name,
            help=entry.help_text,
            description=entry.description or entry.help_text,
            aliases=_command_aliases(entry),
        )
        _add_arguments(sub, entry.handler, container)

    return parser


def _add_arguments(
    subparser: argparse.ArgumentParser,
    fn: Any,
    container: "DIContainer | None" = None,
) -> None:
    """Add CLI arguments to *subparser* from *fn*'s signature.

    Service parameters (types known to *container*) are skipped entirely.
    """
    for param in get_params(fn):
        annotation = param.annotation

        # Skip parameters the DI container will inject
        if (
            container is not None
            and annotation is not inspect.Parameter.empty
            and isinstance(annotation, type)
            and container.has(annotation)
        ):
            continue

        # Boolean flags
        if is_bool_flag(annotation):
            subparser.add_argument(
                f"--{param.name}",
                action="store_true",
                default=param.default if param.has_default else False,
                help=f"{param.name} (flag)",
            )
            continue

        arg_type = resolve_argparse_type(annotation)
        optional = param.has_default or is_optional(annotation)

        if optional:
            kwargs: dict[str, Any] = {
                "dest": param.name,
                "default": param.default,
                "help": f"{param.name} (optional)",
            }
            if arg_type is not None:
                kwargs["type"] = arg_type
            subparser.add_argument(f"--{param.name}", **kwargs)
        else:
            kwargs = {"help": param.name}
            if arg_type is not None:
                kwargs["type"] = arg_type
            subparser.add_argument(param.name, **kwargs)


def _command_aliases(entry: Any) -> list[str]:
    """
    Convert metadata aliases into argparse subcommand aliases.

    ``ops`` entries like ``-g`` and ``--greet`` are normalized to ``g``
    and ``greet`` for argparse, while ``registry.run()`` still accepts
    the original flag-style tokens.
    """
    aliases: list[str] = []
    for op in getattr(entry, "ops", ()):
        candidate = op.lstrip("-")
        if candidate and candidate != entry.name and candidate not in aliases:
            aliases.append(candidate)
    return aliases
