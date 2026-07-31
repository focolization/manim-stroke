"""Hershey 字形 → 变形笔画。纯几何，不依赖 manim。

流程（专家）：Hershey 几何 → 归一化到字高=1、bbox 居中 → 弧长均匀采样 → 法线 AR(1) 噪声
→ 每笔算弧长与时长。HersheyFonts 延迟导入（可选依赖，只有用字母才需要）。

返回 HandwritingStroke 列表（点列 + 弧长 + 时长），供 marks 层 get_stroke 描边、
animation 层按 Σ-lognormal 速度播放。glyph 级 rotation/scale/平移由 marks 层施加，
不在这里做（路径层只出规范帧里的笔画）。
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List

from .deform import polyline_length, resample_arclength, wobble_polyline_normal
from .segment import segment_deform
from .slant import shear_polyline
from .style import HandwritingStyle
from .structure import structure_deform
from .timing import detect_peaks, stroke_duration


@dataclass(frozen=True)
class HandwritingStroke:
    """一条 pen-down 笔画：变形后的中心线 + 弧长 + 播放时长。"""
    points: List[List[float]]    # 已变形、字高=1 坐标系
    arc_length: float            # 字高=1 单位
    duration: float              # 秒（由弧长按等时性定）
    n_peaks: int = 1             # 本笔的 Sigma-Lognormal 运动基元数


@dataclass(frozen=True)
class HandwritingGlyph:
    """一个字的全部笔画 + 规范帧 bbox（字高=1，宽=width，居中于原点）。"""
    strokes: List[HandwritingStroke]
    width: float                 # 字高=1 单位
    height: float                # = 1.0（归一化后）


_HERSHEY_CACHE: dict = {}   # font_name -> HersheyFonts 实例（load 一次复用）


def _hershey(font: str, height: float):
    """延迟导入并缓存 HersheyFonts 实例。"""
    if font not in _HERSHEY_CACHE:
        from HersheyFonts import HersheyFonts   # 延迟导入：可选依赖
        hf = HersheyFonts()
        hf.load_default_font(font)
        _HERSHEY_CACHE[font] = hf
    hf = _HERSHEY_CACHE[font]
    hf.normalize_rendering(height)
    return hf


def _normalize_to_unit_height(strokes, bbox):
    """把笔画平移+缩放到字高=1、bbox 居中于原点。返回 (新strokes, width)。"""
    x0, y0, x1, y1 = bbox
    w = x1 - x0
    h = y1 - y0
    if h <= 0:
        h = 1.0
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0
    scale = 1.0 / h
    out = []
    for s in strokes:
        out.append([[(p[0] - cx) * scale, (p[1] - cy) * scale] for p in s])
    return out, w * scale


def _normalize_to_font_metrics(strokes, bbox, font_height: float = 21.0):
    """Keep a font's shared vertical metrics instead of normalizing each glyph.

    Hershey's normalized default fonts use y=0..21 for the line frame.  Mapping
    that common frame to [-.5, .5] preserves lowercase x-height, ascenders and
    descenders (``e`` is no longer scaled to the height of ``l``).  X remains
    locally centered; word placement supplies the per-glyph advance.
    """
    x0, _y0, x1, _y1 = bbox
    cx = (x0 + x1) / 2.0
    scale = 1.0 / font_height
    out = []
    for s in strokes:
        out.append([[(p[0] - cx) * scale, p[1] * scale - 0.5] for p in s])
    return out, (x1 - x0) * scale


def sample_glyph_ratios(style: HandwritingStyle, seed: int):
    """从 seed 采样 per-glyph 宽高比（TruncNormal，clamp ±limit）。返回 (w_ratio, h_ratio)。"""
    rng = random.Random(seed + 31)
    lim = style.glyph_ratio_limit
    wr = max(1.0 - lim, min(1.0 + lim, rng.gauss(1.0, style.glyph_width_std)))
    hr = max(1.0 - lim, min(1.0 + lim, rng.gauss(1.0, style.glyph_height_std)))
    return wr, hr


def letter_glyph(char: str, font: str = "futural",
                 style: HandwritingStyle = None, seed: int = 1,
                 slant: float = 0.0,
                 width_ratio: float = 1.0, height_ratio: float = 1.0,
                 segment: bool = False, structure: bool = False,
                 preserve_metrics: bool = False) -> HandwritingGlyph:
    """取一个字的变形笔画。

    `char`：单字符（Hershey 拉通字母/数字/符号；无中文）。
    `font`：Hershey 内置字体名（futural 最干净，cursive/scripts 手写感）。
    `seed`：空间噪声的随机身份；同 seed 同字可复现。
    """
    if style is None:
        from .style import DEFAULT_HANDWRITING
        style = DEFAULT_HANDWRITING
    if len(char) != 1:
        raise ValueError(f"letter_glyph 需要单字符；got {char!r}")

    hf = _hershey(font, 21.0)                       # 任意高度先取，后面再归一化到 1
    raw = [list(s) for s in hf.strokes_for_text(char)]
    if not raw:
        raise ValueError(f"字体 {font!r} 无字符 {char!r} 的笔画（Hershey 不含该字）")

    xs = [p[0] for s in raw for p in s]
    ys = [p[1] for s in raw for p in s]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    norm, width = (_normalize_to_font_metrics(raw, bbox)
                   if preserve_metrics else _normalize_to_unit_height(raw, bbox))

    # Glyph-level G_i: width/height ratio + baseline shear slant.
    # Values come from the caller (marks layer); defaults are identity so the
    # pure-glyph contract (height=1, bbox centered) used by old tests is preserved.
    transformed = norm
    if width_ratio != 1.0 or height_ratio != 1.0:
        transformed = [[[p[0] * width_ratio, p[1] * height_ratio] for p in s]
                       for s in transformed]
    if slant != 0.0:
        # A metric-preserving lowercase glyph may descend below the baseline.
        baseline_y = -0.25 if preserve_metrics else min(p[1] for s in transformed for p in s)
        transformed = [shear_polyline(s, slant, baseline_y) for s in transformed]
    if structure:
        transformed = structure_deform(transformed, style, seed=seed)
    if transformed is not norm:
        xs = [p[0] for s in transformed for p in s]
        width = max(xs) - min(xs)

    step = style.sample_step                       # 字高=1 单位
    strokes: List[HandwritingStroke] = []
    for i, poly in enumerate(transformed):
        if len(poly) < 2:
            continue
        sampled = resample_arclength(poly, step)
        n_peaks = 1 + len(detect_peaks(
            sampled, tau=math.radians(style.peak_turn_threshold_deg),
            min_segment_length=style.peak_min_segment_length,
            max_peaks=style.peak_max_per_stroke))
        if segment:
            sampled = segment_deform(sampled, style, seed=seed + i * 4099 + 101)
        deformed = wobble_polyline_normal(
            sampled, step=step,
            jitter_rms=style.jitter_rms,
            correlation_length=style.correlation_length,
            seed=seed + i * 7919,                  # 每笔不同子 seed，整字同 seed 可复现
            envelope=style.endpoint_envelope,
        )
        al = polyline_length(deformed)
        strokes.append(HandwritingStroke(points=deformed, arc_length=al,
                                          duration=stroke_duration(al, style, n_peaks),
                                          n_peaks=n_peaks))
    return HandwritingGlyph(strokes=strokes, width=width, height=1.0)
