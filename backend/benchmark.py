import time
from dataclasses import dataclass, field
from typing import List, Dict
from functools import wraps  # <--- garante que o nome da função original seja preservado


@dataclass
class BenchmarkHistory:
    balance_times_ms: List[float] = field(default_factory=list)
    route_times_ms: List[float] = field(default_factory=list)
    optimize_times_ms: List[float] = field(default_factory=list)

    def add_balance_time(self, elapsed_ms: float):
        self.balance_times_ms.append(elapsed_ms)

    def add_route_time(self, elapsed_ms: float):
        self.route_times_ms.append(elapsed_ms)

    def add_optimize_time(self, elapsed_ms: float):
        self.optimize_times_ms.append(elapsed_ms)

    def summary(self) -> Dict[str, float]:
        def avg(lst):
            return sum(lst) / len(lst) if lst else 0.0

        return {
            "balance_avg_ms": avg(self.balance_times_ms),
            "route_avg_ms": avg(self.route_times_ms),
            "optimize_avg_ms": avg(self.optimize_times_ms),
        }


benchmark_history = BenchmarkHistory()


def timed_balance(fn):
    """Decorator para medir tempo de funções de balanceamento."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = fn(*args, **kwargs)
        elapsed_ms = (time.time() - start) * 1000.0
        benchmark_history.add_balance_time(elapsed_ms)
        return result
    return wrapper


def timed_route(fn):
    """Decorator para medir tempo de funções de roteamento."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = fn(*args, **kwargs)
        elapsed_ms = (time.time() - start) * 1000.0
        benchmark_history.add_route_time(elapsed_ms)
        return result
    return wrapper


def timed_optimize(fn):
    """Decorator para medir tempo de funções de otimização."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = fn(*args, **kwargs)
        elapsed_ms = (time.time() - start) * 1000.0
        benchmark_history.add_optimize_time(elapsed_ms)
        return result
    return wrapper
