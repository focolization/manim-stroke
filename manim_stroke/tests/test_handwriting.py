"""handwriting 纯核心回归测试（不依赖 Manim；HersheyFonts 需已安装）。"""
from __future__ import annotations

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from manim_stroke.handwriting import (HandwritingStyle, DEFAULT_HANDWRITING,
    lognormal_mu_for_duration, lognormal_cumulative, lognormal_progress,
    lognormal_progress_multi, detect_peaks, stroke_duration, pen_up_gap, polyline_length, resample_arclength,
    wobble_polyline_normal, letter_glyph, slant_sequence, shear_polyline,
    sample_glyph_ratios, segment_deform, minimum_jerk_transition,
    minimum_jerk_velocity, speed_curvature_violation)
import random


class TimingTests(unittest.TestCase):
    def test_mu_reverse_calc_matches_expert_table(self):
        # 专家表：σ=0.35，99.5% 分位
        self.assertAlmostEqual(lognormal_mu_for_duration(0.40, 0.35), -1.818, places=2)
        self.assertAlmostEqual(lognormal_mu_for_duration(0.50, 0.35), -1.595, places=2)
        self.assertAlmostEqual(lognormal_mu_for_duration(0.60, 0.35), -1.412, places=2)

    def test_mu_raises_when_duration_le_t0(self):
        with self.assertRaises(ValueError):
            lognormal_mu_for_duration(0.0, 0.35)
        with self.assertRaises(ValueError):
            lognormal_mu_for_duration(0.3, 0.35, t0=0.3)

    def test_cumulative_monotonic_and_completes(self):
        mu = lognormal_mu_for_duration(0.5, 0.35)
        ts = [0.05, 0.1, 0.2, 0.3, 0.5]
        vals = [lognormal_cumulative(t, mu, 0.35) for t in ts]
        self.assertTrue(all(vals[i] < vals[i + 1] for i in range(len(vals) - 1)))
        # 在 T=0.5 处累计应接近 0.995
        self.assertAlmostEqual(lognormal_cumulative(0.5, mu, 0.35) / 1.0, 0.995, places=2)

    def test_progress_monotonic_in_unit(self):
        alphas = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        vals = [lognormal_progress(a, 0.35) for a in alphas]
        self.assertEqual(vals[0], 0.0)
        self.assertEqual(vals[-1], 1.0)
        self.assertTrue(all(0.0 <= v <= 1.0 for v in vals))
        self.assertTrue(all(vals[i] < vals[i + 1] for i in range(len(vals) - 1)))

    def test_duration_sublinear_and_clamped(self):
        st = DEFAULT_HANDWRITING
        t1 = stroke_duration(1.0, st)
        t2 = stroke_duration(2.0, st)
        t4 = stroke_duration(4.0, st)
        # 等时性：长度翻倍时长只增一点点（≈×1.13），不是线性
        self.assertGreater(t2, t1)
        self.assertLess(t2, t1 * 1.2)
        self.assertLess(t4, t1 * 1.3)
        # 超大长度被 clamp 到 duration_max
        self.assertEqual(stroke_duration(1000.0, st), st.duration_max)
        # 极小长度被 clamp 到 duration_min
        self.assertEqual(stroke_duration(0.0, st), st.duration_min)

    def test_detect_peaks_splits_a_hard_corner_but_not_a_line(self):
        elbow = [[0, 0], [0.3, 0], [0.6, 0], [0.6, 0.3], [0.6, 0.6]]
        self.assertEqual(detect_peaks(elbow, math.radians(50), 0.12), [2])
        self.assertEqual(detect_peaks([[0, 0], [0.5, 0], [1, 0]]), [])

    def test_multi_peak_progress_smooth_and_monotonic_single_is_legacy(self):
        # n=1 is deliberately bit-for-bit the old curve.
        self.assertEqual(lognormal_progress_multi(.37, .35, 1, .4),
                         lognormal_progress(.37, .35))
        # Overlapping pulses: progress is strictly increasing with NO hard zero
        # plateau (the corner pause of the old command_spacing model is gone).
        p = [lognormal_progress_multi(a / 100, .35, 3, .4) for a in range(101)]
        diffs = [p[i + 1] - p[i] for i in range(100)]
        self.assertTrue(all(d >= 0 for d in diffs))               # monotonic
        self.assertAlmostEqual(p[0], 0.0); self.assertAlmostEqual(p[100], 1.0)
        # no hard plateau in the interior (the tiny 0 at the very start is just
        # the lognormal's near-zero launch underflowing a 1% sample)
        self.assertGreater(min(diffs[5:95]), 0.0)
        # more overlap ⇒ smoother (higher min speed) than serial (overlap=0)
        serial = [lognormal_progress_multi(a / 100, .35, 3, 0.0) for a in range(101)]
        ser_min = min(serial[i + 1] - serial[i] for i in range(5, 95))
        self.assertGreater(min(diffs[5:95]), ser_min)

    def test_more_peaks_no_longer_pad_duration(self):
        # Corner deceleration is produced by the overlapping pulses, so the
        # duration no longer grows with peak count (no command_spacing pad).
        st = HandwritingStyle(duration_min=0.0, duration_max=10.0)
        self.assertAlmostEqual(stroke_duration(1.0, st, 3), stroke_duration(1.0, st, 1))

    def test_minimum_jerk_transition_endpoints_and_velocity(self):
        p0, p1 = [0.0, 0.0], [1.0, 2.0]
        self.assertEqual(minimum_jerk_transition(0.0, 1.0, p0, p1), [0.0, 0.0])
        end = minimum_jerk_transition(1.0, 1.0, p0, p1)
        self.assertAlmostEqual(end[0], 1.0); self.assertAlmostEqual(end[1], 2.0)
        # zero velocity at both endpoints (smooth lift / lower)
        self.assertEqual(minimum_jerk_velocity(0.0, 1.0, p0, p1), [0.0, 0.0])
        self.assertEqual(minimum_jerk_velocity(1.0, 1.0, p0, p1), [0.0, 0.0])

    def test_speed_curvature_law_penalizes_fast_turns(self):
        # human law |v| ∝ κ^(-1/3): a slow sharp turn (high κ, low v) keeps
        # v·κ^(1/3) near constant → low violation.  A fast sharp turn is bad.
        good = speed_curvature_violation([1.0, 0.5, 0.25], [0.1, 0.8, 6.4])
        bad = speed_curvature_violation([1.0, 1.0, 1.0], [0.1, 0.8, 6.4])
        self.assertIsNotNone(good)
        self.assertLess(good, bad)


    def test_pen_up_gap_clamped(self):
        st = DEFAULT_HANDWRITING
        rng = random.Random(12345)
        for _ in range(200):
            g = pen_up_gap(rng, st)
            self.assertGreaterEqual(g, st.pen_up_min)
            self.assertLessEqual(g, st.pen_up_max)


