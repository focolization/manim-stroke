# 标记 API

每个标记函数都接收一个 Manim `VMobject` 作为 `target`，返回 `Mark`。`target` 可以是
`Text`、`MathTex`、`VGroup` 或文字切片（例如 `text[2:4]`）。

```python
mark = underline(term, color="#6FA8C8", seed=8)
self.play(DrawMark(mark))
```

## 通用参数

`size` 是笔迹直径；`None` 时按 target 高度自适应。`color`、`thinning`、`cap`、`taper`、
`smoothing` 可直接传入，也可由 [`MarkStyle`](styles.md#markstyle) 提供。`seed=None` 每次生成
新的稳定手势；指定整数则可复现。`variation=0` 关闭手势随机性，`variation=1` 为默认强度。

## 函数

| 函数 | 默认速度 | 专属参数 | 效果 |
|---|---|---|---|
| `underline(target, ...)` | `line` | `offset`, `n_points=24`, `jitter=.012` | 目标下方轻微起伏线 |
| `strike(target, ...)` | `line` | `n_points=24`, `jitter=.007` | 目标中线删除线 |
| `check(target, ...)` | `check` | `mark_size`, `curvature=.15`, `offset`, `num_points=50` | 目标下方连续 ✓ |
| `cross(target, ...)` | `line` | `mark_size`, `n_points=18` | 覆盖目标的两笔 × |
| `circle(target, ...)` | `circle` | `ratio=1.25`, `closed`, `n_points=40` | 围绕 bbox 的椭圆圈 |
| `star(target, ...)` | `line` | `mark_size`, `position`, `offset` | 一笔五角星 |
| `dot_circle(target, ...)` | `circle` | `ratio=.22`, `offset` | 单字下方小圆 |
| `lparen(target, ...)` / `rparen(target, ...)` | `circle` | `ratio=.6`, `offset` | 目标左右的手绘括号 |
| `highlight(target, ...)` | `line` | `opacity=.4`, `cap=True`, `jitter=.05`, `pad`, `n_points=32` | 荧光笔高亮：粗、圆鼻头、半透明、手绘抖动 |

`circle(..., closed=None)` 会依据 seed 选择闭合、留缺口或略微重叠；传 `True` 或 `False` 强制
闭合或开口。`star(..., position=...)` 支持 `below` 与 `upper-right`。

`highlight` 是荧光笔式半透明粗带：`size` 作带宽（默认 ~ 目标高度 0.85 倍），`opacity`
控半透明（默认 0.4，文字透得出），`cap=True` 给圆鼻头，`jitter`（默认 0.05）给中心线
低频抖动以保留手绘感，`pad` 让高亮左右比目标多出一点。

## Mark

`Mark` 是 `VGroup`，可直接 `add`、`shift`、`scale`。当 target 会移动或缩放时：

```python
focus = circle(term, seed=8).follow()
self.add(term, focus)
self.play(term.animate.shift(RIGHT * 2))
focus.unfollow()
```

`refresh()` 立即按当前 target bbox 重建；`follow()` 增加刷新 updater；`unfollow()` 停止跟随。
