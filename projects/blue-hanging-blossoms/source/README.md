# V8 最终工程与重渲染

直接打开 [scene.blend](scene.blend)。时间轴 1–384，24 fps，七个镜头由时间轴标记绑定相机。三组远景与原有近景相机、焦点、形态键、几何节点和材质均可继续编辑。

实际环境为 Blender 5.2.1 LTS / Cycles / NVIDIA OptiX。脚本沿用本作出图设置，编码与检查使用 FFmpeg、FFprobe 和 Python 标准库；其他设备与操作系统未在本次归档中试渲染。

## 先看预览

在本目录执行，`blender` 需在命令搜索路径中：

```powershell
blender --background --disable-autoexec --python-exit-code 1 --python render_final.py -- preview
```

生成 `renders/preview/0360.png`，360 × 640、32 采样，不修改保存的工程。

## 完整 4K

```powershell
./render_all.ps1 -Blender blender -Python python
```

Blender 或 Python 没有加入搜索路径时，给上述参数传入各自的完整可执行文件路径。脚本每 12 帧重启渲染进程，跳过尺寸、位深和文件尾有效的现有 PNG，最后编码并检查 16 秒成片。

也可以只渲染一段：

```powershell
blender --background --disable-autoexec --python-exit-code 1 --python render_final.py -- render 1 12
```

全片序列生成后，单独编码：

```powershell
python encode_and_verify.py
```

完整渲染使用原生 2160 × 3840、最高 128 自适应采样、16 位 RGB PNG。输出位于 `source/renders/`，不覆盖仓库里的 1080 预览或 Release 下载件。

## 归档范围

源工程基于实际 V8 最终交付。发布副本仅更新内嵌使用说明、预览提示与相对输出路径，并清空文件浏览器目录；未修改视觉场景。渲染和编码入口是为公开目录整理的可移植版本，使用相对路径和可传入的程序路径。

本次保留最终 `.blend`，没有附从零创建全部早期版本的构建链；脚本负责从保存的工程重新出图。未随仓库打包约 8.9 GB 的 4K 帧序列、本机后台任务脚本或日志。

[场景重开检查](scene-check.json) · [回到作品](../README.md)
