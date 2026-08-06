"""渲染命令：PYTHONPATH=. uv run manim -qm manim_stroke/examples/math_annotations_demo.py MathAnnotationsDemo"""
from __future__ import annotations

from manim import (
    DOWN,
    RIGHT,
    UP,
    FadeIn,
    MathTex,
    Rectangle,
    Scene,
    Text,
    VGroup,
    Write,
    config,
)

from manim_stroke import DrawMark, MarkStyle, check, circle, highlight, underline


class MathAnnotationsDemo(Scene):
    """只展示 manim-stroke 的数学批注笔触，不引入额外时间轴。"""

    BLUE = "#4F86C6"
    GREEN = "#3BA67A"
    PEACH = "#D9895B"
    LAVENDER = "#8A67B5"
    INK = "#243447"

    def construct(self) -> None:
        background = Rectangle(
            width=config.frame_width,
            height=config.frame_height,
            fill_color="#F7F3EB",
            fill_opacity=1,
            stroke_opacity=0,
        )
        title = Text("MANIM-STROKE", font_size=34, color=self.INK).to_edge(UP, buff=0.35)
        subtitle = Text("数学公式上的自然手绘批注", font_size=19, color="#667085").next_to(
            title, DOWN, buff=0.12
        )
        self.add(background, title, subtitle)

        equation = MathTex(r"x^2-5x+6=0", font_size=62, color=self.INK).move_to([-2.8, 1.3, 0])
        factorized = MathTex(r"(x-2)(x-3)=0", font_size=50, color=self.INK).move_to([2.8, 1.3, 0])
        answer = VGroup(
            MathTex(r"x=2", font_size=52, color=self.INK),
            Text("或", font_size=34, color=self.INK),
            MathTex(r"x=3", font_size=52, color=self.INK),
        ).arrange(RIGHT, buff=0.3).move_to([0, -0.05, 0])
        note = Text("解的集合", font_size=18, color="#667085").next_to(answer, DOWN, buff=0.48)

        self.play(Write(equation), Write(factorized), run_time=1.0)

        blue_ink = MarkStyle(color=self.BLUE, size=0.075, cap=True, smoothing=0.55)
        peach_ink = MarkStyle(color=self.PEACH, size=0.075, cap=True, smoothing=0.55)
        green_ink = MarkStyle(color=self.GREEN, size=0.075, cap=True, smoothing=0.55)
        lavender_ink = MarkStyle(color=self.LAVENDER, size=0.075, cap=True, smoothing=0.55)

        # 一笔下划线：沿公式中心线留下完整、略带抖动的实心笔迹。
        self.play(DrawMark(underline(equation, style=blue_ink), run_time=0.9))
        # 荧光笔：粗、半透明、圆头，底下的公式仍然可读。
        self.play(DrawMark(highlight(factorized, style=peach_ink, opacity=0.45), run_time=0.85))
        self.play(FadeIn(answer, note, run_time=0.65))
        # 圈选两个不同目标，展示 bbox 自适应和每次独立的自然手势。
        self.play(DrawMark(circle(answer[0], style=green_ink), run_time=0.8))
        self.play(DrawMark(circle(answer[2], style=lavender_ink), run_time=0.8))
        # 最后一笔勾选整组答案。
        self.play(DrawMark(check(answer, color=self.GREEN, size=0.07), run_time=0.65))
        self.wait(1.2)
