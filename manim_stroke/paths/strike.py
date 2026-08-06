"""划线(删除线)中心线。"""
import numpy as np
from ._helpers import _smooth_wobble


def strike_path(x0: float, x1: float, y: float, n: int = 24,
                jitter: float = 0.007, seed: int = 1,
                variation: float = 1.0):
    """近直、果断的一笔划线。"""
    rng = np.random.default_rng(seed)
    amount = jitter * variation
    wobble = _smooth_wobble(n, amount, rng, knots=2)
    span = abs(x1 - x0)
    slope = rng.uniform(-.055, .055) * min(variation, 2.5) * min(span, 1.5)
    return [[x0 + (x1 - x0) * i / (n - 1),
             y + wobble[i] + slope * (i / (n - 1) - .5)] for i in range(n)]