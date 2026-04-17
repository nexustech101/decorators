import pytest

import functionals.cli as cli


@pytest.fixture(autouse=True)
def _reset_registry():
    cli.reset_registry()
    yield
    cli.reset_registry()


class _TTYStdin:
    def isatty(self) -> bool:
        return True


class _PipeLikeStdin:
    def isatty(self) -> bool:
        return False


def _input_from_lines(lines: list[str]):
    iterator = iter(lines)
    def _read(_prompt: str) -> str:
        return next(iterator)
    return _read


def _register_interactive_commands() -> None:
    @cli.register(description="Add item")
    @cli.option("--add")
    @cli.argument("title", type=str)
    def add(title: str) -> str:
        return f"added:{title}"

    @cli.register(description="Run")
    @cli.option("--run")
    @cli.argument("verbose", type=bool)
    def run_cmd(verbose: bool = False) -> str:
        return f"verbose={verbose}"


def test_empty_argv_enters_shell_when_tty(monkeypatch):
    monkeypatch.setattr("functionals.cli.registry.sys.stdin", _TTYStdin())

    called: dict[str, object] = {}

    def _fake_run_shell(**kwargs):
        called.update(kwargs)
        return "shell-entered"

    monkeypatch.setattr(cli.get_registry(), "run_shell", _fake_run_shell)

    result = cli.run([], print_result=False)

    assert result == "shell-entered"
    assert called["print_result"] is False


def test_empty_argv_shows_help_when_not_tty(monkeypatch, capsys):
    monkeypatch.setattr("functionals.cli.registry.sys.stdin", _PipeLikeStdin())

    @cli.register(description="Noop")
    @cli.option("--noop")
    def noop() -> None:
        return None

    assert cli.run([], print_result=False) is None
    out = capsys.readouterr().out
    assert "Decorates CLI Help" in out
    assert "noop" in out


def test_interactive_flag_enters_shell(monkeypatch):
    called = {"count": 0}

    def _fake_run_shell(**_kwargs):
        called["count"] += 1
        return None

    monkeypatch.setattr(cli.get_registry(), "run_shell", _fake_run_shell)

    assert cli.run(["--interactive"], print_result=False) is None
    assert cli.run(["-i"], print_result=False) is None
    assert called["count"] == 2


def test_interactive_mode_dispatches_registered_commands(capsys):
    _register_interactive_commands()

    cli.run_shell(
        input_fn=_input_from_lines(
            [
                "add Alpha",
                "--add Beta",
                "add --title Gamma",
                "run",
                "run --verbose",
                "exit",
            ]
        )
    )

    out = capsys.readouterr().out
    assert "added:Alpha" in out
    assert "added:Beta" in out
    assert "added:Gamma" in out
    assert "verbose=False" in out
    assert "verbose=True" in out


def test_interactive_mode_keeps_running_after_parse_and_unknown_errors(capsys):
    _register_interactive_commands()

    cli.run_shell(
        input_fn=_input_from_lines(
            [
                "add",
                "ad",
                "add Working",
                "exit",
            ]
        )
    )

    out = capsys.readouterr().out
    assert "Missing required argument 'title'" in out
    assert "Did you mean 'add'" in out
    assert "added:Working" in out


def test_interactive_mode_supports_shell_local_commands(capsys):
    _register_interactive_commands()

    cli.run_shell(
        input_fn=_input_from_lines(
            [
                "commands",
                "help",
                "help add",
                "quit",
            ]
        ),
        print_result=False,
    )

    out = capsys.readouterr().out
    assert "Available commands:" in out
    assert "Decorates CLI Help" in out
    assert "Command Help: add" in out
