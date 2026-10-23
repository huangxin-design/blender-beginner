# 黄花鱼频道 · 教程与封面 Skill

**v1.2.0 · 2026-10-23**

把当前案例的真实作品、与 AI 对话的经验、工程讲解放进一条 3:4 教程，并配套制作复古电视封面。保留频道的字体、配音、稳定转场和荧光黄半调排版，作品、标题与讲解内容由新案例提供。

[Skill 源码](../skills/huanghuayu-tutorial-video/SKILL.md) · [完整 ZIP](https://github.com/huangxin-design/blender-beginner/releases/download/huanghuayu-tutorial-video-v1.2.0/huanghuayu-tutorial-video-v1.2.0.zip) · [版本发布页](https://github.com/huangxin-design/blender-beginner/releases/tag/huanghuayu-tutorial-video-v1.2.0)

## 封面：核心视觉铺满电视

旧版会把竖图缩在电视中间，模糊侧边和内缩的矩形框让主体偏小。v1.2.0 先选核心区域，再等比放大铺满内屏，以曲边遮罩贴合玻璃边缘；允许裁去次要长枝和留白，保留花心、花头等关键视觉。裁切由实际画面决定，脚本不自动识别主体。

![三案例对照：上排旧版，下排核心裁切与曲边铺满](assets/huanghuayu-screen-fit-v1.2.0.jpg)

图中使用三个实际案例的作品：青蓝垂花、旋转花枝、银蓝花。封面为原生作品图与 AI 生成电视背景的二维透视合成，不是重新渲染的 Blender 电视场景。比较图不代表三个工程的内容被改动。

## 安装与调用

可以把这段发给 Codex：

```text
请帮我安装或更新这个教程与封面 Skill：
https://github.com/huangxin-design/blender-beginner/tree/main/skills/huanghuayu-tutorial-video
将完整文件夹安装到本机个人 Skill 目录，保留脚本、参考资料和素材。
如果已有同名目录，先比较并保留我的自定义修改。核验后告诉我实际安装路径。
这次只安装，不生成配音、视频或封面。
```

在其他对话中调用：

```text
使用 $huanghuayu-tutorial-video，为这个案例制作一条教程视频和配套封面。
结合这次对话的关键修改与工程实际操作，沿用已确认的频道风格。
封面围绕核心视觉放大铺满电视屏幕；素材在……，想重点讲……。
```

只要封面时直接说明“只制作封面”。手动安装时，将 ZIP 内的完整同名文件夹放入个人 Skill 目录，不要只复制 `SKILL.md`。可在新对话中检查 Skill 是否可用，也可提供其 `SKILL.md` 路径。

**旧案例升级**：如果项目曾复制一份 `template/scripts/render_cover.py`，它不会随个人 Skill 自动更新。改用当前安装版本的渲染器，按[封面文档](../skills/huanghuayu-tutorial-video/references/cover.md#修复旧案例)移除同款电视的旧几何配置，再重新选择核心裁切。自定义电视仍需自己的屏幕坐标与遮罩。

## 包含什么

- `SKILL.md`：按视频、封面或整套教程选择流程。
- `scripts/`：教程剪辑、逐句配音、封面原生文字排版、核心裁切和曲边映屏。
- `assets/`：电视背景、半调纹理、屏幕遮罩、已确认版式，以及可运行的示例与配置。
- `references/`：视觉、配音、视频配置、封面取景与旧案例迁移说明。
- `package-manifest.json`：版本、文件大小及 SHA256，便于核验完整性。

教程默认为 1080 × 1440、30 fps，支持单图、双图、四图和图文卡。主屏普通切换约 0.267 秒，章节切换约 0.4 秒，时长按帧率取整；机身保持稳定，字幕在自然停顿间持续显示。封面输出 1080 × 1440 PNG、360px 缩略图、屏幕局部检查图、文字图层、报告和可编辑 SVG。

## 依赖与已验证范围

离线制作需要 Python 3.10+、Pillow 和已安装的中文字体；视频另需 FFmpeg/FFprobe。新配音使用 Edge TTS 的 `zh-CN-XiaoxiaoNeural`，语速 +12%、音高 −2Hz，需要相应网络服务；已有音频可离线剪辑。这个声音不是 Dot 语音对话音色。

字体优先抖音美好体、MiSans 和 Consolas，包内不分发字体；换机后须检查中文缺字与断行。Windows 已实际运行，不代表其他系统均已实测。

v1.2.0 已查看上述三案的完整封面、缩略图和屏内细节；检查遮罩内没有未填充像素、屏幕外机身不变、裁切保持比例、越界裁切明确报错，以及已有完整海报模式逐像素不变。视频流程此前通过另一个测试案例的 24 fps、6 秒离线验证。本次封面修正未重新测试在线配音服务。

示例素材用于说明流程，不能冒充新案例作品。工程截图须来自当前实际工程。调用 Skill 本身不授权上传 GitHub 或发送消息。
