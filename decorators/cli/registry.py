"""
The CommandRegistry stores command metadata and provides the @register
decorators. It is intentionally decoupled from argparse and dispatching —
it only knows about *what* commands exist, not *how* to invoke them.

Usage::

    registry = CommandRegistry()

    @registry.register("greet", help_text="Greet someone")
    def greet(name: str) -> str:
        return f"Hello, {name}!"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Sequence

from decorators.cli.exceptions import DuplicateCommandError, UnknownCommandError

if TYPE_CHECKING:
    from decorators.cli.middleware import MiddlewareChain
    from decorators.cli.container import DIContainer


@dataclass
class CommandEntry:
    """All metadata the framework needs for a single command."""
    name: str
    handler: Callable[..., Any]
    help_text: str = ""
    description: str = ""
    ops: tuple[str, ...] = field(default_factory=tuple)


class CommandRegistry:
    """
    Maps command names to their handlers and metadata.

    Registries can be merged to support modular / plugin-based apps.
    """

    def __init__(self) -> None:
        self._commands: dict[str, CommandEntry] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        name: str | None = None,
        *,
        help_text: str = "",
        description: str = "",
        ops: Sequence[str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorators that registers a callable as a CLI command.

        Args:
            name:      The subcommand name used on the CLI.
            help_text: Short description shown in --help output.
            description: Longer description for docs / help output.
            ops: Optional command aliases such as ``["-g", "--greet"]``.

        Raises:
            DuplicateCommandError: If *name* is already registered.
        """
        if name is None:
            raise TypeError("register() missing required argument: 'name'")

        summary = description or help_text
        normalized_ops = tuple(ops or ())

        def decorators(fn: Callable[..., Any]) -> Callable[..., Any]:
            if name in self._commands:
                raise DuplicateCommandError(name)
            self._commands[name] = CommandEntry(
                name=name,
                handler=fn,
                help_text=summary,
                description=description,
                ops=normalized_ops,
            )
            return fn

        return decorators

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, name: str) -> CommandEntry:
        """
        Return the entry for *name*.

        Raises:
            UnknownCommandError: If *name* has not been registered.
        """
        if name not in self._commands:
            raise UnknownCommandError(name)
        return self._commands[name]

    def all(self) -> dict[str, CommandEntry]:
        """Return a shallow copy of the command map."""
        return dict(self._commands)

    def has(self, name: str) -> bool:
        """Return True if *name* is registered."""
        return name in self._commands

    def list_clis(self) -> None:
        """Print the registered commands and any configured aliases."""
        if not self._commands:
            print("No commands registered.")
            return

        print("Available commands:")
        for entry in self._commands.values():
            aliases = f" [{', '.join(entry.ops)}]" if entry.ops else ""
            summary = entry.help_text or entry.description or "(no description)"
            print(f"  {entry.name}{aliases}: {summary}")

    def run(
        self,
        argv: Sequence[str] | None = None,
        *,
        container: "DIContainer | None" = None,
        middleware: "MiddlewareChain | None" = None,
        print_result: bool = True,
    ) -> Any:
        """
        Parse CLI arguments and dispatch the matching command.

        This is a convenience wrapper around ``build_parser`` and
        ``Dispatcher`` for small scripts that don't need a custom
        bootstrap module.
        """
        import sys

        from decorators.cli.dispatcher import Dispatcher
        from decorators.cli.parser import build_parser
        from decorators.cli.container import DIContainer

        parser = build_parser(self, container)
        raw_argv = list(sys.argv[1:] if argv is None else argv)
        args = parser.parse_args(self._normalize_argv(raw_argv))

        if not args.command:
            parser.print_help()
            return None

        cli_args = {k: v for k, v in vars(args).items() if k != "command"}
        dispatcher = Dispatcher(self, container or DIContainer(), middleware)
        result = dispatcher.dispatch(args.command, cli_args)

        if print_result and result is not None:
            print(result)

        return result

    def _normalize_argv(self, argv: Sequence[str]) -> list[str]:
        """Map command aliases like ``-g`` or ``--greet`` to the command name."""
        normalized = list(argv)
        if not normalized:
            return normalized

        first = normalized[0]
        alias_map: dict[str, str] = {}
        for entry in self._commands.values():
            for op in entry.ops:
                alias_map[op] = entry.name
                stripped = op.lstrip("-")
                if stripped:
                    alias_map[stripped] = entry.name

        if first in alias_map:
            normalized[0] = alias_map[first]

        return normalized

    # ------------------------------------------------------------------
    # Merging (plugin / modular support)
    # ------------------------------------------------------------------

    def merge(self, other: "CommandRegistry", *, allow_override: bool = False) -> None:
        """
        Merge all commands from *other* into this registry.

        Args:
            other:           The registry to merge in.
            allow_override:  If False (default), raises DuplicateCommandError
                             on name collisions. If True, *other* wins.
        """
        for name, entry in other.all().items():
            if name in self._commands and not allow_override:
                raise DuplicateCommandError(name)
            self._commands[name] = entry

    def __len__(self) -> int:
        return len(self._commands)

    def __repr__(self) -> str:
        names = ", ".join(self._commands)
        return f"CommandRegistry([{names}])"
