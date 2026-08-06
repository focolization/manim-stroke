"""手写字形数据源（按语种隔离）。

- :class:`GlyphSource`：管道输入协议。
- :class:`HersheySource`：拉丁字母/数字/符号（Hershey 字体）。
- :class:`HanziSource`：汉字（Make Me a Hanzi medians）——见 hanzi.py。
"""
from .base import (BBox, GlyphSource, RawGlyph, Stroke, glyph_bbox,
                   normalize_font_metrics, normalize_unit_height)
from .latin import HersheySource
from .hanzi import HanziSource, HanziData, catmull_rom

__all__ = [
    "GlyphSource", "HersheySource", "HanziSource", "HanziData", "catmull_rom",
    "glyph_bbox", "normalize_unit_height", "normalize_font_metrics",
    "Stroke", "RawGlyph", "BBox",
]
