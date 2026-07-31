"""手绘字母：Sigma-Lognormal 时间 + 法线相关噪声 + Hershey 字形。

分四层（各自可单测、无循环依赖）：
    style   配置（叶模块，零依赖）
    timing  Σ-lognormal 速度/累计/时长/提笔间隔（纯 math）
    deform  弧长采样 + 法线 AR(1) 噪声（纯几何）
    glyph   Hershey → 变形笔画（延迟导入 HersheyFonts）

manim 绑定在 marks/letter.py，播放动画在 animation.py（DrawHandwriting）。
"""
from .style import HandwritingStyle, DEFAULT_HANDWRITING
from .timing import (lognormal_mu_for_duration, lognormal_velocity, lognormal_cumulative,
                     lognormal_progress, lognormal_progress_multi, detect_peaks,
                     stroke_duration, pen_up_gap)
from .deform import (polyline_length, resample_arclength, wobble_polyline_normal)
from .segment import segment_deform
from .slant import slant_sequence, shear_polyline
from .structure import structure_deform
from .glyph import letter_glyph, HandwritingStroke, HandwritingGlyph, sample_glyph_ratios

__all__ = [
    "HandwritingStyle", "DEFAULT_HANDWRITING",
    "lognormal_mu_for_duration", "lognormal_velocity", "lognormal_cumulative",
    "lognormal_progress", "lognormal_progress_multi", "detect_peaks", "stroke_duration", "pen_up_gap",
    "polyline_length", "resample_arclength", "wobble_polyline_normal",
    "segment_deform",
    "slant_sequence", "shear_polyline",
    "structure_deform",
    "letter_glyph", "HandwritingStroke", "HandwritingGlyph", "sample_glyph_ratios",
]
