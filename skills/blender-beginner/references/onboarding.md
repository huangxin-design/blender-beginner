# 环境准备：先让新手能够开工

用户希望安装、设置 Blender、指定 D/E 盘工作位置时读取本文件。普通看图评估或术语翻译不需要先安装软件。本技能第一版自动安装器支持 Windows x64、Blender 5.2 系列便携版；其他系统或版本先检查官方安装方法，不使用这个 Windows 脚本。

## 1. 先检测，再决定是否安装

读取用户已给出的路径和项目安装记录；检查已有可执行文件、实际版本、操作系统架构、目标盘是否存在与剩余空间。读取 GPU 情况；涉及 4K、动画或卡顿时按 [设备适配评估](device-assessment.md) 做有限时的试渲染。检测不包含全盘存储扫描。

已有可用 Blender 默认复用。用户要新建隔离环境时另选空目录；不迁移或覆盖旧安装。目录沿用用户选择，例如 `D:\Blender` 或 `E:\CreativeTools\Blender`。未指定且确实要安装时，提出一个存在且有空间的候选位置，集中询问一次关键路径选择；“用户举 D 盘为例”不等于授权迁移其现有软件。

## 2. 核验版本与来源

安装前查 [官方 LTS 页面](https://www.blender.org/download/lts/)，读取具体版本和对应的 [官方下载目录](https://download.blender.org/release/)。优先适配已经验证的稳定/LTS 分支。不要把研究日期时的最新版本永久写成“最新版”。本次开发验证为 5.2.1。

新手看见的准备卡应包含：实际安装位置、版本、下载来源、约需空间、项目/渲染/临时文件位置、是否沿用已有安装。已有明确安装授权后直接完成，不重复询问；仅做需求讨论时产出准备卡，不开始下载数百 MB 的软件。

## 3. 执行便携安装与配置

[安装脚本](../scripts/install_blender_windows.ps1) 由 Codex 在 PowerShell 调用。`$skillRoot` 是本技能目录的绝对路径；`$targetRoot` 是已选定的安装根目录；`$version` 是本次核验的版本号。

```powershell
& "$skillRoot/scripts/install_blender_windows.ps1" -InstallRoot $targetRoot -Version $version -PlanOnly
& "$skillRoot/scripts/install_blender_windows.ps1" -InstallRoot $targetRoot -Version $version
```

`-PlanOnly` 只输出路径与来源，不写入或下载；真正执行要求目标目录不存在或为空。脚本从官方源下载 ZIP 和校验文件，匹配完整包名校验 SHA256 后才解压；核对 ZIP 路径不会越出目标目录，随后创建独立 `portable` 配置。

已有官方下载包时，可以传 `-ArchivePath` 和 `-ChecksumPath` 复用。校验文件必须先有官方来源依据；不要把来源不明的 ZIP 和同样来源不明的摘要搭配起来就视为可信。首次用户安装不必让新手手工寻找校验文件。

下载失败保留日志与已下载文件并说明原因，不静默改用来源不明的下载站。脚本不会覆盖非空目录；若执行中断，应先查失败阶段，按该阶段修复或选新目录，不一遍遍盲目重跑。完整重复安装不属于恢复策略。

配置脚本只在新安装的 `portable` 目录内保存用户偏好和启动文件：

| 设置 | 初始值或规则 |
| --- | --- |
| 界面与提示 | 简体中文；新对象与数据名保持英文，便于后续脚本访问 |
| 自动保存与备份 | 2 分钟自动保存，保留 2 个保存备份 |
| 单位与输出 | 公制，1920 × 1080，30 fps；场景制作时按需求改 |
| 渲染 | Cycles、降噪；探测 GPU 并实际小图渲染，普通失败时改用 CPU |
| 场景起点 | `projects/start.blend`，含默认物体、相机与灯光 |
| 工作文件 | 根目录内 `projects`、`renders`、`temp`、`verification` |

GPU 驱动导致进程直接崩溃时，进程内的异常处理不能兜底；检查退出码和日志，必要时用明确的 CPU 配置流程恢复。不要因为枚举到了设备就宣称 GPU 可用。

## 4. 独立复核与交付

配置完成后，读 `installation.json` 与 `verification/setup.json`，查看 `verification/setup-preview.png`。再次启动该便携副本，检查中文偏好、自动保存、路径和渲染设备是否读回，并重新打开 `projects/start.blend`。`--factory-startup` 会跳过保存的启动文件，复核启动场景时不加它。

环境设置成功需要四项证据：可执行文件启动成功、偏好与启动文件路径在指定根内、保存设置在新进程中读回、真正渲染出图。只有静态检查时如实标明。

这里的 320 × 240 小图是安装连通性检查，不是 4K 或动画性能证明；不能据此给设备贴上“支持任何高清渲染”的标签。

给用户“从哪里打开软件、工程放在哪里、怎样继续贴参考图”三条提示即可。不要要求用户理解脚本、MCP 或节点接口。用户需要桌面快捷方式时再创建；保留默认文件关联与全局 PATH。

## 官方依据与范围

- [Windows 安装](https://docs.blender.org/manual/en/latest/getting_started/installing/windows.html)
- [便携版目录结构](https://docs.blender.org/manual/en/latest/advanced/blender_directory_layout.html)：当前版本的 Windows `portable` 位于可执行文件同级。
- “放在 D 盘”指本次安装、项目和可控制的工作路径；不能承诺操作系统或显卡驱动绝不在其他盘生成缓存。
