# 底层几何 API

这些函数适合已有中心线、但想复用 manim_stroke 笔迹外观的场景。它们不依赖 Manim：输出二维点列，
由调用方自行创建 `Polygon` 或其它对象。

```python
from manim_stroke import get_stroke

outline = get_stroke([[-2, 0], [-1, .1], [1, -.05], [2, 0]],
                     size=.08, thinning=0, smoothing=.5, last=True)
ink = Polygon(*[(x, y, 0) for x, y in outline], fill_color="#6FA8C8",
              fill_opacity=1, stroke_width=0)
```

| API | 返回值 | 用途 |
|---|---|---|
| `get_stroke(points, size=16, thinning=.5, smoothing=.5, ...)` | 闭合轮廓点列 | 一步生成可填充笔迹 |
| `get_stroke_points(points, streamline=.5, size=16, last=False)` | `StrokePoint` 列表 | 仅计算中心线采样、速度/压力信息 |
| `get_stroke_outline_points(stroke_points, ...)` | 闭合轮廓点列 | 从已计算的 StrokePoint 生成外轮廓 |
| `StrokePoint` | dataclass | `point`、`pressure`、`vector`、`distance`、`running_length` |

`points` 可为 `[x, y]`、`[x, y, pressure]` 或含 `x/y/pressure` 的 dict。`thinning=0` 是固定笔宽；
设为正值并启用相关压力选项可得到速度/压力相关笔宽。`last=True` 确保最后一个输入点就是笔尖位置，
适合逐帧动画。
