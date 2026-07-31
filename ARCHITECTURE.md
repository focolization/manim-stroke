# strokes 架构

`strokes` 的目标是把“课堂手写批注”绑定到 Manim 对象，并按真实书写过程播放。

```text
VMobject target
    │
    ├─ marks/：读取 bbox，决定标注位置、默认尺寸和颜色
    │
    ├─ paths/：生成下划线、勾、叉、圈等中心线
    │
    ├─ freehand.py：把中心线扩展成有宽度、端帽和渐细的闭合轮廓
    │
    └─ animation.py：截取当前已走过的中心线，逐帧重建已写出的轮廓
```

## 分层职责

- `freehand/freehand.py`：纯数学层，不依赖 Manim。`get_stroke()` 处理“笔尖轨迹如何成为
  实心笔迹”。
- `paths/`：纯手势层，不依赖 Manim。每个文件一个标记的中心线函数，只产生二维中心线；
  它不知道颜色、场景和动画。
- `marks/`：Manim 绑定层。高层 API 在这里读取目标 bbox、调用 paths 与 freehand，
  并打包成 `Mark`。每个文件一个标记。
- `animation.py`：Manim 动画层。`ProgressiveStroke` 负责一笔，`DrawMark` 组合多笔。

`paths/` 与 `marks/` 是平行的「一个标记一个文件」包：paths 只管几何，marks 只管绑定，
复用同一个 path 的标记（如 dot_circle/lparen/rparen 复用 circle_path）在 marks 侧 import 即可，
不必在 paths 侧重复文件。

## 为什么动画不直接用 `Create`

`get_stroke()` 的输出是一个实心 Polygon；对它使用普通轮廓动画会沿外边界描边，视觉上不
像笔尖书写。`ProgressiveStroke` 反而按弧长截取中心线，再使用同一套 freehand 参数生成
当前已写出的实心笔迹，因此笔尖经过的区域会立即留下完整粗细的墨迹。

## 随机性的边界

随机层只在创建 `Mark` 时依据 `seed` 生成并固定。`variation` 放大或减弱这种手势差异；
动画帧和 `.follow()` 重建沿用同一 seed，因此形状不会逐帧跳变。
