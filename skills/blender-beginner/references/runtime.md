# 执行与排错

需要生成、修改、检查文件时读取。命令由 Codex 执行，交付给用户时优先展示文件和结果。路径均应替换为本次实际发现的绝对路径。

## 找到运行环境

先读取项目已有的 Blender 安装说明或配置，再查 `Get-Command blender`（Windows）或 `command -v blender`（macOS/Linux）。最后才查看常见安装位置。运行可执行文件的 `--version`；不要仅凭文件夹名字判断版本。系统 Python 可用于文本处理，但场景脚本必须通过 Blender 的 `--python` 执行。

## 新建与复核

使用 [限时执行器](../scripts/run_blender.py) 执行已检查的生成或复核脚本。系统 Python 只负责启动进程，场景脚本仍在 Blender 中运行。先发现可用的 Python 3.10+；辅助运行环境不可用时说明这项依赖，不让用户在系统 Python 中安装 `bpy`。

下面是 PowerShell 示例。`$pythonExe`、`$runner`、`$blenderExe`、`$buildScript`、`$blendFile`、`$inspectScript`、`$reportFile`、`$previewFile` 及两个日志目录应先设为本次任务的绝对路径。每次日志目录必须全新。120 秒仅为小场景示例预算，由 Codex 按用户总预算和已有实测选择；正式渲染没有固定 300 秒上限。模板参数为 `--output`，改写脚本应保留或明确更新参数契约。

```powershell
& $pythonExe $runner --blender $blenderExe --script $buildScript --log-dir $buildLogDir --timeout 120 -- --output $blendFile
if ($LASTEXITCODE -ne 0) { throw '场景生成失败，请查看 Blender 日志。' }

& $pythonExe $runner --blender $blenderExe --blend $blendFile --script $inspectScript --log-dir $checkLogDir --timeout 120 -- --report $reportFile --preview $previewFile
if ($LASTEXITCODE -ne 0) { throw '重新打开或渲染检查失败，请查看检查报告和日志。' }
```

macOS/Linux 使用同样的执行器参数，以 `"$pythonExe" "$runner"` 调用并正确引用路径。脚本放在文件中，不把用户文字拼成 shell 代码。每一步读取返回值。执行器用参数列表启动独立后台进程，记录 `run.json` 和 `blender.log`；其中 `completed` 只表示进程成功，仍要核对预期文件、检查报告与实际画面。

超时或中断只结束本次启动的 Blender；记录失败后检查是否有完整的中间文件，重新打开验证后才作为续做起点。执行器不保证任意脚本派生的子进程被管理，也不限制任意脚本的文件访问；输出保护依赖所调用的已审查脚本，不能把它当作不可信文件沙箱。安装器内部的配置调用仍有自己的流程，本执行器不等于已经改造全部安装步骤。

执行器保持 Blender 参数顺序：启动选项在前，输入 `.blend` 在检查脚本之前，`--` 后是脚本参数。`--python-exit-code 1` 让异常成为命令失败；`--disable-autoexec` 关闭文件内自动脚本执行，不阻止显式脚本。依赖自定义 Python 驱动的工程应单独评估，不能承诺关闭自动执行后所有驱动仍有效。

模板只在全新输出路径保存工程，已有目标会报错。检查器的报告和预览也需新路径；复核可使用 `qa-02.json` 与 `preview-02.png`。初次生成和初次检查推荐 `scene.blend`、`qa.json`、`preview.png`。

检查器适用于已加载的普通静态场景，未做全量资产审计。其 JSON 中的范围、警告和 `errors` 必须一并阅读。渲染使用工程保存的相机、帧、引擎和分辨率，仅在检查进程中将输出设为 PNG，不写回 `.blend`。

只读工程前先看保存的渲染成本；昂贵设置可先只出结构报告（省略 `--preview`），再用保持目标画幅的限时小样。普通检查器与性能探测共用 [单图渲染保护](../scripts/render_guards.py)：检测到合成器 File Output、多视图或活动视频序列时拒绝预览。需要这些功能时先在新副本中安排受控输出并采用相应验收；不静默关闭它们后声称原效果验证通过。仅结构检查不等于渲染或视觉完成。

## 本次任务进度

