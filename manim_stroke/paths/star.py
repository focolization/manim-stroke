"""一笔画五角星中心线(跳2连顶点,5笔交叉)。"""
import math
import numpy as np
from typing import List


def star_path(cx: float, cy: float, size: float, n: int = 5,
              jitter: float = 0.02, seed: int = 1, variation: float = 1.0,
              points_per_seg: int = 14) -> List[List[float]]:
    """一笔画五角星(不抬笔,跳2连顶点 0→2→4→1→3→0),返回中心线点序列。

    5 条直线交叉,中间自然成星,像随手画的强调星。
    """
    rng = np.random.default_rng(seed)
    verts = []
    for k in range(n):
        ang = math.pi / 2 + k * 2 * math.pi / n
        verts.append([cx + size * math.cos(ang), cy + size * math.sin(ang)])
    # 跳2连顶点:n=5 → [0,2,4,1,3,0],5 笔回起点
    order = list(range(0, n, 2)) + list(range(1, n, 2)) + [0]
    pts = []
    for a, b in zip(order, order[1:]):
        for i in range(points_per_seg):
            t = i / points_per_seg
            x = verts[a][0] * (1 - t) + verts[b][0] * t
            y = verts[a][1] * (1 - t) + verts[b][1] * t
            jx = float(rng.normal(0, jitter * size * variation))
            jy = float(rng.normal(0, jitter * size * variation))
            pts.append([x + jx, y + jy])
    pts.append(verts[0])   # 闭合回起点(不抖)
    return pts