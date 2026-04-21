from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from dnf_tool.models import AutomationRequest
from dnf_tool.services.automation import AutomationService


LogHandler = Callable[[str], None]
PopupHandler = Callable[[str, str, str], None]
StateHandler = Callable[[bool], None]


class AutomationController:
    """Coordinates UI requests and future automation logic."""

    def __init__(
        self,
        logger: LogHandler,
        popup: PopupHandler,
        set_running_state: StateHandler,
    ) -> None:
        self._logger = logger
        self._service = AutomationService(
            logger=self._log_with_timestamp,
            popup=popup,
            set_running_state=set_running_state,
        )

    def start(self, request: AutomationRequest) -> None:
        self._service.start(request)

    def stop(self) -> None:
        self._service.stop()

    @property
    def is_running(self) -> bool:
        return self._service.is_running

    def _log_with_timestamp(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._logger(f"[{timestamp}] {message}")
