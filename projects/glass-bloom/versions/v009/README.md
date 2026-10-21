# V9 · 同表现的材质版

沿用 V8 已保存彩色工程的原始字节，渲染紫粉半透明材质。

![盛开阶段](bloom.jpg)

[15 秒预览](preview.mp4) · [完整工程 ZIP](https://github.com/huangxin-design/blender-beginner/releases/download/works-glass-bloom-2026-10-21/Glass_Bloom_4K_Project.zip) · [返回案例](../../README.md) · [制作对话](../../conversation.md)

源工程位于完整下载包内的 `glass-bloom/versions/v009/scene.blend`，并非 Git LFS 指针。其 SHA-256 为 `2c64fd43c7216231532f5ea4c4a13001f01711352a8b965d63cb03d49fbd1a16`。

制作环境：Blender 5.2.1 / Cycles / 64 samples；3072 × 4096 / 24 fps / 1–360 帧。预览是主片的缩小版。花瓣几何、花蕊节奏与镜头与另一版相同；灯光、色管和材质按白模 / 彩色用途分别设置。

修改花瓣可查看每个物体的绝对形态键；`FLOWER` 整体比例恒为 1，`STAMENS` 控制延后伸展。贴图 PNG 内嵌，编辑 `textures/` 外部 SVG / PNG 后，需要在 Blender 重新载入和打包。

复现命令与实际渲染流程见[案例说明](../../README.md#重新渲染)。脚本是现有工程的重渲染入口，不是从零创建花朵的建模脚本。早期 V1–V7 未随本次案例归档，实际迭代关系保留于对话摘要。原生画面没有生成式图像后期；已做和未做的检查见[验证范围](../../verification.json)。
