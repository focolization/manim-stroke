"""手写汉字标记：在目标旁画一个手写汉字（永/中/我…）。

与 :func:`letter` 同构，但走汉字管道：
取 :func:`hanzi_glyph` 的变形笔画 → 缩放到目标高度 → per-glyph 微旋微缩 →
平移到 target 旁 → 每笔 get_stroke 描边 → 组装多笔 Mark。

播放由 DrawHandwriting 按 per-stroke Σ-lognormal 时长 + 提笔间隔驱动。
排版/描边助手与 letter 共用（见 _common.py）。
"""
from __future__ import annotations

import random
from typing import Optional

from ._common import (Mark, MarkStyle, _resolve_style, _height, _resolve_seed,
                      _glyph_center, _glyph_placement_params, _render_strokes,
                      _make_mark)
from ..handwriting import (hanzi_glyph, HandwritingStyle, HANZI_HANDWRITING,
                           HanziSource, pen_up_gap, slant_sequence,
                           sample_glyph_ratios)


def hanzi(target, char: str,
          size: Optional[float] = None, color=None,
          position: str = "left", offset: Optional[float] = None,
          handwriting: Optional[HandwritingStyle] = None,
          source: Optional[HanziSource] = None,
          seed: Optional[int] = None, speed: str = "handwriting",
          style: Optional[MarkStyle] = None) -> Mark:
    """在目标旁画一个手写汉字。

    ``char``：单汉字。
    ``source``：汉字数据源；缺省用平滑 Catmull-Rom 的 ``HanziSource()``。
    ``handwriting``：HandwritingStyle 参数集；None 用汉字默认 HANZI_HANDWRITING。
    ``position``：相对目标的位置——left/right/above/below/upper-right/center。
    ``seed``：空间噪声 + 微旋微缩 + 提笔间隔的随机身份；同 seed 可复现。
    """
    hw = handwriting or HANZI_HANDWRITING
    st = _resolve_style(style, default_color="#2E7D6B", color=color, size=size,
                        thinning=None, cap=None, taper=None, smoothing=None)
    seed = _resolve_seed(seed)
    desired_h = size if size is not None else _height(target) * 0.9
    gap = offset if offset is not None else _height(target) * 0.15

    # 变形笔画一次算定（空间噪声只依赖 seed，不依赖目标位置 → follow 重建可复用）
    slant = slant_sequence(1, hw, seed)[0]
    w_ratio, h_ratio = sample_glyph_ratios(hw, seed)
    # 汉字 v1 关闭结构变形（HANZI_HANDWRITING.structure_std=0；部件级变形待后续）
    glyph = hanzi_glyph(char, source=source, style=hw, seed=seed,
                        slant=slant, width_ratio=w_ratio, height_ratio=h_ratio,
                        segment=True, structure=False)

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

    mark = _make_mark(target, "hanzi", build, speed=speed, seed=seed, variation=1.0)
    mark.handwriting_durations = durations
    mark.handwriting_peaks = [s.n_peaks for s in glyph.strokes]
    mark.handwriting_gaps = gaps
    mark.handwriting_style = hw
    return mark
