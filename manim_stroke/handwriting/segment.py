"""局部分段变形（论文第六节）：高曲率切分 → 逐段旋转缩放 → 段起点钉到上一段变形终点。

破掉 Hershey 的 CAD 精确感，让"同一个人每次写得不一样"。每段独立小幅仿射，
段间锚点链接（a_{j+1} = 第 j 段变形后的终点）保证路径连续。每个字母/每笔用独立
seed → 字母间 visibly 不同。

处理顺序在 shear 之后、法线噪声之前。纯几何，不依赖 manim。
"""
from __future__ import annotations

import math
import random
from typing import List, Sequence

from .style import HandwritingStyle


def _turning_angles_deg(points: Sequence[Sequence[float]]) -> List[float]:
    """每个内部点 j（1..n-1）处的离散转角（度）。turns[j-1] 对应点 j。"""
    n = len(points)
    if n < 3:
        return []
    phi = []
    for i in range(n):
        if i == 0:
            dx = points[1][0] - points[0][0]
            dy = points[1][1] - points[0][1]
        elif i == n - 1:
            dx = points[-1][0] - points[-2][0]
            dy = points[-1][1] - points[-2][1]
        else:
            dx = points[i + 1][0] - points[i - 1][0]
            dy = points[i + 1][1] - points[i - 1][1]
        phi.append(math.atan2(dy, dx))
    turns = []
    for i in range(n - 1):
        d = phi[i + 1] - phi[i]
        while d > math.pi:
            d -= 2 * math.pi
        while d < -math.pi:
            d += 2 * math.pi
        turns.append(math.degrees(d))
    return turns


def _arclength(points: Sequence[Sequence[float]], a: int, b: int) -> float:
    return sum(math.dist(points[k], points[k + 1]) for k in range(a, b))


def _split_segments(points, tau_deg: float, min_len: float) -> List[int]:
    """返回分段边界索引 [0, j1, j2, ..., n-1]。高曲率点作边界，最小段长约束。"""
    n = len(points)
    if n < 4:
        return [0, n - 1]
    turns = _turning_angles_deg(points)
    # 候选边界：内部点 j（1..n-2）处 |turns[j-1]| > tau
    cand = [j for j in range(1, n - 1) if abs(turns[j - 1]) > tau_deg]
    splits = [0]
    last = 0
    for j in cand:
        if _arclength(points, last, j) >= min_len:
            splits.append(j)
            last = j
    # 末段太短则丢掉最后一个内部分点，再补 n-1
    if len(splits) > 1 and _arclength(points, splits[-1], n - 1) < min_len:
        splits.pop()
    if splits[-1] != n - 1:
        splits.append(n - 1)
    return splits


def segment_deform(points: Sequence[Sequence[float]],
                   style: HandwritingStyle, seed: int) -> List[List[float]]:
    """对一条 polyline 施加局部分段变形（ chained per-segment affine ）。

    第一个点固定（第一段锚点）；后续每段绕自己的起点（=上一段变形终点）旋转+缩放。
    """
    n = len(points)
    if n < 4:
        return [list(p) for p in points]

    rng = random.Random(seed)
    tau = style.segment_turn_threshold_deg
    min_len = style.segment_min_length
    rot_std = math.radians(style.segment_rot_std_deg)
    rot_lim = math.radians(style.segment_rot_limit_deg)
    sx_std = style.segment_scale_x_std
    sy_std = style.segment_scale_y_std
    slim = style.segment_scale_limit

    splits = _split_segments(points, tau, min_len)

    def clamp_rot(v):
        return max(-rot_lim, min(rot_lim, v))

    def clamp_scale(v):
        return max(1.0 - slim, min(1.0 + slim, v))

    out: List[List[float]] = [list(points[0])]
    for si in range(len(splits) - 1):
        a, b = splits[si], splits[si + 1]
        ax, ay = out[-1]                      # chained anchor = previous deformed end
        alpha = clamp_rot(rng.gauss(0.0, rot_std))
        sx = clamp_scale(rng.gauss(1.0, sx_std))
        sy = clamp_scale(rng.gauss(1.0, sy_std))
        c, s = math.cos(alpha), math.sin(alpha)
        for p in points[a + 1:b + 1]:         # skip the shared start (already in out)
            dx = (p[0] - ax) * sx
            dy = (p[1] - ay) * sy
            out.append([ax + dx * c - dy * s, ay + dx * s + dy * c])
    return out