class DeformTests(unittest.TestCase):
    def test_polyline_length(self):
        self.assertEqual(polyline_length([[0, 0], [3, 4]]), 5.0)
        self.assertEqual(polyline_length([[0, 0], [0, 0]]), 0.0)
        self.assertEqual(polyline_length([[1, 2]]), 0.0)

    def test_resample_keeps_endpoints_and_step(self):
        pts = [[0, 0], [10, 0]]            # 水平 10 单位
        s = resample_arclength(pts, 2.0)
        self.assertEqual(s[0], [0, 0])
        self.assertEqual(s[-1], [10, 0])
        # 每段间距约 2（末段除外）
        for a, b in zip(s[:-1], s[1:]):
            self.assertAlmostEqual(math.dist(a, b), 2.0, places=6)

    def test_resample_too_few_points(self):
        self.assertEqual(resample_arclength([[1, 1]], 0.5), [[1, 1]])
        self.assertEqual(resample_arclength([], 0.5), [])

    def test_wobble_endpoints_anchored(self):
        # 水平线 20 点，法线噪声后首末点不该动（端点包络）
        pts = [[i * 0.05, 0.0] for i in range(20)]
        wob = wobble_polyline_normal(pts, step=0.05, jitter_rms=0.02,
                                     correlation_length=0.18, seed=5, envelope=True)
        self.assertEqual(wob[0], [pts[0][0], pts[0][1]])
        self.assertEqual(wob[-1], [pts[-1][0], pts[-1][1]])

    def test_wobble_displaces_along_normal(self):
        # 水平线的法线是 y 方向 → 变形只改 y，不改 x（中心差切向是 x 轴）
        pts = [[i * 0.05, 0.0] for i in range(20)]
        wob = wobble_polyline_normal(pts, step=0.05, jitter_rms=0.02,
                                     correlation_length=0.18, seed=5, envelope=True)
        for i in range(len(wob)):
            self.assertAlmostEqual(wob[i][0], pts[i][0], places=6)   # x 不变
        # 中间点 y 有偏移
        self.assertGreater(abs(wob[10][1]), 0.0)

    def test_wobble_smooth_not_jagged(self):
        # 默认步长 0.015、相关长度 0.18 → ρ≈0.92，相邻点高度相关：连续弯曲非锯齿。
        # 独立随机（ρ→0）相邻差会到 ~2·rms；AR(1) 高相关应明显更小。
        pts = [[i * 0.015, 0.0] for i in range(60)]
        wob = wobble_polyline_normal(pts, step=0.015, jitter_rms=0.02,
                                     correlation_length=0.18, seed=5, envelope=True)
        ys = [p[1] for p in wob]
        diffs = [abs(ys[i + 1] - ys[i]) for i in range(len(ys) - 1)]
        self.assertLess(max(diffs), 0.02 * 2.0)   # 远小于独立随机的 ~2·rms

    def test_wobble_seed_reproducible(self):
        pts = [[i * 0.05, 0.0] for i in range(20)]
        a = wobble_polyline_normal(pts, step=0.05, jitter_rms=0.02,
                                   correlation_length=0.18, seed=99, envelope=True)
        b = wobble_polyline_normal(pts, step=0.05, jitter_rms=0.02,
                                   correlation_length=0.18, seed=99, envelope=True)
        self.assertEqual(a, b)

    def test_wobble_zero_jitter_is_identity(self):
        pts = [[i * 0.05, i * 0.01] for i in range(10)]
        wob = wobble_polyline_normal(pts, step=0.05, jitter_rms=0.0,
                                     correlation_length=0.18, seed=1, envelope=True)
        self.assertEqual(wob, [[p[0], p[1]] for p in pts])


