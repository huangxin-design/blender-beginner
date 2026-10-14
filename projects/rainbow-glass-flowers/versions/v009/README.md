# 打开、渲染与检查 v009

优先直接打开 [scene.blend](scene.blend)。这是制作完成后的实际工程，贴图已内嵌，含 1–360 帧、四个相机镜头与原生景深。

下面命令在本目录执行，把 `blender` 替换为本机 Blender 程序。制作环境为 Blender 5.2.1 LTS；脚本中采用 NVIDIA OptiX 渲染。其他设备可在 Blender 中改选兼容设备或 CPU 后手动渲染，未做跨设备一致性验证。

```text
blender -b scene.blend --python-exit-code 1 --python scripts/render.py -- check 1 97 217 360
blender -b scene.blend --python-exit-code 1 --python scripts/render.py -- film
python scripts/encode.py
```

`film` 输出实际交付规格的 720×960、32 samples PNG 序列到 `renders/frames_final/`，默认跳过已经存在的帧。中断后先核验帧文件；如有损坏，使用 `repair` 指定帧号补渲，不要仅凭文件存在认定成功：

```text
blender -b scene.blend --python-exit-code 1 --python scripts/render.py -- repair 9 10 11
```

编码需要 Python 3.10+、FFmpeg 和 ffprobe，在本目录生成 `film-15s.mp4`，并核对全部 PNG 尺寸、360 帧、24 fps、15 秒、3:4 和全片解码。`still` 模式按 1080×1440、64 samples 渲染指定静帧；母版没有因为生成浏览视频而降为 720×960。

```text
blender -b scene.blend --python-exit-code 1 --python scripts/render.py -- still 1
blender -b --python-exit-code 1 --python scripts/audit_cross.py -- --source scene.blend --output renders/cross_audit.json --frames 1:360 --clearance
blender -b --python-exit-code 1 --python scripts/audit_petals.py
```

两份几何检查脚本只在内存中读取或标记网格，不保存源工程。`audit_petals.py` 使用 Blender 自带的 NumPy；它检查包含尖根的完整花瓣之间的相交，并将花心/花托连接区另行记录。

这些入口可以从保存的场景重新渲染和检查，不重新搭建模型或重做前八版。历史验证结果保存在作品根目录的 [qa](../../qa/)，当时检查的范围与现在重新运行的结果应分别记录。
