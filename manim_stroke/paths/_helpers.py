"""路径共享:低频连续偏移辅助(无 Manim 依赖)。"""
import math
import numpy as np


def _smooth_wobble(n: int, amplitude: float, rng, knots: int = 4) -> np.ndarray:
    """端点归零的低频连续偏移,避免逐点随机的毛刺。"""
    if n <= 1 or amplitude == 0:
        return np.zeros(n)
    values = np.concatenate(([0.0], rng.uniform(-amplitude, amplitude, knots), [0.0]))
    positions = np.linspace(0, n - 1, len(values))
    result = np.zeros(n)
    for index in range(len(values) - 1):
        start, end = int(round(positions[index])), int(round(positions[index + 1]))
        if end <= start:
            continue
        t = np.linspace(0, 1, end - start + 1)
        t = t * t * (3 - 2 * t)
        result[start:end + 1] = values[index] + (values[index + 1] - values[index]) * t
    return result


def _periodic_wobble_terms(amplitude: float, rng):
    """整圈只抽一次的谐波项 (freq, weight, amp, phase)。

    幅度与相位在一整圈里固定不变,这样频率 1/2/3 才真正合成出
    低频连续、首尾自动对齐的波形(整数频率保证 sin(2π·f·0+φ)=
    sin(2π·f·1+φ))。
    """
    return [(f, w, rng.uniform(-amplitude, amplitude), rng.uniform(0, 2 * math.pi))
            for f, w in ((1, .55), (2, .30), (3, .15))]


def _periodic_wobble_at(t: float, terms) -> float:
    """用预先抽好的谐波项,在参数 t 处求径向偏移。"""
    return sum(w * a * math.sin(2 * math.pi * f * t + phi)
               for f, w, a, phi in terms)
