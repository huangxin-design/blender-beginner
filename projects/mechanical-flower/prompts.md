# 可复用提示词

以下是事后整理稿，用于继续制作或学习，不是历史用户原话，也不表示每一段已按原文执行。真实需求摘录见 [conversation.md](conversation.md)。继续修改本案例时，应以工程包中的 `source/scene.blend` 为输入，另存新版本。

## 1. 动作与白膜审查

```text
以已保存的机械花场景为基础，先检查白膜动画。画面为竖版 3:4，关注飞行主体接近、停靠、花瓣开合、充能与离场的连续动作。逐项检查翅膀、花瓣和机械支撑是否穿插，接触与锁定是否可信，动作重点是否在相机内清楚可见。先用低分辨率预览指出问题，再修改相关部件；保持现有主体造型和动作顺序。
```

## 2. 金属与磨砂玻璃材质

```text
保留既有模型、相机和动画，为机械花增加可信的金属加工细节：方向一致的细拉丝、克制的粗糙度变化、机械环与螺钉的局部高光。翅膀为磨砂玻璃，边缘稍通透，翼面有细而清楚的青色发光纹理。将粗糙度、法线与发光信息分开控制，避免整片玻璃变成不透明白板，也避免发光遮住翼脉。所有视觉结果在 Blender 中渲染验证。
```

## 3. 科幻声音与动作同步

```text
为这段 16.375 秒机械花动画制作分轨音效：玻璃气流振翅、磁性悬浮驱动、花瓣伺服、停靠锁定、充能和起飞释放。挥翅在上下行中有细微差异，强弱与飞行距离同步；停靠后留白，起飞前渐次启动。避免持续同音高蜂鸣和机械重复点击。按现有动画事件时间表编排，输出 48 kHz 立体声的分轨与混音，检查无削波。
```

## 4. 4K 渲染与播放检查

```text
从保存的 Blender 场景渲染 1–393 帧、24 fps、3072×4096 的完整 PNG 序列。确认没有缺帧后分别编码 VP9/WebM 和 HEVC/MP4，加入已有科幻混音。检查尺寸、帧数、时间戳与音频时长，并在可用的本机硬件解码路径下与软件解码逐帧比较；退出码正常不能替代画面验证。记录实际验证范围，保留旧版作为故障对照。
```

## 尚未执行的 ElevenLabs 音效试验

以下三组提示词在 2026-09-29 的资料研究后准备，**未用于本片生成**。这是后续试验建议，不是已试听的质量结论；服务能力和账户条件需在实际执行时重新确认。官方建议将复杂声音拆开制作后组合，可参考 [Sound Effects 指南](https://elevenlabs.io/docs/eleven-creative/playground/sound-effects) 与 [API 参数](https://elevenlabs.io/docs/api-reference/text-to-sound-effects/convert)。

### 玻璃翼飞行纹理

建议起点：6 秒，循环素材，`prompt_influence=0.45`。

```text
Seamless six-second loop of a tiny levitating mechanical insect with frosted-glass wings. Soft airy wing pulses around 3.6 Hz, warm magnetic suspension, delicate glass friction, subtle irregular spectral motion. Light, curious, premium sci-fi; different upstrokes and downstrokes. Close, dry, restrained stereo width. No speech, music, melody, harsh beeps, propeller drone or clocklike clicks.
```

### 机械花展开

建议起点：0.7 秒，非循环，`prompt_influence=0.70`。

```text
One isolated 0.7-second sci-fi mechanical flower opening: a soft magnetic servo sweep, a staggered unfurling of thin metal-and-glass petals, fine internal gear texture, then a gentle damped lock. Crisp onset, small scale, dry close detail, short clean tail. Elegant and tactile, not heavy industrial. No voice, music, bell melody or background hum.
```

### 充能与起飞

建议起点：1 秒，非循环，`prompt_influence=0.60`。

```text
One isolated one-second energy-charge and takeoff accent for a tiny glass-winged robot: a compact warm magnetic charge gathers, a soft bright flux shimmer flickers, then releases into a light upward air whoosh with a quick fading tail. Futuristic, agile and tactile; clear attack, restrained bass, no piercing whistle. No voice, music, melody, explosion or long drone.
```

后期仍需自行对齐动作。提示词中的 3.6 Hz 不保证模型准确逐拍输出；6 秒也不是 3.6 Hz 的整数周期，应将生成结果作为纹理层，保留本地节奏包络或重新处理循环接缝。候选先统一响度，再与现版盲听比较，避免把音量更大误判为质量更好。
