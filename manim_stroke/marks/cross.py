"""× 叉标记。"""
from __future__ import annotations
from typing import Optional
from ._common import (Mark, MarkStyle, _resolve_style, _require_at_least_two_points,
                      _height, _default_stroke_size, _default_mark_size, _resolve_seed,
                      _opts, _to_polygon, _make_mark)
from ..paths import cross_path
from ..freehand import get_stroke


def cross(target, size=None, mark_size=None, color=None, thinning=None, cap=None,
          taper=None, jitter=0.008, seed=None, variation=1.0, speed="line",
          smoothing=None, n_points=18, style: Optional[MarkStyle] = None) -> Mark:
    """在目标中心叠加自适应 ×。"""
    _require_at_least_two_points("n_points", n_points)
    style = _resolve_style(style, default_color="#F4B6C2", color=color, size=size,
                           thinning=thinning, cap=cap, taper=taper, smoothing=smoothing)
    seed = _resolve_seed(seed)

    def build():
        stroke_size = style.size if style.size is not None else _default_stroke_size(target)
        symbol_size = mark_size if mark_size is not None else _default_mark_size(target)
        center = target.get_center()
        lines = cross_path(center[0], center[1], symbol_size, n=n_points,
                           jitter=jitter, seed=seed, variation=variation)
        options = _opts(style, stroke_size, last=True)
        return ([_to_polygon(get_stroke(line, **options), style.color) for line in lines],
                lines, [stroke_size] * len(lines), [False] * len(lines),
                [options] * len(lines))

    return _make_mark(target, "cross", build, speed=speed, seed=seed, variation=variation)