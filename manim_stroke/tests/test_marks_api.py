"""高层 API 的兼容性测试；用最小 Manim 替身避免依赖渲染环境。"""
from __future__ import annotations

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class Polygon:
    def __init__(self, *points, **kwargs):
        self.points = points
        self.kwargs = kwargs


class VGroup:
    def __init__(self, *submobjects):
        self.submobjects = list(submobjects)
        self.points = []

    def add_updater(self, updater):
        self.updater = updater

    def clear_updaters(self):
        self.updater = None


class Animation:
    def __init__(self, *args, **kwargs):
        pass


class AnimationGroup(Animation):
    pass


fake_manim = types.ModuleType("manim")
fake_manim.Polygon = Polygon
fake_manim.VGroup = VGroup
fake_manim.Animation = Animation
fake_manim.AnimationGroup = AnimationGroup
fake_manim.linear = lambda alpha: alpha
sys.modules.setdefault("manim", fake_manim)

from manim_stroke import MarkStyle, check, circle, cross, strike, underline  # noqa: E402


class Target:
    width = 2.0
    height = 1.0

    def get_left(self):
        return [-1.0, 0.0, 0.0]

    def get_right(self):
        return [1.0, 0.0, 0.0]

    def get_bottom(self):
        return [0.0, -0.5, 0.0]

    def get_center(self):
        return [0.0, 0.0, 0.0]


class MarksApiTests(unittest.TestCase):
    def setUp(self):
        self.target = Target()

    def test_existing_defaults_are_preserved(self):
        self.assertEqual(underline(self.target, seed=1).stroke_options[0]["smoothing"], 0.5)
        self.assertEqual(strike(self.target, seed=1).stroke_options[0]["thinning"], 0)
        self.assertTrue(check(self.target, seed=1).stroke_options[0]["start"]["cap"])
        self.assertEqual(cross(self.target, seed=1).stroke_options[0]["end"]["taper"], 0)
        self.assertEqual(circle(self.target, seed=1).stroke_options[0]["size"], 0.08)

    def test_style_is_reused_and_explicit_values_override_it(self):
        style = MarkStyle(size=0.12, thinning=0.3, cap=False, taper=0.04, smoothing=0.2)
        from_style = check(self.target, seed=1, style=style)
        overridden = check(self.target, seed=1, style=style, size=0.07, cap=True)
        self.assertEqual(from_style.stroke_options[0]["size"], 0.12)
        self.assertEqual(from_style.stroke_options[0]["thinning"], 0.3)
        self.assertFalse(from_style.stroke_options[0]["start"]["cap"])
        self.assertEqual(from_style.stroke_options[0]["smoothing"], 0.2)
        self.assertEqual(overridden.stroke_options[0]["size"], 0.07)
        self.assertTrue(overridden.stroke_options[0]["start"]["cap"])

    def test_invalid_path_resolution_is_rejected_early(self):
        with self.assertRaises(ValueError):
            underline(self.target, n_points=1)
        with self.assertRaises(ValueError):
            check(self.target, num_points=1)
        with self.assertRaises(ValueError):
            circle(self.target, ratio=0)


if __name__ == "__main__":
    unittest.main()
