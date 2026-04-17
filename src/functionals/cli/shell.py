"""
Interactive REPL shell for ``functionals.cli`` command registries.
"""

from __future__ import annotations

from collections.abc import Callable
import logging
from pathlib import Path
import shlex
import sys
from typing import Any

from functionals.cli.exceptions import CommandExecutionError, FrameworkError, UnknownCommandError
from functionals.cli.parser import ParseError, parse_command_args, render_command_usage
from functionals.cli.registry import HELP_ALIASES

logger = logging.getLogger(__name__)

class InteractiveShell:
    """Run an interactive command loop against a :class:`CommandRegistry`."""

    def __init__(
        self,
        registry: Any,
        *,
        print_result: bool = True,
        prompt: str = "cli> ",
        program_name: str | None = None,
        input_fn: Callable[[str], str] | None = None,
    ) -> None:
        self._registry = registry
        self._print_result = print_result
        self._prompt = prompt
        self._program_name = program_name or Path(sys.argv[0]).name or "app.py"
        self._input_fn = input_fn or input

    def run(self) -> None:
        print(
            f"Interactive mode. Type 'help' for commands, 'commands' to list "
            f"registered commands, or 'exit' to quit."
        )

        while True:
            raw = self._read_line()
            if raw is None:
                return

            line = raw.strip()
            if not line:
                continue

            tokens = self._tokenize(line)
            if tokens is None:
                continue

            if self._handle_shell_builtin(tokens):
                return

            self._dispatch(tokens)

    def _read_line(self) -> str | None:
        try:
            return self._input_fn(self._prompt)
        except EOFError:
            print()
            return None
        except KeyboardInterrupt:
            print()
            return ""

    @staticmethod
    def _tokenize(line: str) -> list[str] | None:
        try:
            return shlex.split(line)
        except ValueError as exc:
            print(f"Error: {exc}")
            return None

    def _handle_shell_builtin(self, tokens: list[str]) -> bool:
        token = tokens[0]
        if token in {"exit", "quit"}:
            if len(tokens) > 1:
                print(f"Error: '{token}' does not take arguments.")
                return False
            return True

        if token == "commands":
            if len(tokens) > 1:
                print("Error: 'commands' does not take arguments.")
                return False
            self._registry.list_commands()
            return False

        if token in HELP_ALIASES:
            if len(tokens) > 2:
                print("Error: help accepts at most one command name.")
                return False

            if len(tokens) == 2:
                target = tokens[1]
                try:
                    self._registry.print_help(target, program_name=self._program_name)
                except UnknownCommandError:
                    suggestion = self._registry.suggest(target)
                    if suggestion:
                        print(f"Did you mean '{suggestion}'?")
                    else:
                        print(f"Unknown command '{target}'.")
                return False

            self._registry.print_help(program_name=self._program_name)
            return False

        return False

    def _dispatch(self, tokens: list[str]) -> None:
        command_token = tokens[0]

        try:
            entry = self._registry.get(command_token)
        except UnknownCommandError:
            suggestion = self._registry.suggest(command_token)
            if suggestion:
                print(f"Did you mean '{suggestion}'?")
            else:
                print("Unknown command")
            return

        try:
            kwargs = parse_command_args(entry, tokens[1:])
        except ParseError as exc:
            print(f"Error: {exc}")
            print(render_command_usage(entry, program_name=self._program_name))
            return

        try:
            result = entry.handler(**kwargs)
        except FrameworkError as exc:
            print(f"Error: {exc}")
            return
        except Exception as exc:
            logger.exception("Unhandled command failure in shell for '%s'.", entry.name)
            wrapped = CommandExecutionError(entry.name, str(exc))
            print(f"Error: {wrapped}")
            return

        if self._print_result and result is not None:
            print(result)