class GlyphTests(unittest.TestCase):
    def test_A_has_three_strokes_C_has_one(self):
        st = DEFAULT_HANDWRITING
        self.assertEqual(len(letter_glyph("A", "futural", st, seed=1).strokes), 3)
        self.assertEqual(len(letter_glyph("C", "futural", st, seed=1).strokes), 1)

    def test_normalized_height_is_one(self):
        g = letter_glyph("A", "futural", DEFAULT_HANDWRITING, seed=1)
        ys = [p[1] for s in g.strokes for p in s.points]
        self.assertAlmostEqual(max(ys) - min(ys), 1.0, places=2)

    def test_glyph_bbox_centered_at_origin(self):
        g = letter_glyph("B", "futural", DEFAULT_HANDWRITING, seed=1)
        xs = [p[0] for s in g.strokes for p in s.points]
        ys = [p[1] for s in g.strokes for p in s.points]
        self.assertAlmostEqual((max(xs) + min(xs)) / 2, 0.0, places=2)
        self.assertAlmostEqual((max(ys) + min(ys)) / 2, 0.0, places=2)

    def test_each_stroke_has_positive_arc_length_and_duration(self):
        g = letter_glyph("D", "futural", DEFAULT_HANDWRITING, seed=1)
        for s in g.strokes:
            self.assertGreater(s.arc_length, 0.0)
            self.assertGreaterEqual(s.duration, DEFAULT_HANDWRITING.duration_min)

    def test_seed_reproducible(self):
        a = letter_glyph("A", "futural", DEFAULT_HANDWRITING, seed=7)
        b = letter_glyph("A", "futural", DEFAULT_HANDWRITING, seed=7)
        self.assertEqual(a.strokes[0].points, b.strokes[0].points)

    def test_rejects_non_single_char(self):
        with self.assertRaises(ValueError):
            letter_glyph("AB", "futural", DEFAULT_HANDWRITING, seed=1)


