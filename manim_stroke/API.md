# strokes API

本页记录当前建议依赖的 API。除非另有说明，所有高层标记函数都返回 `Mark`，第一个
参数都是 Manim `VMobject`（如 `Text`、`MathTex`、`VGroup` 或文字切片）。

## 高层标记

```python
underline(target, ..., style=None)
strike(target, ..., style=None)
check(target, ..., style=None)
cross(target, ..., style=None)
circle(target, ..., style=None)
highlight(target, ..., style=None)
```

它们根据 `target` 的 bbox 自适应位置和大小：下划线、删除线、勾、叉、圈分别对应五种
课堂批注语义，`highlight` 是粗圆头、半透明、带手绘抖动的荧光笔横扫。`check` 与
`cross` 用 `mark_size` 控制符号整体大小；其他标记使用 `size` 控制笔迹直径。`circle` 的
`ratio` 控制圈相对 target bbox 的放大比例。`highlight` 另有 `opacity`(半透明度)、
`pad`(左右多出量)、`jitter`(中心线手绘抖动)。

所有函数共有的视觉参数如下：

| 参数 | 含义 |
| --- | --- |
| `style` | 可复用的 `MarkStyle`；显式传入的同名视觉参数优先。 |
| `color` | 笔迹填充颜色。 |
| `size` | 笔迹直径；`None` 时按目标高度自适应。 |
| `thinning` | 压力对粗细的影响；`0` 为固定笔宽。 |
| `cap` | 是否使用圆头。 |
| `taper` | 起笔和收笔的渐细长度。 |
| `smoothing` | freehand 轮廓的平滑度。 |
| `seed` | 手势随机种子；相同创建参数和相同 seed 生成相同手势。 |
| `variation` | 手势随机层的强度；`0` 为规整几何。 |
| `speed` | 默认书写节奏，可在 `DrawMark` 中覆盖。 |

`underline` 有 `offset` 与 `n_points`；`strike` 有 `n_points`；`check` 有 `mark_size`、
`curvature`、`offset` 与 `num_points`；`cross` 有 `mark_size` 与 `n_points`；`circle` 有
`ratio`、`closed` 与 `n_points`；`highlight` 有 `opacity`、`pad`、`jitter`、`n_points` 与
`variation`。点数必须至少为 2，`ratio` 必须大于 0。

## 手写（handwriting）API

手写入口在 `marks` 层，播放动画在 `animation.DrawHandwriting`。它们返回 `Mark`，与其它
标记一样可 `Scene.add()`、移动、缩放，并交给 `DrawHandwriting` 逐笔写出来。

```python
# 拉丁字母（Hershey）：letter(target, char, ...)
# 单个汉字：hanzi(target, char, ...)
# 整词：StrokeText("learn with manim")
```

### `letter(target, char, font="futural", size=None, color=None, position="left",
        offset=None, handwriting=None, seed=None, speed="handwriting", style=None) -> Mark`

在目标旁画一个手绘**拉丁**字母/数字/符号（Hershey，不支持中文，中文用 `hanzi`）。
`font` 选字体（`futural` 干净、`cursive`/`scripts` 手写感）；`size` 字母高度（None 自适应
目标高度）；`position` 相对目标方位——`left/right/above/below/upper-right/center`；
`handwriting` 传 `HandwritingStyle`（默认 `DEFAULT_HANDWRITING`）；`seed` 决定笔迹身份。

### `hanzi(target, char, size=None, color=None, position="left", offset=None,
        handwriting=None, source=None, seed=None, speed="handwriting", style=None) -> Mark`

在目标旁画一个手写**汉字**。`char` 为单个汉字（内置 9500+ 常用字数据，无需联网/字体）。
`handwriting` 默认 `HANZI_HANDWRITING`；`source` 可传自定义数据源，缺省用内置 medians
数据。`size` 为字高，其余参数同 `letter`。

### `StrokeText(text, font="futural", size=1.5, color="#6FA8C8", at=ORIGIN,
        handwriting=None, seed=None, letter_gap=None, speed="handwriting",
        segment=True, space_width=0.42) -> Mark`

手写一整词：字母并排成一条 `Mark`，交给 `DrawHandwriting` 整词播放。空格是排版前进量，
不是字形——`"learn with manim"` 直接可用。`space_width` 以 `size` 为单位。

### `DrawHandwriting(mark, handwriting=None)`

按真实笔顺把 `letter()` / `hanzi()` / `StrokeText` 写出来（每个笔画用其 `Mark` 自带时长）。
返回 manim `Succession` 动画，`Scene.play(DrawHandwriting(mark))` 即可。

### `HandwritingStyle` / `DEFAULT_HANDWRITING` / `HANZI_HANDWRITING`

`HandwritingStyle` 是不可变 dataclass，集中视觉与运动参数（笔宽、倾斜、抖动、笔锋、
书写节奏等）。预设两个：`DEFAULT_HANDWRITING`（拉丁）、`HANZI_HANDWRITING`（汉字，
方形字格、关闭结构变形）。通过 `handwriting=` 传入上述函数即可调观感；内部的时间/噪声
算法对调用方透明，通常无需逐个手调。

> 说明：底层变形/时间算法（噪声、速度曲线等）属内部实现，不构成公开 API，详见
> `ARCHITECTURE.md`。

## `MarkStyle`

```python
MarkStyle(
    color="#6FA8C8", size=None, thinning=0,
    cap=True, taper=0, smoothing=0.5,
)
```

这是不可变的视觉样式值对象。它可在多个标记间复用：

```python
ink = MarkStyle(color="#6FA8C8", size=0.065)
circle(term, style=ink)
check(answer, style=ink, taper=0.08)
```

## `Mark`

`Mark` 是 `VGroup` 子类，因此可以正常 `Scene.add()`、移动和缩放。高层函数创建的
`Mark` 支持：

```python
mark.refresh()   # 立即按当前 target bbox 重建
mark.follow()    # 每帧跟随 target 的移动和缩放；可链式调用
mark.unfollow()  # 停止跟随，保留当前形状
```

`centerlines`、`stroke_options` 等字段供动画实现使用；不要把它们当成稳定的日常 API。

## `DrawMark`

```python
DrawMark(mark, run_time=1.2, lag_ratio=1.0, speed=None)
```

按真实笔顺使一个 `Mark` 生长。`speed=None` 时沿用创建标记时的速度；可选值为
`steady`、`natural`、`decisive`、`careful`、`flick`、`line`、`check`、`circle`。未知值会在
构造动画时抛出 `ValueError`。

## 低层 freehand API

```python
get_stroke(points, size=16, thinning=0, smoothing=0.5, ...)
```

输入中心线 `[[x, y], ...]` 或带 pressure 的 `[[x, y, pressure], ...]`，返回可交给
`Polygon` 填充的闭合轮廓点列。`get_stroke_points()` 返回内部的 `StrokePoint` 序列，
`get_stroke_outline_points()` 将该序列转为轮廓；它们用于高级定制，通常直接使用
`get_stroke()` 即可。

## 兼容性约定

当前已有的 `underline(target, color=...)` 等调用保持有效，默认颜色、默认笔宽、默认速度
与此前一致。`style=` 是新增的可选入口，不要求迁移现有项目代码。
