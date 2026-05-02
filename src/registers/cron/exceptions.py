"""
Typed cron exceptions with structured context.
"""

from __future__ import annotations

from typing import Any

from registers.core.errors import RegistrationErrorBase


class CronError(RegistrationErrorBase):
    """Base class for cron module errors."""

    DEFAULT_OPERATION: str | None = None

    def __init__(
        self,
        message: str | None = None,
        *,
        operation: str | None = None,
        context: dict[str, Any] | None = None,
        **extra: Any,
    ) -> None:
        resolved_operation = operation if operation is not None else self.DEFAULT_OPERATION
        super().__init__(
            message or self.__class__.__name__,
            operation=resolved_operation,
            module="cron",
            context=context,
            **extra,
        )


class CronRegistrationError(CronError, ValueError):
    """Raised when a cron job cannot be registered due to invalid metadata."""

    DEFAULT_OPERATION = "registration"


class CronTriggerError(CronRegistrationError):
    """Raised when trigger helper input is invalid."""

    DEFAULT_OPERATION = "trigger_validation"


class CronLookupError(CronError, KeyError):
    """Raised when a requested cron job cannot be found."""

    DEFAULT_OPERATION = "lookup"


class CronRuntimeError(CronError, RuntimeError):
    """Raised for cron runtime failures."""

    DEFAULT_OPERATION = "runtime"


class CronWorkspaceError(CronError, ValueError):
    """Raised for invalid workspace/workflow configuration."""

    DEFAULT_OPERATION = "workspace"


class CronWorkspaceRuntimeError(CronRuntimeError):
    """Raised when workflow execution cannot be launched."""

    DEFAULT_OPERATION = "workspace_runtime"


class CronAdapterError(CronRuntimeError):
    """Raised for deployment adapter command and host compatibility failures."""

    DEFAULT_OPERATION = "adapter"
