"""倾斜模型：基于基线的水平 shear + 分层随机（写者 / 单词 / 字符 AR(1)）。

shear 不是旋转——基线上的点不动，越高的点 x 偏移越大，字母仍稳稳站在基线上。
θ_i = θ_writer + δ_word + u_i，u_i 一阶相关（相邻字母倾斜相关，不会左一下右一下）。

纯 math，不依赖 manim / numpy / HersheyFonts。
"""
from __future__ import annotations

import math
import random
from typing import List, Optional, Sequence

from .style import HandwritingStyle


def slant_sequence(n: int, style: HandwritingStyle, seed: int,
                   writer_slant_deg: Optional[float] = None) -> List[float]:
    """返回 n 个字符的倾斜角（弧度）。

    θ_i = θ_writer + δ_word + u_i
    δ_word ~ N(0, σ_word²)                 整词共享一次
    u_0    ~ N(0, σ_char²)                 平稳分布
    u_i    = ρ·u_{i-1} + ε_i,  ε_i~N(0, σ_char²(1-ρ²))   → Var(u_i)=σ_char²
    |u_i|  ≤ char_slant_limit
    """
    if n <= 0:
        return []
    rng = random.Random(seed)
    theta_w = math.radians(writer_slant_deg if writer_slant_deg is not None
                           else style.writer_slant_deg)
    sigma_word = math.radians(style.word_slant_std_deg)
    sigma_char = math.radians(style.char_slant_std_deg)
    rho = style.char_slant_rho
    limit = math.radians(style.char_slant_limit_deg)
    delta_word = rng.gauss(0.0, sigma_word)
    var_eps = sigma_char ** 2 * (1.0 - rho ** 2)
    std_eps = math.sqrt(var_eps) if var_eps > 0 else 0.0

    us: List[float] = []
    for i in range(n):
        if i == 0:
            u = rng.gauss(0.0, sigma_char)
        else:
            u = rho * us[-1] + rng.gauss(0.0, std_eps)
        u = max(-limit, min(limit, u))
        us.append(u)
    return [theta_w + delta_word + u for u in us]


def shear_polyline(points: Sequence[Sequence[float]], theta: float,
                   baseline_y: float) -> List[List[float]]:
    """对一条 polyline 施加水平 shear（关于基线 baseline_y）。

    x' = x + tan(theta)·(y - baseline_y),  y' = y
    """
    t = math.tan(theta)
    return [[p[0] + t * (p[1] - baseline_y), p[1]] for p in points]