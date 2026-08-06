"""左括号 ( (目标左侧,弧凸向远离字、开口朝字),复用 circle_path 半弧。"""
from __future__ import annotations
import math
from typing import Optional
from ._common import (Mark, MarkStyle, _resolve_style, _require_at_least_two_points,
                      _height, _default_stroke_size, _resolve_seed, _opts, _to_polygon, _make_mark)
from ..paths import circle_path
from ..freehand import get_stroke


def lparen(target, size=None, color=None, thinning=None, cap=None, taper=None,
           jitter=0.03, seed=None, variation=1.0, speed="circle",
           smoothing=None, n_points=22, ratio=0.6, offset=None,
           style: Optional[MarkStyle] = None) -> Mark:
    """在目标左侧画左括号 ( 。"""
    _require_at_least_two_points("n_points", n_points)
    style = _resolve_style(style, default_color="#6FA8C8", color=color, size=size,
                           thinning=thinning, cap=cap, taper=taper, smoothing=smoothing)
    seed = _resolve_seed(seed)

    def build():
        stroke_size = style.size if style.size is not None else _default_stroke_size(target)
        cy = target.get_center()[1]
        gap = _height(target) * 0.03 if offset is None else offset
        cx = target.get_left()[0] - gap
        r = _height(target) * ratio
        # 半弧凸向左(远离字、开口朝字):start π/2, sweep π, 经 π(左最远点) = (
        points = circle_path(cx, cy, r, r, n=n_points, jitter=jitter, seed=seed,
                             variation=variation, start_angle=math.pi / 2,
                             direction=1, sweep_angle=math.pi, tilt=0.0)
        options = _opts(style, stroke_size, last=True)
        return ([_to_polygon(get_stroke(points, **options), style.color)],
                [points], [stroke_size], [False], [options])

    return _make_mark(target, "lparen", build, speed=speed, seed=seed, variation=variation)