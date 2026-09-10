# 继续修改或重新输出

[scene.blend](scene.blend) 是 v006 最终保存的工程，归档时仅改了文件名，字节与原 `HUANGHUAYU_Flower_4K.blend` 相同。它包含花穗、原生开花控制、材质、景深、薄雾和水印，使用 Blender 5.2.1 制作。

打开工程后按数字键盘 **0** 看相机，在时间轴播放动画。`Bloom Controls` 的自定义属性控制开花，`Focus` 对象及相机控制景深，`Mist` 材质控制雾，文字对象保留可编辑的 HUANGHUAYU。没有外部贴图或缓存，关闭自动执行也能求值 216 条原生数学驱动。

## 两个脚本分别做什么

| 原始脚本 | 用途与条件 |
| --- | --- |
| [render_final.py](render_final.py) | 对当前打开的工程逐帧渲染，输出到脚本旁的 `frames/`。要求 2160×3840、1–240 帧、30 fps、64 samples；原脚本使用 NVIDIA OptiX。 |
| [encode_and_verify.py](encode_and_verify.py) | 读取完整的 240 张原生 PNG，编码 4K 与 1080p 视频，生成第 155 帧海报并做全片软硬解码对比。需要 Python 的 NumPy、Pillow，以及 PATH 中的 FFmpeg/ffprobe 和可用的 NVIDIA `h264_cuvid`。 |

两个脚本保持原字节，没有替换成通用跨平台工具。它们覆盖最后的渲染与编码，不是从空场景重建全部建模历史。其他设备可以打开工程，再由 Codex 根据实际设备设置渲染后端；Mac 与其他显卡未在本次归档中测试。

## 重新跑之前

把这个 `source` 文件夹复制到一个新的工作目录，再开始渲染。原渲染脚本会复用 `frames/` 中文件头、尺寸和结束标记通过检查的 PNG，**不会确认已有帧是否来自同一版材质、灯光或动画**。修改过工程后请使用新的输出目录，避免把两版帧混在一起；不要只靠相同文件名判断可以续跑。

让 Codex 用已安装的 Blender、关闭自动执行，在独立后台进程打开 `scene.blend` 并执行 `render_final.py`，设定明确的时间上限。先评估当前设备，再决定是否进行完整 4K 渲染。此原脚本不会保存修改后的工程或用户偏好。

240 张 PNG 完成后，再从这个新工作目录执行 `encode_and_verify.py`。它保留原输出名 `HUANGHUAYU_Flower_4K.mp4` 与 `HUANGHUAYU_Flower_Preview_1080.mp4`，发现同名 MP4 会拒绝覆盖。脚本的工具检查不能代替实际播放器检查；重新导出后需按新视频重新验收。

本次只在搬移后重开工程并核对依赖与动画控制，没有再次渲染、编码或修改原工程。[已有验证范围](../verification.json) · [SHA256](../manifest.json) · [成品下载](../README.md)
