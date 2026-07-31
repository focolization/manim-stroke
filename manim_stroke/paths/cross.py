"""× 叉中心线(两条对角线)。"""
import numpy as np
from ._helpers import _smooth_wobble


def cross_path(cx: float, cy: float, size: float, n: int = 18,
               jitter: float = .008, seed: int = 1,
               variation: float = 1.0):
    """×:先 \(左上→右下),再 /(右上→左下)。"""
    rng = np.random.default_rng(seed)
    s = size * .5
    structure = min(variation, 2.5)

    def diagonal(start, end):
        direction = np.array(end) - np.array(start)
        normal = np.array([-direction[1], direction[0]]) / np.linalg.norm(direction)
        wobble = _smooth_wobble(n + 1, jitter * variation, rng, knots=3)
        return [(np.array(start) + direction * i / n + normal * wobble[i]).tolist()
                for i in range(n + 1)]

    def endpoint(sign_x, sign_y):
        length = 1 + rng.uniform(-.18, .18) * structure
        return (cx + sign_x * s * length, cy + sign_y * s * length)

    return [diagonal(endpoint(-1, 1), endpoint(1, -1)),
            diagonal(endpoint(1, 1), endpoint(-1, -1))]