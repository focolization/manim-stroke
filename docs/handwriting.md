# 手写文字 API

## letter

```python
mark = letter(target, "A", font="futural", position="left", seed=12)
self.play(DrawHandwriting(mark))
```

`letter(target, char, font="futural", size=None, color=None, position="left", offset=None,
handwriting=None, seed=None, speed="handwriting", style=None)` 在 target 附近书写单个 Hershey
字符。`position` 可为 `left`、`right`、`above`、`below`、`upper-right` 或 `center`；`size=None`
时使用 target 高度的 90%。`char` 必须是一个 Hershey 支持的单字符。

## StrokeText

```python
word = StrokeText("learn", font="rowmans", size=.55, at=ORIGIN,
                  color="#4D81A9", seed=41, letter_gap=.10)
self.play(DrawHandwriting(word))
```

`StrokeText(text, font="futural", size=1.5, color="#6FA8C8", at=ORIGIN, handwriting=None,
seed=None, letter_gap=None, speed="handwriting", segment=True, space_width=.42)` 创建英文文字并按字符、笔画
顺序播放。

- `futural` 是默认、最稳定的可读字体；`rowmans`、`timesr` 推荐用于传统 Roman 风格。
- `scripts`、`cursive` 是装饰性字体，原始字形更宽且上/下行更夸张。
- 小写采用共享 font metrics：`e/a` 保留 x-height，`l/h` 保留 ascender，`g/p/y` 保留 descender。
- `text` 可包含空格，例如 `StrokeText("learn with manim")`；空格是布局 advance，并会带来更长的
  pen-up 间隔。`space_width` 以 `size` 为单位控制其宽度。
- 文字位置会烤进中心线；创建后不要对成品调用 `move_to()` 再播放。要换位置应重新创建。

## 字体、结构和笔顺

HersheyFonts 决定每个字符原始 stroke 列表及每笔点序；本项目按这个默认顺序播放，并控制速度、
提笔、倾斜、抖动和结构变形。该顺序适用于正常绘制，但不保证教材级英文笔顺。需要严格笔顺时，
应在核心层增加字符级 stroke 排序规则。

结构变形默认在 `letter()` 与 `StrokeText` 开启：双腿+横杠、stem+bowl 和单曲线等 primitive
通过共享锚点保持连接。更完整的视觉与时间参数见 [styles.md](styles.md)。

时间参数化、字形来源和论文方法的归因，以及“已实现”和“仅作未来扩展”的边界，见
[致谢与参考](references.md)。
