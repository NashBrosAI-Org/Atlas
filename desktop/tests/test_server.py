import socket

from desktop.server import find_free_port, wait_until_ready


def test_find_free_port_returns_bindable_port():
    port = find_free_port()
    assert isinstance(port, int)
    assert 1024 < port < 65536
    # The port is free right now, so we can bind it.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", port))


def test_wait_until_ready_returns_true_when_probe_succeeds():
    calls = {"n": 0}

    def probe():
        calls["n"] += 1
        return calls["n"] >= 3  # not ready twice, then ready

    slept = []
    ok = wait_until_ready(
        probe, timeout=5.0, interval=0.01,
        sleep=slept.append, now=_fake_clock([0.0, 0.0, 0.0, 0.0]),
    )
    assert ok is True
    assert calls["n"] == 3
    assert len(slept) == 2  # slept after the two not-ready probes


def test_wait_until_ready_times_out():
    ok = wait_until_ready(
        lambda: False, timeout=0.05, interval=0.01,
        sleep=lambda _s: None, now=_fake_clock([0.0, 0.02, 0.04, 0.06]),
    )
    assert ok is False


def _fake_clock(values):
    it = iter(values)
    last = [0.0]

    def now():
        try:
            last[0] = next(it)
        except StopIteration:
            last[0] += 1.0
        return last[0]

    return now
