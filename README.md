# Blender 开工助手

**零基础也能开始做 3D。你说想法，Codex 帮你安装 Blender、做作品、记用量、看渲染进度。**

[English](README.en.md) · [开始使用](docs/quickstart.md) · [作品与源文件](#作品源文件与精简对话) · [Token 与渲染进度](docs/usage-progress.md)

这是给 Codex 使用的 Blender 新手 Skill，当前为 **v05 / Early Preview**。[启用后](docs/quickstart.md)，直接把下面这些话交给它。

## 这些地方，它能帮上忙

**零基础安装｜“我从没用过 Blender，帮我装到 D 盘，项目也放这里。”**

→ 帮你下载安装，设好中文界面和自动保存，建好项目与渲染目录，交付能打开、能出图的起步工程。

**参考图变作品｜“照这张图，帮我做一个能继续修改的 3D 作品。”**

→ 拆解造型、材质和灯光，告诉你难点与预计差别；先出小样，再按反馈完善，交付可编辑的 `.blend` 和预览图。

**Token 有记录｜“从现在开始，帮我记下这个会话做项目用的 Token。”**

→ 建好记录起点，随时查看已记录用量、统计截至时间和待补记状态，做作品也能看清用量。

**渲染倒计时｜“开始渲染，把进度和预计还要等多久显示出来。”**

→ 打开本地进度页，持续更新阶段、已用时间和完成帧数；有足够完整帧后，显示动态的预计剩余时间范围。

**先测电脑｜“我的电脑能做 4K 或动画吗？用这个工程测一下。”**

→ 测出显卡、显存和内存，验证 GPU 加速，跑限时试渲染，给你实测耗时和适合这台电脑的设置建议。

**[我也想试试 →](docs/quickstart.md)**

<details>
<summary>展开完整用法：参考图评分、材质调整、局部修改、源文件交付等</summary>

| 你想解决的事 | 你只要这样说，Skill 就会动手 |
| --- | --- |
| 不会安装，也不知道文件放哪 | 说 **“帮我把 Blender 装到 D 盘，项目也放这里”** → 完成下载安装、中文界面与自动保存设置，建好项目和渲染目录，交付能打开、能出图的起步工程。 |
| 不知道电脑能不能做 4K 或动画 | 说 **“用这个工程测一下我的电脑，看看适合出 4K 图还是动画”** → 检测显卡型号、显存和内存，验证 GPU 加速，跑限时小样；交付实测耗时、加速是否可用及验证结果，以及 4K 和动画各自的设置建议与待验证项。 |
| 有参考图，想先知道能做到哪一步 | 说 **“给这张图评个分，把难做的地方和预计差别告诉我”** → 交付有依据的 0–100 分方案评估，拆清造型、材质、灯光镜头、素材和设备限制，列出优先验证的难点。 |
| 只会说感觉，不会调节点 | 说 **“把这个球做成磨砂玻璃，边缘有光晕，背景虚一点”** → 把描述落实为材质节点、光晕和景深设置，生成可编辑工程与预览图。 |
| 做出来不满意，想接着改 | 说 **“木头凹槽太亮了，只改这里，其他保持不变”** → 从当前工程调整对应效果，另存新版和对比预览，复核要保留的物体、材质与构图。 |
| 想拿到能继续编辑的源文件 | 说 **“把能继续改的工程、素材和预览一起给我”** → 交付 `.blend`、必要素材和制作脚本；重新打开工程、检查依赖，再渲染并实际查看预览。 |
| 想知道项目消耗了多少 Token | 说 **“从现在开始，记录这个会话做这个项目用的 Token”** → 建立记录起点，输出已记录用量、统计截至时间和待补记状态，后续可以随时查看。 |
| 渲染时想知道还要等多久 | 说 **“帮我开始渲染，把进度和剩余时间显示出来”** → 打开本次渲染的本地进度页，显示阶段、已用时间和完成帧数；积累足够完整帧后，自动更新预计剩余时间范围。 |

你负责说效果、看预览，Codex 负责动手；当前自动安装适用于 Windows，Mac 仍需真机验证，评分不是还原百分比，用量只覆盖指定会话的记录区间，剩余时间依据本次受控渲染的完整帧估计，具体范围见 [快速开始](docs/quickstart.md) 与 [用量和进度说明](docs/usage-progress.md)。

</details>

## 大白话，也能变成 Blender 里的具体效果

![用大白话描述 AI 材质球，让 Codex 设置磨砂、透光、光晕与景深](docs/assets/language-to-blender.png)

## 想先问问，还是直接开做？

![工作流：选择任务，按需检查，制作小样，局部反馈，验证并交付](docs/assets/workflow.png)

- **先聊聊想法**：比如“这张图能不能做”“为什么看起来像塑料”。先给解释和建议，等你提出制作需求，再开始动手。
- **开始做一个版本**：你说“按这张图帮我做出来”，它会把影响结果的关键要求弄清楚，先出预览，再逐步完善。
- **接着改已有作品**：比如“木头凹槽别那么亮”。从你指定的最新版工程继续，检查需要保留的部分，并另存一版。
- **电脑或时间有点吃紧**：先说清楚按原要求做会卡在哪里，再给出可以调整的地方和相应取舍，由你决定怎么继续。

参考图的 **0–100 分属于方案评估**，应附依据、置信度和预计差异。它不表示还原百分比或成功概率，缺少关键证据时保留待评估项。看不到的模型背面也需要明确假设。

## 用量监控与渲染进度

![Codex 监控小鱼 v0.3.1：项目 Token、人民币订阅成本摊算与下一轮重置时间，全部为模拟数据](docs/assets/codex-monitor-fish-v0.3.1.png)

<sub>新版看板示例来自 [Codex 监控小鱼](https://github.com/huangxin-design/codex-monitor-fish)，任务、用量、金额与重置时间均为模拟数据，不代表这些作品的真实用量或账户状态。</sub>

**项目用量看板**：搭配 Codex 监控小鱼 v0.3.1，在网页选择 Blender 项目，查看任务与子任务的累计 Token，支持亿／整数切换、CSV 导出和持续刷新。总 Token、人民币订阅成本摊算与下一轮周额度重置集中在顶部。

**金额与重置时间**：人民币金额按用户设定的 20x 账户口径摊算，汇率可修改；它不代表按次扣费、额外支出或官方固定 Token 配额。重置卡片显示已知的 Codex 周额度时间与倒计时，不预测获赠重置机会的概率。

**v05 单次会话记录**仍支持一个明确指定的本地 Codex 会话来源，从开始记录的基线累计。缓存输入和推理输出显示为子项，不重复相加；结束时保留待补记状态。旧作品缺少原始记录时显示未知，这个内置记录器不自动合并子任务或计算费用。

**渲染进度**由 Blender 的本地程序更新页面，无需每秒调用模型。首版支持本次启动的受控 PNG 静图或帧序列；首帧单列，至少三个后续完整帧后才给经验范围。时间可以上升，信息过期会撤回估计，执行结束仍需检查输出和画面。

<details>
<summary>查看 Blender v05 渲染进度页面（模拟数据）</summary>

![Blender v05 本地渲染进度与单次会话 Token 记录示例，使用模拟数据](docs/assets/progress-panel-v05.png)

<sub>此页展示 Blender 渲染阶段、帧数与预计剩余范围；上方监控小鱼看板展示项目用量，两者分别运行。</sub>

</details>

[查看使用方法、限制与验证记录 →](docs/usage-progress.md) · [监控小鱼使用指南](https://github.com/huangxin-design/codex-monitor-fish/blob/main/docs/使用说明.md)

## 作品、源文件与精简对话

花卉与数字盆景已更新至最新完成版，用量读取于 **2026-09-09 19:20（北京时间）**；AI 材质球与粉色波浪保留当天 16:59 的快照。数字对应关联制作任务的累计记录，各案例分别说明覆盖范围。[用量来源与统计方法](docs/showcase-measurements.md)

### 当 AI 有了触感


![真实 Blender 作品：OpenAI 金属球、Claude 木纹球、DeepSeek 石材球与 Gemini 磨砂玻璃球](projects/ai-brand-materials/preview.jpg)

**提示词 · 根据本案例整理的示例**

> 给这四个 AI 品牌做一组材质球：OpenAI 像金属，Claude 像木头，DeepSeek 像石头，Gemini 像磨砂玻璃。标识要刻进球面，背景用粉色。先给我看小样，再决定哪里要改。

**Token 用量：** 相关制作任务已记录 **40,779,249**（含主任务与 10 个子任务；未单独拆分到这四张图）。[统计范围](docs/showcase-measurements.md)<br>
**显卡渲染耗时：** 制作设备档案为 **RTX 4070 Ti / 12 GB**；四张原图合计约 **15.1 秒**（历史整组进程计时，含启动、场景载入和保存；Cycles / OptiX，每张 960 × 1280、128 samples）。显卡型号与计时口径见 [用量与耗时说明](docs/showcase-measurements.md)。

**[看制作过程与源文件 →](projects/ai-brand-materials/README.md)** · [下载 20 秒动画预览](projects/ai-brand-materials/preview.mp4) · [试试这组提示词](projects/ai-brand-materials/prompts.md)

<sub>四张原生 Blender 渲染拼图，未做 AI 图像精修。提示词是制作回顾中的整理稿；计时仅覆盖这次静图输出，不含前期建模、修改或整段动画制作。[参考与素材出处](projects/ai-brand-materials/credits.md)</sub>

### 粉色波浪 · 20 秒解压动画

https://github.com/user-attachments/assets/09e1b56e-4b11-4e15-ac81-7e638166a24d

**提示词 · 整理示例**

> 做一片粉色圆柱阵列，让金属和陶瓷小球轮流滚过，柱子跟着起伏成波浪。光线柔和、接触自然，输出方形 4K 循环动画，重复到 20 秒，保留可编辑工程。

**Token 用量：** 关联分叉任务已记录 **3,810,251**（含 1 个子任务；不包含继承的前期制作历史）。[统计范围](docs/showcase-measurements.md)<br>
**显卡与历史渲染耗时：** RTX 4070 Ti / 12 GB，**58 分 7.7 秒**（3840 × 3840、64 采样、200 帧原生循环）。循环三遍合成 20 秒，播放器展示 1080 预览；计时不含建模与编码。

[案例与源工程](projects/pink-wave-original/README.md) · [提示词](projects/pink-wave-original/prompts.md) · [制作回顾](projects/pink-wave-original/conversation.md) · [计时与验收](projects/pink-wave-original/verification.json)

### 花卉粒子 · 把开花的几秒钟，留在薄雾里

https://github.com/user-attachments/assets/3afd119c-94a4-4a06-8d26-1b859ca1b54d

**提示词 · 整理示例**

> 让珊瑚红和浅桃色的花瓣沿细茎一层层展开，像一股向上流动的开花波。前面的花清楚，后面的植物虚一点，周围留一点薄雾。加上 HUANGHUAYU 水印，给我 8 秒竖屏 4K 动画和能继续修改的 Blender 工程。

**Token 用量：** 相关制作任务已记录 **24,574,578**（主任务 + 3 个子任务；跨版本累计）。读取于 **2026-09-09 19:20（北京时间）**。[统计范围](docs/showcase-measurements.md)<br>
**显卡与实测渲染耗时：** 制作档案为 RTX 4070 Ti / 12 GB，全部 240 帧的渲染段累计约 **50 分 30 秒**（2160 × 3840、64 采样、Cycles / OptiX）。包含续跑 238 帧与复用的两张 4K 样张，不含建模、修改与编码；播放器展示 1080 预览。

[4K 最终版案例](projects/flower-bloom/README.md) · [下载 4K 成片](https://github.com/huangxin-design/blender-beginner/releases/download/works-2026-09-09/huanghuayu-flower-4k.mp4) · [源工程](projects/flower-bloom/source/scene.blend) · [提示词](projects/flower-bloom/prompts.md) · [制作回顾](projects/flower-bloom/conversation.md) · [计时与验收](projects/flower-bloom/verification.json)

### 数字盆景 · 让一棵树长出数字花园

https://github.com/user-attachments/assets/39fd6bea-291f-4274-95b8-5e4cbbbeaf30

**提示词 · 整理示例**

> 让一棵树从石台上生长出来，叶片展开、花苞打开。数字和连线在生长阶段就出现，文字再清楚一点，花朵加上玫瑰粉和珊瑚红。保留横向切片转场和古典电子配乐，给我 7 秒竖屏动画与完整可编辑工程。

**Token 用量：** 相关制作任务已记录 **63,990,527**（主任务 + 6 个子任务；跨版本累计，不是第 7 版单独成本）。读取于 **2026-09-09 19:20（北京时间）**。[统计范围](docs/showcase-measurements.md)<br>
**显卡与 v007 实测渲染耗时：** 同机设备记录为 RTX 4070 Ti / 12 GB，累计 **11 分 48.5 秒**（720 × 1280、48 采样、Cycles / OptiX，175 帧主镜头 + 20 帧转场近景）。三次渲染进程含启动、载入共 **12 分 3.7 秒**；建模、配乐与合成编码另计。

[第 7 版案例](projects/tree-study/README.md) · [完整工程包](https://github.com/huangxin-design/blender-beginner/releases/download/works-2026-09-09/tree-study-v007-project.zip) · [提示词](projects/tree-study/prompts.md) · [制作回顾](projects/tree-study/conversation.md) · [计时与验收](projects/tree-study/verification.json) · [保留的第 6 版](projects/tree-study/versions/v006/README.md)

下面三个早期作品也保留了提示词、工程与制作记录。它们与上面的 AI 材质球都是作者单独整理的 GitHub 展示资料，独立于 Skill，不作为当前版本一次生成的效果验证。

### 粉色装置

<img src="projects/pink-installation/preview.png" width="560" alt="粉色玩具装置，Blender 底稿加图像精修成品">

**提示词 · 整理示例**

> 按参考图做一个粉色玩具装置：珊瑚粉褶柱、蓝色背板、薄荷色珠子和金白悬球。陶瓷温润、金属有反光、绒面柔软。先确认造型，再调整材质和灯光。

**Token 用量：** 未记录。<br>
**本机显卡实测：** RTX 4070 Ti / 12 GB，渲染 **5.95 秒**；含启动与载入共 **7.14 秒**（1080 × 1048、128 采样上限）。不含上图的后期精修。[本次原生出图](projects/pink-installation/measurements/2026-09-08/native-render.png) · [实测记录](projects/pink-installation/measurements/2026-09-08/measurement.json)

[源文件与原生渲染](projects/pink-installation/README.md) · [完整提示词](projects/pink-installation/prompts.md) · [制作过程与出处](projects/pink-installation/conversation.md)

### 毛绒兔骑士

<img src="projects/plush-rabbit-knight/preview.png" width="560" alt="粉色毛绒兔骑士，Blender 底稿加图像精修成品">

**提示词 · 整理示例**

> 做一只站在树墩上的粉色毛绒兔骑士，举着金色水晶剑，拿着木盾。绒毛要柔软，剑光轻轻照到脸和手，背景放三朵圆润的云。先看小样，再检查毛发和发光效果。

**Token 用量：** 未记录。<br>
**本机显卡实测：** RTX 4070 Ti / 12 GB，渲染 **55.47 秒**；含启动与载入共 **57.52 秒**（1000 × 1000、1024 采样上限）。不含上图的剑光与云朵精修。[本次原生出图](projects/plush-rabbit-knight/measurements/2026-09-08/native-render.png) · [实测记录](projects/plush-rabbit-knight/measurements/2026-09-08/measurement.json)

[源文件与原生渲染](projects/plush-rabbit-knight/README.md) · [完整提示词](projects/plush-rabbit-knight/prompts.md) · [制作过程与出处](projects/plush-rabbit-knight/conversation.md)

### 悬浮几何动画

<img src="projects/floating-geometry-animation/preview.jpg" width="760" alt="悬浮几何动画的五套配色预览">

**提示词 · 整理示例**

> 让密褶球、空心管、圆环和方框各自转动、起伏，镜头保持不动。做白底彩色、黑金、冰蓝、紫黄和黑白五套配色，每套 6 秒，连成 30 秒动画。先检查穿插和管口，再出整片。

**Token 用量：** 未记录。<br>
**显卡渲染耗时：** 完整成片总耗时未记录；成片为 720 × 1280、30 fps、900 帧。渲染设置与记录范围见 [用量与耗时说明](docs/showcase-measurements.md)。

[源文件与成片](projects/floating-geometry-animation/README.md) · [完整提示词](projects/floating-geometry-animation/prompts.md) · [制作过程与出处](projects/floating-geometry-animation/conversation.md)

<sub>上面的短提示词是根据已有记录整理的示例，不是逐字聊天。两张早期静图的图像精修效果未写回 `.blend`。耗时缺失不代表零耗时，也不能据此推算其他显卡或 Mac 的速度。[全部作品](projects/README.md) · [用量与耗时说明](docs/showcase-measurements.md)</sub>

准备分享作品时，维护者可按 [作品归档约定](docs/project-archive.md) 整理源文件和输入来源。日常使用 Skill 无需执行这些资料整理步骤。

每个作品的 `conversation.md` 保留关键需求、修改反馈与对应版本，让你能看到“大白话怎样变成结果”。按 [精简对话方法](docs/conversation-archive.md) 保留有意义的返工，区分原话与摘要。AI 材质球的过程依据现有制作记录整理，完整说明见 [制作回顾](projects/ai-brand-materials/conversation.md)。

## 设备支持与验证范围

| 项目 | 当前状态 |
| --- | --- |
| Windows 自动安装 | 支持 x64、Blender 5.2 系列的独立目录安装；优先复用已有可用版本 |
| Windows 制作与复核 | Blender 5.2.1 已完成实际执行与台灯案例验证 |
| Mac 设备评估 | 已实现 Intel / Apple Silicon、统一内存与 Metal 相关评估路径；Mac 真机待验证 |
| Linux | 尚未建立完整安装与制作验证记录 |
| 4K / 动画 | 根据目标场景与设置单独评估；简单静帧的结果不能证明复杂动画的耗时或稳定性 |

v04 已完成 **14 项执行检查、5 组文字决策试用和 1 次独立工程修改试用**。其中中断处理使用模拟检查。这些是开发阶段的有限验证，不构成任意参考图的质量保证。

v05 新增用量边界与异常记录检查、真实小图帧序列试渲染、超时和失败状态联调，以及桌面／手机尺寸的面板检查。具体范围见 [v05 验证记录](docs/usage-progress.md#验证记录)；Mac 真机与复杂动画仍未因此得到验证。

生成后会分别检查进程、工程结构和实际预览。基础检查器覆盖静态场景的一部分问题；视觉质量、拓扑、3D 打印和复杂动画还需要与用途相符的检查。限时执行器控制本次启动的 Blender 进程，不能完整隔离任意脚本的访问行为。

## 仓库结构

```text
skills/blender-beginner/
  SKILL.md            # Codex 技能入口
  agents/             # 技能显示信息
  references/         # 评估、制作、反馈与验收规则
  scripts/            # 安装、探测、限时执行与检查工具
  assets/             # 台灯起步模板
docs/                 # 使用说明与介绍素材
projects/             # 展示作品、可编辑源文件与精简对话
templates/            # 版本说明与精简对话模板
```

技能采用本地 Blender 脚本与文件交付流程。实时 MCP 连接可按需另行接入；当前仓库未预先配置该连接。

从 [快速开始](docs/quickstart.md) 安装，或先阅读 [技能入口](skills/blender-beginner/SKILL.md) 了解完整行为。
