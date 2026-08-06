"""汉字数据源 + hanzi_glyph 测试。

依赖 Make Me a Hanzi 的 graphics.txt（env ``MAKE_ME_A_HANZI`` 或相对路径
``graphics.txt``）；文件不存在时整组跳过，保持套件不因 vendor 决策未定而红。
"""
from __future__ import annotations

import math
import os
import unittest

from manim_stroke.handwriting import (HANZI_HANDWRITING, HanziData, HanziSource,
                                       catmull_rom, hanzi_glyph)

# 中=4、永=5、我=7（Make Me a Hanzi medians 实际笔数）
STROKE_COUNTS = {"中": 4, "永": 5, "我": 7}


def _max_turn(points) -> float:
    """折线最大单点转角（弧度）——尖角越小越平滑。"""
    m = 0.0
    for i in range(1, len(points) - 1):
        v1 = (points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1])
        v2 = (points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
        m = max(m, abs(math.atan2(v1[0] * v2[1] - v1[1] * v2[0],
                                  v1[0] * v2[0] + v1[1] * v2[1])))
    return m


class HanziTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = os.environ.get("MAKE_ME_A_HANZI") or HanziData().path   # 缺省用内置全集
        if not os.path.exists(path):
            raise unittest.SkipTest(f"汉字数据不存在（{path}），跳过")
        # 共享一个 HanziData：6.5MB 文件只在首次访问时解析一次
        cls.data = HanziData(path=path)
        cls.smooth = HanziSource(data=cls.data, smooth=True, smooth_samples=8)
        cls.raw = HanziSource(data=cls.data, smooth=False)

    def test_stroke_counts(self):
        for char, n in STROKE_COUNTS.items():
            self.assertEqual(len(self.raw.strokes_for(char)), n, char)

    def test_normalized_height_is_one_in_em_cell(self):
        g = hanzi_glyph("我", seed=7)
        self.assertAlmostEqual(g.height, 1.0, places=4)
        xs = [p[0] for s in g.strokes for p in s.points]
        ys = [p[1] for s in g.strokes for p in s.points]
        # 墨迹应落在 em 方块字格 [-0.5, 0.5]² 内（不是居中，是按格内自然位置）
        self.assertGreaterEqual(min(xs), -0.5)
        self.assertLessEqual(max(xs), 0.5)
        self.assertGreaterEqual(min(ys), -0.5)
        self.assertLessEqual(max(ys), 0.5)

    def test_flat_char_not_absurdly_wide(self):
        # 回归：按墨迹 bbox 归一化会让「一」这种横笔被拉成超长横线；
        # 按 em 方块归一化后应保持正常比例（约 0.7~0.9 em 宽）。
        g = hanzi_glyph("一", seed=1)
        xs = [p[0] for s in g.strokes for p in s.points]
        ys = [p[1] for s in g.strokes for p in s.points]
        w = max(xs) - min(xs)
        h = max(ys) - min(ys)
        self.assertLess(w, 1.5)       # 旧 bug 会到 ~15
        self.assertLess(h, 0.5)       # 一 应仍是横条，不是撑满整格

    def test_width_near_square(self):
        # 汉字满格方块，宽度应接近 1（对比拉丁 e 的窄字）
        for char in "中永我":
            g = hanzi_glyph(char, seed=1)
            self.assertTrue(0.6 < g.width < 1.2, (char, g.width))

    def test_seed_reproducible(self):
        a = hanzi_glyph("永", seed=7)
        b = hanzi_glyph("永", seed=7)
        self.assertEqual(len(a.strokes), len(b.strokes))
        self.assertTrue(all(s.points == t.points
                            for s, t in zip(a.strokes, b.strokes)))

    def test_smooth_adds_points(self):
        raw = self.data.medians_for("我")
        for s, r in zip(self.smooth.strokes_for("我"), raw):
            self.assertGreater(len(s), len(r))

    def test_smooth_reduces_max_turn(self):
        a = self.smooth.strokes_for("我")[0]   # 平滑后第一笔
        b = self.raw.strokes_for("我")[0]
        self.assertLess(_max_turn(a), _max_turn(b))

    def test_catmull_rom_keeps_endpoints(self):
        pts = [[0.0, 0.0], [1.0, 1.0], [2.0, 0.0], [3.0, 1.0]]
        sm = catmull_rom(pts, samples=4)
        self.assertEqual(sm[0], pts[0])
        self.assertEqual(sm[-1], pts[-1])

    def test_rejects_non_single_char(self):
        with self.assertRaises(ValueError):
            hanzi_glyph("你好", seed=1)

    def test_unknown_char_raises(self):
        with self.assertRaises(ValueError):
            hanzi_glyph("A", seed=1)   # 拉丁字母不在汉字 medians 数据里

    def test_preserve_metrics_raises_for_hanzi(self):
        raw = self.raw.strokes_for("中")
        xs = [p[0] for s in raw for p in s]
        ys = [p[1] for s in raw for p in s]
        bbox = (min(xs), min(ys), max(xs), max(ys))
        with self.assertRaises(ValueError):
            self.raw.normalize(raw, True, bbox)

    def test_strokes_have_positive_arc_length_and_duration(self):
        g = hanzi_glyph("永", seed=3)
        self.assertTrue(all(s.arc_length > 0 and s.duration > 0 for s in g.strokes))

    def test_hanzi_style_is_square_and_calmer(self):
        # 汉字默认风格应比拉丁更端正、抖动更小、宽高比更紧
        self.assertEqual(HANZI_HANDWRITING.writer_slant_deg, 2.0)
        self.assertEqual(HANZI_HANDWRITING.structure_std, 0.0)
        self.assertLess(HANZI_HANDWRITING.jitter_rms, 0.006)
        self.assertLess(HANZI_HANDWRITING.glyph_ratio_limit, 0.05)


if __name__ == "__main__":
    unittest.main()
