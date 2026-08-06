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
```

它们根据 `target` 的 bbox 自适应位置和大小：下划线、删除线、勾、叉和圈分别对应五种
课堂批注语义。`check` 与 `cross` 用 `mark_size` 控制符号整体大小；其他标记使用 `size`
控制笔迹直径。`circle` 的 `ratio` 控制圈相对目标 bbox 的放大比例。

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
`ratio`、`closed` 与 `n_points`。点数必须至少为 2，`ratio` 必须大于 0。

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
