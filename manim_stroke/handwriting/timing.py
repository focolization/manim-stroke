"""Sigma-Lognormal 时间曲线 + 笔画时长 + 提笔间隔。纯 math，不依赖 manim/numpy/Hershey。

核心原则（专家）：不要把 μ 当独立随机参数。先定 T 和 σ，再反算 μ 使在 T 处完成
`completion_quantile` 分位。归一化后进度曲线只依赖 σ（与 T 无关），T 只决定真实时长。

单峰速度：  v(t) = D / (σ√(2π)(t-t0)) · exp(-(ln(t-t0)-μ)² / (2σ²))
累计路程：  S(t) = D · Φ((ln(t-t0)-μ)/σ)
归一进度：  progress(α) = S(αT)/S(T) = Φ(ln(α)/σ + z) / Φ(z)，α∈[0,1]，z=inv_cdf(quantile)
"""
from __future__ import annotations

import math
import random
from statistics import NormalDist

from .style import HandwritingStyle


def _z_for_quantile(q: float) -> float:
    """标准正态的分位点 z（completion_quantile → z）。"""
    return NormalDist().inv_cdf(q)


def lognormal_mu_for_duration(duration: float, sigma: float = 0.35,
                              t0: float = 0.0, completion_quantile: float = 0.995) -> float:
    """反算 μ：使在 `duration` 处累计到 `completion_quantile`。

    μ = ln(duration - t0) - z·σ。这是把「T、σ 定了，μ 随之定」的约束做成显式公式。
    """
    if duration <= t0:
        raise ValueError(f"duration must be greater than t0; got duration={duration}, t0={t0}")
    return math.log(duration - t0) - _z_for_quantile(completion_quantile) * sigma


def lognormal_velocity(t: float, mu: float, sigma: float,
                       t0: float = 0.0, D: float = 1.0) -> float:
    """单峰对数正态速度 v(t)。t ≤ t0 时返回 0。"""
    dt = t - t0
    if dt <= 0:
        return 0.0
    return (D / (sigma * math.sqrt(2.0 * math.pi) * dt)
            * math.exp(-(math.log(dt) - mu) ** 2 / (2.0 * sigma * sigma)))


def lognormal_cumulative(t: float, mu: float, sigma: float,
                         t0: float = 0.0, D: float = 1.0) -> float:
    """累计路程 S(t) = D·Φ((ln(t-t0)-μ)/σ)。t ≤ t0 时返回 0。"""
    dt = t - t0
    if dt <= 0:
        return 0.0
    return D * 0.5 * (1.0 + math.erf((math.log(dt) - mu) / (sigma * math.sqrt(2.0))))


def lognormal_progress(alpha: float, sigma: float = 0.35,
                       completion_quantile: float = 0.995) -> float:
    """归一化 Sigma-Lognormal 进度：α∈[0,1] → 已走路程比例。

    与 T 无关（T 只缩放时间轴）；形状只由 σ 与 completion_quantile 决定。
    给动画的 rate_func 用：起笔慢→中间快→收笔慢的不对称钟形。
    """
    alpha = max(0.0, min(1.0, alpha))
    if alpha == 0.0:
        return 0.0
    z = _z_for_quantile(completion_quantile)
    cdf = lambda t: 0.5 * (1.0 + math.erf((math.log(t) + z * sigma) / (sigma * math.sqrt(2.0))))
    return min(1.0, cdf(alpha) / cdf(1.0))


def detect_peaks(polyline, tau: float = math.radians(55.0),
                 min_segment_length: float = 0.12, max_peaks: int = 3):
    """Return interior indices that split a polyline into motor primitives.

    A primitive boundary is placed after the accumulated unsigned turning angle
    exceeds ``tau`` *and* both adjacent pieces have enough arclength.  This is
    deliberately geometric (no glyph-name table): an L-shaped pen stroke gets
    two commands, while a smooth C remains one.  At most ``max_peaks`` commands
    are returned, i.e. at most ``max_peaks - 1`` boundaries.
    """
    if len(polyline) < 3 or max_peaks <= 1:
        return []
    seg = [math.dist(a, b) for a, b in zip(polyline, polyline[1:])]
    total = sum(seg)
    if total < 2.0 * min_segment_length:
        return []
    travelled = 0.0
    turn = 0.0
    out = []
    for i in range(1, len(polyline) - 1):
        travelled += seg[i - 1]
        ax, ay = polyline[i][0] - polyline[i - 1][0], polyline[i][1] - polyline[i - 1][1]
        bx, by = polyline[i + 1][0] - polyline[i][0], polyline[i + 1][1] - polyline[i][1]
        na, nb = math.hypot(ax, ay), math.hypot(bx, by)
        if na == 0.0 or nb == 0.0:
            continue
        cosine = max(-1.0, min(1.0, (ax * bx + ay * by) / (na * nb)))
        turn += math.acos(cosine)
        remaining = total - travelled
        if (turn >= tau and travelled >= min_segment_length
                and remaining >= min_segment_length):
            out.append(i)
            if len(out) >= max_peaks - 1:
                break
            travelled = 0.0
            turn = 0.0
            total = remaining
    return out


def lognormal_progress_multi(alpha: float, sigma: float = 0.35,
                             n_peaks: int = 1, t0_spacing: float = 0.0,
                             completion_quantile: float = 0.995) -> float:
    """Progress for sequential Sigma-Lognormal commands, normalized to [0, 1].

    ``t0_spacing`` is expressed in the same normalized time axis as ``alpha``.
    Each command receives equal path length and a full lognormal pulse; the
    spacing becomes a genuine low-speed plateau at a hard corner.  One peak is
    exactly the legacy :func:`lognormal_progress` curve.
    """
    n_peaks = max(1, int(n_peaks))
    if n_peaks == 1:
        return lognormal_progress(alpha, sigma, completion_quantile)
    alpha = max(0.0, min(1.0, alpha))
    gap = max(0.0, float(t0_spacing))
    # Leave every command a usable interval even if a caller supplies a large gap.
    gap = min(gap, 0.8 / max(1, n_peaks - 1))
    command_span = (1.0 - gap * (n_peaks - 1)) / n_peaks
    result = 0.0
    for command in range(n_peaks):
        start = command * (command_span + gap)
        local = (alpha - start) / command_span
        if local >= 1.0:
            progress = 1.0
        elif local <= 0.0:
            progress = 0.0
        else:
            progress = lognormal_progress(local, sigma, completion_quantile)
        result += progress / n_peaks
    return min(1.0, result)


def stroke_duration(length: float, style: HandwritingStyle, n_peaks: int = 1) -> float:
    """笔画时长（秒）。等时性：T = T_ref·(length/ref)^exponent，再 clamp。

    长度翻倍 → 时长约 ×1.13；不是线性。复杂笔画更久应来自峰更多，而非弧长拖长。
    """
    if length <= 0:
        return style.duration_min
    T = style.duration_ref * (length / style.reference_length) ** style.length_exponent
    T += max(0, int(n_peaks) - 1) * style.command_spacing
    return max(style.duration_min, min(style.duration_max, T))


def pen_up_gap(rng: random.Random, style: HandwritingStyle) -> float:
    """笔画间提笔静默时长（秒）。截断高斯，均值 ~90ms。"""
    return max(style.pen_up_min, min(style.pen_up_max,
                                     rng.gauss(style.pen_up_mean, style.pen_up_std)))
