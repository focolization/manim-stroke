"""手绘字母的视觉与运动参数（v1 默认值，专家拍板）。

纯数据 dataclass，不依赖 manim / numpy / HersheyFonts——是 handwriting 子包的叶模块，
timing / deform / glyph 都从这里读参数。改默认 = 改这里一处。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HandwritingStyle:
    """手绘字母的完整参数集。字母高度归一为 1 时，所有空间量都以「字高」为单位。"""

    # ── 时间：Sigma-Lognormal ──
    duration_ref: float = 0.50          # 参考笔画时长（秒），字高=1 时
    length_exponent: float = 0.18       # 等时性：T ∝ length^exponent（次线性）
    reference_length: float = 1.0       # power-law 的参考长度（字高=1）
    lognormal_sigma: float = 0.35       # 对数时间标准差
    completion_quantile: float = 0.995  # 在总时长 T 时完成此分位 → 反算 μ
    command_spacing: float = 0.08       # 多峰时相邻运动基元之间的停顿（秒）
    peak_turn_threshold_deg: float = 55.0  # 累计转角超过此值时新增一个运动基元
    peak_min_segment_length: float = 0.12  # 峰之间最短弧长（字高=1）
    peak_max_per_stroke: int = 3
    duration_min: float = 0.35
    duration_max: float = 0.75

    # ── 提笔（pen-up）──
    pen_up_mean: float = 0.090          # 秒
    pen_up_std: float = 0.015
    pen_up_min: float = 0.060
    pen_up_max: float = 0.130

    # ── 空间抖动：法线方向 AR(1) 相关噪声 ──
    sample_step: float = 0.015          # 弧长均匀采样步长（字高=1）
    jitter_rms: float = 0.006           # 法线噪声 RMS（字高=1）
    correlation_length: float = 0.18    # 相关长度（字高=1）；ρ = exp(-step/corr_len)
    endpoint_envelope: bool = True      # 端点附近 sin(π·progress)² 衰减，接缝不乱跑

    # ── 整字母仿射（per-glyph，不是 per-stroke）──
    glyph_rotation_std_deg: float = 0.4
    glyph_rotation_limit_deg: float = 1.0
    glyph_scale_std: float = 0.007
    glyph_scale_min: float = 0.985
    glyph_scale_max: float = 1.015

    # Slant (baseline horizontal shear, NOT rotation)
    writer_slant_deg: float = 8.0       # writer main slant
    word_slant_std_deg: float = 0.5     # word-level drift sigma
    char_slant_std_deg: float = 1.2     # char-level sigma
    char_slant_rho: float = 0.65        # char-level AR(1) correlation
    char_slant_limit_deg: float = 3.0   # |u_i| clamp

    # Glyph width/height ratio
    glyph_width_std: float = 0.02       # width sigma (+-2%)
    glyph_height_std: float = 0.02      # height sigma (+-2%)
    glyph_ratio_limit: float = 0.05     # ratio clamp +-5%

    # Structural variation.  The same two latent variables are reused by a glyph's
    # primitives, so bowls, legs and openings vary as one writer rather than as
    # independent noise.  ``structure`` remains opt-in at letter_glyph level.
    structure_std: float = 0.055
    structure_limit: float = 0.12

    # Local segment deformation (paper sec 6): break CAD precision, per-letter variation
    segment_turn_threshold_deg: float = 50.0   # high-curvature split threshold
    segment_min_length: float = 0.12           # min segment arclength (height=1 units)
    segment_rot_std_deg: float = 1.2           # per-segment rotation sigma
    segment_rot_limit_deg: float = 3.0         # rotation clamp
    segment_scale_x_std: float = 0.02          # per-segment x-scale sigma (+-2%)
    segment_scale_y_std: float = 0.012         # per-segment y-scale sigma (+-1.2%)
    segment_scale_limit: float = 0.05          # scale clamp +-5%

    # ── 描边（交 perfect-freehand）──
    streamline: float = 0.25
    smoothing: float = 0.55
    stroke_size_ratio: float = 0.085     # 笔宽 = 字高 × 此值（对齐下划线/删除线的 ~0.08）
    pen_taper_frac: float = 0.0         # 起笔/收笔渐细长度 = 笔画弧长 × 此值（0=圆头，>0=渐尖，毛笔感）

    # ── 笔宽 × 速度耦合（v1 关闭）──
    # 真实笔压与运动学弱相关；v1 先保路径/速度/起收笔自然，压感留待后续。
    speed_width_alpha: float = 0.0


# 子包内共享的单一默认实例；调用方也可传自己的。
DEFAULT_HANDWRITING = HandwritingStyle()
