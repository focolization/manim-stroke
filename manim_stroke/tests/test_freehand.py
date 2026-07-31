"""不依赖 Manim 的 freehand / 手势回归测试。"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


freehand = load_module("strokes_freehand_under_test", ROOT / "freehand" / "freehand.py")
sys.path.insert(0, str(ROOT))
import paths as paths   # paths 已解耦为包（纯几何，不引 manim）


class FreehandTests(unittest.TestCase):
    def test_empty_centerline_has_no_outline(self):
        self.assertEqual(freehand.get_stroke([]), [])

    def test_short_centerlines_produce_closed_outlines(self):
        for points in ([[0, 0]], [[0, 0], [1, 0]]):
            outline = freehand.get_stroke(points, size=0.1, last=True)
            self.assertGreaterEqual(len(outline), 3)

    def test_pressure_points_are_accepted(self):
        outline = freehand.get_stroke(
            [[0, 0, 0.2], [0.5, 0.1, 0.8], [1, 0, 0.4]],
            size=0.1,
            thinning=0.6,
            last=True,
        )
        self.assertGreaterEqual(len(outline), 3)


class PathTests(unittest.TestCase):
    def test_fixed_seed_reproduces_an_underline(self):
        kwargs = dict(n=24, jitter=0.012, seed=2026, variation=1.0)
        self.assertEqual(
            paths.underline_path(-1, 1, 0, **kwargs),
            paths.underline_path(-1, 1, 0, **kwargs),
        )

    def test_cross_has_two_strokes_in_documented_order(self):
        first, second = paths.cross_path(0, 0, 1, seed=8)
        self.assertLess(first[0][0], first[-1][0])  # \\ : 左上到右下
        self.assertGreater(second[0][0], second[-1][0])  # / : 右上到左下


if __name__ == "__main__":
    unittest.main()
