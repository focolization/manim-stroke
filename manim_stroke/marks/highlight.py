"""荧光笔高亮标记：粗、圆鼻头、半透明、带手绘抖动的宽带横扫目标。

和 underline/strike 同属"一条直线手势"，但质感不同：
  - 粗：带宽 ~ 文字高度的 0.85 倍，远大于细笔迹；
  - 圆鼻头：``cap=True``，两端圆头（马克笔鼻头），不是方截；
  - 半透明：``fill_opacity=opacity``，文字透得出来；
  - 手绘感：中心线低频抖动（``jitter`` + knots=6）+ 一点手部斜度，让带宽边缘自然颤。

半透明通过本地 :func:`_to_polygon_alpha` 写入最终多边形的 ``fill_opacity``；
animation 层的 ``_polygon_from_outline`` 从模板读 ``get_fill_opacity()``，
所以逐笔增长动画全程保持半透明，无需改 animation / _common。
"""
from __future__ import annotations
from typing import Optional

from manim import Polygon

from ._common import (Mark, MarkStyle, _resolve_style, _require_at_least_two_points,
                      _height, _resolve_seed, _opts, _make_mark)
from ..paths import highlight_path
from ..freehand import get_stroke


def _to_polygon_alpha(outline, color: str, opacity: float) -> Polygon:
    """带不透明度的实心轮廓多边形（区别于 _common._to_polygon 的固定 opacity=1）。"""
    return Polygon(
        *[(p[0], p[1], 0) for p in outline],
        fill_color=color, fill_opacity=opacity, stroke_width=0,
    )


def highlight(target, size=None, color=None, opacity=0.4, cap=True,
              taper=None, thinning=None, jitter=0.05, seed=None,
              variation=1.0, speed="line", smoothing=None, n_points=32,
              pad=None, style: Optional[MarkStyle] = None) -> Mark:
    """在目标上横扫一笔荧光笔高亮：粗、**圆鼻头**、半透明、带手绘抖动。

    ``cap=True``（圆头马克笔鼻头）、``jitter`` 给中心线低频抖动（手绘感）、
    ``size`` 作为带宽（默认 ~ 目标高度 0.85 倍）、``opacity`` 半透明
    （默认 0.4，文字透得出）、``pad`` 让高亮左右多出一点。
    其余参数与其它标记一致（seed/speed 等）。
    """
    _require_at_least_two_points("n_points", n_points)
    style = _resolve_style(style, default_color="#FFE066", color=color, size=size,
                           thinning=thinning, cap=cap, taper=taper, smoothing=smoothing)
    seed = _resolve_seed(seed)

    def build():
        band = style.size if style.size is not None else _height(target) * 0.85
        pad_x = pad if pad is not None else band * 0.08
        x0 = target.get_left()[0] - pad_x
        x1 = target.get_right()[0] + pad_x
        y = target.get_center()[1]
        points = highlight_path(x0, x1, y, n=n_points, jitter=jitter,
                                seed=seed, variation=variation)
        options = _opts(style, band, last=True)
        return ([_to_polygon_alpha(get_stroke(points, **options), style.color, opacity)],
                [points], [band], [False], [options])

    return _make_mark(target, "highlight", build, speed=speed, seed=seed,
                      variation=variation)