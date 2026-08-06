"""perfect-freehand 核心算法的 Python 移植(纯几何,无 manim 依赖,只 import math)。

输入:中心线点序列 [[x,y], ...] 或 [[x,y,pressure], ...]
输出:包围轨迹的可变宽度封闭轮廓点 [[x,y], ...] → 连接填充即笔迹形状

默认 thinning=0(固定粗细,不接压力算法)。需要力度起伏时设 thinning>0 +
simulate_pressure=True(保留了 simulate_pressure,但默认关闭)。

移植自 steveruizok/perfect-freehand (MIT),getStrokePoints + getStrokeOutlinePoints。
"""
import math
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple

Vec2 = Tuple[float, float]

# ---------------------------- 常量 ----------------------------
RATE_OF_PRESSURE_CHANGE = 0.275
FIXED_PI = math.pi + 0.0001
START_CAP_SEGMENTS = 13
END_CAP_SEGMENTS = 29
CORNER_CAP_SEGMENTS = 13
# perfect-freehand's fixed 3-unit noise threshold assumes its usual pixel-like
# coordinate system (where a typical pen size is 16).  Manim scenes commonly
# use sub-unit coordinates, so keeping it absolute discards an entire short
# stroke before the final point.  Express it relative to pen size instead.
END_NOISE_THRESHOLD_RATIO = 3 / 16
MIN_STREAMLINE_T = 0.15
STREAMLINE_T_RANGE = 0.85
MIN_RADIUS = 0.01
DEFAULT_FIRST_PRESSURE = 0.25
DEFAULT_PRESSURE = 0.5
UNIT_OFFSET: Vec2 = (1.0, 1.0)


# ---------------------------- 向量工具 ----------------------------
def neg(a: Vec2) -> Vec2: return (-a[0], -a[1])
def add(a: Vec2, b: Vec2) -> Vec2: return (a[0] + b[0], a[1] + b[1])
def sub(a: Vec2, b: Vec2) -> Vec2: return (a[0] - b[0], a[1] - b[1])
def mul(a: Vec2, n: float) -> Vec2: return (a[0] * n, a[1] * n)
def div(a: Vec2, n: float) -> Vec2: return (a[0] / n, a[1] / n)
def per(a: Vec2) -> Vec2: return (a[1], -a[0])           # 垂直
def dpr(a: Vec2, b: Vec2) -> float: return a[0]*b[0] + a[1]*b[1]   # 点积
def is_equal(a: Vec2, b: Vec2) -> bool: return a[0] == b[0] and a[1] == b[1]
def vlen(a: Vec2) -> float: return math.hypot(a[0], a[1])
def dist2(a: Vec2, b: Vec2) -> float:
    dx, dy = a[0]-b[0], a[1]-b[1]; return dx*dx + dy*dy
def uni(a: Vec2) -> Vec2:                                   # 单位化
    l = vlen(a); return (a[0]/l, a[1]/l) if l else (0.0, 0.0)
def dist(a: Vec2, b: Vec2) -> float: return math.hypot(a[1]-b[1], a[0]-b[0])
def med(a: Vec2, b: Vec2) -> Vec2: return mul(add(a, b), 0.5)
def rot_around(a: Vec2, c: Vec2, r: float) -> Vec2:
    s, co = math.sin(r), math.cos(r)
    px, py = a[0]-c[0], a[1]-c[1]
    return (px*co - py*s + c[0], px*s + py*co + c[1])
def lrp(a: Vec2, b: Vec2, t: float) -> Vec2:               # 插值
    return add(a, mul(sub(b, a), t))
def prj(a: Vec2, b: Vec2, c: float) -> Vec2:                # 沿方向投影
    return add(a, mul(b, c))


# ---------------------------- 压力 / 半径 ----------------------------
def _simulate_pressure(prev: float, distance: float, size: float) -> float:
    """按速度模拟压力(画快细、慢粗)。默认不启用。"""
    sp = min(1, distance / size)
    rp = min(1, 1 - sp)
    return min(1, prev + (rp - prev) * (sp * RATE_OF_PRESSURE_CHANGE))


def get_stroke_radius(size: float, thinning: float, pressure: float,
                      easing: Callable[[float], float]) -> float:
    return size * easing(0.5 - thinning * (0.5 - pressure))


# ---------------------------- StrokePoint ----------------------------
@dataclass
class StrokePoint:
    point: Vec2
    pressure: float
    vector: Vec2
    distance: float
    running_length: float


def _is_valid_pressure(p) -> bool:
    return p is not None and not (isinstance(p, float) and math.isnan(p)) and p >= 0


def _normalize(points: Sequence) -> List[List[float]]:
    """把输入点统一成 [[x, y, pressure], ...]。"""
    out = []
    for p in points:
        if isinstance(p, (list, tuple)):
            x, y = p[0], p[1]
            pr = p[2] if len(p) > 2 and _is_valid_pressure(p[2]) else DEFAULT_PRESSURE
            out.append([float(x), float(y), float(pr)])
        else:  # dict-like {x, y, pressure}
            x, y = p["x"], p["y"]
            pr = p.get("pressure", DEFAULT_PRESSURE)
            out.append([float(x), float(y), float(pr) if _is_valid_pressure(pr) else DEFAULT_PRESSURE])
    return out


