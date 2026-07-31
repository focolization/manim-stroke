"""手写单词 StrokeText：多字母并排，位置在创建时烤进 polygons+centerlines。

用法：
    word = StrokeText("TEACH", font="futural", size=1.8, at=ORIGIN,
                      handwriting=HandwritingStyle(), seed=7)
    self.play(DrawHandwriting(word))

整词是一条 Mark：所有字母的笔画按书写顺序串成一个 centerlines/durations/gaps 序列，
DrawHandwriting 用 Succession 逐笔播放，笔间和字母间都留 pen-up 静默。
位置只能创建时定（``at``），不能事后 move_to——centerlines 是绝对坐标，move_to 只挪
成品多边形会让动画在原位画（如需移动，重建时换 ``at``）。
"""
from __future__ import annotations

import random
from typing import Optional

from manim import ORIGIN

from ._common import Mark, _resolve_seed
from ..handwriting import (letter_glyph, HandwritingStyle, DEFAULT_HANDWRITING,
                           pen_up_gap, slant_sequence, sample_glyph_ratios)
from .letter import _glyph_placement_params, _render_strokes


def _build_glyph_at(glyph, size, hw, seed, tx, ty, color):
    """从已建好的 HandwritingGlyph 变形笔画到 (tx,ty) 居中，返回
    (polygons, centerlines, options, durations, n_strokes)。"""
    glyph_rot, _gs, pen_w, scale = _glyph_placement_params(hw, seed, size)
    return _render_strokes(glyph, scale, glyph_rot, tx, ty, pen_w, hw, color)


class StrokeText(Mark):
    """手写单词：字母并排，整词一条 Mark，DrawHandwriting 整词播放。"""

    def __init__(self, text: str, font: str = "futural", size: float = 1.5,
                 color: str = "#6FA8C8", at=ORIGIN,
                 handwriting: Optional[HandwritingStyle] = None,
                 seed: Optional[int] = None, letter_gap: Optional[float] = None,
                 speed: str = "handwriting", segment: bool = True,
                 space_width: float = 0.42):
        """Create handwritten Latin text.

        Spaces are layout advances, not Hershey glyphs: ``"learn with manim"``
        works directly.  ``space_width`` is expressed in units of ``size``.
        """
        hw = handwriting or DEFAULT_HANDWRITING
        seed = _resolve_seed(seed)
        if not text or not text.strip():
            raise ValueError("StrokeText requires at least one non-space character")
        if space_width < 0:
            raise ValueError("space_width must be non-negative")
        lgap = letter_gap if letter_gap is not None else 0.15 * size
        gap_rng = random.Random(seed)
        slants = slant_sequence(len(text), hw, seed)          # 单词级倾斜 AR(1) 序列

        # Whitespace has no Hershey strokes; retain it as an advance before the
        # next drawable glyph instead of attempting letter_glyph(" ").
        # Each entry is (glyph, rendered_width, number_of_leading_spaces).
        entries = []
        pending_spaces = 0
        for i, ch in enumerate(text):
            if ch.isspace():
                pending_spaces += 1
                continue
            wr, hr = sample_glyph_ratios(hw, seed + i)
            g = letter_glyph(ch, font, hw, seed=seed + i,
                             slant=slants[i], width_ratio=wr, height_ratio=hr,
                             segment=segment, structure=True,
                             preserve_metrics=True)
            entries.append((g, g.width * size, pending_spaces))
            pending_spaces = 0

        total = (sum(width for _glyph, width, _spaces in entries)
                 + lgap * (len(entries) - 1)
                 + sum(spaces * space_width * size
                       for _glyph, _width, spaces in entries))
        cursor = at[0] - total / 2
        ty = at[1]

        all_polys, all_clines, all_opts, all_durs, all_peaks, all_gaps = [], [], [], [], [], []
        for i, (glyph, w, leading_spaces) in enumerate(entries):
            cursor += leading_spaces * space_width * size
            cx = cursor + w / 2
            polys, clines, opts, durs, n_strokes = _build_glyph_at(
                glyph, size, hw, seed + i, cx, ty, color)
            all_polys += polys
            all_clines += clines
            all_opts += opts
            all_durs += durs
            all_peaks += [s.n_peaks for s in glyph.strokes]
            all_gaps += [pen_up_gap(gap_rng, hw) for _ in range(n_strokes - 1)]  # 笔间
            if i < len(entries) - 1:
                # A word boundary is a visibly longer pen-up movement, while
                # still using the same deterministic random identity.
                gap = pen_up_gap(gap_rng, hw)
                if entries[i + 1][2]:
                    gap += entries[i + 1][2] * hw.pen_up_mean
                all_gaps.append(gap)
            cursor += w + lgap

        super().__init__(*all_polys, kind="letter", speed=speed, seed=seed,
                         centerlines=all_clines, stroke_options=all_opts)
        self.handwriting_durations = all_durs
        self.handwriting_peaks = all_peaks
        self.handwriting_gaps = all_gaps
        self.handwriting_style = hw
