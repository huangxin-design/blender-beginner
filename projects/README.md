# 作品资料

这里收录作者的早期 Blender 实践和后续演示：成品、可编辑源文件、提示词与精简制作过程。它们是 GitHub 展示资料，独立于 Skill；安装 Skill 只需要 `skills/blender-beginner/`。

## 最早的三个作品

按作者提供的 2026-09-06 资料包顺序展示，不推定三件作品的准确开工日期。这些实践早于当前 Skill 框架整理，不作为 v04 的效果验证。

![三个早期作品：粉色装置、毛绒兔骑士、悬浮几何动画](../docs/assets/early-works.jpg)

| 作品 | 成品与源文件 | 制作过程 |
| --- | --- | --- |
| [粉色装置](pink-installation/README.md) | [精修 PNG](pink-installation/preview.png) · [三维底稿](pink-installation/source/editable-base.blend) | [过程摘要](pink-installation/conversation.md) · [优化提示词](pink-installation/prompts.md) |
| [毛绒兔骑士](plush-rabbit-knight/README.md) | [精修 PNG](plush-rabbit-knight/preview.png) · [三维底稿](plush-rabbit-knight/source/editable-base.blend) | [过程摘要](plush-rabbit-knight/conversation.md) · [优化提示词](plush-rabbit-knight/prompts.md) |
| [悬浮几何动画](floating-geometry-animation/README.md) | [30 秒 MP4](floating-geometry-animation/final.mp4) · [完整动画工程](floating-geometry-animation/source/scene.blend) | [过程摘要](floating-geometry-animation/conversation.md) · [优化提示词](floating-geometry-animation/prompts.md) |

两张静图的最后一步是生成式图像精修，新增效果未写回 `.blend`；各作品同时保留原生渲染和 EXR。动画为原生 Blender 渲染。六轮提示词来自随包的优化重写稿，过程摘要依据制作记录整理，两者都不冒充原始聊天。

原参考作者及制作贡献分别见 [粉色装置出处](pink-installation/credits.md)、[兔骑士出处](plush-rabbit-knight/credits.md)、[动画出处](floating-geometry-animation/credits.md)。

## 后续演示

[绿色台灯 · v001 / v002](green-desk-lamp/README.md)：展示读取已有工程、隔离共享材质、局部修改、保存与预览检查。

## 源文件与检查

三份核心工程沿用原文件字节，导入时重新打开检查，结果见 [本次源文件检查](early-works-source-check.md)。历史初版、五套独立动画场景与制作脚本保留在 [重建支持资料](_early-work-support/README.md)。[导入清单](early-works-manifest.json) 记录附件内相对来源及文件 SHA256。

下载工程时，在 GitHub 文件页选择 **Download raw file**，或下载并解压整个仓库。继续编辑优先打开各作品页面链接的核心 `.blend`；历史脚本的适用范围见重建支持说明。
