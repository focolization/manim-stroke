"""汉字数据源：Make Me a Hanzi medians（中心线）。

数据致谢：medians 来自 Make Me a Hanzi（github.com/skishore/makemeahanzi）的
graphics.txt，派生自 Arphic PL KaitiM GB / UKai 字体，遵循 **Arphic Public
License**。完整致谢见 ``handwriting/data/README.md``。本库只取 medians，
不用 SVG ``strokes``。

坐标系坑（务必记住）：medians 的 y 是**向上**的（顶 y=900、底 y=-124），
与 manim(+y 上) 一致，经 em 方块归一化后无需翻 y。只有转成 SVG（SVG 的 y
向下）才需要 ``scale(1,-1) translate(0,-900)``。

数据格式：graphics.txt 每行一个 JSON：:

    {"character":"中","strokes":[<SVG路径>...],"medians":[[[x,y],..]..],...}

``medians`` 是按正确笔顺的每笔中心线折线；``strokes`` 是 SVG 描边路径（本库不用）。
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Sequence, Tuple

from .base import (BBox, GlyphSource, RawGlyph, normalize_em, normalize_unit_height)

_DEFAULT_PATH_ENV = "MAKE_ME_A_HANZI"
# 内置全集数据（9574 常用字，仅 medians，去 SVG 后约 6.5MB）。
# 路径解析顺序：env MAKE_ME_A_HANZI（可选，指向更全/更小的文件）→ 内置文件。
_BUNDLED = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "data", "hanzi_medians.json")
_DEFAULT_PATH = _BUNDLED

# Make Me a Hanzi 的方块字格（em）：1024² 画布，约 x[0,1024] y[-128,896]。
# 汉字按这个固定 em 归一化，保持各字在格内的自然位置/比例（见 normalize_em）。
_MMAH_EM = (0.0, -128.0, 1024.0, 896.0)


def _parse_medians(content: str) -> Dict[str, RawGlyph]:
    """解析两种数据格式，统一成 {char: [[[x,y],...],...]}。

    - 内置精简格式：整个文件是一个 dict ``{char: [[[x,y],...],...]}``。
    - 原始 graphics.txt：每行一个 JSON ``{"character":..,"strokes":..,"medians":..}``。
    """
    try:
        obj = json.loads(content)
    except json.JSONDecodeError:
        obj = None
    if isinstance(obj, dict):
        return {c: [[[float(pt[0]), float(pt[1])] for pt in s] for s in m]
                for c, m in obj.items()}
    table: Dict[str, RawGlyph] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        table[o["character"]] = [[[float(pt[0]), float(pt[1])] for pt in s]
                                 for s in o["medians"]]
    return table


def catmull_rom(points: Sequence[Sequence[float]], samples: int = 8) -> List[List[float]]:
    """Catmull-Rom 对折线逐段补点，得到平滑中心线。

    Make Me a Hanzi 的 medians 一笔常只有 3–10 点，直线插值会有棱角；在
    进入变形管道前先补点平滑。端点用 clamped（重复端点）处理。
    返回约 ``(n-1)*samples+1`` 个点。
    """
    n = len(points)
    if n < 3:
        return [list(p) for p in points]
    p = [list(pt) for pt in points]
    out: List[List[float]] = [list(p[0])]
    for i in range(n - 1):
        p0 = p[max(i - 1, 0)]
        p1 = p[i]
        p2 = p[i + 1]
        p3 = p[min(i + 2, n - 1)]
        for t in range(1, samples + 1):
            s = t / samples
            s2 = s * s
            s3 = s2 * s
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * s
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * s2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * s3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * s
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * s2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * s3)
            out.append([x, y])
    return out


class HanziData:
    """加载并缓存 Make Me a Hanzi medians。

    ``path`` 缺省时依次读环境变量 ``MAKE_ME_A_HANZI``、内置全集文件
    ``handwriting/data/hanzi_medians.json``（9574 常用字）。整文件首访时
    解析一次并缓存。
    """

    def __init__(self, path: Optional[str] = None):
        self._path = path or os.environ.get(_DEFAULT_PATH_ENV, _DEFAULT_PATH)
        self._medians: Optional[Dict[str, RawGlyph]] = None

    @property
    def path(self) -> str:
        return self._path

    def _ensure(self) -> Dict[str, RawGlyph]:
        if self._medians is None:
            with open(self._path, encoding="utf-8") as f:
                content = f.read()
            self._medians = _parse_medians(content)
        return self._medians

    def medians_for(self, char: str) -> Optional[RawGlyph]:
        """返回该字按正确笔顺的每笔中心线；无此字返回 None。"""
        return self._ensure().get(char)


class HanziSource:
    """从 Make Me a Hanzi 取汉字的中心线。

    ``smooth=True`` 时先用 Catmull-Rom 补点平滑稀疏 medians。
    坐标语义恒为满格方块（汉字无字体度量，``preserve_metrics`` 只能为 False）。
    """

    def __init__(self, data: Optional[HanziData] = None,
                 smooth: bool = True, smooth_samples: int = 8,
                 em: Optional[Tuple[float, float, float, float]] = None):
        self._data = data or HanziData()
        self.smooth = smooth
        self.smooth_samples = smooth_samples
        self._em = em or _MMAH_EM

    def strokes_for(self, char: str) -> RawGlyph:
        medians = self._data.medians_for(char)
        if medians is None:
            raise ValueError(f"Make Me a Hanzi 无字符 {char!r} 的 medians")
        if self.smooth:
            medians = [catmull_rom(s, self.smooth_samples) for s in medians]
        return medians

    def normalize(self, raw: RawGlyph, preserve_metrics: bool,
                  bbox: BBox) -> Tuple[RawGlyph, float]:
        if preserve_metrics:
            raise ValueError("汉字没有字体度量，preserve_metrics 只能为 False")
        # 汉字按固定方块字格（em）归一化，避免「一」这类扁字被墨迹 bbox 拉长。
        return normalize_em(raw, bbox, self._em)

    def __repr__(self) -> str:                       # noqa: D105
        return (f"HanziSource(smooth={self.smooth}, "
                f"smooth_samples={self.smooth_samples}, data={self._data.path!r})")
