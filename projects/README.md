# 看作品，也看看怎么做

这里收录作者的早期 Blender 实践和后续演示：成品、可编辑源文件、提示词与精简制作过程。它们是 GitHub 展示资料，独立于 Skill；安装 Skill 只需要 `skills/blender-beginner/`。

花卉与数字盆景为最新完成版，任务用量读取于 **2026-09-09 19:20（北京时间）**；AI 品牌与粉色波浪保留当天 16:59 的快照。覆盖范围见各案例与[统计说明](../docs/showcase-measurements.md)。

## 当 AI 有了触感

[![OpenAI 金属、Claude 木纹、DeepSeek 石材与 Gemini 磨砂玻璃材质球](ai-brand-materials/preview.jpg)](ai-brand-materials/README.md)

> 把这段解压动画里的小球换成四个 AI 品牌：OpenAI 做银色金属，Claude 做温暖木纹，DeepSeek 做浅色石材，Gemini 做磨砂玻璃。让标识真的凹进球面，小球滚过粉色柱阵时，柱子也跟着变色。再各拍一张单球海报，保留原生 Blender 工程。

**Token 用量：** 相关制作任务已记录 **40,779,249**（含主任务与 10 个子任务；未单独拆分到这四张图）。[统计范围](../docs/showcase-measurements.md)<br>
**显卡渲染时间：** 四张单球共 15.124 秒，含工程加载与图片保存；960 × 1280，Cycles / OptiX，128 samples。<br>
**显卡记录：** 制作设备档案为 RTX 4070 Ti 12 GB；这批渲染日志未单独写入显卡型号。<br>
**展示规格：** 四张单球图各为 960 × 1280；动画预览为 1080 × 1080、30 fps、20 秒。

[完整案例](ai-brand-materials/README.md) · [源文件](ai-brand-materials/source/scene.blend) · [动画](ai-brand-materials/preview.mp4) · [分轮提示词](ai-brand-materials/prompts.md) · [实测记录](../docs/showcase-measurements.md) · [出处](ai-brand-materials/credits.md)

这组图片来自原生 Blender 渲染。工程内的 200 帧动作循环重复三次，组成 20 秒视频；[检查记录](ai-brand-materials/verification.json) 保留了工程、静图与视频各自的验证范围。

## 粉色波浪 · 20 秒解压动画

https://github.com/user-attachments/assets/09e1b56e-4b11-4e15-ac81-7e638166a24d

**提示词 · 整理示例**

> 做一片粉色圆柱阵列，让金属和陶瓷小球轮流滚过，柱子跟着起伏成波浪。光线柔和、接触自然，输出方形 4K 循环动画，重复到 20 秒，保留可编辑工程。

**Token 用量：** 关联分叉任务已记录 **3,810,251**（含 1 个子任务；不包含继承的前期制作历史）。[统计范围](../docs/showcase-measurements.md)<br>
**显卡与历史渲染耗时：** RTX 4070 Ti / 12 GB，**58 分 7.7 秒**（3840 × 3840、64 采样、200 帧原生循环）。循环三遍合成 20 秒，播放器展示 1080 预览；计时不含建模与编码。

[案例与源工程](pink-wave-original/README.md) · [提示词](pink-wave-original/prompts.md) · [制作回顾](pink-wave-original/conversation.md) · [计时与验收](pink-wave-original/verification.json)

## 花卉粒子 · 把开花的几秒钟，留在薄雾里

https://github.com/user-attachments/assets/3afd119c-94a4-4a06-8d26-1b859ca1b54d

**提示词 · 整理示例**

> 让珊瑚红和浅桃色的花瓣沿细茎一层层展开，像一股向上流动的开花波。前面的花清楚，后面的植物虚一点，周围留一点薄雾。加上 HUANGHUAYU 水印，给我 8 秒竖屏 4K 动画和能继续修改的 Blender 工程。

**Token 用量：** 相关制作任务已记录 **24,574,578**（主任务 + 3 个子任务；跨版本累计）。读取于 **2026-09-09 19:20（北京时间）**。[统计范围](../docs/showcase-measurements.md)<br>
**显卡与实测渲染耗时：** 制作档案为 RTX 4070 Ti / 12 GB，全部 240 帧的渲染段累计约 **50 分 30 秒**（2160 × 3840、64 采样、Cycles / OptiX）。包含续跑 238 帧与复用的两张 4K 样张，不含建模、修改与编码；播放器展示 1080 预览。

