"""下划线中心线。"""
import numpy as np
from ._helpers import _smooth_wobble


def underline_path(x0: float, x1: float, y: float, n: int = 24,
                   jitter: float = 0.012, seed: int = 1,
                   variation: float = 1.0):
    """轻微起伏的一笔下划线。"""
    rng = np.random.default_rng(seed)
    amount = jitter * variation
    wobble = _smooth_wobble(n, amount, rng, knots=4)
    slope = rng.uniform(-amount, amount)
    return [[x0 + (x1 - x0) * i / (n - 1),
             y + wobble[i] + slope * (i / (n - 1) - .5)] for i in range(n)]