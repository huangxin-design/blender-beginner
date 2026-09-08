# 大白话 → Blender 制作任务书

目标是让用户继续用大白话表达，把技术选择交给 Codex。Blender 本身不读取自然语言提示词；Codex 将结构化制作任务书转成当前版本支持的 `bpy` / API 调用，再运行、渲染和检查。

先分清解释与执行：只问术语或提示词时，给视觉目标、实现建议与必要假设，接口和效果标为待执行验证；不要求安装 Blender、探测硬件或试渲染。明确要求制作后才执行下面的运行与回看步骤。修改反馈按 [项目衔接与反馈](project-loop.md) 处理，复用当前工程。

## 翻译约定

1. 原样保留用户描述，分别记录画面目标、技术实现、暂定假设与验收方法。
2. 先说“看起来应该怎样”，再选择节点；用户不需要先学会专业名词。
3. 一个形容词可能包含几件事：“高级”不能只翻译成金属，“透亮”不能直接翻译成透明。
4. 只有影响主体身份、材质类别或工作量的歧义才需要优先澄清；其它记录可逆假设后先预览。
5. 参数范围是制作起点，由本技能给出，不是官方推荐值或必然得到参考效果的配方。
6. 运行前读取 Blender 版本、渲染引擎和实际可用节点插口 / 属性；不要把文档中的显示名称直接当作所有版本的 API。
7. 同时记录场景单位、对象尺寸、相机视距与输出尺寸；肌理尺度、雾密度、灯光和景深都依赖这些条件。

## 常见表达与决策表

