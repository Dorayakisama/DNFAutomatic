from __future__ import annotations

import threading
import time
from collections.abc import Callable

from dnf_tool.constants import MATCH_THRESHOLDS, POLL_INTERVALS, RANK_VALUES, TIMEOUTS
from dnf_tool.models import AutomationRequest
from dnf_tool.services.vision import ScreenVisionService


LogHandler = Callable[[str], None]
PopupHandler = Callable[[str, str, str], None]
StateHandler = Callable[[bool], None]


class AutomationService:
    """Runs the image-driven down-rank workflow on a background thread."""

    def __init__(
        self,
        logger: LogHandler,
        popup: PopupHandler,
        set_running_state: StateHandler,
    ) -> None:
        self._logger = logger
        self._popup = popup
        self._set_running_state = set_running_state
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self, request: AutomationRequest) -> None:
        if self.is_running:
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_workflow,
            args=(request,),
            name="dnf-auto-down-rank",
            daemon=True,
        )
        self._set_running_state(True)
        self._thread.start()

    def stop(self) -> None:
        if self.is_running and not self._stop_event.is_set():
            self._logger("Manual stop requested. Finishing the current polling cycle.")
        self._stop_event.set()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run_workflow(self, request: AutomationRequest) -> None:
        vision = ScreenVisionService(logger=self._logger)

        try:
            self._logger("Starting automation workflow.")
            self._logger(f"Target tier: {request.target_tier}")
            self._logger(
                "Additional runs after reaching target tier: "
                f"{request.additional_runs}"
            )
            self._logger(
                "Make sure the game resolution is already configured and the "
                "correct in-game page is visible before the workflow continues."
            )

            missing_resources = vision.validate_resources()
            if missing_resources:
                details = "\n".join(f"- {item}" for item in missing_resources)
                self._logger("Required image resources are missing. Aborting workflow.")
                self._popup(
                    "Missing Resources",
                    "The automation resources are incomplete:\n"
                    f"{details}\n\n"
                    "Add the required images and try again.",
                    "warning",
                )
                return

            remaining_extra_runs = request.additional_runs
            target_value = RANK_VALUES[request.target_tier]

            while not self._stop_event.is_set():
                current_rank = vision.detect_rank(
                    threshold=MATCH_THRESHOLDS["rank"]
                )
                rank_retry = 0
                while current_rank is None and rank_retry < 10 and not self._stop_event.is_set():
                    self._logger(
                        "No rank icon detected. Retrying rank detection "
                        f"(attempt {rank_retry + 1}/10)..."
                    )
                    time.sleep(3.0)
                    current_rank = vision.detect_rank(
                        threshold=MATCH_THRESHOLDS["rank"]
                    )
                    rank_retry += 1
                if current_rank is None:
                    self._logger(
                        "No rank icon was detected on the current screen. "
                        "Terminating auto-down-rank."
                    )
                    self._popup(
                        "Rank Detection Warning",
                        "No rank icon was detected on the current game screen.\n"
                        "The auto-down-rank workflow has been terminated.",
                        "warning",
                    )
                    return

                current_value = RANK_VALUES[current_rank.label]
                self._logger(
                    "Detected current rank: "
                    f"{current_rank.label} (confidence {current_rank.confidence:.3f})."
                )

                if current_value <= target_value:
                    if remaining_extra_runs > 0:
                        completed_count = request.additional_runs - remaining_extra_runs + 1
                        self._logger(
                            "Current rank is at or below the target rank. "
                            f"Running additional match {completed_count}/"
                            f"{request.additional_runs}."
                        )
                        remaining_extra_runs -= 1
                    else:
                        self._logger("Rank down completed.")
                        self._popup(
                            "Completed",
                            "Rank down completed.",
                            "info",
                        )
                        return
                else:
                    self._logger(
                        f"Current rank is above target rank '{request.target_tier}'. "
                        "Proceeding with another match."
                    )

                if not self._attempt_match_start(vision):
                    return

                if not self._wait_for_vs_icon(vision):
                    return

                if not self._wait_for_round_end(vision):
                    return

        except Exception as exc:  # pragma: no cover - runtime safety net
            self._logger(f"Unexpected automation error: {exc}")
            self._popup(
                "Automation Error",
                f"An unexpected error occurred:\n{exc}",
                "error",
            )
        finally:
            self._stop_event.set()
            self._set_running_state(False)

    def _attempt_match_start(self, vision: ScreenVisionService) -> bool:
        attempt = 0
        while not self._stop_event.is_set():
            attempt += 1
            if attempt > 10:
                self._logger(
                    "Failed to start a match after 10 attempts. Aborting workflow."
                )
                return False
            self._logger(f"Step 2: Searching for Start button. Attempt {attempt}.")
            
            start_match = vision.find_system_target(
                name="start",
                threshold=MATCH_THRESHOLDS["system"],
            )
            if start_match is None:
                self._logger(
                    "Warning: Start button was not found on the game screen. "
                    "Retrying..."
                )
                time.sleep(5)
                continue

            vision.click_match(start_match)
            self._logger(
                "Start button clicked. Waiting for 'Matching In Progress'."
            )

            matching_detected = self._wait_for_matching_in_progress(vision)
            if matching_detected:
                return True

            self._logger(
                "'Matching In Progress' was not detected in time. "
                "Retrying from the Start button."
            )

        self._logger("Automation stop requested before match start completed.")
        return False

    def _wait_for_matching_in_progress(self, vision: ScreenVisionService) -> bool:
        deadline = time.monotonic() + TIMEOUTS["matching_in_progress"]
        while not self._stop_event.is_set():
            if vision.find_system_target(
                name="matching_in_progress",
                threshold=MATCH_THRESHOLDS["system"],
            ):
                self._logger("Step 3: 'Matching In Progress' detected.")
                return True

            if time.monotonic() >= deadline:
                return False

            time.sleep(POLL_INTERVALS["matching"])

        return False

    def _wait_for_vs_icon(self, vision: ScreenVisionService) -> bool:
        self._logger("Step 4: Waiting for VS icon.")
        heartbeat_at = time.monotonic() + 3.0

        while not self._stop_event.is_set():
            vs_match = vision.find_system_target(
                name="vs",
                threshold=MATCH_THRESHOLDS["system"],
            )
            if vs_match:
                self._logger("VS icon detected. Match has started.")
                return True

            if time.monotonic() >= heartbeat_at:
                self._logger("Still waiting for VS icon...")
                heartbeat_at = time.monotonic() + 3.0

            time.sleep(POLL_INTERVALS["vs"])

        self._logger("Automation stop requested while waiting for VS icon.")
        return False

    def _wait_for_round_end(self, vision: ScreenVisionService) -> bool:
        self._logger("Step 5: Waiting for round end until a rank icon reappears.")
        heartbeat_at = time.monotonic() + 2.0

        while not self._stop_event.is_set():
            current_rank = vision.detect_rank(
                threshold=MATCH_THRESHOLDS["rank"]
            )
            if current_rank:
                self._logger(
                    "Rank icon reappeared. Round finished with detected rank "
                    f"{current_rank.label}."
                )
                # time.sleep(1.0)  # brief pause to allow any end-of-round animations to finish
                return True

            if time.monotonic() >= heartbeat_at:
                self._logger("Still waiting for the round to finish...")
                heartbeat_at = time.monotonic() + 2.0

            time.sleep(POLL_INTERVALS["round_end"])

        self._logger("Automation stop requested while waiting for round end.")
        return False
