# 本次归档说明

## 任务与输入

将制作会话中的机械花项目整理到 GitHub，保留真实预览、可编辑工程、关键反馈和制作边界。相关需求见 [精简对话](conversation.md) 第 1–8 节。

本次输入是已有项目：v4 材质场景、v5 原生 4K 渲染结果，以及 v6 播放修复与科幻混音。发布工程以 v4 保存的 `.blend` 为场景基础，搭配 v6 音频和移植后的相对路径脚本。这里没有重新声称完成一套从零建模脚本。

## 相对早期版本的变化

- 白膜阶段先确定动作，再加入金属机械细节、磨砂玻璃翅膀与发光翼纹。
- 固定为竖版 3:4，保留飞行、停靠、开花、充能和离场的动作关系。
- v5 输出原生 4K 帧；v6 直接从这些帧重新编码，解决本机旧 H.264 硬解花屏问题。
- 科幻混音增强玻璃气流、磁性驱动和能量释放，按停靠与起飞动作编排音效。

早期白膜、v2、v3 和声音候选没有在本次逐版公开。当前目录是最终交付的配套归档，不是完整制作历史的镜像。

## 环境与输出

| 项目 | 实际记录 |
| --- | --- |
| Blender | 5.2.1 |
| 渲染 | Cycles；原生 3072 × 4096；64 采样；自适应阈值 0.02，最少 24 采样 |
| 动画 | 1–393 帧；24 fps；16.375 秒 |
| 最终视频 | VP9 + Opus / HEVC Main10 + AAC |
| 声音 | 48 kHz 立体声；本地生成与混音；约 −23 LUFS，真峰值 −3.9 dBFS |

## 工程与复现范围

下载 [mechanical-flower-project.zip](https://github.com/huangxin-design/blender-beginner/releases/download/works-mechanical-flower-2026-10-14/mechanical-flower-project.zip)，按 [source/README.md](source/README.md) 打开 `source/scene.blend`。工程包保留 `source/assets/textures/`、`source/assets/audio/` 和脚本；仓库只保留源目录说明与脚本，不用占位文件假装提供 `.blend`。

`render.py` 对保存的场景重新渲染，`encode.py` 将完整帧序列与科幻混音编码成视频，`generate_scifi_audio.py` 根据保留的声音输入重新生成混音。不同设备、驱动、Blender 或编码器版本可能影响结果，不承诺二进制文件或渲染像素完全相同。输入声音并不是从零合成整条历史音效链的替代品。

完整原始帧序列未随包公开。文件名和 SHA256 以 [SHA256SUMS.txt](https://github.com/huangxin-design/blender-beginner/releases/download/works-mechanical-flower-2026-10-14/SHA256SUMS.txt) 为准。

## 验证与已知边界

旧版花屏定位到本机 D3D11VA 解码路径；原图与软件解码正常。新 VP9 与 HEVC 在同一像素格式下各有 393/393 帧的软件／严格硬件解码哈希一致，证据见 [历史解码对照](qa/full-decode-comparison.json)。此次搬移、工程依赖和发布文件检查的实际范围见 [verification.json](verification.json)。

此前应用内浏览器的权限校验服务不可用，未完成该浏览器内的播放验收，不能将命令行解码结果写成全平台播放保证。WebM 因 Opus 包尾可显示 16.383 秒；实际音频为 786000 个立体声采样点，即 48 kHz 下的 16.375 秒。

ElevenLabs 未接入、未生成；只保留后续试验提示词。项目总耗时、全项目 Token 和总费用没有完整可核对记录，不填写估算成事实。外部参考及生成式贴图的边界见 [credits.md](credits.md)。
