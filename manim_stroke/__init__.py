"""Manim 课堂手绘批注组件。"""
from .animation import DrawMark, DrawHandwriting
from .marks import (
    Mark, MarkStyle,
    check, circle, cross, strike, underline,
    dot_circle, lparen, rparen, star, letter, StrokeText,
    highlight,
)
from .freehand import StrokePoint, get_stroke, get_stroke_outline_points, get_stroke_points
from .handwriting import HandwritingStyle, DEFAULT_HANDWRITING

__all__ = [
    "DrawMark", "DrawHandwriting", "Mark", "MarkStyle",
    "check", "circle", "cross", "strike", "underline",
    "dot_circle", "lparen", "rparen", "star", "letter", "StrokeText",
    "highlight",
    "get_stroke", "get_stroke_outline_points", "get_stroke_points", "StrokePoint",
    "HandwritingStyle", "DEFAULT_HANDWRITING",
]