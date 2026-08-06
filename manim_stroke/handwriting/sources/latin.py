"""拉丁字母数据源：Hershey 字体。"""
from __future__ import annotations

from typing import Tuple

from .base import (BBox, RawGlyph, glyph_bbox, normalize_font_metrics,
                   normalize_unit_height)

_HERSHEY_CACHE: dict = {}   # font_name -> HersheyFonts 实例（load 一次复用）


def _hershey(font: str, height: float):
    """延迟导入并缓存 HersheyFonts 实例。"""
    if font not in _HERSHEY_CACHE:
        from HersheyFonts import HersheyFonts   # 延迟导入：可选依赖
        hf = HersheyFonts()
        hf.load_default_font(font)
        _HERSHEY_CACHE[font] = hf
    hf = _HERSHEY_CACHE[font]
    hf.normalize_rendering(height)
    return hf


class HersheySource:
    """从 Hershey 字体取拉丁字母/数字/符号的中心线。

    坐标语义：默认满格方块；``preserve_metrics=True`` 时保字体度量（x-height）。
    """

    def __init__(self, font: str = "futural"):
        self.font = font

    def strokes_for(self, char: str) -> RawGlyph:
        hf = _hershey(self.font, 21.0)
        return [list(s) for s in hf.strokes_for_text(char)]

    def normalize(self, raw: RawGlyph, preserve_metrics: bool,
                  bbox: BBox) -> Tuple[RawGlyph, float]:
        if preserve_metrics:
            return normalize_font_metrics(raw, bbox)
        return normalize_unit_height(raw, bbox)

    def __repr__(self) -> str:                       # noqa: D105
        return f"HersheySource(font={self.font!r})"
