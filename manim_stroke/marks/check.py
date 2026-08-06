"""✓ 勾标记。"""
from __future__ import annotations
from typing import Optional
from ._common import (Mark, MarkStyle, _resolve_style, _require_at_least_two_points,
                      _height, _default_stroke_size, _default_mark_size, _resolve_seed,
                      _opts, _to_polygon, _make_mark)
from ..paths import check_path
from ..freehand import get_stroke


def check(target, size=None, mark_size=None, color=None, thinning=None, cap=None,
          taper=None, jitter=0.012, seed=None, variation=1.0, speed="check",
          smoothing=None, num_points=50, curvature=0.15, offset=None,
          style: Optional[MarkStyle] = None) -> Mark:
    """在目标下方画 ✓。"""
    _require_at_least_two_points("num_points", num_points)
    style = _resolve_style(style, default_color="#6FA8C8", color=color, size=size,
                           thinning=thinning, cap=cap, taper=taper, smoothing=smoothing)
    seed = _resolve_seed(seed)

    def build():
        stroke_size = style.size if style.size is not None else _default_stroke_size(target)
        symbol_size = mark_size if mark_size is not None else _default_mark_size(target)
        baseline_gap = symbol_size * 0.86 if offset is None else offset
        cy = target.get_bottom()[1] - baseline_gap
        points = check_path(target.get_center()[0], cy, symbol_size, num_points=num_points,
                            curvature=curvature, jitter=jitter, seed=seed, variation=variation)
        options = _opts(style, stroke_size, last=True)
        return ([_to_polygon(get_stroke(points, **options), style.color)],
                [points], [stroke_size], [False], [options])

    return _make_mark(target, "check", build, speed=speed, seed=seed, variation=variation)