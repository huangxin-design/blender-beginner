# 下载完整 v007 工程包

[Tree Study v007 完整工程包 · 约 353 MB](https://github.com/huangxin-design/blender-beginner/releases/download/works-2026-09-09/tree-study-v007-project.zip) · [大小、SHA256 与公开整理变更](../manifest.json) · [v006 历史下载](../versions/v006/README.md)

工程含外部图像序列，请下载完整压缩包再解压打开。

| 文件 | 用途 |
| --- | --- |
| Tree_Study_Final.blend | 三维场景与完整剪辑，默认显示第 165 帧；切换到 FILM EDIT 场景查看 18 条素材轨。 |
| Tree_Study_Render.blend | 主镜头三维源工程，动画第 1—175 帧。 |
| Tree_Study_Close.blend | 转场的近景工程，使用第 91—110 帧。 |
| frames/ | 主镜头的 175 张原生 PNG。 |
| transition_close/ | 近景的 20 张原生 PNG。 |
| bgm.wav | 原始立体声配乐；完整剪辑中也已打包音乐。 |
| textures/ | 树皮与混凝土贴图及来源记录；工程内六张纹理已打包。 |
| render-timings-complete.json | 从已有日志汇总的全部 175 + 20 帧计时及范围。 |

解压后保持这些文件在同一作品文件夹内。只改三维场景不会自动更新已渲染的剪辑图像；需要同步修改近景工程并输出新序列。打开工程不需要启用自动执行脚本。

render_film.py、finish_film.py 和 attach_edit.py 记录已有渲染、合成编码与剪辑步骤，部分步骤会写入同名输出；继续制作前建立新版本。原渲染脚本使用 NVIDIA OptiX，其他设备先调整设置。本次整理没有执行这些历史脚本。

原有 frames-timings.json 只剩后来补渲的开头 39 帧。完整计时记录从三个保留的渲染日志恢复，共 175 张主镜头和 20 张近景，渲染调用累计 708.507 秒，三次进程累计 723.692 秒。日志中的私人电脑路径已清理，测量值保持原样。

三份 .blend、195 张序列图、视频、配乐与贴图保持原字节。本次已从完整公开包的新解压目录独立后台重开 Final：18 条素材轨、195 张相对路径图片、BGM、六张打包纹理及打包字体齐全。外部纹理原路径没有随工程改写，打开时使用内嵌纹理；包内另保留六张贴图原件。源工程未保存，本次没有重读剪辑帧、重新渲染动画或编码视频；既有成片与工程验收另见 [检查记录](../verification.json)。

[回到作品](../README.md)
