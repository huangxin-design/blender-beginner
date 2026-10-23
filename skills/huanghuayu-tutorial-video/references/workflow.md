# 配置与运行

## 环境

需要 Python 3.10+、Pillow、可从命令行调用的 `ffmpeg` / `ffprobe`，以及已安装的中文字体。语音合成另外使用 edge-tts；离线排版与剪辑不需要联网。先检查现有环境，缺失的依赖按本机权限安装，不要为了读这个 skill 就自动安装 Blender 或启动界面。

所有以下 `SKILL_DIR` / `WORK_DIR` 都代表本次实际绝对路径。使用当前可用 Python，不依赖原作者机器的磁盘、用户名或环境变量。

## 从示例开始

将 `assets/example_project/` 完整复制到新的工作目录。示例是约 6 秒的功能演示，默认无声，字幕刻意压短以快速检查换字，不是正式教程的阅读节奏，也不能当作用户新作品。示例已带 `narration_parts`，正式合成后按实测配音长度自动延长镜头并重建字幕。`assets/approved-reference.png` 是已确认的完整频道风格参考；先看它，再看示例配置。

```text
python <SKILL_DIR>/scripts/render_tutorial.py --config <WORK_DIR>/lesson.json --output <WORK_DIR>/preview --prepare-only
```

查看生成的样帧。替换素材与文案后，正式有声制作先按 [语音说明](voice.md) 生成 `lesson.voiced.json`，再运行：

```text
python <SKILL_DIR>/scripts/render_tutorial.py --config <WORK_DIR>/lesson.voiced.json --output <WORK_DIR>/render_v1
```

已有人声配音时可直接配置 `audio_file` 和对应字幕时间，不必重新合成。离线验证可以直接渲染示例的 `lesson.json`。脚本从任何工作目录运行，媒体、音频和明确指定的字体路径都**相对配置文件所在目录**解析；不要把模板安装位置误作用户素材根目录。

## 配置字段

`lesson.json` 为普通 UTF-8 JSON。以附带示例为完整可执行参考，仅替换本次需要的字段。

| 字段 | 含义 |
|---|---|
| `brand`, `brand_tag`, `footer` | 频道名称、英文标签、底部说明 |
| `chapters` | 必填 1–3 项导航数组，元素为 `{code,label}`；示例为对话、工程、资料 |
| `fonts` | 可选 `{title,regular,bold,mono}` 字体文件路径，省略则查找本机字体 |
| `video.fps` | 默认 30；基础版式为 1080 × 1440。转场按 fps 缩放并整帧取整，保持约 0.267/0.4 秒的普通/章节节奏 |
| `video.tail_seconds` | 配音后的镜尾停留，默认 0.35 秒 |
| `shots` | 按顺序排列的镜头数组 |

每个镜头：

| 字段 | 含义 |
|---|---|
| `id`, `title`, `chapter` | 唯一镜头编号、大标题、从 0 开始的章节索引 |
| `layout` | `single` 单图、`split` 双图、`grid` 四图、`card` 图文卡 |
| `kicker`, `note` | 主屏短说明和补充文字 |
| `media` | 素材数组，元素包括 `file`、可选 `label`、`fit`、`crop`、`start_seconds` |
| `card` | 图文卡的 `{eyebrow,lines,note}`；用于资料信息或片尾寄语 |
| `audio_file` | 此镜配音，可选；默认离线示例没有人声 |
| `duration_seconds` | 镜头基础时长，应至少容纳净音频；脚本追加尾停顿并整帧取整 |
| `subtitle_events` | 字幕段数组，每段 `{start,end,lines}`，时间相对本镜起点 |
| `narration_parts` | 语音脚本的逐句输入；详情见语音说明 |

`single`、`split`、`grid` 的素材数量分别为 1、2、4；`card` 可有 0 或 1 张素材。`fit: "contain"` 保留完整前景，背景使用同图模糊铺满；视频使用取用首帧的静态模糊背景，前景继续播放。`cover` 填满素材框，可能裁掉边缘。`crop:[左,上,右,下]` 是源素材像素坐标，用于放大 Blender 节点、参数或局部细节。视频的 `start_seconds` 是取用起点；素材较短时保持末帧，不为凑时长反复跳回片头。

一句字幕最多两行优先；可增加字幕段而不增加镜头。字幕 `end` 可记录净语音末尾，展示窗口会延长至下一段 `start`；最后一句保持到镜头末尾。每镜第一句从 0 开始，不能把静音间隔误写成无字幕区。语音合成脚本输出与播放器字幕应使用相同的时间轴。

## 内容如何替换

先从本次对话提取具体约束和修正过程，例如“用预览发现花蕊过早出现，然后调整显示时机”。再在真实工程中找到对应对象、动画或节点。不要为了凑两个章节而编造操作步骤，或照抄花朵案例的 13 个对象、360 个姿态、17 张贴图等项目事实。

用于其他软件或主题时可更改章节名称和技术内容，保持视觉即可。片尾仓库链接和“喜欢 Blender 的朋友”等文案也要与主题相符。

## 最终交付

保留当期 JSON、字幕、人声源文件、成片和所需图片/视频，另附运行命令。不要把整个 Python 环境、缓存、字体、凭据或原作者的大型 Blender 工程装进新的教程包。

先完成版式与内容检查，再测试完整解码、切点与字幕连续性。修改文案或全局样式后使用新输出目录，避免旧镜头缓存混入。不要把本机通过误写成 Windows、macOS、Linux 都已经实测。
