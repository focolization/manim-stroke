# 致谢、第三方 notices 与方法参考

本页区分三件事：直接使用或移植的第三方软件、当前实现借鉴的方法，以及尚未实现的研究方向。
这不是“算法名清单”；每个条目都对应本项目中的具体职责。

## 直接依赖与代码来源

### Hershey Fonts / HersheyFonts

英文字符的原始单线 stroke 数据来自 Hershey 字形系统（Dr. Allen V. Hershey）。本项目通过
[HersheyFonts](https://github.com/apshu/HersheyFonts) 的 `HersheyFonts` 类取得 glyph/stroke/point
数据；该库将每个 glyph 表示为 stroke 数组，正适合作为 pen-down 中心线。

- 软件：HersheyFonts，Copyright © 2020 apshu，MIT License。
- 在本项目中的用途：`handwriting/glyph.py` 的字形拓扑与点序来源。
- 本项目不声称创造 Hershey 字形，也不改变其默认 stroke 顺序。

### Manim Community

[Manim Community](https://www.manim.community/) 是 `marks/` 和 `animation.py` 所使用的矢量场景与
动画运行时。

- 软件：Manim Community，MIT License。
- 在本项目中的用途：`Polygon`、`VGroup`、`Animation`、`Succession` 等显示与时间线接口。

### perfect-freehand

`freehand/freehand.py` 是对 [perfect-freehand](https://github.com/steveruizok/perfect-freehand) 的
Python 移植，并在源文件中保留了来源说明。其原始 `getStroke` 过程先从输入点生成平滑中心线，再
生成包围路径的可填充 outline。

- 软件：perfect-freehand，Copyright © 2021 Stephen Ruiz Ltd，MIT License。
- 在本项目中的用途：中心线到可变宽度、端帽、转角与 pressure-aware 轮廓的几何构造。
- 这是直接移植/改写的来源，不应称为本项目原创算法。

完整第三方许可证文本位于 [`../LICENSES/`](../LICENSES)。发布包含该移植代码的发行包时，必须保留
相应 copyright notice 与 MIT license。

## 当前实现的方法来源

### Sigma-Lognormal 时间参数化

本项目采用对数正态速度剖面控制笔尖沿**既定 Hershey 中心线**的累计弧长进度。它受 Réjean
Plamondon 的快速运动运动学理论及 Lognormal Handwriter 工作启发：

1. Plamondon, R. *A Kinematic Theory of Rapid Human Movements. Part I: Movement Representation and Generation.* Biological Cybernetics, 72, 295–307, 1995. DOI: [10.1007/BF00202785](https://doi.org/10.1007/BF00202785).
2. Plamondon, R. *A Kinematic Theory of Rapid Human Movements. Part II: Movement Time and Control.* Biological Cybernetics, 72, 309–320, 1995. DOI: [10.1007/BF00202786](https://doi.org/10.1007/BF00202786).
3. Plamondon, R., O’Reilly, C., Rémi, C., & Duval, T. *The Lognormal Handwriter: Learning, Performing, and Declining.* Frontiers in Psychology, 4, 945, 2013. DOI: [10.3389/fpsyg.2013.00945](https://doi.org/10.3389/fpsyg.2013.00945).

当前实现仅是“基于 Sigma-Lognormal 理论的时间参数化”：`timing.py` 用 lognormal CDF 将归一时间
映射为路径进度，并对硬折角顺序组合多个脉冲。它**不是**完整的二维 Sigma-Lognormal 神经运动
模型，也不从真实轨迹拟合运动命令。

### 分层风格、倾斜与局部分段

Lin 与 Wan 提出的英语手写合成分层思路启发了本项目将字形、倾斜、局部变化、时间和描边分开：

4. Lin, Z., & Wan, L. *Style-Preserving English Handwriting Synthesis.* Pattern Recognition, 40(7), 2097–2109, 2007. DOI: [10.1016/j.patcog.2006.11.024](https://doi.org/10.1016/j.patcog.2006.11.024).

当前代码据此采用基线 shear、按高转角分段、逐段小旋转/缩放、以及字形/运动分层；具体的阈值、AR(1)
法线噪声、共享锚点 primitive 和 Manim 播放管线是本项目的参数化工程实现，并非逐行复现论文。

## 相关但尚未实现

Wang 等的工作将统计形状模型与 Delta-Lognormal 运动模型结合：

5. Wang, J., Wu, C., Xu, Y.-Q., & Shum, H.-Y. *Combining Shape and Physical Models for Online Cursive Handwriting Synthesis.* International Journal on Document Analysis and Recognition, 7, 219–227, 2005. DOI: [10.1007/s10032-004-0131-6](https://doi.org/10.1007/s10032-004-0131-6).

它是后续扩展的参考，但本项目**尚未**收集真实样本、建立点对应、训练 PCA 统计字形模型，亦未实现完整
Delta-Lognormal 或连笔连接优化。因此不得描述为“已实现 Wang et al. 的统计形状模型”。

## 本项目的工程组合

以下是本项目的设计组合，而非某一篇论文的直接复制：保留 Hershey 几何而只替换时间进度；以共享锚点构造
leg/bar、stem/bowl、single-curve 结构 primitive；以相关长度参数化 AR(1) 法线扰动；将笔顺、提笔、
弧长推进和逐帧实心轮廓增长接入 Manim。有关具体 API，见 [styles.md](styles.md)、
[handwriting.md](handwriting.md) 与 [geometry.md](geometry.md)。