需要显示本次执行进度时，在脚本参数分隔符 `--` 之前添加 `--progress`。日志目录中会生成 `progress.json` 和自动刷新的 `progress.html`；结束后页面停止刷新。使用 [受控帧输出与时间估计](render-progress.md) 可记录明确 PNG 帧计划；普通脚本没有可靠帧计划时不计算整段 ETA。可选 `--usage-report` 指向 [Token 工具](token-usage.md) 已生成的本地报告，显示它已有的数据；执行器不会读取会话或自动结算用量。更新该报告需在工作节点另行执行用量工具，不能把页面刷新当作新的用量结算。

面板写入失败会停止本轮页面更新，保留渲染及其超时保护，并在 `run.json` 记录 `progress_error`；已有页面过期后隐藏 ETA。结束时会再尝试保存最终状态。不要把未更新的旧面板当作实时进度，读取本次执行记录判断结果。

## 修改已有文件

先打开文件并列出对象、集合、材质、相机、帧范围和外部依赖，再创建针对性脚本。调用方式是在 `--python` 前加输入 `.blend`；脚本保存到新版本。不要调用新建模板中的场景清空逻辑。

通过执行器传 `--blend` 指定实际输入。用户已手动修改并保存时，以该最新版为起点；位置不明确只补问文件位置，不索取例行方案批准。保存修改脚本及其输入路径供复现，不用旧建模脚本重建来覆盖手动改动。任务与版本衔接见 [项目衔接与反馈](project-loop.md)。

复核修改前后需保留的结构；只改颜色时比较对象、网格数量、变换和相机，避免用重新生成的相似场景代替用户原文件。MCP 会话修改也应另存并重新打开检查。

局部改色时先检查材质被哪些对象共用。目标部件与需保留的部件共享材质时，复制材质后只赋给目标部件，避免连带改变其他对象。灯罩顶盖等独立对象是否算同一外观部件，应结合原始需求和预览判断。

材质内的节点组、贴图等还可能共享；沿着本轮要修改的数据检查使用者，只隔离需要修改的部分。更换材质不能顺便改相机、灯光或用户保留的其他部件。

受限环境中，Blender 保存文件时可能另写系统缩略图缓存。若本次只需交付独立预览 PNG，可在当前进程保存前设置 `bpy.context.preferences.filepaths.file_preview_type = 'NONE'`；不要调用 `save_userpref`。该属性已在本机 5.2.1 验证，其他版本先核对；它仅控制文件预览，不是完整的写入隔离机制。

## 常见失败

| 现象 | 下一步 |
| --- | --- |
| `No module named bpy` | 改为通过 Blender 执行脚本 |
| 路径带中文或空格失败 | 用参数形式与绝对路径；不要拼接转义不清的命令字符串 |
| 操作器 `poll()` 失败 | 查看模式、活动对象与上下文；可行时改用数据接口 |
| 材质插槽或属性不存在 | 查询安装版本 API 或本机 RNA，修正具体属性 |
| GPU 初始化失败 | 查看设备日志；允许时改为 CPU 小图定位问题，说明实际使用的后端 |
| 生成成功但黑图或主体缺失 | 查活动相机、集合隐藏、视图层、光照和裁剪；必须查看新预览 |
| 粉色材质或外部文件丢失 | 检查贴图路径、打包状态、链接库和交付目录 |
| 动画依赖缓存 | 验证缓存文件和代表帧，不能沿用静态检查结论 |

## MCP 扩展

仅在需要实时场景交互时增加连接。先确认环境实际提供了哪些工具，再调用获取场景、执行脚本、截图或保存工具；不要假定工具名称。MCP 负责通信，skill 负责需求转译与验收，两者职责不同。第三方资产服务及其凭据属于单独依赖，不作为首个 `.blend` 的前置条件。

## 官方参考

- [Blender 命令行文档](https://docs.blender.org/manual/en/5.2/advanced/command_line/arguments.html)
- [Blender Python API](https://docs.blender.org/api/5.2/)
- 遇到文档不可访问时可读取本机 `blender --help` 和 Python RNA；本框架命令已在 Blender 5.2.1 的本机帮助中核对。不同版本按实际 API 调整。