class SlantTests(unittest.TestCase):
    def test_slant_sequence_length_and_range(self):
        st = DEFAULT_HANDWRITING
        s = slant_sequence(5, st, 42)
        self.assertEqual(len(s), 5)
        low = math.radians(st.writer_slant_deg - st.char_slant_limit_deg - st.word_slant_std_deg * 4)
        high = math.radians(st.writer_slant_deg + st.char_slant_limit_deg + st.word_slant_std_deg * 4)
        for v in s:
            self.assertGreater(v, low)
            self.assertLess(v, high)

    def test_slant_sequence_empty(self):
        self.assertEqual(slant_sequence(0, DEFAULT_HANDWRITING, 1), [])

    def test_slant_sequence_reproducible(self):
        st = DEFAULT_HANDWRITING
        self.assertEqual(slant_sequence(4, st, 7), slant_sequence(4, st, 7))

    def test_slant_sequence_char_clamp(self):
        st = HandwritingStyle(char_slant_std_deg=20.0, char_slant_limit_deg=3.0,
                              word_slant_std_deg=0.0)
        s = slant_sequence(50, st, 1)
        base = math.radians(st.writer_slant_deg)
        for v in s:
            self.assertLessEqual(abs(v - base), math.radians(st.char_slant_limit_deg) + 1e-6)

    def test_shear_baseline_fixed(self):
        # baseline_y 上的点不动；更高的点向右偏（正 theta）
        pts = [[0.0, -0.5], [0.0, 0.5]]
        out = shear_polyline(pts, math.radians(10.0), -0.5)
        self.assertAlmostEqual(out[0][0], 0.0)          # 底（基线）不动
        self.assertGreater(out[1][0], 0.0)              # 顶右移
        self.assertAlmostEqual(out[0][1], -0.5)         # y 不变
        self.assertAlmostEqual(out[1][1], 0.5)

    def test_shear_zero_is_identity(self):
        pts = [[1.0, 2.0], [3.0, 4.0]]
        self.assertEqual(shear_polyline(pts, 0.0, 0.0), [[1.0, 2.0], [3.0, 4.0]])

    def test_glyph_slant_shifts_top_right(self):
        st = DEFAULT_HANDWRITING
        g0 = letter_glyph("T", "futural", st, seed=5, slant=0.0)
        g1 = letter_glyph("T", "futural", st, seed=5, slant=math.radians(12.0))
        self.assertGreater(g1.width, g0.width)          # shear 拓宽
        # 倾斜后顶点 x 比底点 x 大（右倾）
        pts = [p for s in g1.strokes for p in s.points]
        ys = [p[1] for p in pts]; ymid = (min(ys) + max(ys)) / 2
        top_x = sum(p[0] for p in pts if p[1] > ymid) / max(1, len([p for p in pts if p[1] > ymid]))
        bot_x = sum(p[0] for p in pts if p[1] <= ymid) / max(1, len([p for p in pts if p[1] <= ymid]))
        self.assertGreater(top_x, bot_x)

    def test_glyph_default_identity_preserved(self):
        # 默认 slant=0, ratios=1 → 高度仍 1、bbox 仍居中（旧契约不变）
        g = letter_glyph("A", "futural", DEFAULT_HANDWRITING, seed=1)
        ys = [p[1] for s in g.strokes for p in s.points]
        self.assertAlmostEqual(max(ys) - min(ys), 1.0, places=2)

    def test_sample_glyph_ratios_clamped(self):
        st = HandwritingStyle(glyph_width_std=0.5, glyph_height_std=0.5, glyph_ratio_limit=0.05)
        for sd in range(20):
            wr, hr = sample_glyph_ratios(st, sd)
            self.assertGreaterEqual(wr, 1 - 0.05 - 1e-9)
            self.assertLessEqual(wr, 1 + 0.05 + 1e-9)
            self.assertGreaterEqual(hr, 1 - 0.05 - 1e-9)
            self.assertLessEqual(hr, 1 + 0.05 + 1e-9)


