"""课堂手绘批注包。

每个标记一个文件,共享辅助在 _common。``from manim_stroke.marks import circle`` 等仍可用。
"""
from ._common import Mark, MarkStyle
from .underline import underline
from .strike import strike
from .check import check
from .cross import cross
from .circle import circle
from .dot_circle import dot_circle
from .lparen import lparen
from .rparen import rparen
from .star import star
from .letter import letter
from .hanzi import hanzi
from .stroke_text import StrokeText
from .highlight import highlight

__all__ = [
    "Mark", "MarkStyle",
    "underline", "strike", "check", "cross", "circle",
    "dot_circle", "lparen", "rparen", "star", "letter", "hanzi", "StrokeText",
    "highlight",
]