| 用户说法 | 面向 Codex 的制作选择 | 起点与验收重点 |
| --- | --- | --- |
| 混合材质、mix、两种质感拼一起 | 颜色或纹理叠加用 Mix（Color）进入单个 BSDF；粗糙度渐变混合数值；两种着色响应才考虑 Mix Shader；透明漆层优先 Principled Coat。[混合颜色](https://docs.blender.org/manual/en/4.0/render/shader_nodes/converter/mix.html) · [混合着色器](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/mix.html) | 先确定混合区域、遮罩与过渡；不要见到“混合”就创建两个完整材质。 |
| 有肌理、凹凸、颗粒、纹路 | 先区分颜色纹路、粗糙度变化和高度起伏；细小高度用 Bump，现成法线贴图用 Normal Map，改变轮廓的起伏用真实位移或几何。[位移手册](https://docs.blender.org/manual/en/latest/render/materials/components/displacement.html) | 近景看凹凸，侧面看轮廓；不能用颜色噪声代替所有表面结构。 |
| 辉光、发光、光晕 | 发光表面用 Emission；画面亮部扩散用合成器 Glare / Fog Glow；照亮其它物体由灯光和引擎的光照计算负责。[Glare](https://docs.blender.org/manual/en/4.4/compositing/types/filter/glare.html) | 先控制亮部，再少量叠加光晕；发光不是提高整个画面的曝光。 |
| 背景虚一点、有景深 | Camera DOF 指定焦点对象 / 距离并调光圈；同时考虑焦距、拍摄距离、主体和背景间距。[相机](https://docs.blender.org/manual/en/4.3/render/cameras.html) | 产品镜头可从 50–85 mm、f/4–f/8 试起；主体关键边缘清晰，背景变软。 |
| 塑料、玩具感 | 非金属 Principled，先定光滑或哑光，再用粗糙度与反射形状表现硬塑料；软胶可另考虑次表面散射。 | Metallic 从 0 开始；不能只凭鲜艳颜色判定“塑料感”。 |
| 玻璃、水晶、透明 | 用透射、IOR、粗糙度及真实厚度形成折射；检查法线和渲染引擎能力，先做小样。 | 普通玻璃 IOR 可从约 1.45–1.52 试起；Alpha 降低并不等于玻璃。 |
| 金属、银色、拉丝 | 裸金属先用 Metallic 1；由粗糙度、反射环境和必要的各向异性 / 方向纹理表现拉丝。 | “银色油漆”与裸金属需区分；没有可反射的环境可能显得黑。 |
| 磨砂、哑光 | 通常先提高粗糙度；微小颗粒另加弱 Bump。磨砂玻璃仍要保留透射与厚度。 | 非金属粗糙度可从 0.45–0.7 试起；哑光仍应保留柔和高光。 |
| 毛茸茸、绒面 | 细绒反光可用 Sheen；可辨识的长毛和轮廓毛发需要曲线 / 毛发几何，按镜头距离控制密度。 | Sheen 不会长出毛；侧面轮廓必须符合用户想要的毛长。 |
| 胶片颗粒、胶片感 | 将颗粒作为合成 / 输出层效果，另拆分色调、对比和高光响应；动画需考虑颗粒随帧变化。 | 先完成干净渲染，再叠少量颗粒；不靠降低采样制造未收敛噪点。 |
| 雾气、空气感、光束 | 在有限体积内用 Principled Volume 的散射 / 密度，结合实际光源；只有远景变淡时可评估合成简化。[体积材质](https://docs.blender.org/manual/en/4.4/render/shader_nodes/shader/volume_principled.html) | 从接近 0 的密度逐步加；Fog Glow 不会生成场景内的体积光束。 |
| 柔光、边缘柔亮、轮廓光 | 柔和阴影通常增加光源相对主体的面积；边缘亮线用侧后方灯光照出反射 / 轮廓。[灯光](https://docs.blender.org/manual/id/dev/render/lights/light_object.html) | 先试较大 Area Light；先改位置和面积，再调亮度。 |
| 透亮、通透、润 | 分辨“明亮干净”“能看穿”“玉石 / 蜡质透光”三种目标，分别调整光照、透射、次表面散射。 | 根据参考和物体类别选择；不明时记录解释，避免一律玻璃化。 |
| 圆润、别那么硬 | 建模轮廓、倒角 Bevel、必要的细分和表面平滑分别处理；轮廓先于高光。 | 倒角宽度按对象尺寸与镜头判断；平滑法线不能改变方形外轮廓。 |
| 奶油色、温柔、高级 | 将颜色、明暗、材质、光线、构图拆开描述；奶油色先解释为低饱和暖白，高级感转为具体画面条件。 | 以中性光下的预览判断底色；不能用黄色灯光补偿错误材质色。 |

塑料、玻璃、金属、磨砂、Coat、Sheen 和次表面等选择参考 [Principled BSDF 手册](https://docs.blender.org/manual/en/4.0/render/shader_nodes/shader/principled.html)；表内数值与组合为可调整的实施起点。

## 三类“混合”必须区分

- 颜色混合：红蓝纹理通过遮罩混合到 Base Color，同一种表面可仍使用单个 BSDF。
- 属性混合：污渍使局部更粗糙，可用遮罩改变 Roughness；不必另外建一个完整着色器。
- 着色响应混合：确实需要两套不同响应时再用 Mix Shader；Factor 决定两者权重，不代表物理厚度。
- 覆盖层：上清漆优先 Coat；真实玻璃外壳、夹层或明显厚度应建几何，不能靠混合权重表现空间关系。

以上是基于 [Mix Shader](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/mix.html)、[Mix Node](https://docs.blender.org/manual/en/4.0/render/shader_nodes/converter/mix.html) 和 [Principled 层结构](https://docs.blender.org/manual/en/4.0/render/shader_nodes/shader/principled.html) 的选型规则。

## 肌理与发光的误译检查

- Bump 用高度变化扰动着色法线，Normal Map 从编码法线图读取方向；二者本身都不增加几何起伏或改变剪影。
- 法线图要匹配 UV、法线空间和贴图约定；作为数据读取，检查 Non-Color，不能当普通彩色照片接入。[Normal Map](https://docs.blender.org/manual/id/5.2/render/shader_nodes/displacement/normal_map.html)
- 真实 Displacement 会改变表面，需要足够几何和引擎支持；明显沟槽、砖块边缘及印刷制造用途需要真实结构。[位移](https://docs.blender.org/manual/en/latest/render/materials/components/displacement.html)
- Emission 描述表面发光，Glare 描述图像亮部周围的扩散；Glare 可以作用于明亮反射，不要求物体自发光。[发光材质](https://docs.blender.org/manual/en/4.0/render/shader_nodes/shader/principled.html) · [Glare](https://docs.blender.org/manual/en/4.4/compositing/types/filter/glare.html)
- 发光材质是否有效照亮其它物体，需要按当前引擎、间接光设置与预览验证；需要明确投光时安排实际灯光。
- Blender 4.2 已移除旧 EEVEE Bloom 功能；新流程走合成器 Glare，并按运行版本探测其插口 / 属性。[迁移说明](https://developer.blender.org/docs/release_notes/4.2/eevee_migration/)

## 输出示例

用户原话：“奶油色磨砂花瓶，背景虚一点，边缘柔光和少许发光。”

先向用户展示一句自然语言解释：“做一个奶油色的哑光陶瓷花瓶，瓶身保持清楚，背景轻微虚化；侧后方柔光勾出边缘，亮边带一点淡淡光晕。”
记录歧义：“少许发光”暂按亮边光晕理解；如果参考明显是灯具或用户明确要求花瓶自己发光，再采用局部 Emission，并验证其对周围的照明。

再形成供 Codex 执行的任务书，而不是把一串节点名交给用户：

```yaml
原话: 奶油色磨砂花瓶，背景虚一点，边缘柔光和少许发光
目的: 制作方案示例；仅在用户要求实际制作时交付工程与渲染
暂定假设:
  物体: 不透明陶瓷花瓶，不是磨砂玻璃
  尺寸: 暂按高约 25 厘米，后续依用户要求或参考比例调整
  发光: 轮廓亮部的淡光晕，花瓶本体暂不自发光
几何:
  主体: 按参考轮廓制作，瓶口有厚度，口沿倒角
  可编辑性: 保留主体、背景、相机、灯光分组与命名
材质:
  颜色目标: 中性照明下呈低饱和暖白，避免偏黄
  起点: 非金属 Principled，粗糙度约 0.6
  肌理: 微弱细颗粒 Bump，尺度按真实尺寸及成片近景调节
灯光:
  主光: 大面积柔光，呈现瓶腹体积与哑光高光
  轮廓光: 侧后方 Area Light，亮边保留细节
相机:
  对焦: 独立焦点对象放在花瓶需要清晰的位置
  起点: 约 70 mm，f/5.6；视距先按构图设置
  调整: 先拉开背景距离，再用光圈微调虚化
合成:
  光晕: 对实际亮部叠加少量 Glare / Fog Glow
  限制: 不使主体泛白，不把轮廓光当成物体发光材质
验证:
  - 当前 Blender 版本和节点接口已探测
  - 花瓶主体及瓶口清晰，背景能辨认但轻微失焦
  - 奶油底色、哑光高光、细肌理在真实渲染中可见
  - 侧后方亮边存在，光晕轻微，不丢失瓶身轮廓
  - 保存的工程可重新打开，材质与所需素材完整
```

## 执行与回看

任务书只表达制作意图；脚本必须在本机 Blender 中检查接口后生成，不能照抄未知版本属性。
先做低成本预览验证材质类别、轮廓光和虚化，再提高成片质量；一次只改与反馈相关的参数。
把每条用户意图对应到可观察结果。若实现路线改变，例如长毛改为绒面着色，须说明外观与可编辑性的差别。
参考图未提供的背面、内部结构和真实材质不写成事实；假设要留在任务书里，方便后续修改。
官方资料核对日期：2026-09-07。`latest` / `dev` 链接内容可能变化，实施时以实际安装版本为准。
