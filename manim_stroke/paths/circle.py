"""椭圆圈中心线(dot_circle/lparen/rparen 都复用)。"""
import math
import random
from ._helpers import _periodic_wobble_terms, _periodic_wobble_at


def circle_path(cx: float, cy: float, rx: float, ry: float, n: int = 40,
                jitter: float = .02, seed: int = 1,
                variation: float = 1.0, start_angle: float = 0.0,
                direction: int = 1, sweep_angle: float = 2 * math.pi,
                tilt: float = 0.0):
    """带随机起笔、行笔方向与收笔角度的椭圆中心线。"""
    rng = random.Random(seed)
    terms = _periodic_wobble_terms(jitter * variation, rng)   # 整圈只抽一次,谐波才真
    points = []
    for i in range(n):
        t = i / n
        angle = start_angle + direction * sweep_angle * t
        radial = _periodic_wobble_at(t, terms)
        local_x, local_y = (rx + radial) * math.cos(angle), (ry + radial) * math.sin(angle)
        points.append([cx + local_x * math.cos(tilt) - local_y * math.sin(tilt),
                       cy + local_x * math.sin(tilt) + local_y * math.cos(tilt)])
    return points