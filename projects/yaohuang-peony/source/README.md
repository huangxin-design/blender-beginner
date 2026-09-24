# v007 最终工程与渲染

打开 [scene.blend](scene.blend)。工程停在第 1 帧，时间轴 1–240，24 fps，尺寸 2160 × 3840；花瓣形态键、材质、灯光、相机与合成效果均已保存。工程不依赖外部图片、链接库或音频。

本目录保留实际使用的 [render_final_4k.py](render_final_4k.py)，脚本字节未改。它只负责渲染保存的场景，不从零建立牡丹。最终工程为原文件复制并更名，未重新保存。

## 重新渲染

先把本目录复制到新的工作目录。实际制作使用 Blender 5.2.1 LTS、NVIDIA OptiX；`blender` 和 `ffmpeg` 需已安装并能在终端调用。在新目录运行：

```powershell
blender --background --disable-autoexec scene.blend --python-exit-code 1 --python render_final_4k.py
```

脚本输出 16 位 RGB PNG 到 `frames_4k/`，保留有效的已完成帧，可断点继续；`progress.json` 和 `frame_timings.jsonl` 记录本次渲染进度。若修改画面，应使用新的空输出目录，避免沿用旧帧。只想检查一张原生样帧，可在命令末尾加 `-- --check`，输出第 165 帧。

脚本会选择 OptiX、启用 GPU 降噪、512 像素分块，并让合成器在 CPU 上运行。没有 NVIDIA OptiX 时，请在 Blender 界面选择适合本机的设备后正常渲染动画；原脚本没有自动降级实现。

## 将新帧编码成视频

以下是归档时整理的可移植编码命令，使用与交付视频一致的尺寸、帧率和色彩标记；它没有在本次归档中重新执行完整序列编码：

```powershell
ffmpeg -framerate 24 -start_number 1 -i frames_4k/%04d.png -frames:v 240 -vf scale=out_color_matrix=bt709 -an -c:v libx264 -preset slow -crf 16 -profile:v high -level:v 5.1 -pix_fmt yuv420p -color_primaries bt709 -color_trc iec61966-2-1 -colorspace bt709 -movflags +faststart yaohuang-peony-4k.mp4
```

重新渲染和编码后的结果需要重新检查，已有校验记录只对应发布的原成片。历史本机启动器、打包脚本与完整 PNG 序列没有随公开资料发布；下载完整交付包可取得原视频和三张原生静帧。

[返回作品](../README.md) · [版本说明](../brief.md) · [验证记录](../verification.json)
