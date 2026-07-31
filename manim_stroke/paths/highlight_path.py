"""荧光笔高亮带中心线。

与 underline 同属"一条横扫直线"手势，但高亮带很粗、落笔目标是文字中线，
且会再经 freehand 包成平头宽带。轻微起伏 + 一点手部斜度，避免完全机械的直线。
纯几何，无 Manim 依赖。
"""
import numpy as np
from ._helpers import _smooth_wobble


def highlight_path(x0: float, x1: float, y: float, n: int = 32,
                   jitter: float = 0.05, seed: int = 1, variation: float = 1.0):
    """横扫一笔的高亮带中心线。手绘感：较明显的低频起伏（knots=6）+
    一点手部斜度。高亮带粗，起伏让带宽边缘呈现自然的抖。"""
    rng = np.random.default_rng(seed)
    amount = jitter * variation
    wobble = _smooth_wobble(n, amount, rng, knots=6)
    slope = rng.uniform(-amount, amount)
    return [[x0 + (x1 - x0) * i / (n - 1),
             y + wobble[i] + slope * (i / (n - 1) - .5)] for i in range(n)]