"""沿中心线即时留下实心笔迹的 Manim 动画。"""
from __future__ import annotations

import math

from manim import Animation, AnimationGroup, Polygon, Succession, Wait, linear

from .freehand import get_stroke
from .handwriting import (lognormal_progress as _handwriting_progress,
                          lognormal_progress_multi as _handwriting_progress_multi)


def _smoothstep(alpha: float) -> float:
    """谨慎描写：起笔、收笔都明显放缓。"""
    alpha = max(0.0, min(1.0, alpha))
    return alpha * alpha * (3 - 2 * alpha)


def _natural(alpha: float) -> float:
    """日常书写：触纸后渐快，末端仍带一点行笔惯性。"""
    alpha = max(0.0, min(1.0, alpha))
    return alpha * alpha * (2.3 - 1.3 * alpha)


def _decisive(alpha: float) -> float:
    """果断的一笔：快速推进，末端自然收住。"""
    alpha = max(0.0, min(1.0, alpha))
    return 1 - (1 - alpha) ** 3


def _flick(alpha: float) -> float:
    """快速甩笔：大部分位移在前段完成，末端短促收住。"""
    alpha = max(0.0, min(1.0, alpha))
    return 1 - (1 - alpha) ** 4


def _careful(alpha: float) -> float:
    """谨慎描写：起笔和收笔都更明显地放缓。"""
    alpha = max(0.0, min(1.0, alpha))
    return 0.5 - 0.5 * math.cos(math.pi * alpha)


def _circle_gesture(alpha: float) -> float:
    """圈的落笔—巡航—提笔节奏。

    圆周中段曲率近乎恒定，人的手在这里也接近匀速；不自然的部分主要在
    落笔和抬笔。因此把时间分成短暂的落笔定向、较长的稳定巡航，以及尾部
    的减速收笔，而不是给整圈套一个对称缓动。
    """
    alpha = max(0.0, min(1.0, alpha))
    # (时间, 已走过的弧长比例)。中段斜率约 1.20，明显快于两端。
    anchors = ((0.0, 0.0), (0.16, 0.075), (0.83, 0.88), (1.0, 1.0))
    for (t0, p0), (t1, p1) in zip(anchors, anchors[1:]):
        if alpha <= t1:
            local = (alpha - t0) / (t1 - t0)
            return p0 + (p1 - p0) * _smoothstep(local)
    return 1.0


def _lognormal_stroke(alpha: float, *, mu: float = -1.0, sigma: float = 0.55) -> float:
    """一个快速人类笔画的归一化 Sigma-Lognormal 位移。

    Kinematic Theory 将手写的每个运动单元描述为不对称的 lognormal 速度脉冲：
    落笔后加速，较早达到峰值，随后留出更长的收笔尾巴。这里积分该速度得到
    位移；它比对称 ease 更贴近真实的一笔直线或斜线。
    """
    alpha = max(0.0, min(1.0, alpha))
    if alpha == 0.0:
        return 0.0
    scale = sigma * math.sqrt(2.0)
    cdf = lambda t: 0.5 * (1.0 + math.erf((math.log(t) - mu) / scale))
    return min(1.0, cdf(alpha) / cdf(1.0))


_SPEED_CURVES = {
    "steady": lambda alpha: alpha,
    "natural": _natural,
    "decisive": _decisive,
    "careful": _careful,
    "flick": _flick,
    "circle": _circle_gesture,
    "line": _lognormal_stroke,
    "check": _lognormal_stroke,
    "handwriting": _handwriting_progress,   # 字母：Σ-lognormal 归一进度（形状只由 σ 决定）
}


def _partial_centerline(points, alpha: float):
    """按弧长截取中心线，并在当前线段插入精确的笔尖位置。"""
    if len(points) < 2:
        return points
    lengths = [math.dist(a[:2], b[:2]) for a, b in zip(points, points[1:])]
    total = sum(lengths)
    if total == 0:
        return points[:1]

    target = total * alpha
    walked = 0.0
    partial = [points[0]]
    for start, end, length in zip(points, points[1:], lengths):
        if walked + length >= target:
            ratio = 0 if length == 0 else (target - walked) / length
            partial.append([
                start[0] + (end[0] - start[0]) * ratio,
                start[1] + (end[1] - start[1]) * ratio,
            ])
            return partial
        partial.append(end)
        walked += length
    return partial


def _polygon_from_outline(outline, template: Polygon) -> Polygon:
    """用模板的视觉样式创建新的、已增长到当前笔尖的最终笔迹。"""
    return Polygon(
        *[(point[0], point[1], 0) for point in outline],
        fill_color=template.get_fill_color(),
        fill_opacity=template.get_fill_opacity(),
        stroke_width=0,
    )


