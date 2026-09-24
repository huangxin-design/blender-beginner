# v5 · 三种材质的固定花心 4K 动画

本目录对应实际交付的 `v5_4k_trio`。三份 `.blend` 的原始字节保存在 GitHub Release 和完整工程 ZIP 中，未创建占位工程。文件大小及 SHA256 见[清单](../../manifest.json)。

| 材质 | 工程下载 | 4K 盛开静帧 |
| --- | --- | --- |
| 粉色半透金丝 | [01_Rose_Gold_4K.blend](https://github.com/huangxin-design/blender-beginner/releases/download/works-gold-silk-flower-2026-09-24/01_Rose_Gold_4K.blend) | [PNG](https://github.com/huangxin-design/blender-beginner/releases/download/works-gold-silk-flower-2026-09-24/01_Rose_Gold_4K_Hero.png) |
| 浅粉水晶金丝 | [02_Rose_Crystal_4K.blend](https://github.com/huangxin-design/blender-beginner/releases/download/works-gold-silk-flower-2026-09-24/02_Rose_Crystal_4K.blend) | [PNG](https://github.com/huangxin-design/blender-beginner/releases/download/works-gold-silk-flower-2026-09-24/02_Rose_Crystal_4K_Hero.png) |
| 白模布线 | [03_Clay_Wire_4K.blend](https://github.com/huangxin-design/blender-beginner/releases/download/works-gold-silk-flower-2026-09-24/03_Clay_Wire_4K.blend) | [PNG](https://github.com/huangxin-design/blender-beginner/releases/download/works-gold-silk-flower-2026-09-24/03_Clay_Wire_4K_Hero.png) |

## 打开与修改

优先下载[完整工程包](https://github.com/huangxin-design/blender-beginner/releases/download/works-gold-silk-flower-2026-09-24/Gold_Silk_Flower_4K_Project.zip)。解压后，本目录含三份工程、视频、4K 静帧与脚本。单独下载工程也可以直接在 Blender 5.2.1 中打开，无外部贴图依赖。

- 默认停在第 271 帧的盛开状态，时间轴为 1–300 帧。
- `FLOWER | fixed position, orientation and scale` 固定花朵整体位置、方向和缩放。
- `CENTER | locked flower heart` 为不参与渲染的花心辅助点；三片带 `Fixed inner core` 属性的内层花瓣保持静止。
- 其他 48 片花瓣通过形态键控制展开。材质节点、金丝发光与灯光可继续编辑。
- 白模花瓣与叶片为抽稀的 U/V 四边形网格显示；花茎、叶柄使用 Wireframe 修改器。

## 重新渲染

下面的脚本从已保存 `.blend` 渲染，不需要重新生成建模过程。把下载的三份工程放在本目录，与 `manifest.json` 同级。在本目录打开终端，使用本机 Blender 可执行文件运行：

```text
blender -b --disable-autoexec --python-exit-code 1 --python render_variant.py -- --variant crystal --mode preview
blender -b --disable-autoexec --python-exit-code 1 --python render_variant.py -- --variant crystal --mode movie
python encode_video.py --variant crystal
```

`crystal` 可换成 `rose` 或 `clay_wire`。渲染脚本沿用实际生产入口，默认 NVIDIA OptiX；其他硬件和操作系统未验证。编码脚本为公开归档整理版，使用相同的 H.264 / CRF 16 / 30 fps 参数，要求 Python 3.10+ 和 PATH 中的 FFmpeg / FFprobe。

渲染会跳过已有完整帧。修改材质或几何后，应使用新的输出目录，或用 `--force` 明确重渲染，避免混用旧帧。`--mode preview` 仅生成 414 × 736 关键帧预览；`--mode movie` 使用工程中的原生 2160 × 3840 设置。

编码前要求第 1–217 帧完整，依据已验证的静止盛开段补足后续 83 帧，得到 300 帧 / 10 秒视频。`encode_video.py` 会核对视频规格并完整软件解码；这不替代针对修改后文件重新执行的硬件解码与实际播放器检查。

## 文件与验证范围

- [render_variant.py](render_variant.py)：实际使用的原生渲染脚本。
- [verify_trio.py](verify_trio.py)：实际使用的三版动画、固定花心与规格检查。
- [Scene_Validation_4K.json](Scene_Validation_4K.json)：原交付场景验证记录。
- [encode_video.py](encode_video.py)：移除本机路径和发布打包步骤的归档编码入口。
- [build_trio.py](build_trio.py)：保留的历史材质组装脚本，依赖制作目录中的 `v3_luminous` 与 `v4_fixed_center`，这两个前序目录未随本次公开。它不构成独立从零重建入口；直接使用当前 `.blend` 可以编辑和渲染。

发布时保留原工程和视频字节；搬移后的工程检查、900 帧软硬解码对比与播放器检查边界见[验证记录](../../verification.json)。

[作品页](../../README.md) · [制作对话](../../conversation.md)