# ---------------------------- getStrokePoints ----------------------------
def get_stroke_points(points: Sequence, streamline: float = 0.5,
                      size: float = 16, last: bool = False) -> List[StrokePoint]:
    if len(points) == 0:
        return []
    t = MIN_STREAMLINE_T + (1 - streamline) * STREAMLINE_T_RANGE
    pts = _normalize(points)

    # 两点:中间补点,避免锥形起收笔出现 dash
    if len(pts) == 2:
        lastp = pts[1]
        pts = pts[:1]
        for i in range(1, 5):
            pts.append(list(lrp(pts[0], lastp, i / 4)) + [lastp[2]])
    # 单点:补一个偏移点
    if len(pts) == 1:
        o = add(pts[0], UNIT_OFFSET)
        pts = [pts[0], [o[0], o[1], pts[0][2]]]

    first = pts[0]
    stroke = [StrokePoint(
        point=(first[0], first[1]),
        pressure=first[2] if _is_valid_pressure(first[2]) else DEFAULT_FIRST_PRESSURE,
        vector=UNIT_OFFSET, distance=0, running_length=0,
    )]
    has_min = False
    running = 0.0
    prev = stroke[0]
    max_i = len(pts) - 1

    for i in range(1, len(pts)):
        if last and i == max_i:
            point = (pts[i][0], pts[i][1])
        else:
            point = lrp(prev.point, pts[i], t)
        if is_equal(prev.point, point):
            continue
        d = dist(point, prev.point)
        running += d
        if i < max_i and not has_min:
            if running < size:
                continue
            has_min = True
        prev = StrokePoint(
            point=point,
            pressure=pts[i][2] if _is_valid_pressure(pts[i][2]) else DEFAULT_PRESSURE,
            vector=uni(sub(prev.point, point)),
            distance=d, running_length=running,
        )
        stroke.append(prev)

    if len(stroke) > 1:
        stroke[0].vector = stroke[1].vector
    return stroke


# ---------------------------- cap 绘制 ----------------------------
def _draw_dot(center: Vec2, radius: float) -> List[Vec2]:
    op = add(center, (1, 1))
    start = prj(center, uni(per(sub(center, op))), -radius)
    pts = []
    step = 1 / START_CAP_SEGMENTS
    t = step
    while t <= 1:
        pts.append(rot_around(start, center, FIXED_PI * 2 * t))
        t += step
    return pts


def _draw_round_start_cap(center: Vec2, right_point: Vec2, segments: int) -> List[Vec2]:
    cap = []
    step = 1 / segments
    t = step
    while t <= 1:
        cap.append(rot_around(right_point, center, FIXED_PI * t))
        t += step
    return cap


def _draw_flat_start_cap(center: Vec2, left_point: Vec2, right_point: Vec2) -> List[Vec2]:
    cv = sub(left_point, right_point)
    a, b = mul(cv, 0.5), mul(cv, 0.51)
    return [sub(center, a), sub(center, b), add(center, b), add(center, a)]


def _draw_round_end_cap(center: Vec2, direction: Vec2, radius: float, segments: int) -> List[Vec2]:
    cap = []
    start = prj(center, direction, radius)
    step = 1 / segments
    t = step
    while t < 1:
        cap.append(rot_around(start, center, FIXED_PI * 3 * t))
        t += step
    return cap


def _draw_flat_end_cap(center: Vec2, direction: Vec2, radius: float) -> List[Vec2]:
    return [add(center, mul(direction, radius)),
            add(center, mul(direction, radius * 0.99)),
            sub(center, mul(direction, radius * 0.99)),
            sub(center, mul(direction, radius))]


def _compute_taper(taper, size: float, total: float) -> float:
    if taper is False or taper is None:
        return 0
    if taper is True:
        return max(size, total)
    return float(taper)


def _compute_initial_pressure(points: List[StrokePoint], should_sim: bool, size: float) -> float:
    acc = points[0].pressure
    for curr in points[:10]:
        p = curr.pressure
        if should_sim:
            p = _simulate_pressure(acc, curr.distance, size)
        acc = (acc + p) / 2
    return acc


