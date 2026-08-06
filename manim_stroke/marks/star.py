"""一笔画五角星(强调星),复用 star_path。支持 position 定位到目标周围各方位。"""
from __future__ import annotations
from typing import Optional
from ._common import (Mark, MarkStyle, _resolve_style,
                      _default_stroke_size, _default_mark_size, _resolve_seed,
                      _opts, _to_polygon, _make_mark)
from ..paths import star_path
from ..freehand import get_stroke

_POSITIONS = ("below", "above", "upper-right", "upper-left",
              "lower-right", "lower-left")


def star(target, size=None, mark_size=None, color=None, thinning=None, cap=None,
         taper=None, jitter=0.02, seed=None, variation=1.0, speed="line",
         smoothing=None, offset=None, position="below",
         style: Optional[MarkStyle] = None) -> Mark:
    """在目标周围画一笔五角星(不抬笔,5 笔交叉)。

    ``position`` 决定星星中心相对 target bbox 的方位:
      below(默认,正下方居中) / above(正上方) /
      upper-right / upper-left / lower-right / lower-left(四角,贴角外侧)
    大小走 ``mark_size``(默认与字号等高);用于核心强调。
    """
    if position not in _POSITIONS:
        raise ValueError(f"unknown position {position!r}; choose from {_POSITIONS}")
    style = _resolve_style(style, default_color="#F4B6C2", color=color, size=size,
                           thinning=thinning, cap=cap, taper=taper, smoothing=smoothing)
    seed = _resolve_seed(seed)

    def build():
        stroke_size = style.size if style.size is not None else _default_stroke_size(target)
        symbol_size = mark_size if mark_size is not None else _default_mark_size(target)
        r = symbol_size * 0.5
        gap = symbol_size * 0.5 if offset is None else offset
        L, R = target.get_left()[0], target.get_right()[0]
        T, B = target.get_top()[1], target.get_bottom()[1]
        cx_c = target.get_center()[0]
        if position == "below":
            cx, cy = cx_c, B - r * 1.5   # 往上贴近字底,不跑到行间中点
        elif position == "above":
            cx, cy = cx_c, T + gap + r
        elif position == "upper-right":
            cx, cy = R + r * 0.6, T + r * 0.6
        elif position == "upper-left":
            cx, cy = L - r * 0.6, T + r * 0.6
        elif position == "lower-right":
            cx, cy = R + r * 0.6, B - r * 0.6
        else:  # lower-left
            cx, cy = L - r * 0.6, B - r * 0.6
        points = star_path(cx, cy, r, jitter=jitter, seed=seed, variation=variation)
        options = _opts(style, stroke_size, last=True)
        return ([_to_polygon(get_stroke(points, **options), style.color)],
                [points], [stroke_size], [False], [options])

    return _make_mark(target, "star", build, speed=speed, seed=seed, variation=variation)