# V4 · 银蓝材质黑帧修正版

![银蓝花瓣盛开全貌](preview.jpg)

**[播放彩色成片](final.mp4) · [下载 Blender 工程](https://github.com/huangxin-design/blender-beginner/releases/download/works-silver-bloom-2026-10-19/Silver_Bloom_V4_3x4_Fixed.blend)**

任务：完成 15 秒银蓝花开动画，并修复用户指出的数秒黑画面。输入为已制作的 V4 波浪花瓣工程；早期问题版未在本案例归档。

本次补渲第 281–299 帧及第 381–450 帧，共 89 帧；关闭持久渲染缓存、分批重启 Blender，并取消片尾曝光淡出。保留花瓣造型、半透明纹理、波浪和瓣缘轻颤、花枝细毛及四段镜头构图。

| 项目 | 实际设置 |
| --- | --- |
| 视频 | 原生 720 × 960，3:4，30 fps，450 帧，15 秒，无声 |
| 渲染 | Blender 5.2.1 LTS / Cycles，128 采样 |
| 保存工程默认值 | 1080 × 1440，256 采样，停在第 330 帧 |
| 贴图 | 4 张 2048² 底色、高度、法线、粗糙度贴图，已打包 |

Release 文件名为 `Silver_Bloom_V4_3x4_Fixed.blend`。下载后保存为本目录的 `scene.blend`；文件大小与 SHA256 见 [manifest.json](../../manifest.json)。工程本身无需运行外部脚本。`FLOWER · Bloom 主控制` 提供 `Bloom`、`Wave Amount`、`Flutter Amount`。

在案例根目录重渲染：

```sh
python scripts/render_batches.py --version v004
python scripts/encode.py --version v004
```

默认 CPU；支持 OptiX 的 NVIDIA 显卡可向渲染命令追加 `--device OPTIX`。脚本以每 10 帧一个新进程输出到 `output/v004/`，按已归档视频的 720 × 960、128 采样设置渲染，不改写工程或归档视频。环境与小样命令见 [案例说明](../../README.md)。

检查记录确认 450 张源图完整、视频为 450 帧 / 30 fps / 15 秒、完整解码通过且未检测到整帧黑场；原生工程审计确认几何、材质、动画和相机保留，贴图打包且无外部依赖。依据见 [verification.json](../../verification.json) 与 [qa](../../qa/)。本目录不提供原问题视频或完整早期建模链；参考来源见 [credits.md](../../credits.md)。
