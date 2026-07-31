"""课堂标记的中心线手势包(纯几何,无 Manim 依赖)。

每个标记一个文件,共享辅助在 _helpers。``from manim_stroke.paths import circle_path`` 等仍可用。
"""
from .underline import underline_path
from .strike import strike_path
from .check import check_path
from .cross import cross_path
from .circle import circle_path
from .star import star_path
from .highlight_path import highlight_path

__all__ = [
    "underline_path", "strike_path", "check_path",
    "cross_path", "circle_path", "star_path", "highlight_path",
]