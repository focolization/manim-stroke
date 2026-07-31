"""验证新标注:dot_circle/lparen/rparen + 大圈/下划线,用 DrawMark 动画看笔画顺序。"""
import os, sys
from manim import *
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))   # strokes/
from manim_stroke import dot_circle, lparen, rparen, circle, underline, star
from manim_stroke import DrawMark


class NewMarksDemo(Scene):
    def construct(self):
        bg = Rectangle(width=16, height=9, fill_color="#FBF6F0", fill_opacity=1, stroke_width=0)
        self.add(bg)
        words = ["公允价值", "权益工具", "股份支付", "可行权条件"]
        mobs = VGroup(*[Text(w, font="PingFang SC", color="#4A4540", font_size=44) for w in words])
        mobs.arrange(DOWN, buff=0.8).to_edge(LEFT, buff=2)
        self.add(mobs)
        # 逐个画,看笔画顺序
        self.play(DrawMark(dot_circle(mobs[0][2])), run_time=1.0)   # 「价」下小圆
        self.play(DrawMark(dot_circle(mobs[1][0])), run_time=1.0)   # 「权」下小圆
        self.play(DrawMark(lparen(mobs[2])), run_time=1.0)          # 「股份支付」左 (
        self.play(DrawMark(rparen(mobs[3])), run_time=1.0)          # 「可行权条件」右 )
        self.play(DrawMark(circle(mobs[0][0:2])), run_time=1.2)     # 「公允」大圈(对比)
        self.play(DrawMark(underline(mobs[3][2:4])), run_time=1.0)  # 「条件」下划线(对比)
        self.play(DrawMark(star(mobs[1][2:4]), run_time=1.2))      # 「工具」下五角星(below)
        self.play(DrawMark(star(mobs[2][0:2], position="upper-right"), run_time=1.2))  # 「股份」右上角五角星
        self.wait(0.5)