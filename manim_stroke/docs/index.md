# manim_stroke API 文档

`manim_stroke` 是一套 Manim 课堂手绘标记与英文手写文字组件。日常 API 都从顶层包导入：

```python
from manim_stroke import circle, check, StrokeText, DrawMark, DrawHandwriting
```

| 目标 | 文档 |
|---|---|
| 给已有 Manim 对象加圈、勾、划线、括号或星号 | [标记 API](marks.md) |
| 控制标记或文字的播放 | [动画 API](animation.md) |
| 复用笔触、控制随机性和手写合成参数 | [风格与随机性](styles.md) |
| 写英文单字或单词 | [手写文字 API](handwriting.md) |
| 用自己的中心线生成墨迹轮廓 | [底层几何 API](geometry.md) |
| 查看第三方依赖、论文方法来源和实现边界 | [致谢与参考](references.md) |

架构与内部模块边界请看仓库根目录的 [ARCHITECTURE.md](../ARCHITECTURE.md)。`paths/` 和
`handwriting/` 的低层函数不是日常稳定 API，除非相应页面明确列出。
