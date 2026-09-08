# 第一次用 Blender 开工助手

目标是先做出一个能打开、能修改、有真实预览的 `.blend` 工程。当前验证环境是 **Windows x64 + Blender 5.2.1**；Mac 的设备评估流程已编写，Metal 与实际制作仍待真机验证。Windows 自动安装脚本不适用于 Mac。

## 1. 下载并安装 Skill

从本仓库的 **Code → Download ZIP** 下载并解压；也可以使用本地克隆。找到其中的 `skills/blender-beginner` 文件夹。

在 Codex 的本地项目中打开这个解压后的仓库，发送：

> 请把当前仓库的 skills/blender-beginner 完整安装到我的个人 Skill 目录 .agents/skills 中。先确认实际用户目录；复制整个文件夹，保留 scripts、references、assets 和 agents。如果已有同名 Skill，先比较版本并保留旧副本。完成后告诉我实际安装路径，并确认能读取这个 Skill。

也可以手动复制：

| 使用范围 | 放置位置 |
| --- | --- |
| 个人使用，适用于多个项目 | 用户主目录下的 `.agents/skills/blender-beginner/` |
| 只在一个项目使用 | 该项目根目录下的 `.agents/skills/blender-beginner/` |

Windows 的个人目录通常为 `C:\Users\你的用户名\.agents\skills\blender-beginner\`；Mac 为 `/Users/你的用户名/.agents/skills/blender-beginner/`。以实际用户主目录为准。最终应直接看到 `blender-beginner/SKILL.md`，不要多嵌套一层文件夹，也不要只复制这个文件。

Codex 会自动检测本地 Skill；若未出现，重启后再检查。以上发现路径依据 [OpenAI 官方 Skill 文档](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)，核验于 2026-09-07。

## 2. 确认生效，检查制作环境

发送：

> 请使用 blender-beginner，先告诉我你读取的 SKILL.md 路径，再检查这台电脑已有的 Blender 和辅助 Python 环境。现在只做检查，不下载软件、不开始渲染。

确认回复引用的是刚安装的 Skill，并说明找到的 Blender 实际版本。**安装 Skill 和安装 Blender 是两个步骤。** 已有可用 Blender 就直接复用；没有时，再告诉 Codex 允许安装的位置，例如“请把 Blender 安装到 D:\Blender，工程保存在 D:\BlenderProjects”。目录应存在于这台电脑，已有软件不要迁移或覆盖。

制作脚本使用 Blender 自带的 Python；设备检查和限时执行辅助程序需要另一个可用的 **Python 3.10+**。由 Codex 查找现有环境、说明缺项并协助准备，不需要新手自行安装 `bpy`。普通文件制作不要求安装 Blender MCP。

## 3. 完成第一个小项目

在你准备保存作品的本地项目中发送：

> 使用 blender-beginner，做一盏简约桌面台灯，绿色灯罩、金属灯杆、柔和灯光。先做普通尺寸预览，交付可编辑工程、生成脚本和真实预览；保存到独立的新版本目录。请重新打开工程检查，再告诉我文件在哪里。

完成后应得到三项主要文件：`scene.blend`、生成脚本和 `preview.png`。预览应来自保存后的 Blender 工程，并有重新打开的检查记录。脚本准备完成但 Blender 未实际运行时，还不能算工程制作成功。

接着可以说：

> 以刚才保存的工程为起点，只把灯罩改成橙色，底座、镜头和其他部件保持不变。另存新版本并给我看预览。

## 4. 开始自己的作品

贴参考图时，可以先说“只评估这张参考图，不开始制作”；需要高清输出时，补充用途、尺寸和可等待的时间。动画还需要时长、帧率与主要运动。评估分表示当前方案的可行程度，不能当作还原百分比。

4K 或动画需求会触发实际目标设备的评估。小图成功不能证明复杂 4K 动画可行；讨论另一台 Mac 时，需要那台 Mac 的设备信息或试渲染记录。

示例作品可从 [作品目录](../projects/README.md) 浏览下载。作品和对话的 GitHub 展示资料由作者另行整理，使用 Skill 无需完成这些步骤。

## 5. 可选：记录用量和查看渲染进度

需要时可以说：

> 从现在开始记录这个项目的 Token。使用本项目专用会话的明确来源，说明记录起点和未覆盖部分。不要补算没有记录的旧作品。

> 这次渲染给我一个本地进度页面，显示已用时间、已输出帧数，有依据再估计还要多久。不要改我的画面效果，输出放到新目录。

找不到当前会话的可靠用量来源时，Codex 会说明缺项；不会扫描所有历史聊天。进度首版对应它本次启动的受控 PNG 渲染，不接管已在 Blender 界面启动的任务。详见 [用量与进度](usage-progress.md)。

## 遇到问题

| 现象 | 直接告诉 Codex |
| --- | --- |
| Skill 没有生效 | 检查是否复制了完整目录、是否多套一层、是否存在同名版本；重启后确认实际读取路径 |
| 找不到 Blender 或 Python | 检查已有安装和实际版本，说明还缺什么，再准备环境 |
| 渲染超时、黑图或粉色贴图 | 读取本次日志并定位问题；保留成功版本，修复后重新出预览 |
| 我手动改过工程 | 提供最新保存文件的位置，让它从该文件继续 |

详细执行边界见 [执行与排错](../skills/blender-beginner/references/runtime.md)。
