"""字形 → 变形笔画。纯几何，不依赖 manim。

流程（专家）：任一 GlyphSource 的中心线 → 归一化到字高=1、bbox 居中 →
弧长均匀采样 → 法线 AR(1) 噪声 → 每笔算弧长与时长。

核心 ``_glyph`` 只依赖 :class:`GlyphSource` 协议，对语种无感知：拉丁字母走
``HersheySource``，汉字走 ``HanziSource``（见 sources/），变形/定时管道完全共用。
HersheyFonts / 汉字数据均延迟导入（可选依赖）。

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
from .sources import GlyphSource, HersheySource, HanziSource, glyph_bbox
from .style import HandwritingStyle, HANZI_HANDWRITING
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





def sample_glyph_ratios(style: HandwritingStyle, seed: int):
    """从 seed 采样 per-glyph 宽高比（TruncNormal，clamp ±limit）。返回 (w_ratio, h_ratio)。"""
    rng = random.Random(seed + 31)
    lim = style.glyph_ratio_limit
    wr = max(1.0 - lim, min(1.0 + lim, rng.gauss(1.0, style.glyph_width_std)))
    hr = max(1.0 - lim, min(1.0 + lim, rng.gauss(1.0, style.glyph_height_std)))
    return wr, hr


def _glyph(source: GlyphSource, char: str,
           style: HandwritingStyle, seed: int,
           slant: float, width_ratio: float, height_ratio: float,
           segment: bool, structure: bool, preserve_metrics: bool) -> HandwritingGlyph:
    """核心：任一 GlyphSource → 变形笔画。所有语种共用同一段几何/定时管道。"""
    if len(char) != 1:
        raise ValueError(f"_glyph 需要单字符；got {char!r}")

    raw = source.strokes_for(char)
    if not raw:
        raise ValueError(f"{source!r} 无字符 {char!r} 的笔画")

    bbox = glyph_bbox(raw)
    norm, width = source.normalize(raw, preserve_metrics, bbox)

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


def letter_glyph(char: str, font: str = "futural",
                 style: HandwritingStyle = None, seed: int = 1,
                 slant: float = 0.0,
                 width_ratio: float = 1.0, height_ratio: float = 1.0,
                 segment: bool = False, structure: bool = False,
                 preserve_metrics: bool = False) -> HandwritingGlyph:
    """取一个拉丁字母/数字/符号的变形笔画（Hershey）。

    `char`：单字符（Hershey 拉通字母/数字/符号；无中文）。
    `font`：Hershey 内置字体名（futural 最干净，cursive/scripts 手写感）。
    `seed`：空间噪声的随机身份；同 seed 同字可复现。

    本函数是 :class:`HersheySource` 的薄封装，签名与行为保持不变；
    汉字请用 :func:`hanzi_glyph`。
    """
    if style is None:
        from .style import DEFAULT_HANDWRITING
        style = DEFAULT_HANDWRITING
    return _glyph(HersheySource(font), char, style, seed=seed, slant=slant,
                  width_ratio=width_ratio, height_ratio=height_ratio,
                  segment=segment, structure=structure,
                  preserve_metrics=preserve_metrics)


def hanzi_glyph(char: str, source: HanziSource = None,
                style: HandwritingStyle = None, seed: int = 1,
                slant: float = 0.0,
                width_ratio: float = 1.0, height_ratio: float = 1.0,
                segment: bool = False, structure: bool = False) -> HandwritingGlyph:
    """取一个汉字的变形笔画（Make Me a Hanzi medians）。

    `char`：单汉字（中文/全角符号）。
    `source`：汉字数据源；缺省用平滑 Catmull-Rom 的 ``HanziSource()``。
    `style`：缺省用汉字专用默认 :data:`HANZI_HANDWRITING`（更端正、更收敛）。
    `seed`：空间噪声的随机身份；同 seed 同字可复现。
    """
    if style is None:
        style = HANZI_HANDWRITING
    if source is None:
        source = HanziSource()
    # 汉字无字体度量，preserve_metrics 恒为 False。
    return _glyph(source, char, style, seed=seed, slant=slant,
                  width_ratio=width_ratio, height_ratio=height_ratio,
                  segment=segment, structure=structure, preserve_metrics=False)
