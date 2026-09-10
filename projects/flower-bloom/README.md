# 把开花的几秒钟，留在薄雾里

https://github.com/user-attachments/assets/3afd119c-94a4-4a06-8d26-1b859ca1b54d

> 按参考做一段花穗逐层绽放的动画：珊瑚红和浅桃色的花瓣沿细茎慢慢展开，像一股向上流动的开花波。主花穗清楚，后面的植物虚化，开头有轻轻聚焦的感觉，周围留一点薄雾。背景用暖棕色，右下角加半透明 HUANGHUAYU 水印。输出 8 秒、30 fps 的竖版 4K 视频，并保留可以继续修改的 Blender 工程。

这是根据实际需求和制作记录整理的示例提示词，不是历史原话。[查看分轮提示词](prompts.md)

**Token 用量：** 相关制作任务已记录 **24,574,578 Tokens**，包含主任务与 3 个子任务；读取时间为 2026-09-09 19:20:44（北京时间）。这是跨版本制作累计，不是 v006 或单张图片的独立成本。[统计口径](../../docs/showcase-measurements.md)<br>
**显卡渲染时间：** 最终续跑 238 帧用 **50 分 1.1 秒**；另复用两张已确认的 4K 样张，两帧合计 29.24 秒。全部 240 帧的已记录渲染段累计约 **50 分 30 秒**，不含建模、修改和视频编码。<br>
**设备与规格：** 制作档案记录 RTX 4070 Ti 12 GB；Blender 5.2.1、Cycles / OptiX、64 samples，原生 **2160 × 3840、30 fps、8 秒**。这次渲染批次的日志没有单独列出显卡型号。

[播放动画](https://github.com/user-attachments/assets/3afd119c-94a4-4a06-8d26-1b859ca1b54d) · [下载 4K 成片](https://github.com/huangxin-design/blender-beginner/releases/download/works-2026-09-09/huanghuayu-flower-4k.mp4) · [下载 4K 海报](https://github.com/huangxin-design/blender-beginner/releases/download/works-2026-09-09/huanghuayu-flower-poster-4k.png) · [下载源工程](source/scene.blend)

## 从“粒子效果”，到一株会开花的植物

这次的“粒子感”来自花朵沿茎分布，再逐层展开。工程用 156 朵花实例和 54 层原生形态键控制开合，既能改花簇宽度、间距和移动速度，也能保留每一层花瓣的真实形状。

早期 v003 已完成 720p 动画和原生开花控制。后续在已有工程上升级 4K：拉开前后植物距离，加入开头约一秒的轻微聚焦，调整体积雾和远处柔光，再把 HUANGHUAYU 署名放进背景空白处。保留原花瓣几何与开花节奏，画面从三维场景直接渲染，没有把旧版视频放大。

薄雾也改过几轮：较早的 4K 小样雾太浓、有颗粒感，最终版本降低了干扰，让主花穗清楚、后穗柔和退远。这里展示的是 **v006 最终交付版**。上方图片对应最终第 155 帧的缩小预览，全部视觉效果都保留在 `.blend` 中。

## 下载后，还能接着改什么

打开 [source/scene.blend](source/scene.blend)，可以在 `Bloom Controls` 调整开花进度和花簇间距，在相机里调整景深，在 `Mist` 的体积材质里改变薄雾浓度，也可以编辑水印文字。场景使用 Blender 内置字体，没有外部贴图、音频或模拟缓存。

[source/README.md](source/README.md) 说明两个原始脚本怎样重新渲染与编码，以及它们对 NVIDIA OptiX、FFmpeg 和 Python 库的要求。脚本覆盖最终出图步骤；保存的工程是实际场景来源。发布的 MP4 **没有音轨**，它是一次向上开花的过程，未设计为首尾无缝循环。

本次归档在新位置关闭自动执行、独立重开工程，检查分辨率、时间轴、景深、水印与原生驱动。已有交付记录覆盖两版视频各自原生分辨率的 240 帧软硬解码对比，并分别在 QQ 影音实际播放。播放器检查采用适应窗口显示，未验证其他播放器、设备或 Mac；本次归档没有再次渲染或重新编码。详情见 [验证记录](verification.json)。

[制作回顾](conversation.md) · [提示词](prompts.md) · [出处与署名](credits.md) · [文件与 SHA256](manifest.json) · [1080p 备用下载](preview.mp4) · [全部作品](../README.md)
