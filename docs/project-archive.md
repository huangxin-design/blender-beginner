# GitHub 作品资料归档

本页面向仓库维护者，仅用于整理准备展示的作品。作品源文件、提示词与精简对话是 GitHub 资料，不属于 Skill 功能，也不是使用 Skill 的必经流程。导入已有作品时沿用实际文件与版本关系，不要求事后补齐下面的示范结构。

仓库同时保存 Skill 和作品。每个作品有独立目录，每次生成或修改都新增版本；预览帮助浏览，`.blend` 供打开继续编辑，脚本与任务说明记录它是怎样做出来的。每个作品再用一份精简对话串起关键需求、反馈和对应版本，让读者了解修改过程。

## 目录约定

```text
projects/
  desk-lamp/
    README.md
    conversation.md
    versions/
      v001/
        scene.blend
        build.py
        preview.png
        brief.md
      v002/
        scene.blend
        edit.py
        preview.png
        brief.md
```

`desk-lamp` 换成简短的作品名称。首版保存实际生成脚本为 `build.py`；局部修改保存实际修改脚本为 `edit.py`。如果一次版本确实需要多个脚本，都应保留，并在说明中写清顺序。不要把所有作品存成根目录下的 `final.blend`。

各版的 `scene.blend` 是需要归档的正式源文件；Blender 的 `.blend1/.blend2` 和临时自动保存用于故障恢复，不能代替 `versions/vNNN/`。仓库只忽略这些备份与缓存，不忽略 `.blend`。可以复制 [版本说明模板](../templates/version-brief.md) 作为每次记录的起点。

## 每次归档做这五步

1. **新建版本目录。** 从 `v001` 递增，复制本次真实产物，保留旧版本。生成中途失败也可以记录，但应明确“未完成”；未生成的 `.blend` 不填下载链接。
2. **写清本次任务与对话。** `brief.md` 记录原始要求、相对前版的改动、必须保留的内容、实际结果和已知不足；在作品 `conversation.md` 追加相关轮次，并链接本版文件。采用 [精简对话整理方法](conversation-archive.md)，区分原话、摘要与制作回顾。
3. **保留复现条件。** 写 Blender 实际版本、脚本入口和必要参数。修改版注明输入是哪个前序版本；使用脚本参数或仓库内相对路径，避免写死作者电脑的盘符。
4. **检查搬移后能用。** 在新位置重新打开工程并查看预览；贴图、字体、链接库、序列或动画缓存需要随作品保留时放入版本内 `assets/`。不能打包的依赖要说明获取方式和使用条件。
5. **更新作品索引。** 在作品 `README.md` 增加一行版本记录，让读者能找到工程、脚本、预览、说明和精简对话；每个已发布版本保留自己的入口。

仓库内的下载与图片链接使用相对路径。`brief.md` 可以照这个结构填写：

```text
任务：用户这次希望得到什么
输入：从零创建，或输入工程的仓库相对路径
本次改动：与前版的主要差异；是否包含手动修改
环境：Blender 版本、渲染引擎、分辨率和采样
复现：脚本名称、运行顺序、必要参数及依赖
验证：是否重新打开、是否实际查看预览、已检查什么
限制：未完成部分、外部资源或尚未验证的功能
素材：来源及适用的使用条件；没有外部素材也写明
```

脚本不一定能重现工程中的全部手动编辑。遇到这种情况，应以保存的 `.blend` 为本版真实源文件，并在说明中写明脚本覆盖的范围。压缩包、预览或发布文案不应把未做过的验证写成已完成。

## 大文件怎么放

先让 Codex 检查本次待上传文件的实际大小。GitHub 当前规则如下，核验于 2026-09-07：

| 单文件大小或用途 | 上传方式 |
| --- | --- |
| 不超过 25 MiB | 可以网页上传；多个文件也可用本地 Git 管理 |
| 超过 25 MiB、不超过 100 MiB | 用本地 Git 提交推送，不能直接拖进网页 |
| 超过 100 MiB、需要跟随仓库版本 | 先配置 Git LFS，再提交文件 |
| 大型工程包、动画或整套缓存，主要供下载 | 可作为 GitHub Release 附件，作品索引保留对应下载入口 |

GitHub 对普通 Git 中超过 50 MiB 的文件会提示警告，超过 100 MiB 会阻止上传；单个文件达标也不代表长期积累大量二进制版本没有成本。依据：[上传文件](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)、[大文件限制与 Release](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)。

使用 LFS 时，让 Codex 在本地检查 Git LFS，按选定路径或类型建立跟踪规则，并把 `.gitattributes` 一起提交。**网页上传会忽略 `.gitattributes`，不能用来替代 LFS 上传。** 初次配置应在大文件进入 Git 历史之前完成。[LFS 配置说明](https://docs.github.com/en/repositories/working-with-files/managing-large-files/configuring-git-large-file-storage)

LFS 单文件上限依套餐不同，当前为 Free/Pro 2 GB、Team 4 GB、Enterprise Cloud 5 GB；Release 单文件也受当前套餐对应的最大文件限制约束。LFS 的存储、流量与预算另行计算，使用前看自己的账户设置，不预设免费额度或自动购买空间。[LFS 文件上限](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage)、[LFS 计费](https://docs.github.com/en/billing/concepts/product-billing/git-lfs)

## 确保别人下载到的是工程

启用 LFS 后，GitHub 默认的 **Download ZIP** 可能只有指针文件，不能直接当 `.blend` 打开。可以让读者用支持 LFS 的方式克隆，或由仓库管理员启用 ZIP 包含 LFS 对象；后者会计入相应下载流量。也可以上传实际工程 ZIP 为 Release 附件，并在版本索引里写明这种获取方式。[GitHub 的 LFS 压缩包说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/managing-git-lfs-objects-in-archives-of-your-repository)

使用 Release 存储某个源文件时，版本目录保留脚本、预览和说明，在 `brief.md` 和作品索引写明该版本的真实下载链接、文件名与 SHA256。不要创建假的 `scene.blend` 占位文件。

每次发布后，按读者的实际下载入口取回一次工程，在新目录打开检查。预览图片适当缩小以便浏览；4K 原图、视频和完整工程包可以另设下载入口。这样每个版本既容易看，也有源文件可用。
