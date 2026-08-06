"""路径变形：弧长均匀采样 + 法线方向 AR(1) 相关噪声。纯几何，不依赖 manim/Hershey。

专家定的一层变形（不是两层）：
    按弧长均匀采样 → 在采样点法线方向加 AR(1) 相关噪声 → 端点包络衰减 →（描边交给 perfect-freehand）
ρ 不存固定值，存「相关长度」：ρ = exp(-sample_step / correlation_length)，步长变了 ρ 跟着变。
噪声是 AR(1)/OU：n[i] = ρ·n[i-1] + √(1-ρ²)·ε[i]，ε~N(0, jitter_rms²)，rms 稳定为 jitter_rms。
绝不逐点独立随机（会成锯齿），绝不每帧重算（线会蠕动）——seed 固定，build 时一次算定。
"""
from __future__ import annotations

import math
import random
from typing import List, Sequence

Point = Sequence[float]


def polyline_length(points: Sequence[Point]) -> float:
    """折线总弧长。"""
    if len(points) < 2:
        return 0.0
    return sum(math.dist(points[i][:2], points[i + 1][:2]) for i in range(len(points) - 1))


def resample_arclength(points: Sequence[Point], step: float) -> List[List[float]]:
    """按弧长均匀重采样，步长 `step`。保留首末点；step 过大或点太少时原样返回。"""
    n = len(points)
    if n < 2 or step <= 0:
        return [[p[0], p[1]] for p in points]
    seg = [math.dist(points[i][:2], points[i + 1][:2]) for i in range(n - 1)]
    total = sum(seg)
    if total == 0 or step >= total:
        return [[points[0][0], points[0][1]], [points[-1][0], points[-1][1]]]

    out: List[List[float]] = [[points[0][0], points[0][1]]]
    i = 0                      # 当前所在段的索引
    acc = 0.0                  # 已走出当前段的距离
    target = step              # 下一个采样点的累计弧长
    walked = 0.0               # 已走总弧长
    while i < n - 1:
        seg_len = seg[i]
        remain_seg = seg_len - acc
        remain_to_target = target - walked
        if remain_seg >= remain_to_target:
            # 在当前段内插出一个采样点
            acc += remain_to_target
            walked = target
            r = acc / seg_len if seg_len > 0 else 0.0
            a, b = points[i], points[i + 1]
            out.append([a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r])
            target += step
        else:
            walked += remain_seg
            acc = 0.0
            i += 1
    # 末点严格落回原末点，避免采样误差把端点挪走
    if (out[-1][0] != points[-1][0]) or (out[-1][1] != points[-1][1]):
        out.append([points[-1][0], points[-1][1]])
    return out


def _tangents(points: Sequence[Point]) -> List[List[float]]:
    """每点切向（单位向量）。端点用前/后向差，中间用中心差。"""
    n = len(points)
    tang = [[0.0, 0.0]] * n
    for i in range(n):
        if i == 0:
            dx = points[1][0] - points[0][0]; dy = points[1][1] - points[0][1]
        elif i == n - 1:
            dx = points[-1][0] - points[-2][0]; dy = points[-1][1] - points[-2][1]
        else:
            dx = points[i + 1][0] - points[i - 1][0]; dy = points[i + 1][1] - points[i - 1][1]
        L = math.hypot(dx, dy)
        tang[i] = [dx / L, dy / L] if L > 0 else [1.0, 0.0]
    return tang


def wobble_polyline_normal(points: Sequence[Point], *, step: float,
                           jitter_rms: float, correlation_length: float,
                           seed: int, envelope: bool = True) -> List[List[float]]:
    """沿采样点法线方向施加 AR(1) 相关噪声，返回变形后的点列。

    要求 `points` 已按弧长均匀采样、间距约 `step`（先用 resample_arclength）。
    ρ = exp(-step/correlation_length)；端点包络 sin(π·progress)² 让首末不动。
    """
    n = len(points)
    if n < 2 or jitter_rms == 0 or correlation_length <= 0:
        return [[p[0], p[1]] for p in points]
    rho = math.exp(-step / correlation_length)
    rng = random.Random(seed)
    drift = math.sqrt(max(0.0, 1.0 - rho * rho))

    # AR(1) 法向噪声序列（rms 稳定 = jitter_rms）
    noise = [rng.gauss(0.0, 1.0) * jitter_rms]
    for _ in range(1, n):
        noise.append(rho * noise[-1] + drift * rng.gauss(0.0, 1.0) * jitter_rms)

    tang = _tangents(points)
    out: List[List[float]] = []
    for i in range(n):
        if envelope and (i == 0 or i == n - 1):
            out.append([points[i][0], points[i][1]])      # 端点钉死，接缝不乱跑
            continue
        # 法向 = 切向逆时针转 90°：(tx,ty) → (-ty,tx)
        nx, ny = -tang[i][1], tang[i][0]
        amp = noise[i]
        if envelope:
            prog = i / (n - 1)
            amp *= math.sin(math.pi * prog) ** 2          # 端点附近衰减
        out.append([points[i][0] + nx * amp, points[i][1] + ny * amp])
    return out