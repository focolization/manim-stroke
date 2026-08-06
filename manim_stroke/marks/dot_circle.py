"""单字下方的小圆圈(不标准手绘着重圈),复用 circle_path。"""
from __future__ import annotations
import math
import random
from typing import Optional
from ._common import (Mark, MarkStyle, _resolve_style, _require_at_least_two_points,
                      _height, _default_stroke_size, _resolve_seed, _opts, _to_polygon, _make_mark)
from ..paths import circle_path
from ..freehand import get_stroke


def dot_circle(target, size=None, color=None, thinning=None, cap=None, taper=None,
               jitter=0.06, seed=None, variation=1.0, speed="circle",
               smoothing=None, n_points=44, ratio=0.22, offset=None,
               style: Optional[MarkStyle] = None) -> Mark:
    """在单个字下方画小圆圈(不标准手绘)。

    针对「单字」target:小椭圆落字下,故意 jitter 大、不规整,像随手点的着重圈。
    """
    _require_at_least_two_points("n_points", n_points)
    style = _resolve_style(style, default_color="#F4B6C2", color=color, size=size,
                           thinning=thinning, cap=cap, taper=taper, smoothing=smoothing)
    seed = _resolve_seed(seed)
    gr = random.Random(seed)
    start_angle = gr.uniform(0, 2 * math.pi)
    direction = gr.choice((-1, 1))
    tilt = gr.uniform(-.18, .18) * min(variation, 2.5)

    def build():
        stroke_size = style.size if style.size is not None else _default_stroke_size(target)
        cx = target.get_center()[0]
        gap = _height(target) * 0.22 if offset is None else offset
        cy = target.get_bottom()[1] - gap - _height(target) * ratio * 0.5
        rx = max(target.width * 0.5 * ratio, stroke_size * 2)
        ry = max(_height(target) * ratio, stroke_size * 2)
        points = circle_path(cx, cy, rx, ry, n=n_points, jitter=jitter, seed=seed,
                             variation=variation, start_angle=start_angle,
                             direction=direction, sweep_angle=2 * math.pi, tilt=tilt)
        points.append(points[0])
        options = _opts(style, stroke_size, last=True)
        return ([_to_polygon(get_stroke(points, **options), style.color)],
                [points], [stroke_size], [True], [options])

    return _make_mark(target, "dot_circle", build, speed=speed, seed=seed, variation=variation)