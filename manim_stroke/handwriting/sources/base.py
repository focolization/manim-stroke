"""GlyphSource 协议：手写管道的输入抽象。

每种字形数据源（Hershey 拉丁、Make Me a Hanzi 汉字 medians、将来日文/假名/
韩文等）只需实现 :meth:`strokes_for` 与 :meth:`normalize`，即可复用 glyph.py
里同一套变形/定时/描边管道。``normalize`` 决定各语种的坐标系语义（拉丁保
字体度量、汉字满格方块）。
"""
from __future__ import annotations

from typing import List, Protocol, Sequence, Tuple

# 一条笔画的中心线折线：[(x, y), ...]
Stroke = List[List[float]]
# 一个字的所有笔画（按正确书写顺序）
RawGlyph = List[Stroke]
BBox = Tuple[float, float, float, float]


def glyph_bbox(raw: RawGlyph) -> BBox:
    """整字包围盒 (x0, y0, x1, y1)。"""
    xs = [p[0] for s in raw for p in s]
    ys = [p[1] for s in raw for p in s]
    return (min(xs), min(ys), max(xs), max(ys))


def normalize_unit_height(raw: RawGlyph, bbox: BBox) -> Tuple[RawGlyph, float]:
    """把笔画平移+缩放到字高=1、bbox 居中于原点。返回 (新strokes, width)。"""
    x0, y0, x1, y1 = bbox
    w = x1 - x0
    h = y1 - y0
    if h <= 0:
        h = 1.0
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0
    scale = 1.0 / h
    out: RawGlyph = []
    for s in raw:
        out.append([[(p[0] - cx) * scale, (p[1] - cy) * scale] for p in s])
    return out, w * scale


def normalize_font_metrics(raw: RawGlyph, bbox: BBox,
                           font_height: float = 21.0) -> Tuple[RawGlyph, float]:
    """Keep a font's shared vertical metrics instead of normalizing each glyph.

    Hershey's normalized default fonts use y=0..21 for the line frame.  Mapping
    that common frame to [-.5, .5] preserves lowercase x-height, ascenders and
    descenders (``e`` is no longer scaled to the height of ``l``).  X remains
    locally centered; word placement supplies the per-glyph advance.
    """
    x0, _y0, x1, _y1 = bbox
    cx = (x0 + x1) / 2.0
    scale = 1.0 / font_height
    out: RawGlyph = []
    for s in raw:
        out.append([[(p[0] - cx) * scale, p[1] * scale - 0.5] for p in s])
    return out, (x1 - x0) * scale


def normalize_em(raw: RawGlyph, bbox: BBox,
                 em: Tuple[float, float, float, float] = (0.0, -128.0, 1024.0, 896.0)
                 ) -> Tuple[RawGlyph, float]:
    """按数据源的方块字格（em）归一化，而非按单个字的墨迹 bbox。

    汉字在方块字格里占固定位置/大小（如「一」是格中一根横条，不是撑满整格）。
    若按墨迹 bbox 归一化，横笔（一）这类墨迹高≈0 的字会被拉到 1/≈0 的巨大缩放，
    变成一根超长横线。用固定 em 方块可保持各字在格内的自然位置与比例。
    返回 (strokes, width=1.0)（em 为正方形，边长为 1）。
    """
    ex0, ey0, ex1, ey1 = em
    ecx = (ex0 + ex1) / 2.0
    ecy = (ey0 + ey1) / 2.0
    scale = 1.0 / (ex1 - ex0)          # em 是正方形
    out: RawGlyph = []
    for s in raw:
        out.append([[(p[0] - ecx) * scale, (p[1] - ecy) * scale] for p in s])
    return out, (ex1 - ex0) * scale    # = 1.0



class GlyphSource(Protocol):
    """一个手写字形数据源：取中心线 + 定义坐标系归一化语义。"""

    def strokes_for(self, char: str) -> RawGlyph:
        """返回按正确书写顺序的每笔中心线折线（原始坐标）。"""
        ...

    def normalize(self, raw: RawGlyph, preserve_metrics: bool,
                  bbox: BBox) -> Tuple[RawGlyph, float]:
        """把原始笔画归一化到字高=1、bbox 居中；返回 (strokes, width)。

        各语种自定义坐标系语义：拉丁可保字体度量（``preserve_metrics=True``），
        汉字恒为满格方块（忽略该标志）。
        """
        ...
