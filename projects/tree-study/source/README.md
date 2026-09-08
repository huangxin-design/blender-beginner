# 请下载完整工程包

[Tree Study v006 完整工程包](https://github.com/huangxin-design/blender-beginner/releases/download/showcase-2026-09-08/tree-study-v006-project.zip) · [大小、SHA256 与公开整理变更](../manifest.json)

工程含外部图像序列，因此本目录不放一个缺少素材的 `.blend` 下载入口。

| 文件 | 用途 |
| --- | --- |
| Tree_Study_Final.blend | 三维场景与完整剪辑，默认显示第 165 帧；切换到 FILM EDIT 场景查看 18 条素材轨。 |
| Tree_Study_Render.blend | 主镜头三维源工程，动画第 1—175 帧。 |
| Tree_Study_Close.blend | 转场的近景工程，使用第 91—110 帧。 |
| frames/ | 主镜头的 175 张原生 PNG。 |
| transition_close/ | 近景的 20 张原生 PNG。 |
| bgm.wav | 原始立体声配乐；完整剪辑中也已打包音乐。 |
| textures/ | 树皮与混凝土贴图及来源记录。 |

解压后保持这些文件在同一作品文件夹内。只改三维场景不会自动更新已经渲染的剪辑图像；需要同步修改相应近景工程并输出新序列。

附带的 render_film.py、finish_film.py 和 attach_edit.py 记录已有的渲染、合成编码与剪辑步骤。它们使用作品目录中的相对素材，部分步骤会写入同名输出；继续制作前请让 Codex 建立新版本。原渲染脚本使用 NVIDIA OptiX，其他设备应先调整设置。脚本没有在本次归档中重新执行。

本次公开副本保持三份工程、195 张图片、视频与音频原字节，只清理三个报告和两份解码日志内的本机路径，并补充已有主镜头工程、脚本、计时数据和清单。原版验收与公开包检查分别记录。本次已安全解压公开包并用独立 Blender 进程重开：18 条素材轨、195 张相对路径图片、配乐及六张打包贴图齐全，剪辑第 100 帧重读后与原版逐像素一致。源工程未保存或改写；未重新渲染三维动画或编码视频。

[回到作品](../README.md)
