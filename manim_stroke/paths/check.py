"""✓ 勾中心线(一笔连续:短腿下落→拐点上挑)。"""
import math
import numpy as np


def check_path(cx: float, cy: float, size: float, num_points: int = 50,
               curvature: float = .15, jitter: float = .012, seed: int = 1,
               variation: float = 1.0):
    """一笔连续 ✓:短腿下落,到拐点后立即上挑。"""
    rng = np.random.default_rng(seed)
    ys = -1
    structure = min(variation, 2.5)
    short_x = .48 * (1 + rng.uniform(-.14, .14) * structure)
    short_y = .28 * (1 + rng.uniform(-.16, .16) * structure)
    long_x = .80 * (1 + rng.uniform(-.16, .16) * structure)
    long_y = .70 * (1 + rng.uniform(-.14, .14) * structure)
    p0 = np.array([cx - short_x * size + rng.uniform(-.02, .02) * size * structure,
                   cy - short_y * size * ys + rng.uniform(-.02, .02) * size * structure])
    p1 = np.array([cx - .05 * size + rng.uniform(-.06, .06) * size * structure,
                   cy + .18 * size * ys + rng.uniform(-.05, .05) * size * structure])
    p2 = np.array([cx + long_x * size + rng.uniform(-.03, .03) * size * structure,
                   cy - long_y * size * ys + rng.uniform(-.03, .03) * size * structure])
    curve = curvature * (1 + rng.uniform(-.18, .18) * variation)
    control = (p1 + p2) / 2 + np.array([1.0, .8 * ys]) * curve * size

    n1 = int(num_points * .35)
    t1 = np.linspace(0, 1, n1) ** 1.2
    t2 = np.linspace(0, 1, num_points - n1 + 1) ** .8
    downstroke = (1 - t1[:, None]) * p0 + t1[:, None] * p1
    upstroke = ((1 - t2) ** 2)[:, None] * p1 + \
               (2 * (1 - t2) * t2)[:, None] * control + \
               (t2 ** 2)[:, None] * p2

    def jitter_segment(segment):
        raw = rng.normal(0, jitter * size * variation, segment.shape)
        kernel = np.ones(5) / 5
        smooth = np.column_stack((np.convolve(raw[:, 0], kernel, mode="same"),
                                  np.convolve(raw[:, 1], kernel, mode="same")))
        envelope = np.sin(np.linspace(0, math.pi, len(segment))) ** .8
        return segment + smooth * envelope[:, None]

    return np.vstack((jitter_segment(downstroke), jitter_segment(upstroke)[1:])).tolist()