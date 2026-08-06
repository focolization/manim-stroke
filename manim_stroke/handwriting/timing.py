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
                             n_peaks: int = 1, overlap: float = 0.4,
                             completion_quantile: float = 0.995) -> float:
    """Overlapping 1D Sigma-Lognormal pulses → progress, normalized to [0, 1].

    Geometry/kinematics decoupling: the prescribed centerline γ(s) is never
    changed; only the scalar time law s(t) is shaped.  Each ``n_peaks`` virtual
    target contributes a full lognormal velocity pulse, and consecutive pulses
    **overlap** in time (the next starts before the previous has ended).  The
    summed speed (d progress / d α) therefore dips at corners but never hits a
    hard zero plateau — the corner deceleration emerges naturally from the
    pulse overlap and geometry, not from an inserted ``command_spacing`` wait.

    ``overlap`` ∈ [0, 0.95] is the fraction of a pulse's width shared with its
    neighbour.  ``n_peaks == 1`` is exactly the legacy :func:`lognormal_progress`.
    """
    n = max(1, int(n_peaks))
    if n == 1:
        return lognormal_progress(alpha, sigma, completion_quantile)
    alpha = max(0.0, min(1.0, alpha))
    overlap = max(0.0, min(0.95, float(overlap)))
    step = 1.0 / n                       # evenly spaced pulse starts
    width = step / (1.0 - overlap)       # > step ⇒ neighbours overlap

    def raw(a: float) -> float:
        total = 0.0
        for i in range(n):
            local = (a - i * step) / width
            if local <= 0.0:
                c = 0.0
            elif local >= 1.0:
                c = 1.0
            else:
                c = lognormal_progress(local, sigma, completion_quantile)
            total += c / n
        return total

    full = raw(1.0)                      # guarantee p(1) == 1 exactly
    if full <= 0.0:
        return 0.0
    return min(1.0, raw(alpha) / full)


def stroke_duration(length: float, style: HandwritingStyle, n_peaks: int = 1) -> float:
    """笔画时长（秒）。等时性：T = T_ref·(length/ref)^exponent，再 clamp。

    长度翻倍 → 时长约 ×1.13；不是线性。拐角的减速由重叠脉冲自然产生，
    因此不再为多峰额外累加停顿时间。
    """
    if length <= 0:
        return style.duration_min
    T = style.duration_ref * (length / style.reference_length) ** style.length_exponent
    return max(style.duration_min, min(style.duration_max, T))


def minimum_jerk_transition(t: float, T: float, p0, p1):
    """Flash–Hogan minimum-jerk interpolation from ``p0`` to ``p1`` over [0, T].

    Returns the 2D position at time ``t``.  Velocity and acceleration are zero at
    both endpoints (smooth pen lift / lower), matching classical handwriting
    trajectory synthesis (Edelman & Flash 1987).
    """
    u = max(0.0, min(1.0, t / T)) if T > 0 else 1.0
    tau = 10.0 * u ** 3 - 15.0 * u ** 4 + 6.0 * u ** 5
    return [p0[0] + (p1[0] - p0[0]) * tau, p0[1] + (p1[1] - p0[1]) * tau]


def minimum_jerk_velocity(t: float, T: float, p0, p1):
    """Velocity vector of the minimum-jerk transition (zero at both endpoints)."""
    u = max(0.0, min(1.0, t / T)) if T > 0 else 0.0
    dtau = 30.0 * u ** 2 * (1.0 - u) ** 2 / T if T > 0 else 0.0
    return [(p1[0] - p0[0]) * dtau, (p1[1] - p0[1]) * dtau]


def speed_curvature_violation(speeds, curvatures):
    """Two-thirds power law check: |v| ∝ κ^(-1/3) ⇒ |v|·κ^(1/3) ≈ const.

    Returns the coefficient of variation of ``|v|·κ^(1/3)`` over the samples
    (lower is closer to the human law).  ``None`` if no valid samples.
    """
    vals = [v * (k ** (1.0 / 3.0))
            for v, k in zip(speeds, curvatures) if v > 0 and k > 0]
    if not vals:
        return None
    mean = sum(vals) / len(vals)
    if mean <= 0:
        return None
    var = sum((x - mean) ** 2 for x in vals) / len(vals)
    return (var ** 0.5) / mean


def pen_up_gap(rng: random.Random, style: HandwritingStyle) -> float:
    """笔画间提笔静默时长（秒）。截断高斯，均值 ~90ms。"""
    return max(style.pen_up_min, min(style.pen_up_max,
                                     rng.gauss(style.pen_up_mean, style.pen_up_std)))
