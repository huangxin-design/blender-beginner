# GitHub 发布资料

本页及作品源文件、提示词、精简对话都是仓库介绍资料，独立于 `skills/blender-beginner/` 内的 Skill 功能。

## 仓库名称与 About

建议仓库名：`blender-beginner`。

中文简介：

> 面向新手的 Codex × Blender Skill：环境准备、设备与参考图评估、自然语言制作、局部修改，附 .blend 源文件与制作过程档案。

英文简介：

> A beginner-friendly Codex skill for Blender: setup, reference and device assessment, scene creation and revisions, with .blend sources and production records.

可选 Topics：`blender`、`codex`、`agent-skills`、`python`、`bpy`、`3d-modeling`、`beginner-friendly`。

## 发布说明文案

标题：**v05 · 项目用量与渲染进度 / Early Preview**

> Blender 开工助手把新手的参考图和日常描述整理成可以执行的制作需求，并按请求准备环境、评估设备、生成或修改可编辑工程。
>
> v05 加入项目已记录 Token：从明确来源建立基线，区分待结算与未覆盖部分；加入本次渲染的本地进度页面，显示阶段、帧数及有依据的剩余时间范围。页面由本地程序更新，无需每秒调用模型。首版进度针对受控 PNG 输出，执行结束仍需验收。
>
> 仓库保留三个早期作品、绿色台灯两版 `.blend`、制作脚本、真实预览和精简过程资料；它们与 Skill 功能独立。
>
> 当前 Windows Blender 5.2.1 有实际验证；Mac 真机和复杂动画仍待验证。参考图分数是方案评估，不代表还原百分比。

## 项目介绍短文案

> 我在做一个给 Blender 新手使用的 Codex Skill。
>
> 你可以贴参考图，也可以直接说“磨砂一点”“背景虚一点”“灯罩太塑料”。它会按需帮你准备环境、判断制作难点，把描述转成具体操作，再通过真实预览调整。
>
> 我也会在 GitHub 单独整理作品资料，分享 `.blend`、提示词和精简制作过程，让大家能下载、学习提问方式，并接着修改。首批包含粉色装置、毛绒兔骑士、悬浮几何动画三个早期实践，以及绿色台灯修改示例；这些展示资料独立于 Skill 功能。

## 使用这些文件

1. 解压发布包，使用本地 Git（也可通过 GitHub Desktop）上传包内仓库文件，让 `README.md` 位于仓库根目录，保留 `docs/`、`skills/`、`projects/` 和 `templates/` 的相对位置。不要把整个交付 ZIP 当作仓库内文件提交。
2. 首页使用现成的中英文 README；在仓库 About 填写上面的简介和 Topics。
3. 在 Settings → Social preview 选择 [social-preview.png](assets/social-preview.png)。[GitHub 图片要求](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview)为小于 1 MB，推荐 1280×640；本图已按该规格制作。
4. 每次新增作品或修改版本，按 [归档指引](project-archive.md) 保留实际源文件，填写 [版本说明](../templates/version-brief.md) 与 [精简对话](../templates/conversation.md)，再更新作品索引。对话整理方法见 [说明](conversation-archive.md)。
5. 如需创建 Release，可使用上面的标题与说明，并附实际需要的完整工程包。发布后从读者入口下载一次确认能打开。

本资料包没有代选许可证或创建远端仓库。仓库名称、About、Topics 和发布说明均是可直接采用的草稿；文件准备完成不代表已经上传。

## 加入三个早期作品后的文件大小

兔骑士的核心底稿约 30.94 MiB，历史初版约 27.32 MiB，均超过网页单文件 25 MiB 的限制，需要通过本地 Git 上传。其余源文件也随目录一起提交即可；当前没有超过普通 Git 100 MiB 限制的单文件。整个交付 ZIP 用于本地搬移，解压后再提交目录内容。[GitHub 上传限制](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)

作品页保留参考原作者与素材说明。两张静图明确区分精修终图与三维底稿；动画说明包含参考音轨来源范围；六轮提示词标为优化重写稿。三个早期作品是展示资料，不增加 Skill 的验证数量。本地 Token 账本、原始 JSONL 和运行进度文件不默认上传。