class SegmentTests(unittest.TestCase):
    def test_continuity_chained(self):
        # 每段起点 = 上一段终点 → 相邻点距离不为 0 且路径连续（无大跳）
        # V 形：连续路径，中点拐弯
        pts = []
        for i in range(20):
            if i < 10:
                pts.append([i * 0.1, i * 0.1])
            else:
                pts.append([i * 0.1, (19 - i) * 0.1])
        out = segment_deform(pts, DEFAULT_HANDWRITING, seed=5)
        self.assertEqual(len(out), len(pts))
        gaps = [math.dist(out[i], out[i + 1]) for i in range(len(out) - 1)]
        self.assertLess(max(gaps), 0.5)   # 无大跳（变形后仍连续）

    def test_first_point_fixed(self):
        pts = [[i * 0.1, (i % 3) * 0.3] for i in range(30)]
        out = segment_deform(pts, DEFAULT_HANDWRITING, seed=5)
        self.assertAlmostEqual(out[0][0], pts[0][0])
        self.assertAlmostEqual(out[0][1], pts[0][1])

    def test_short_polyline_unchanged(self):
        pts = [[0, 0], [1, 1]]
        self.assertEqual(segment_deform(pts, DEFAULT_HANDWRITING, seed=1), [[0, 0], [1, 1]])

    def test_deform_changes_points(self):
        # 多点带拐点的 polyline 应被变形（与输入不完全相同）
        pts = [[i * 0.05, 0.0 if i < 15 else (i - 15) * 0.2] for i in range(30)]
        out = segment_deform(pts, DEFAULT_HANDWRITING, seed=9)
        diffs = [math.dist(pts[i], out[i]) for i in range(len(pts))]
        self.assertGreater(max(diffs), 0.0)

    def test_reproducible(self):
        pts = [[i * 0.05, (i % 5) * 0.1] for i in range(30)]
        a = segment_deform(pts, DEFAULT_HANDWRITING, seed=42)
        b = segment_deform(pts, DEFAULT_HANDWRITING, seed=42)
        self.assertEqual(a, b)

    def test_glyph_segment_off_by_default(self):
        # 默认 segment=False → 旧契约不变（高度 1）
        g = letter_glyph("A", "futural", DEFAULT_HANDWRITING, seed=1)
        ys = [p[1] for s in g.strokes for p in s.points]
        self.assertAlmostEqual(max(ys) - min(ys), 1.0, places=2)

    def test_glyph_segment_on_changes_shape(self):
        g0 = letter_glyph("C", "futural", DEFAULT_HANDWRITING, seed=5, segment=False)
        g1 = letter_glyph("C", "futural", DEFAULT_HANDWRITING, seed=5, segment=True)
        p0 = g0.strokes[0].points
        p1 = g1.strokes[0].points
        self.assertGreater(
            max(math.dist(p0[i], p1[i]) for i in range(min(len(p0), len(p1)))), 0.0)

    def test_metric_preserving_lowercase_keeps_x_height(self):
        # Text mode must not turn lowercase e into a cap-height l.
        l = letter_glyph("l", "futural", DEFAULT_HANDWRITING, seed=1,
                         preserve_metrics=True)
        e = letter_glyph("e", "futural", DEFAULT_HANDWRITING, seed=1,
                         preserve_metrics=True)
        lh = max(p[1] for s in l.strokes for p in s.points) - min(p[1] for s in l.strokes for p in s.points)
        eh = max(p[1] for s in e.strokes for p in s.points) - min(p[1] for s in e.strokes for p in s.points)
        self.assertGreater(lh, eh * 1.4)


class StructureTests(unittest.TestCase):
    def test_structure_is_opt_in_and_reproducible(self):
        plain = letter_glyph("A", "futural", DEFAULT_HANDWRITING, seed=17, structure=False)
        shaped = letter_glyph("A", "futural", DEFAULT_HANDWRITING, seed=17, structure=True)
        shaped_again = letter_glyph("A", "futural", DEFAULT_HANDWRITING, seed=17, structure=True)
        self.assertNotEqual(plain.strokes[0].points, shaped.strokes[0].points)
        self.assertEqual(shaped.strokes[0].points, shaped_again.strokes[0].points)

    def test_A_crossbar_is_constructed_on_legs(self):
        g = letter_glyph("A", "futural", DEFAULT_HANDWRITING, seed=19, structure=True)
        left, right, bar = [s.points for s in g.strokes]
        # Each endpoint of bar shares its y with, and lies on, one leg segment.
        for endpoint, leg in zip((bar[0], bar[-1]), (left, right)):
            a, b = leg[0], leg[-1]
            t = (endpoint[1] - a[1]) / (b[1] - a[1])
            x = a[0] + t * (b[0] - a[0])
            self.assertAlmostEqual(endpoint[0], x, places=5)

    def test_bowl_attachment_to_stem_is_preserved(self):
        g = letter_glyph("B", "futural", DEFAULT_HANDWRITING, seed=19, structure=True)
        stem_x = g.strokes[0].points[0][0]
        self.assertAlmostEqual(g.strokes[1].points[0][0], stem_x, places=6)
        self.assertAlmostEqual(g.strokes[2].points[0][0], stem_x, places=6)


if __name__ == "__main__":
    unittest.main()
