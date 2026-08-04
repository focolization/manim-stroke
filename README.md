# strokes — Manim 课堂手绘批注

`strokes` 把“圈起来、打勾、划掉、下划线”封装为可直接绑定 Manim 对象的课堂批注。
它接收文字、公式、图形或文字切片，按目标 bbox 自动定位、缩放，并沿真实中心线把
实心笔迹逐步写出来。

## 快速开始

从仓库根目录运行 Manim 时，直接导入：

```python
from manim import *
from manim_stroke import DrawMark, check, circle, cross, strike, underline, highlight


class Example(Scene):
    def construct(self):
        formula = MathTex("a^2+b^2=c^2")
        self.add(formula)

        mark = circle(formula, color="#6FA8C8")
        self.play(DrawMark(mark, run_time=1.8))
```

若场景文件不在本仓库中，将仓库根目录加入 `PYTHONPATH` 后使用相同导入路径。

## 演示视频

下面这支宣传片用同一组课堂批注，直观对比原生 Manim 的规整几何和
`manim-stroke` 的自然笔触：手写文字、下划线、删除线、圈选、高亮和常用手势。

<video controls width="720" src="https://github.com/user-attachments/assets/f5b27c4e-3862-4f2a-82e1-9c6d0025d52a"></video>

如果当前页面不直接播放，也可以[打开视频附件](https://github.com/user-attachments/assets/f5b27c4e-3862-4f2a-82e1-9c6d0025d52a)。

## 原生 Manim vs `manim-stroke`

原生 Manim 当然可以画线、画圆、做高亮；但这些几何通常需要自己计算位置、大小和动画
顺序。`manim-stroke` 把这层重复工作封装起来，并在最终轮廓上加入可复现的自然变化。

### 同一个公式：下划线与圈选

原生写法需要手动根据目标位置和宽高搭几何对象：

```python
from manim import *


class Native(Scene):
    def construct(self):
        formula = MathTex("a^2+b^2=c^2")
        self.add(formula)

        # 位置、长度和半径都要自己估算；这是规整几何。
        line = Line(
            formula.get_left() + DOWN * 0.18,
            formula.get_right() + DOWN * 0.18,
            color="#E85D75",
            stroke_width=5,
        )
        ring = Circle(
            radius=max(formula.height * 0.85, 0.4),
            color="#087EA4",
            stroke_width=5,
        ).move_to(formula)
        self.play(Create(line), Create(ring))
```

`manim-stroke` 直接把目标交给手势函数：

```python
from manim import *
from manim_stroke import DrawMark, circle, underline


class Stroke(Scene):
    def construct(self):
        formula = MathTex("a^2+b^2=c^2")
        self.add(formula)

        # 自动读取目标 bbox；起伏、圆头和绘制过程由库处理。
        line = underline(formula, color="#E85D75", seed=7, variation=1.2)
        ring = circle(formula, color="#087EA4", seed=8, closed=False)
        self.play(DrawMark(line), DrawMark(ring))
```

### 手写文字

```python
# 原生 Manim：Write() 是印刷体字形。
self.play(Write(Text("learn math")))

# manim-stroke：按笔画顺序生成手写字形，带提笔间隔和稳定 seed。
from manim_stroke import DrawHandwriting, StrokeText

word = StrokeText("learn math", font="futural", size=1.0,
                  color="#D97706", at=ORIGIN, seed=11)
self.play(DrawHandwriting(word))
```

### 手写汉字（v0.2.0）

汉字同样逐笔手写，内置 9500+ 常用字的 medians 数据（来自 Make Me a Hanzi，无需联网/字体）：

```python
from manim_stroke import DrawHandwriting, hanzi

h = hanzi(ORIGIN, "永", size=1.0, color="#2E7D6B", position="center", seed=7)
self.play(DrawHandwriting(h))
```

拉丁与汉字共用同一条手写管道（`letter`/`hanzi`/`StrokeText`），只有数据源按语种隔离。

对比的重点不是“原生 Manim 完全做不到”，而是：同样的课堂动作，
`manim-stroke` 不需要每次手写 bbox 计算、路径采样和逐笔动画，且每个标记仍可通过
`seed` 复现、通过 `variation` 控制自然程度。

## 文档

README 保留可快速运行的入口；完整公开 API 按用户任务拆在 [`docs/`](docs/index.md)，避免一个
不断膨胀的单页参考手册。

- [标记 API](docs/marks.md)：下划线、勾、叉、圈、星号、括号等。
- [动画 API](docs/animation.md)：`DrawMark` 与 `DrawHandwriting`。
- [风格与随机性](docs/styles.md)：`MarkStyle`、`HandwritingStyle`、`seed`。
- [手写文字 API](docs/handwriting.md)：`letter`、`hanzi`、`StrokeText`、字体、笔顺与小写 metrics。
- [底层几何 API](docs/geometry.md)：`get_stroke`、`get_stroke_points`、`StrokePoint`。
- [致谢、第三方 notices 与方法参考](docs/references.md)。

### 手写文字（快速开始）

```python
from manim_stroke import StrokeText, DrawHandwriting

self.play(DrawHandwriting(StrokeText("learn with manim")))
```

`futural` 是默认且最稳妥的字体；`rowmans`、`timesr` 也适合可读的小写。完整参数、字体
选择和限制见 [手写文字 API](docs/handwriting.md)。

## 标记 API

所有高层函数的第一个参数都是目标 `VMobject`。它可以是 `Text`、`MathTex`、
`VGroup`，也可以是文字的局部切片，例如 `text[2:4]`。

```python
underline(target, ...)
strike(target, ...)
check(target, ...)
cross(target, ...)
circle(target, ...)
highlight(target, ...)
```

| 函数 | 默认位置 / 手势 |
|---|---|
| `underline` | 目标下方的一笔低频轻微起伏线 |
| `strike` | 目标中线的一笔果断划线 |
| `check` | 目标下方的一笔连续 ✓，拐点后上挑 |
| `cross` | 覆盖目标：先 `\` 左上→右下，再 `/` 右上→左下 |
| `circle` | 沿目标 bbox 绘制手绘椭圆圈 |
| `highlight` | 沿目标中线横扫一笔荧光笔高亮：粗、圆鼻头、半透明、带手绘抖动 |

默认笔画直径约为目标高度的 8%；✓ 和 × 的大小约为目标高度的 80%。所以标注会随
字号或图形大小自动适配。

### 通用视觉参数

```python
mark = check(
    answer,
    color="#6FA8C8",  # 笔迹颜色
    size=None,         # 笔画直径；None 表示自适应
    thinning=0,        # 压力对粗细的影响；0 为固定笔宽
    cap=True,          # 圆头起笔/收笔
    taper=0,           # 起笔、收笔渐细长度
    smoothing=0.5,     # 轮廓平滑度
)
```

当同一场景需要多个相同笔触风格的标记时，可复用 ``MarkStyle``。单次调用中
显式传入的视觉参数会覆盖 ``style`` 的同名值：

```python
from manim_stroke import MarkStyle, check, circle

blue_ink = MarkStyle(color="#6FA8C8", size=0.065, cap=True)
focus = circle(term, style=blue_ink)
answer_mark = check(answer, style=blue_ink, taper=0.08)
```

除 ``target`` 外，建议始终用关键字传递参数。``n_points`` / ``num_points`` 至少为
2，``circle(..., ratio=...)`` 的 ``ratio`` 必须大于 0。

### 手势随机层

每次不传 `seed` 创建标记时，都会得到一个新的自然手势；该随机结果会保存在 `Mark`
中，因此动画过程、暂停画面和 `.follow()` 期间都不会跳变。

```python
# 每次创建都不同，但同一个 mark 始终稳定。
one = underline(text, variation=1.1)
two = underline(text, variation=1.1)

# 固定 seed，用于可复现的课件渲染。
stable = check(answer, seed=2026, variation=0.8)
```

| 参数 | 作用 |
|---|---|
| `seed=None` | 手势随机种子；`None` 为每次创建生成新 seed |
| `variation=1.0` | 随机层强度；`0` 为规整几何，`1` 为默认自然程度 |
| `jitter` | 此标记的基础偏移幅度；实际偏移约为 `jitter × variation` |

随机只影响创建时的形状：下划线/划线的平滑起伏与倾斜、✓ 的拐点和上挑、× 的法向偏移、
以及圈的径向偏移。它不会改变 × 的笔顺，也不会每帧重新抽样。

### 标记专属参数

```python
underline(text, offset=None, n_points=24)
strike(text, n_points=24)
check(answer, mark_size=None, curvature=0.15, offset=None, num_points=50)
cross(option, mark_size=None, n_points=18)
circle(term, ratio=1.25, closed=None, n_points=40)
highlight(target, opacity=0.4, cap=True, jitter=0.05, pad=None, n_points=32)
```

`circle(..., closed=None)`（默认）会按 `seed` 随机决定起笔位置、顺逆时针方向和
收笔手势：`normal`（闭合）、`open`（缺口）或 `overlap`（略压过起笔点）。
传 `closed=True` 可强制闭合，传 `closed=False` 可强制开口。

`highlight` 是荧光笔式的**半透明**粗带：`size`（默认 ~ 目标高度 0.85 倍）作带宽，
`opacity`（默认 0.4）控半透明（文字透得出），`cap=True` 给圆鼻头，`jitter`（默认 0.05）
给中心线低频抖动以保留手绘感。它走 `line` 速度，一笔横扫。

## 动画 API

`DrawMark` 沿中心线增长同一个最终 freehand Polygon：笔尖经过的位置立刻留下完整粗细
的墨迹；它不描绘 Polygon 的外周，也不会在结束时淡入替换另一个对象。

```python
mark = cross(wrong_option, speed="flick")
self.play(DrawMark(mark, run_time=1.6))

# 可在播放时覆盖创建时指定的速度。
self.play(DrawMark(mark, run_time=2.0, speed="careful"))
```

| `speed` | 书写节奏 |
|---|---|
| `steady` | 匀速推进 |
| `natural` | 触纸后渐快，末端保留一点行笔惯性 |
| `circle` | 圈专属：短暂落笔定向，圆周中段近匀速巡航，尾部减速提笔；圈默认使用 |
| `line` | 直线/斜线专属：一个不对称 Sigma-Lognormal 速度脉冲；下划线、删除线、× 默认使用 |
| `check` | 两个连续的 Sigma-Lognormal 笔画单元；短腿落下、过拐点后重新上挑；✓ 默认使用 |
| `flick` | 大部分位移快速完成，末端短促收住 |
| `decisive` | 快速推进后较平缓地收住 |
| `careful` | 起笔与收笔都明显放缓 |

速度并非按图标“凭感觉”分配：手写运动可分解为不对称的 Sigma-Lognormal 速度单元。
因此 ✓ 的两段各自有一次速度脉冲，× 的两笔严格串行且各自有一次速度脉冲；第二笔只在
第一笔完成后开始。需要更夸张的课堂强调时，仍可显式传 `speed="flick"`。

## 跟随目标

调用 `.follow()` 后，目标移动或缩放时，标记会按创建时的同一 seed 和参数重新定位。

```python
label = Text("关键结论")
focus = circle(label, seed=8).follow()
self.add(label, focus)
self.play(label.animate.shift(RIGHT * 2))

focus.unfollow()  # 需要固定位置时停止跟随
```

`Mark` 是 `VGroup` 子类，因此可像普通 Manim mobject 一样 `add`、`shift`、`scale`。

## 底层笔迹 API

如需自定义中心线，可直接调用纯几何函数：

```python
from manim import Polygon
from manim_stroke import get_stroke

points = [[-2, 0], [-1, 0.1], [0, -0.05], [2, 0]]
outline = get_stroke(points, size=0.08, smoothing=0.5, last=True)
ink = Polygon(*[(x, y, 0) for x, y in outline], fill_color="#6FA8C8",
              fill_opacity=1, stroke_width=0)
```

`get_stroke` 只做“中心线 → 闭合笔迹轮廓”的几何计算，无 Manim 场景依赖。

## API 边界

- 日常使用：从 ``manim_stroke`` 导入 ``underline``、``strike``、``check``、
  ``cross``、``circle``、``highlight``、``Mark``、``MarkStyle``、``DrawMark`` 和 ``get_stroke``。
- 高级几何使用：``get_stroke_points``、``get_stroke_outline_points``、``StrokePoint``。
- ``paths/`` 是内部几何层（生成手势中心线），不作为稳定的日常 API 承诺。

完整参数和行为约定见 [docs/](docs/index.md)，实现分层说明见
[ARCHITECTURE.md](ARCHITECTURE.md)。

## 目录

```text
manim_stroke/
├── __init__.py             # 对外导出 API
├── animation.py            # ProgressiveStroke 与 DrawMark
├── freehand/
│   └── freehand.py         # 中心线 → perfect-freehand 风格轮廓
├── paths/                  # 纯几何层（不依赖 Manim）：一个标记一个文件
│   ├── _helpers.py         #   低频抖动 _smooth_wobble / 闭合谐波 _periodic_wobble
│   ├── circle.py cross.py check.py star.py strike.py underline.py highlight_path.py
├── marks/                  # Manim 绑定层：一个标记一个文件
│   ├── _common.py          #   Mark / MarkStyle / 目标自适应辅助
│   ├── circle.py cross.py check.py star.py strike.py underline.py highlight.py
│   └── dot_circle.py lparen.py rparen.py   # 复用 circle_path
├── examples/               # 可运行演示场景
└── tests/                  # freehand / 高层 API 回归测试
```
