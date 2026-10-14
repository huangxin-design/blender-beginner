# 机械花 · 可编辑 Blender 工程

请先[下载完整工程包](https://github.com/huangxin-design/blender-beginner/releases/download/works-mechanical-flower-2026-10-14/mechanical-flower-project.zip)，解压后进入 `mechanical-flower/source/`。仓库此目录提供操作说明和脚本；实际 `.blend`、贴图及音频保存在该 Release 工程包内。

`scene.blend` 包含最终模型、动画、材质、相机与灯光，9 张贴图和最新科幻混音已经打包。所有资源地址为相对路径，外部素材仍保留在 `assets/`，便于修改。

- 原生输出：3072 × 4096，竖版 3:4，24 fps，1–393 帧（16.375 秒）。
- 制作与验收版本：Blender 5.2.1 LTS。建议使用同版本或兼容版本。
- `assets/audio/Mix_SciFi.wav` 是当前正式混音，3 个独立分轨同目录。
- 此音效由本地脚本制作，没有调用 ElevenLabs。

## 重新渲染

以下命令在本目录运行。把 `blender` 替换为自己电脑的 Blender 可执行文件，或加入 PATH。

```sh
blender -b scene.blend --python-exit-code 1 --python scripts/render.py
```

原生 PNG 帧保存在 `renders/`。脚本默认使用可用的 NVIDIA OptiX；否则使用 CPU 与 Open Image Denoise。可添加 `-- --cpu` 强制 CPU，其他显卡也可以在 Blender 界面中自行选择相应 Cycles 后端。再次运行会跳过同尺寸、完整的 PNG。

快速查看一帧：

```sh
blender -b scene.blend --python-exit-code 1 --python scripts/render.py -- --frame 301 --percentage 25 --samples 8
```

缩小预览保存在 `preview_renders/`，不会混入原生帧序列。修改模型、材质、灯光、动画或采样设置后，请先移走已有的 `renders/` 或 `preview_renders/` 文件夹，再重新运行；否则脚本会跳过已有同尺寸帧，继续沿用旧画面。渲染脚本不覆盖源 `.blend`。

## 合成视频

需要 Python 3，以及 PATH 中带 `libvpx-vp9`、`libx265`、`libopus`、AAC 支持的 FFmpeg / ffprobe（本次使用 FFmpeg 9.0.1）。编码脚本仅使用 Python 标准库。

```sh
python scripts/encode.py --codec vp9
python scripts/encode.py --codec hevc
```

脚本读取 `renders/0001.png` 至 `0393.png` 与正式科幻混音，视频输出到 `exports/`。VP9 为 WebM，HEVC Main10 为 MP4。Blender 的音效轨用于编辑和播放；最终音视频合成由 FFmpeg 完成。两种编码的原始正式交付已通过本机全片软件／D3D11VA 解码像素一致性检查；不同设备的解码支持可能不同。

## 再生成科幻音效

`scripts/generate_scifi_audio.py` 使用 NumPy 和 FFmpeg，把 `assets/audio/sources/` 中保留的四个原始输入分轨与程序生成的磁悬浮、伺服、充能等声层合成。

```sh
python scripts/generate_scifi_audio.py
```

需要安装 NumPy，或使用 Blender 自带的 Python。输出写入 `generated_audio/`，保留当前正式混音。经本机实际重跑，生成的混音与三分轨均与正式 WAV 字节一致：48 kHz、立体声、786000 样本、16.375 秒；混音 −23.0 LUFS、真峰值 −3.9 dBFS。重新生成后如要用于编码，请自行将选定混音替换到 `assets/audio/Mix_SciFi.wav`，并在 Blender 中同步替换、重新打包声音。

本包提供最终可编辑场景、渲染和编码脚本，以及从保留输入重建科幻音效的脚本。历史建模迭代脚本没有纳入，不宣称可从空场景一键重建所有模型；发光翼纹艺术图也以最终资产形式保留。