[4K 最终版案例](flower-bloom/README.md) · [下载 4K 成片](https://github.com/huangxin-design/blender-beginner/releases/download/works-2026-09-09/huanghuayu-flower-4k.mp4) · [源工程](flower-bloom/source/scene.blend) · [提示词](flower-bloom/prompts.md) · [制作回顾](flower-bloom/conversation.md) · [计时与验收](flower-bloom/verification.json)

## 数字盆景 · 让一棵树长出数字花园

https://github.com/user-attachments/assets/39fd6bea-291f-4274-95b8-5e4cbbbeaf30

**提示词 · 整理示例**

> 让一棵树从石台上生长出来，叶片展开、花苞打开。数字和连线在生长阶段就出现，文字再清楚一点，花朵加上玫瑰粉和珊瑚红。保留横向切片转场和古典电子配乐，给我 7 秒竖屏动画与完整可编辑工程。

**Token 用量：** 相关制作任务已记录 **63,990,527**（主任务 + 6 个子任务；跨版本累计，不是第 7 版单独成本）。读取于 **2026-09-09 19:20（北京时间）**。[统计范围](../docs/showcase-measurements.md)<br>
**显卡与 v007 实测渲染耗时：** 同机设备记录为 RTX 4070 Ti / 12 GB，累计 **11 分 48.5 秒**（720 × 1280、48 采样、Cycles / OptiX，175 帧主镜头 + 20 帧转场近景）。三次渲染进程含启动、载入共 **12 分 3.7 秒**；建模、配乐与合成编码另计。

[第 7 版案例](tree-study/README.md) · [完整工程包](https://github.com/huangxin-design/blender-beginner/releases/download/works-2026-09-09/tree-study-v007-project.zip) · [提示词](tree-study/prompts.md) · [制作回顾](tree-study/conversation.md) · [计时与验收](tree-study/verification.json) · [保留的第 6 版](tree-study/versions/v006/README.md)

## 粉色装置

[![粉色玩具装置，经过图像精修的展示成品](pink-installation/preview.png)](pink-installation/README.md)

> 按参考图做一个粉色玩具装置：珊瑚粉褶柱、蓝色背板、薄荷珠和金白悬球，保留上下堆叠的趣味感。先给我看构图小样，再把陶瓷、金属和短绒做出不同的触感。保存可编辑的 Blender 工程；图片精修另存一份。

**Token 用量：** 未记录。<br>
**本机显卡实测：** RTX 4070 Ti / 12 GB，渲染 **5.95 秒**；含启动与载入共 **7.14 秒**。不含图片精修。[本次出图与记录](pink-installation/README.md)<br>
**底稿设置：** Cycles，1080 × 1048，128 samples。

[完整案例](pink-installation/README.md) · [源文件](pink-installation/source/editable-base.blend) · [分轮提示词](pink-installation/prompts.md) · [制作过程](pink-installation/conversation.md) · [出处](pink-installation/credits.md)

上图为生成式图像精修成品；新增效果未写回 `.blend`。同时保留了[原生渲染](pink-installation/native-render.png)与 [EXR 母版](pink-installation/source/beauty.exr)。

## 毛绒兔骑士

[![粉色毛绒兔骑士，经过图像精修的展示成品](plush-rabbit-knight/preview.png)](plush-rabbit-knight/README.md)

> 把参考图里的兔子做成一位毛绒小骑士：粉色绒毛、金色水晶剑、橙色木盾，站在树墩上，背后有三朵软软的云。毛发要蓬松，剑光轻轻照亮靠近它的脸和耳朵。先确认姿势，再细化材质，保留能继续修改的 Blender 工程。

**Token 用量：** 未记录。<br>
**本机显卡实测：** RTX 4070 Ti / 12 GB，渲染 **55.47 秒**；含启动与载入共 **57.52 秒**。不含图片精修。[本次出图与记录](plush-rabbit-knight/README.md)<br>
**底稿设置：** Cycles，1000 × 1000，1024 samples。

[完整案例](plush-rabbit-knight/README.md) · [源文件](plush-rabbit-knight/source/editable-base.blend) · [分轮提示词](plush-rabbit-knight/prompts.md) · [制作过程](plush-rabbit-knight/conversation.md) · [出处](plush-rabbit-knight/credits.md)

上图另做过生成式图像精修，最后的剑光与云朵效果未写回 `.blend`；可另看[原生渲染](plush-rabbit-knight/native-render.png)与 [EXR 母版](plush-rabbit-knight/source/beauty.exr)。

## 悬浮几何动画

[![悬浮几何动画，五种配色的预览](floating-geometry-animation/preview.jpg)](floating-geometry-animation/README.md)

> 让参考图里的几何玩具动起来：褶球慢慢转，空心管错开起伏，圆环和方框轻轻摇摆，镜头保持不动。做白底彩色、黑金、冰蓝虹彩、紫黄糖果和黑白五种配色，每种播放 6 秒，拼成 30 秒竖屏动画。先检查动作小样，再输出成片和可编辑工程。

**Token 用量：** 未记录。<br>
**显卡渲染时间：** 未记录；保留了 OptiX 设置，没有具体显卡型号与全片渲染耗时。<br>
**成片规格：** Cycles / OptiX，720 × 1280，64 samples；30 fps，900 帧，30 秒。

[完整案例](floating-geometry-animation/README.md) · [源文件](floating-geometry-animation/source/scene.blend) · [动画](floating-geometry-animation/final.mp4) · [分轮提示词](floating-geometry-animation/prompts.md) · [制作过程](floating-geometry-animation/conversation.md) · [出处](floating-geometry-animation/credits.md)

成片来自 Blender 原生动画渲染。每套配色内的动作可循环，整片首尾颜色不同；音轨来源与重建范围见作品页。

以上提示词均根据现有材料整理，方便复制尝试，不是历史聊天原话。后面三个作品按 2026-09-06 资料包顺序展示，不推定准确开工日期；所有案例都是已有作品的归档，不作为当前 Skill 一次生成的效果证明。未记录的用量与耗时保留为空缺，具体范围见[制作消耗说明](../docs/showcase-measurements.md)。

历史功能演示另见 [绿色台灯 · v001 / v002](green-desk-lamp/README.md)，演示已有工程的局部材质修改。

## 源文件与检查

三份核心工程沿用原文件字节，导入时重新打开检查，结果见 [本次源文件检查](early-works-source-check.md)。历史初版、五套独立动画场景与制作脚本保留在 [重建支持资料](_early-work-support/README.md)。[导入清单](early-works-manifest.json) 记录附件内相对来源及文件 SHA256。

下载工程时，在 GitHub 文件页选择 **Download raw file**，或下载并解压整个仓库。继续编辑优先打开各作品页面链接的核心 `.blend`；历史脚本的适用范围见重建支持说明。
