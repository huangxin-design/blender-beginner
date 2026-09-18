# V11 最终工程与复现

直接打开 [HuangHuaYu_Outline07_4K.blend](HuangHuaYu_Outline07_4K.blend)。打开时停在文字画面；时间轴 1–600，30 FPS。心脏、玫瑰、文字目标、材质与几何节点已保存，不需要重新安装字体。

## 完整渲染

实际环境：Blender 5.2.1 / Eevee / 32 samples；编码需要 FFmpeg，外部 Python 需要 NumPy、Pillow。以下命令在本目录运行，`blender`、`python`、`ffmpeg` 需可调用：

```powershell
blender --background --disable-autoexec --python-exit-code 1 --python render_v11.py -- all
python encode_v11.py
python verify_movie.py
```

`all` 从完整场景渲染 600 张原生 PNG。Blender 内部的简单表达式驱动用于动画，本次检查在关闭自动执行的情况下重开并验证了保存工程。`verify_movie.py` 要求 NVIDIA `h264_cuvid` 硬件解码器，以及编码所用的全部源 PNG；缺少条件时不能宣称完成相同验收。

视频检查会把播放器检查标为 pending，重新编码后需要重新实际播放。仓库中的已有验收记录对应原交付文件，不自动覆盖新渲染的成片。

## 重建文字修改

通常无需重建。若要查看 V11 怎样从 V8 改出来：

```powershell
python prepare_targets.py
blender --background --disable-autoexec --python-exit-code 1 --python build_v11.py
blender --background --disable-autoexec --python-exit-code 1 --python verify_source.py
```

输入包括 `source/Heart_Rose_V8.blend`、`source/07_mask.png` 与 `source/07_styled_mask.png`。采样结果保存在 `source/title_targets.npz`。这些已全部随工程保留；重建会覆盖本目录的最终工程与相关检查记录，建议先复制整个作品目录再试。

## 区域渲染与静帧复用

`render_region.py` 和 `assemble_regions.py` 是本次加速导出的历史实现：渲染 381–469 与 510–585 帧，其余使用已验证的前段帧、文字定帧与黑场。用于组装的原生第 490、600 帧位于 `stills/`。

**公开包没有前 380 张 PNG，也没有完整 600 张序列。** 首次下载请使用上面的 `render_v11.py -- all`，不要把区域渲染脚本误当作从空目录即可获得全片的入口。区域与全画幅的差异说明见 [经验总结](../lessons.md)。

`render_v11.py -- full` 仅渲染 381–600 帧；`-- native` 渲染代表原生样帧；无参数为低分辨率关键帧检查。`audit_prefix.py` 比较 V8 / V11 的已选状态，`verify_region.py` 比较随包保存的两张文字渲染。

## 包含与未包含

- 当前仓库包含最终 V11、V8 工程、相关制作脚本、选定字形遮罩、字体提案对比图和检查记录；V7 素材和早期基础工程已撤下。
- 4K MP4 单独提供下载；1080 预览位于作品目录 `preview.mp4`。
- 旧源资料 ZIP 已撤下，源文件请从当前仓库下载。没有打包全部 PNG 序列或字体文件。
- 历史 V8 重建脚本依赖未公开的早期基础工程和 Windows 标准字体，不能从当前公开目录完整重建 V8；直接打开 V8 或最终 `.blend` 无需重建这些字形。

[返回作品](../README.md) · [全部文件与 SHA256](../manifest.json)
