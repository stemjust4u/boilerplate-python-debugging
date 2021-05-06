from time import perf_counter_ns
from contextlib import ContextDecorator
from dataclasses import dataclass, field
import time
from typing import Any, Callable, ClassVar, Dict, Optional

def test():
    print("test")

class TimerError(Exception):
    """Exception for Timer Class errors"""

@dataclass
class Timer(ContextDecorator):
    """Can use as class, decorator, context manager"""

    timers: ClassVar[Dict[str, float]] = dict()
    name: Optional[str] = None
    text: str = "{} time: {:.3f} {}"
    logger: Optional[Callable[[str], None]] = print
    units: Optional[str] = "ms"
    _start_time: Optional[float] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialization: update timers dict with new timer"""
        if self.name:
            self.timers.setdefault(self.name, 0)

    def start(self) -> None:
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError(f"Timer is already running. Use .stop() to stop it")

        self._start_time = time.perf_counter_ns()

    def stop(self) -> float:
        """Stop the timer and report delta time"""
        if self._start_time is None:
            raise TimerError(f"There is no timer running. Use .start() to start a timer")

        # Calculate delta time
        Delta_time = time.perf_counter_ns() - self._start_time
        self._start_time = None

        # Report Delta time
        if self.logger and self.units == "ms":
            self.logger(self.text.format(self.name, Delta_time/10**6, self.units))
        if self.logger and self.units == "us":
            self.logger(self.text.format(self.name, Delta_time/10**3, self.units))
        if self.name:
            self.timers[self.name] += Delta_time

        return Delta_time

    def __enter__(self) -> "Timer":
        """Start a new timer as a context manager"""
        self.start()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        """Stop the context manager timer"""
        self.stop()

if __name__ == "__main__":
    @Timer(name="test", units="ms")
    def test(x, n):
        for _ in range(n):
            x = x + 1.1
    x=1
    n=1000
    test(x, n)