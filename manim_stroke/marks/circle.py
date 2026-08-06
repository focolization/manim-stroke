"""围绕目标的手绘椭圆圈。"""
from __future__ import annotations
import math
import random
from typing import Optional
from ._common import (Mark, MarkStyle, _resolve_style, _require_at_least_two_points,
                      _height, _default_stroke_size, _resolve_seed, _opts, _to_polygon, _make_mark)
from ..paths import circle_path
from ..freehand import get_stroke


def circle(target, size=None, color=None, thinning=None, cap=None, taper=None,
           jitter=0.02, seed=None, variation=1.0, speed="circle",
           smoothing=None, n_points=40, ratio=1.25, closed=None,
           style: Optional[MarkStyle] = None) -> Mark:
    """围绕目标画手绘椭圆圈。"""
    _require_at_least_two_points("n_points", n_points)
    if ratio <= 0:
        raise ValueError(f"ratio must be greater than 0; got {ratio}")
    style = _resolve_style(style, default_color="#6FA8C8", color=color, size=size,
                           thinning=thinning, cap=cap, taper=taper, smoothing=smoothing)
    seed = _resolve_seed(seed)
    gesture_rng = random.Random(seed)
    start_angle = gesture_rng.uniform(0, 2 * math.pi)
    direction = gesture_rng.choice((-1, 1))
    tilt = gesture_rng.uniform(-.12, .12) * min(variation, 2.5)
    if closed is True:
        gesture, sweep_angle, is_closed = "normal", 2 * math.pi, True
    elif closed is False:
        gesture, sweep_angle, is_closed = "open", 2 * math.pi - gesture_rng.uniform(.16, .46), False
    else:
        selector = gesture_rng.random()
        if selector < .60:
            gesture, sweep_angle, is_closed = "normal", 2 * math.pi, True
        elif selector < .86:
            gesture, sweep_angle, is_closed = "open", 2 * math.pi - gesture_rng.uniform(.16, .46), False
        else:
            gesture, sweep_angle, is_closed = "overlap", 2 * math.pi + gesture_rng.uniform(.10, .30), False

    def build():
        stroke_size = style.size if style.size is not None else _default_stroke_size(target)
        center = target.get_center()
        rx = max(target.width * 0.5 * ratio, stroke_size * 2)
        ry = max(_height(target) * 0.5 * ratio, stroke_size * 2)
        points = circle_path(center[0], center[1], rx, ry, n=n_points,
                             jitter=jitter, seed=seed, variation=variation,
                             start_angle=start_angle, direction=direction,
                             sweep_angle=sweep_angle, tilt=tilt)
        if is_closed:
            points.append(points[0])
        options = _opts(style, stroke_size, last=True)
        return ([_to_polygon(get_stroke(points, **options), style.color)],
                [points], [stroke_size], [is_closed], [options])

    mark = _make_mark(target, "circle", build, speed=speed, seed=seed, variation=variation)
    mark.gesture = gesture
    return mark