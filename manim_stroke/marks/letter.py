"""手绘字母标记：在目标旁画一个手绘字母（A/B/C…），整字母微旋微缩。

绑 manim 层：取 handwriting.letter_glyph 的变形笔画 → 缩放到目标高度 → 整字母 per-glyph
旋转/缩放 → 平移到 target 旁 → 每笔 get_stroke 描边 → 组装多笔 Mark。

层级（专家）：
    字库原始路径（glyph.py 已做法线噪声）
    → 整个 glyph 的旋转、缩放、平移（这里做，per-glyph 不是 per-stroke）
    → 排版定位

播放由 DrawHandwriting 按 per-stroke Σ-lognormal 时长 + 提笔间隔驱动；时长/间隔在
build 时按 seed 一次算定，存到 mark.handwriting_durations / mark.handwriting_gaps。
"""
from __future__ import annotations

import random
from typing import Optional

from ._common import (Mark, MarkStyle, _resolve_style, _height, _resolve_seed,
                      _to_polygon, _make_mark, _glyph_center, _transform_point,
                      _glyph_placement_params, _render_strokes)
from ..handwriting import (letter_glyph, HandwritingStyle, DEFAULT_HANDWRITING,
                            pen_up_gap, slant_sequence, sample_glyph_ratios)


def letter(target, char: str, font: str = "futural",
           size: Optional[float] = None, color=None,
           position: str = "left", offset: Optional[float] = None,
           handwriting: Optional[HandwritingStyle] = None,
           seed: Optional[int] = None, speed: str = "handwriting",
           style: Optional[MarkStyle] = None) -> Mark:
    """在目标旁画一个手绘字母。

    ``char``：单字符（Hershey 拉丁字母/数字/符号，无中文）。
    ``font``：Hershey 字体名（futural 干净、cursive/scripts 手写感）。
    ``size``：字母高度（manim 单位）；None 时按目标高度自适应。
    ``position``：相对目标的位置——left/right/above/below/upper-right/center。
    ``handwriting``：HandwritingStyle 参数集；None 用默认。
    ``seed``：空间噪声 + 字母微旋微缩 + 提笔间隔的随机身份；同 seed 可复现。
    """
    hw = handwriting or DEFAULT_HANDWRITING
    st = _resolve_style(style, default_color="#6FA8C8", color=color, size=size,
                        thinning=None, cap=None, taper=None, smoothing=None)
    seed = _resolve_seed(seed)
    desired_h = size if size is not None else _height(target) * 0.9
    gap = offset if offset is not None else _height(target) * 0.2

    # 变形笔画一次算定（空间噪声只依赖 seed，不依赖目标位置 → follow 重建可复用）
    slant = slant_sequence(1, hw, seed)[0]               # 单字：写者倾斜 + 字符变化
    w_ratio, h_ratio = sample_glyph_ratios(hw, seed)
    glyph = letter_glyph(char, font, hw, seed=seed,
                         slant=slant, width_ratio=w_ratio, height_ratio=h_ratio,
                         segment=True, structure=True)

    # 整字母 per-glyph 微旋微缩 + 提笔间隔（同 seed 稳定）
    glyph_rot, glyph_scale, pen_w, scale = _glyph_placement_params(hw, seed, desired_h)
    glyph_w = glyph.width * scale
    glyph_h = scale
    gap_rng = random.Random(seed + 101)
    gaps = [pen_up_gap(gap_rng, hw) for _ in range(max(0, len(glyph.strokes) - 1))]
    durations = [s.duration for s in glyph.strokes]

    def build():
        tx, ty = _glyph_center(target, position, glyph_w, glyph_h, gap)
        polys, clines, opts, _durs, n = _render_strokes(
            glyph, scale, glyph_rot, tx, ty, pen_w, hw, st.color)
        return (polys, clines, [pen_w] * n, [False] * n, opts)

    mark = _make_mark(target, "letter", build, speed=speed, seed=seed, variation=1.0)
    mark.handwriting_durations = durations
    mark.handwriting_peaks = [s.n_peaks for s in glyph.strokes]
    mark.handwriting_gaps = gaps
    mark.handwriting_style = hw
    return mark