class ProgressiveStroke(Animation):
    """把同一个最终 Polygon 逐帧增长为已写出的 freehand 笔迹。"""

    def __init__(self, polygon: Polygon, centerline, stroke_options: dict,
                 speed="natural", kind: str = "mark", **kwargs):
        # speed 可以是 _SPEED_CURVES 的键，也可以是直接的可调用速率曲线 α→进度。
        # 后者供 DrawHandwriting 传入按 HandwritingStyle.σ 生成的 Σ-lognormal 曲线。
        if callable(speed):
            self.progress_curve = speed
            self.speed = "custom"
        elif speed in _SPEED_CURVES:
            self.progress_curve = _SPEED_CURVES[speed]
            self.speed = speed
        else:
            raise ValueError(f"unknown speed {speed!r}; choose from {tuple(_SPEED_CURVES)} or pass a callable")
        self.centerline = centerline
        self.stroke_options = dict(stroke_options)
        self._final_polygon = polygon.copy()
        self.kind = kind
        super().__init__(polygon, introducer=True, rate_func=linear, **kwargs)

    def interpolate_mobject(self, alpha: float) -> None:
        if self.kind == "check" and self.speed == "check":
            # ✓ 是两个独立的运动单元：短腿落下，过拐点后重新上挑。每段分别
            # 用不对称的 Sigma-Lognormal 脉冲，而不是把整条折线当成一笔。
            corner_time, corner_length = 0.36, 0.34
            if alpha < corner_time:
                progress = corner_length * _lognormal_stroke(alpha / corner_time,
                                                              mu=-.82, sigma=.62)
            else:
                progress = corner_length + (1 - corner_length) * _lognormal_stroke(
                    (alpha - corner_time) / (1 - corner_time), mu=-1.10, sigma=.50
                )
        else:
            progress = self.progress_curve(alpha)
        if progress <= 0:
            self.mobject.set_opacity(0)
            return

        partial = _partial_centerline(self.centerline, progress)
        options = dict(self.stroke_options)
        # 当前笔尖必须就是当前中心线末端，不能被 streamline 滞后。
        options["last"] = True
        outline = get_stroke(partial, **options)
        self.mobject.become(_polygon_from_outline(outline, self._final_polygon))

    def finish(self) -> None:
        # 最后一帧严格回到创建 Mark 时预先算好的最终轮廓，无任何对象替换或淡入。
        self.mobject.become(self._final_polygon)
        super().finish()


class DrawMark(AnimationGroup):
    """按真实书写顺序逐笔增长 ``Mark`` 的实心 freehand 轮廓。"""

    def __init__(self, mark, run_time=1.2, lag_ratio=1.0, speed=None, **kwargs):
        """绘制标记。

        ``speed`` 可选 ``steady``、``natural``、``decisive``、``flick``、``careful``、
        ``line``、``check``、``circle``；
        未指定时使用创建 Mark 时设置的速度类型。
        """
        final_strokes = list(mark.submobjects)
        if not getattr(mark, "centerlines", None):
            raise ValueError("DrawMark requires a Mark created by manim_stroke")

        speed = mark.speed if speed is None else speed
        super().__init__(
            *(ProgressiveStroke(final, points, options, speed=speed, kind=mark.kind)
              for final, points, options in zip(
                  final_strokes, mark.centerlines, mark.stroke_options,
              )),
            run_time=run_time,
            lag_ratio=lag_ratio,
            **kwargs,
        )


class DrawHandwriting(Succession):
    """按 Σ-lognormal 逐笔手写一个字母 Mark，笔间留提笔静默。

    每笔 ProgressiveStroke 用各自的 ``run_time`` = 该笔时长（由弧长按等时性定），
    速率曲线为归一化 Sigma-Lognormal 进度（起笔慢→中间快→收笔慢）；
    笔画之间插入 ``Wait(pen_up_gap)`` 作为 pen-up 静默。σ / 分位从 Mark 自带的
    HandwritingStyle 读，与时长计算同源。
    """

    def __init__(self, mark, handwriting=None, **kwargs):
        from .handwriting import DEFAULT_HANDWRITING

        hw = handwriting or getattr(mark, "handwriting_style", None) or DEFAULT_HANDWRITING
        durations = getattr(mark, "handwriting_durations", None)
        peaks = getattr(mark, "handwriting_peaks", None)
        gaps = getattr(mark, "handwriting_gaps", None) or []
        if not durations:
            raise ValueError(
                "DrawHandwriting 需要一个由 letter() 创建的 Mark（缺 handwriting_durations）")
        if len(mark.centerlines) != len(durations):
            raise ValueError("centerlines 与 handwriting_durations 长度不一致")
        if peaks is None:
            peaks = [1] * len(durations)  # compatible with pre-multipeak Marks
        if len(peaks) != len(durations):
            raise ValueError("handwriting_peaks 与 handwriting_durations 长度不一致")

        anims = []
        for i, (final, points, options) in enumerate(
                zip(mark.submobjects, mark.centerlines, mark.stroke_options)):
            n_peaks = peaks[i]
            duration = durations[i]
            curve = (lambda alpha, n=n_peaks, d=duration: _handwriting_progress_multi(
                alpha, hw.lognormal_sigma, n, hw.command_spacing / d,
                hw.completion_quantile))
            anims.append(ProgressiveStroke(final, points, options,
                                           speed=curve, kind="letter",
                                           run_time=duration))
            if i < len(gaps) and gaps[i] > 0:
                anims.append(Wait(gaps[i]))        # pen-up：不出墨，笔尖静默挪到下一笔起点
        super().__init__(*anims, **kwargs)
