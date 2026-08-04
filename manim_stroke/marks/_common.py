"""标记共享:视觉参数、辅助函数、Mark 容器(无 Manim 依赖的几何在 paths.py)。"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
import secrets
from typing import Callable, Optional

from manim import Polygon, VGroup

from ..freehand import get_stroke
from ..handwriting import HandwritingStyle, polyline_length


@dataclass(frozen=True)
class MarkStyle:
    """所有标记共用的视觉参数。``None`` 表示按目标高度自适应。"""

    color: str = "#6FA8C8"
    size: Optional[float] = None
    thinning: float = 0
    cap: bool = True
    taper: float = 0
    smoothing: float = 0.5


def _resolve_style(style: Optional[MarkStyle], *, default_color: str, color, size,
                   thinning, cap, taper, smoothing) -> MarkStyle:
    """合并可复用 ``MarkStyle`` 与一次调用中的显式覆盖参数。"""
    if style is not None and not isinstance(style, MarkStyle):
        raise TypeError("style must be a MarkStyle or None")
    base = style if style is not None else MarkStyle(color=default_color)
    return MarkStyle(
        color=base.color if color is None else color,
        size=base.size if size is None else size,
        thinning=base.thinning if thinning is None else thinning,
        cap=base.cap if cap is None else cap,
        taper=base.taper if taper is None else taper,
        smoothing=base.smoothing if smoothing is None else smoothing,
    )


def _require_at_least_two_points(name: str, count: int) -> None:
    """避免路径生成器在不足两个点时产生除零或无意义笔迹。"""
    if count < 2:
        raise ValueError(f"{name} must be at least 2; got {count}")


def _height(target) -> float:
    """为极小或扁平对象提供稳定的缩放基准。"""
    return max(float(target.height), 0.1)


def _default_stroke_size(target) -> float:
    return min(max(_height(target) * 0.08, 0.035), 0.14)


def _default_mark_size(target) -> float:
    return min(max(_height(target) * 0.8, 0.28), 1.6)


def _resolve_seed(seed) -> int:
    """未指定 seed 时为这一次标记生成随机但稳定的手势身份。"""
    return secrets.randbelow(2**32) if seed is None else int(seed)


def _opts(style: MarkStyle, size: float, *, last: bool = False) -> dict:
    return {
        "size": size,
        "thinning": style.thinning,
        "smoothing": style.smoothing,
        "last": last,
        "start": {"cap": style.cap, "taper": style.taper},
        "end": {"cap": style.cap, "taper": style.taper},
    }


def _to_polygon(outline, color: str) -> Polygon:
    return Polygon(
        *[(point[0], point[1], 0) for point in outline],
        fill_color=color,
        fill_opacity=1,
        stroke_width=0,
    )


class Mark(VGroup):
    """一个或多个手绘笔迹组成的课堂批注。

    ``Mark`` 是普通 ``VGroup``，可直接 ``Scene.add``。若目标在动画中移动或缩放，
    调用 :meth:`follow`，批注会在每帧按同一套参数重新定位。
    """

    def __init__(self, *strokes, target=None, builder: Optional[Callable] = None,
                 kind: str = "mark", centerlines=None, stroke_sizes=None,
                 closed_strokes=None, stroke_options=None, speed: str = "natural",
                 seed: Optional[int] = None, variation: float = 1.0):
        super().__init__(*strokes)
        self.target = target
        self.kind = kind
        self._builder = builder
        self._following = False
        self.centerlines = centerlines or []
        self.stroke_sizes = stroke_sizes or []
        self.closed_strokes = closed_strokes or []
        self.stroke_options = stroke_options or []
        self.speed = speed
        self.seed = seed
        self.variation = variation

    def refresh(self) -> "Mark":
        """立刻按当前目标 bbox 重建自身。"""
        if self.target is None or self._builder is None:
            return self
        replacement = self._builder()
        self.submobjects = replacement.submobjects
        self.points = replacement.points.copy()
        self.centerlines = replacement.centerlines
        self.stroke_sizes = replacement.stroke_sizes
        self.closed_strokes = replacement.closed_strokes
        self.stroke_options = replacement.stroke_options
        self.speed = replacement.speed
        self.seed = replacement.seed
        self.variation = replacement.variation
        return self

    def follow(self) -> "Mark":
        """使批注跟随目标的移动和缩放；重复调用无副作用。"""
        if not self._following:
            self.add_updater(lambda mark: mark.refresh())
            self._following = True
        return self

    def unfollow(self) -> "Mark":
        """停止跟随，保留当前位置。"""
        self.clear_updaters()
        self._following = False
        return self


def _make_mark(target, kind: str, build: Callable, *, speed: str, seed: int,
               variation: float) -> Mark:
    strokes, centerlines, stroke_sizes, closed_strokes, stroke_options = build()
    return Mark(
        *strokes,
        target=target,
        builder=lambda: _make_mark(target, kind, build, speed=speed, seed=seed, variation=variation),
        kind=kind,
        centerlines=centerlines,
        stroke_sizes=stroke_sizes,
        closed_strokes=closed_strokes,
        stroke_options=stroke_options,
        speed=speed,
        seed=seed,
        variation=variation,
    )


# ── 手写 glyph → 场景坐标 的共享助手（letter / hanzi 共用）──

def _glyph_center(target, position: str, glyph_w: float, glyph_h: float, gap: float):
    """按 position 算字母中心坐标（manim 场景坐标）。"""
    cx, cy = target.get_center()[:2]
    if position == "center":
        return cx, cy
    if position == "left":
        return target.get_left()[0] - gap - glyph_w / 2, cy
    if position == "right":
        return target.get_right()[0] + gap + glyph_w / 2, cy
    if position == "above":
        return cx, target.get_top()[1] + gap + glyph_h / 2
    if position == "below":
        return cx, target.get_bottom()[1] - gap - glyph_h / 2
    if position == "upper-right":
        return (target.get_right()[0] + gap + glyph_w / 2,
                target.get_top()[1] + gap + glyph_h / 2)
    raise ValueError(f"unknown position {position!r}; "
                     f"choose from left/right/above/below/upper-right/center")


def _transform_point(p, scale: float, rot: float, tx: float, ty: float):
    """缩放→旋转→平移。p 在字高=1 坐标系。"""
    x, y = p[0] * scale, p[1] * scale
    c, s = math.cos(rot), math.sin(rot)
    return [x * c - y * s + tx, x * s + y * c + ty]


def _glyph_placement_params(hw: HandwritingStyle, seed: int, size: float):
    """从 seed 算 per-glyph 微旋/微缩 + 笔宽 + 缩放比。返回
    (glyph_rot, glyph_scale, pen_w, scale)。"""
    grng = random.Random(seed)
    glyph_rot = math.radians(max(-hw.glyph_rotation_limit_deg,
                                 min(hw.glyph_rotation_limit_deg,
                                     grng.gauss(0.0, hw.glyph_rotation_std_deg))))
    glyph_scale = max(hw.glyph_scale_min, min(hw.glyph_scale_max,
                                              grng.gauss(1.0, hw.glyph_scale_std)))
    pen_w = size * hw.stroke_size_ratio * glyph_scale
    scale = size * glyph_scale
    return glyph_rot, glyph_scale, pen_w, scale


def _render_strokes(glyph, scale: float, glyph_rot: float, tx: float, ty: float,
                    pen_w: float, hw: HandwritingStyle, color):
    """把 glyph 各笔 缩放→旋转→平移到 (tx,ty)，逐笔 get_stroke 描边。
    返回 (polygons, centerlines, options, durations, n_strokes)。opt 字典只此一份。"""
    polys, clines, opts, durs = [], [], [], []
    for s in glyph.strokes:
        pts = [_transform_point(p, scale, glyph_rot, tx, ty) for p in s.points]
        taper = polyline_length(pts) * hw.pen_taper_frac
        opt = {"size": pen_w, "thinning": 0.0, "smoothing": hw.smoothing,
               "streamline": hw.streamline, "last": True,
               "start": {"cap": True, "taper": taper}, "end": {"cap": True, "taper": taper}}
        polys.append(_to_polygon(get_stroke(pts, **opt), color))
        clines.append(pts)
        opts.append(opt)
        durs.append(s.duration)
    return polys, clines, opts, durs, len(glyph.strokes)