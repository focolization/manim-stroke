# 动画 API

## DrawMark

```python
self.play(DrawMark(mark, run_time=1.2, speed="natural"))
```

`DrawMark` 沿 `Mark` 保存的中心线增长实心笔迹，而不是描 Polygon 外边界。默认按创建 `Mark`
时的 `speed` 播放；传 `speed` 可覆盖。

| speed | 含义 |
|---|---|
| `steady` | 匀速 |
| `natural` | 落笔后渐快、末端自然收住 |
| `line` | 单峰 Sigma-Lognormal，适合直线 |
| `check` | 两个连续的运动单元，适合 ✓ |
| `circle` | 落笔、巡航、收笔节奏 |
| `flick` / `decisive` / `careful` | 更快、更果断、或更谨慎的手势 |

## DrawHandwriting

```python
word = StrokeText("learn", seed=7)
self.play(DrawHandwriting(word))
```

`DrawHandwriting` 仅用于 `letter()` 或 `StrokeText` 创建的 `Mark`。它读取创建时固定的每笔时长、
峰数和笔间提笔间隔；因此不会因帧率而重新抽样。硬折角笔画会自动用多峰
Sigma-Lognormal 节奏播放。
