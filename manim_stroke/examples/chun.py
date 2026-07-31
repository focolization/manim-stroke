"""朱自清《春》——展示 strokes 笔触库 9 种标注。
每种笔触画一个,看手绘书写感。
用法: manim -ql chun.py Chun   (或 -qh 高清)
"""
import os, sys
from manim import *
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))   # strokes/
from manim_stroke import circle, underline, dot_circle, lparen, rparen, star, check, cross, strike
from manim_stroke import DrawMark

INK = "#4A4540"
ACCENT = "#F4B6C2"   # 粉强调
BLUE = "#6FA8C8"


def word(t, color=INK, size=40):
    return Text(t, font="PingFang SC", color=color, font_size=size)


class Chun(Scene):
    def construct(self):
        bg = Rectangle(width=16, height=9, fill_color="#FBF6F0", fill_opacity=1, stroke_width=0)
        self.add(bg)
        title = Text("春 · 朱自清", font="PingFang SC", color=INK, font_size=52)
        title.to_edge(UP, buff=0.6)
        self.add(title)

        # 第一行:盼望着,盼望着,东风来了,春天的脚步近了
        l1 = VGroup(*[word(w) for w in ["盼望着","，","盼望着","，","东风","来了","，","春天","的","脚步","近了","。"]])
        l1.arrange(RIGHT, buff=0.12).move_to(UP*1.5)
        # 第二行:小草偷偷地从土里钻出来,嫩嫩的,绿绿的
        l2 = VGroup(*[word(w) for w in ["小草","偷偷地","从土里","钻出来","，","嫩嫩的","，","绿绿的","。"]])
        l2.arrange(RIGHT, buff=0.12).move_to(DOWN*1.0)
        self.play(FadeIn(l1), FadeIn(l2), run_time=0.6)

        # 9 种笔触,逐个画
        # 1 underline:盼望着(第一行[0])
        self.play(DrawMark(underline(l1[0], color=BLUE)), run_time=0.5)
        self.wait(0.2)
        # 2 circle:东风(第一行[4])
        self.play(DrawMark(circle(l1[4], color=ACCENT)), run_time=0.7)
        self.wait(0.2)
        # 3 star:春天(第一行[7]) below
        self.play(DrawMark(star(l1[7], color=ACCENT, position="below")), run_time=0.8)
        self.wait(0.2)
        # 4 dot_circle:小草(第二行[0]) 的「草」下小圆
        self.play(DrawMark(dot_circle(l2[0][1], color=ACCENT)), run_time=0.5)
        self.wait(0.2)
        # 5 lparen + 6 rparen:嫩嫩的(第二行[5]) 括起来
        self.play(DrawMark(lparen(l2[5], color=BLUE)), run_time=0.5)
        self.play(DrawMark(rparen(l2[5], color=BLUE)), run_time=0.5)
        self.wait(0.2)
        # 7 underline:绿绿的(第二行[7])
        self.play(DrawMark(underline(l2[7], color=BLUE)), run_time=0.5)
        self.wait(0.2)
        # 8 check:脚步(第一行[9]) 打勾
        self.play(DrawMark(check(l1[9], color="#6BA368")), run_time=0.6)
        self.wait(0.2)
        # 9 cross:偷偷地(第二行[1]) 打叉(标记要改)
        self.play(DrawMark(cross(l2[1], color="#D9534F")), run_time=0.6)
        self.wait(0.2)
        # 加一个 strike 展示(钻出来 划掉?诗意里划掉不合适,改用「钻」strike 演示删除线)
        self.play(DrawMark(strike(l2[3][0], color="#D9534F")), run_time=0.5)
        self.wait(1.5)