# ---------------------------- getStrokeOutlinePoints ----------------------------
def get_stroke_outline_points(
    points: List[StrokePoint],
    size: float = 16,
    smoothing: float = 0.5,
    thinning: float = 0,
    simulate_pressure: bool = False,
    easing: Optional[Callable[[float], float]] = None,
    start: Optional[dict] = None,
    end: Optional[dict] = None,
    last: bool = False,
) -> List[Vec2]:
    if easing is None:
        easing = lambda t: t
    start = start or {}
    end = end or {}
    cap_start = start.get("cap", True)
    taper_start_ease = start.get("easing", lambda t: t * (2 - t))
    cap_end = end.get("cap", True)
    taper_end_ease = end.get("easing", lambda t: (t - 1) ** 3 + 1)

    if len(points) == 0 or size <= 0:
        return []

    total_length = points[-1].running_length
    taper_start = _compute_taper(start.get("taper"), size, total_length)
    taper_end = _compute_taper(end.get("taper"), size, total_length)
    min_distance = (size * smoothing) ** 2
    end_noise_threshold = size * END_NOISE_THRESHOLD_RATIO

    left_pts: List[Vec2] = []
    right_pts: List[Vec2] = []
    prev_pressure = _compute_initial_pressure(points, simulate_pressure, size)
    radius = get_stroke_radius(size, thinning, points[-1].pressure, easing)
    first_radius = None
    prev_vector = points[0].vector
    prev_left = points[0].point
    prev_right = prev_left
    is_prev_sharp = False

    for i in range(len(points)):
        sp = points[i]
        pressure = sp.pressure
        point, vector, distance, running = sp.point, sp.vector, sp.distance, sp.running_length
        is_last = i == len(points) - 1
        if not is_last and total_length - running < end_noise_threshold:
            continue

        if thinning:
            if simulate_pressure:
                pressure = _simulate_pressure(prev_pressure, distance, size)
            radius = get_stroke_radius(size, thinning, pressure, easing)
        else:
            radius = size / 2

        if first_radius is None:
            first_radius = radius

        taper_start_strength = taper_start_ease(running / taper_start) if running < taper_start else 1
        taper_end_strength = taper_end_ease((total_length - running) / taper_end) if (total_length - running) < taper_end else 1
        radius = max(MIN_RADIUS, radius * min(taper_start_strength, taper_end_strength))

        next_vector = (points[i + 1] if not is_last else points[i]).vector
        next_dpr = dpr(vector, next_vector) if not is_last else 1.0
        prev_dpr = dpr(vector, prev_vector)

        is_sharp = prev_dpr < 0 and not is_prev_sharp
        is_next_sharp = next_dpr < 0 if not is_last else False

        if is_sharp or is_next_sharp:
            offset = mul(per(prev_vector), radius)
            step = 1 / CORNER_CAP_SEGMENTS
            t = 0.0
            while t <= 1:
                left_pts.append(rot_around(sub(point, offset), point, FIXED_PI * t))
                right_pts.append(rot_around(add(point, offset), point, FIXED_PI * -t))
                t += step
            prev_left = left_pts[-1]
            prev_right = right_pts[-1]
            is_prev_sharp = True if is_next_sharp else False
            continue

        is_prev_sharp = False

        if is_last:
            offset = mul(per(vector), radius)
            left_pts.append(sub(point, offset))
            right_pts.append(add(point, offset))
            continue

        offset = mul(per(lrp(next_vector, vector, next_dpr)), radius)
        tl = sub(point, offset)
        if i <= 1 or dist2(prev_left, tl) > min_distance:
            left_pts.append(tl); prev_left = tl
        tr = add(point, offset)
        if i <= 1 or dist2(prev_right, tr) > min_distance:
            right_pts.append(tr); prev_right = tr

        prev_pressure = pressure
        prev_vector = vector

    # caps
    first_point = points[0].point
    last_point = points[-1].point if len(points) > 1 else add(points[0].point, (1, 1))
    start_cap, end_cap = [], []

    if len(points) == 1:
        if (not (taper_start or taper_end)) or last:
            return _draw_dot(first_point, first_radius or radius)
    else:
        if taper_start or (taper_end and len(points) == 1):
            pass
        elif cap_start:
            start_cap.extend(_draw_round_start_cap(first_point, right_pts[0], START_CAP_SEGMENTS))
        else:
            start_cap.extend(_draw_flat_start_cap(first_point, left_pts[0], right_pts[0]))

        direction = per(neg(points[-1].vector))
        if taper_end or (taper_start and len(points) == 1):
            end_cap.append(last_point)
        elif cap_end:
            end_cap.extend(_draw_round_end_cap(last_point, direction, radius, END_CAP_SEGMENTS))
        else:
            end_cap.extend(_draw_flat_end_cap(last_point, direction, radius))

    return left_pts + end_cap + list(reversed(right_pts)) + start_cap


# ---------------------------- 入口 ----------------------------
def get_stroke(points: Sequence, size: float = 16, thinning: float = 0,
               smoothing: float = 0.5, streamline: float = 0.5,
               simulate_pressure: bool = False, easing: Optional[Callable] = None,
               start: Optional[dict] = None, end: Optional[dict] = None,
               last: bool = False) -> List[Vec2]:
    """输入中心线点 → 输出封闭轮廓多边形点。默认固定粗细(thinning=0,无压力)。"""
    sp = get_stroke_points(points, streamline=streamline, size=size, last=last)
    return get_stroke_outline_points(sp, size=size, smoothing=smoothing, thinning=thinning,
                                     simulate_pressure=simulate_pressure, easing=easing,
                                     start=start, end=end, last=last)
