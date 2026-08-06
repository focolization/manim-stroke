"""下划线标记。"""
from __future__ import annotations
from typing import Optional
from ._common import (Mark, MarkStyle, _resolve_style, _require_at_least_two_points,
                      _height, _default_stroke_size, _resolve_seed, _opts, _to_polygon, _make_mark)
from ..paths import underline_path
from ..freehand import get_stroke


def underline(target, size=None, color=None, thinning=None, cap=None, taper=None,
              jitter=0.012, seed=None, variation=1.0, speed="line",
              smoothing=None, n_points=24, offset=None,
              style: Optional[MarkStyle] = None) -> Mark:
    """在目标下方画自适应下划线。"""
    _require_at_least_two_points("n_points", n_points)
    style = _resolve_style(style, default_color="#F4B6C2", color=color, size=size,
                           thinning=thinning, cap=cap, taper=taper, smoothing=smoothing)
    seed = _resolve_seed(seed)

    def build():
        stroke_size = style.size if style.size is not None else _default_stroke_size(target)
        gap = _height(target) * 0.16 if offset is None else offset
        y = target.get_bottom()[1] - gap
        points = underline_path(target.get_left()[0], target.get_right()[0], y,
                                n=n_points, jitter=jitter, seed=seed, variation=variation)
        options = _opts(style, stroke_size, last=True)
        return ([_to_polygon(get_stroke(points, **options), style.color)],
                [points], [stroke_size], [False], [options])

    return _make_mark(target, "underline", build, speed=speed, seed=seed, variation=variation)