"""
KOVIRX Endpoint Agent — Task Scheduler.

Central orchestrator for all background loops: heartbeat, flow flush,
queue flush, health check, and version check. Each task runs in its own
daemon thread with independent timing and error isolation.
"""

import logging
import threading
import time
from typing import Callable

logger = logging.getLogger("kovirx.agent.scheduler")


class ScheduledTask:
    """Represents a repeating background task with its own thread."""

    def __init__(
        self,
        name: str,
        target: Callable[[], None],
        interval: float,
        initial_delay: float = 0.0,
    ):
        self.name = name
        self.target = target
        self.interval = interval
        self.initial_delay = initial_delay
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.run_count: int = 0
        self.error_count: int = 0
        self.last_run: float | None = None

    def start(self) -> None:
        """Start the scheduled task in a daemon thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("Task '%s' is already running.", self.name)
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name=f"Task-{self.name}",
            daemon=True,
        )
        self._thread.start()
        logger.info("Scheduled task '%s' started (interval=%.1fs)", self.name, self.interval)

    def stop(self) -> None:
        """Signal the task to stop and wait for completion."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval + 2.0)
        logger.info("Scheduled task '%s' stopped. Runs: %d, Errors: %d",
                     self.name, self.run_count, self.error_count)

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run_loop(self) -> None:
        """Main loop: wait for interval, then execute target."""
        if self.initial_delay > 0:
            self._stop_event.wait(self.initial_delay)

        while not self._stop_event.is_set():
            try:
                self.target()
                self.run_count += 1
                self.last_run = time.time()
            except Exception as e:
                self.error_count += 1
                logger.error("Task '%s' error (attempt %d): %s",
                             self.name, self.error_count, e)

            self._stop_event.wait(self.interval)


class AgentScheduler:
    """
    Manages all scheduled background tasks for the endpoint agent.

    Provides a single start/stop interface for orchestrating:
    - Heartbeat (30s)
    - Flow flush (2s)
    - Queue flush (10s)
    - Health check (60s)
    - Version check (3600s)
    """

    def __init__(self):
        self._tasks: dict[str, ScheduledTask] = {}

    def register(
        self,
        name: str,
        target: Callable[[], None],
        interval: float,
        initial_delay: float = 0.0,
    ) -> None:
        """Register a new scheduled task."""
        if name in self._tasks:
            logger.warning("Task '%s' already registered. Replacing.", name)
            self._tasks[name].stop()

        self._tasks[name] = ScheduledTask(
            name=name,
            target=target,
            interval=interval,
            initial_delay=initial_delay,
        )

    def start_all(self) -> None:
        """Start all registered tasks."""
        logger.info("Starting %d scheduled tasks...", len(self._tasks))
        for task in self._tasks.values():
            task.start()

    def stop_all(self) -> None:
        """Stop all running tasks gracefully."""
        logger.info("Stopping all scheduled tasks...")
        for task in self._tasks.values():
            task.stop()

    def get_status(self) -> dict[str, dict]:
        """Return status of all registered tasks."""
        return {
            name: {
                "running": task.is_running,
                "run_count": task.run_count,
                "error_count": task.error_count,
                "interval": task.interval,
                "last_run": task.last_run,
            }
            for name, task in self._tasks.items()
        }

    def get_task(self, name: str) -> ScheduledTask | None:
        """Get a specific task by name."""
        return self._tasks.get(name)
