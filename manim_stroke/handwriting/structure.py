"""Constraint-preserving, primitive-level glyph structure variation.

This module intentionally knows geometry rather than a catalogue of 26 glyph
solvers.  It recognises three reusable arrangements in Hershey polylines:
two diagonal legs plus a bar, a vertical stem plus bowls, and a lone curved
outline.  Shared latent samples alter each arrangement while endpoint anchors
are constructed from the parent primitive, not repaired after the fact.
"""
from __future__ import annotations

import math
import random
from typing import List

from .style import HandwritingStyle


def _copy(strokes):
    return [[[float(p[0]), float(p[1])] for p in s] for s in strokes]


def _length(stroke):
    return sum(math.dist(a, b) for a, b in zip(stroke, stroke[1:]))


def _orientation(stroke):
    a, b = stroke[0], stroke[-1]
    return math.atan2(b[1] - a[1], b[0] - a[0])


def _near_vertical(stroke):
    if len(stroke) < 2:
        return False
    a, b = stroke[0], stroke[-1]
    return abs(b[1] - a[1]) > 2.2 * abs(b[0] - a[0])


def _is_bar(stroke):
    if len(stroke) < 2:
        return False
    a, b = stroke[0], stroke[-1]
    return abs(b[0] - a[0]) > 2.2 * abs(b[1] - a[1])


def _point_at_y(a, b, y):
    dy = b[1] - a[1]
    if abs(dy) < 1e-9:
        return [a[0], y]
    t = max(0.0, min(1.0, (y - a[1]) / dy))
    return [a[0] + t * (b[0] - a[0]), y]


def _leg_bar(strokes, z_width, z_height):
    """Construct an A-like skeleton: bar endpoints are intersections with legs."""
    bars = [i for i, s in enumerate(strokes) if _is_bar(s)]
    # A's legs are often steep enough to look "near vertical" under a broad
    # stem detector; only reject truly vertical strokes here.
    diagonals = [i for i, s in enumerate(strokes) if len(s) >= 2 and not _is_bar(s)
                 and abs(s[-1][0] - s[0][0]) > 0.06]
    if not bars or len(diagonals) < 2:
        return False
    diagonals = sorted(diagonals, key=lambda i: _length(strokes[i]), reverse=True)[:2]
    # It must actually be an apex: the upper endpoints need to meet closely.
    tops, bottoms = [], []
    for i in diagonals:
        a, b = strokes[i][0], strokes[i][-1]
        tops.append(a if a[1] >= b[1] else b)
        bottoms.append(b if a[1] >= b[1] else a)
    if math.dist(tops[0], tops[1]) > 0.18:
        return False
    apex_x = (tops[0][0] + tops[1][0]) / 2 + 0.045 * z_width
    top_y = (tops[0][1] + tops[1][1]) / 2
    gap = max(0.0, 0.025 + 0.030 * z_width)
    spread = 1.0 + 0.10 * z_width
    new_legs = []
    for side, bottom in zip((-1, 1), bottoms):
        top = [apex_x + side * gap / 2, top_y]
        new_bottom = [apex_x + (bottom[0] - apex_x) * spread, bottom[1]]
        original = strokes[diagonals[0 if side == -1 else 1]]
        # Preserve stroke direction.
        new_legs.append(([top, new_bottom] if original[0][1] >= original[-1][1]
                         else [new_bottom, top]))
    for i, leg in zip(diagonals, new_legs):
        strokes[i] = leg
    bar_i = max(bars, key=lambda i: _length(strokes[i]))
    bar = strokes[bar_i]
    h = max(min((bar[0][1] + bar[-1][1]) / 2 + 0.08 * z_height,
                top_y - 0.12), min(b[1] for b in bottoms) + 0.12)
    tilt = 0.035 * z_width
    left, right = sorted(new_legs, key=lambda s: (s[0][0] + s[-1][0]) / 2)
    ql = _point_at_y(left[0], left[-1], h - tilt)
    qr = _point_at_y(right[0], right[-1], h + tilt)
    strokes[bar_i] = [ql, qr] if bar[0][0] <= bar[-1][0] else [qr, ql]
    return True


def _stem_bowls(strokes, z_width, z_height):
    stems = [i for i, s in enumerate(strokes) if _near_vertical(s)]
    if not stems:
        return False
    stem_i = max(stems, key=lambda i: _length(strokes[i]))
    stem = strokes[stem_i]
    stem_x = (stem[0][0] + stem[-1][0]) / 2
    changed = False
    scale = 1.0 + 0.11 * z_width
    for i, curve in enumerate(strokes):
        if i == stem_i or len(curve) < 4:
            continue
        # A bowl is attached to the stem at at least one endpoint.  Scaling
        # relative to stem_x leaves every such attachment exactly invariant.
        attached = min(abs(curve[0][0] - stem_x), abs(curve[-1][0] - stem_x)) < 0.08
        if not attached:
            continue
        n = len(curve) - 1
        out = []
        for j, p in enumerate(curve):
            u = j / n
            # sin(pi u) is zero at anchors, so bulge cannot make a hook there.
            out.append([stem_x + (p[0] - stem_x) * scale,
                        p[1] + 0.025 * z_height * math.sin(math.pi * u)])
        strokes[i] = out
        changed = True
    return changed


def _single_curve(strokes, z_width, z_height):
    if len(strokes) != 1 or len(strokes[0]) < 5:
        return False
    s = strokes[0]
    # A curve, not a one-stroke straight glyph (I, etc.).
    turn = sum(abs(math.atan2((s[i][0]-s[i-1][0])*(s[i+1][1]-s[i][1]) -
                              (s[i][1]-s[i-1][1])*(s[i+1][0]-s[i][0]),
                              (s[i][0]-s[i-1][0])*(s[i+1][0]-s[i][0]) +
                              (s[i][1]-s[i-1][1])*(s[i+1][1]-s[i][1])))
               for i in range(1, len(s) - 1))
    if turn < math.radians(70):
        return False
    cx = (min(p[0] for p in s) + max(p[0] for p in s)) / 2
    cy = (min(p[1] for p in s) + max(p[1] for p in s)) / 2
    rx, ry = 1.0 + 0.09 * z_width, 1.0 + 0.06 * z_height
    strokes[0] = [[cx + (p[0] - cx) * rx, cy + (p[1] - cy) * ry] for p in s]
    return True


def structure_deform(strokes: List[List[List[float]]], style: HandwritingStyle,
                     seed: int) -> List[List[List[float]]]:
    """Apply a small, reproducible structural variation without changing topology."""
    out = _copy(strokes)
    if not out:
        return out
    rng = random.Random(seed + 2027)
    limit = style.structure_limit
    z_width = max(-limit, min(limit, rng.gauss(0.0, style.structure_std))) / max(limit, 1e-9)
    z_height = max(-limit, min(limit, rng.gauss(0.0, style.structure_std))) / max(limit, 1e-9)
    # Recognisers are ordered from constrained skeleton to less constrained curve.
    if _leg_bar(out, z_width, z_height):
        return out
    if _stem_bowls(out, z_width, z_height):
        return out
    _single_curve(out, z_width, z_height)
    return out
