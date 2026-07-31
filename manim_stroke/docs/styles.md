# 风格与随机性

## MarkStyle

`MarkStyle` 用于普通标记复用外观：

```python
blue_ink = MarkStyle(color="#6FA8C8", size=.065, cap=True, smoothing=.5)
focus = circle(term, style=blue_ink)
```

字段：`color`、`size`、`thinning`、`cap`、`taper`、`smoothing`。函数上显式传入的同名参数会
覆盖 `style`。

## HandwritingStyle

`HandwritingStyle` 是英文手写文字的完整配置；只需按需要覆盖字段：

```python
hw = HandwritingStyle(writer_slant_deg=7, jitter_rms=.004,
                      char_slant_std_deg=.8, command_spacing=.08)
```

| 参数组 | 关键字段 | 用途 |
|---|---|---|
| 时间 | `duration_ref`, `lognormal_sigma`, `command_spacing`, `pen_up_mean` | 笔画速度、折角停顿和提笔 |
| 峰检测 | `peak_turn_threshold_deg`, `peak_min_segment_length`, `peak_max_per_stroke` | 何时把硬折角分为多运动命令 |
| 倾斜 | `writer_slant_deg`, `word_slant_std_deg`, `char_slant_std_deg`, `char_slant_rho` | 基线 shear 与字间相关变化 |
| 抖动 | `jitter_rms`, `correlation_length`, `endpoint_envelope`, `sample_step` | 法线 AR(1) 相关噪声 |
| 整字 | `glyph_rotation_std_deg`, `glyph_scale_std`, `glyph_width_std` | 微旋、微缩、宽高变化 |
| 结构 | `structure_std`, `structure_limit` | 腿/横杠、stem/bowl、曲线 primitive 的共享变化 |
| 分段 | `segment_turn_threshold_deg`, `segment_rot_std_deg`, `segment_scale_x_std` | 局部折角和 CAD 感消除 |
| 描边 | `stroke_size_ratio`, `streamline`, `smoothing`, `pen_taper_frac` | 笔宽、轮廓平滑与渐细 |

建议先调 `writer_slant_deg`，再调 `jitter_rms`；结构与分段参数只做小幅修改。默认值定义在
`handwriting/style.py`，并可通过 `DEFAULT_HANDWRITING` 取得。

## Seed

`seed` 决定一次创建的随机身份。同一 API、参数和 seed 会得到同一形状；不传 seed 时生成新的
稳定随机值。动画不会逐帧改变笔迹。
