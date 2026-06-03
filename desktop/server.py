"""Run the Atlas FastAPI app in a background thread for the desktop shell.

Pure helpers (`find_free_port`, `wait_until_ready`) are unit-tested; the
threaded uvicorn `ServerThread` is exercised by the launcher and the manual
smoke test.
"""
from __future__ import annotations

import socket
import time
import urllib.error
import urllib.request
from threading import Thread
from typing import Callable

import uvicorn


def find_free_port() -> int:
    """Ask the OS for an unused TCP port on the loopback interface."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def wait_until_ready(
    probe: Callable[[], bool],
    timeout: float = 15.0,
    interval: float = 0.1,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.monotonic,
) -> bool:
    """Poll ``probe`` until it returns True or ``timeout`` seconds elapse."""
    deadline = now() + timeout
    while now() < deadline:
        if probe():
            return True
        sleep(interval)
    return False


def http_probe(url: str, timeout: float = 1.0) -> bool:
    """Return True if ``url`` answers with HTTP 200."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (loopback only)
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


class ServerThread:
    """A uvicorn server running in a daemon thread, with a clean stop."""

    def __init__(self, app, host: str = "127.0.0.1", port: int = 8000) -> None:
        self.host = host
        self.port = port
        config = uvicorn.Config(app, host=host, port=port, log_level="warning")
        self._server = uvicorn.Server(config)
        self._thread = Thread(target=self._server.run, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=5)
