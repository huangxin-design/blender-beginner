# 配音与分句字幕

当前频道使用 Microsoft Edge TTS 的 `zh-CN-XiaoxiaoNeural`（晓晓），语速 `+12%`、音高 `-2Hz`。这不是已确认的 Dot 音色。语气用自然、亲切的讲解文案控制；不要承诺未经验证的音色复刻，也不需要保存 API 密钥。

## 配置

把每个镜头的讲解拆成适合一次显示的短句。`text` 是完整口播，`subtitle_lines` 是该句字幕的人工换行，不应删改口播含义。不要用字符数量估算字幕时间。

```json
{
  "voice_settings": {
    "voice": "zh-CN-XiaoxiaoNeural",
    "rate": "+12%",
    "pitch": "-2Hz",
    "gap_seconds": 0.15
  },
  "shots": [
    {
      "id": "M01",
      "narration_parts": [
        {
          "text": "先看这朵花的开合。",
          "subtitle_lines": ["先看这朵花的开合。"]
        },
        {
          "text": "再把动画和材质分别拆开。",
          "subtitle_lines": ["再把动画和材质", "分别拆开。"]
        }
      ]
    }
  ]
}
```

这只是配音字段示例，实际 `lesson.json` 还应保留渲染器要求的画面和字体配置。镜头 `id` 用唯一的英文字母、数字、下划线或短横线；输出文件按 `id` 命名。无口播镜头可省略 `narration_parts`，其原配置保持不变。

## 执行

依赖 Python 3.9+、PATH 上的 FFmpeg；在线生成另需 `edge-tts`，已验证使用版本为 `7.3.1`。依赖安装不是脚本自动行为。

```sh
python -m pip install edge-tts==7.3.1
python <SKILL_DIR>/scripts/synthesize_voice.py --config <WORK_DIR>/lesson.json --validate-only
python <SKILL_DIR>/scripts/synthesize_voice.py --config <WORK_DIR>/lesson.json
```

只有明确执行最后一条合成命令才会连接 Edge 在线语音服务，发送配置中的口播文字。加载 skill、导入脚本、`--help`、`--validate-only` 都不会联网。脚本不播放音频、不操作窗口。网络请求失败时直接报错，不切换音色或无限重试。

每句先生成独立 MP3，再经 FFmpeg 转成 48 kHz、单声道、16-bit PCM WAV，响度处理目标为 `I=-18 LUFS / TP=-2 dBTP / LRA=9`。句间插入 150 ms 静音；可用 `gap_seconds` 调整。此值是新增间隔，原始 TTS 句尾自带停顿也会保留。脚本检查每句及合并音轨非静音、无满幅削波；没有自动进行听感审校。

## 输出与渲染器接口

所有输出写在 `lesson.json` 所在目录；重复运行会重建同名音频和清单，输入 JSON 不改写。

- `audio/M01_source_01.mp3` 等：在线合成的分句源文件。
- `audio/M01_part_01.wav` 等：统一格式的分句音轨。
- `audio/M01.wav`：镜头完整音轨。
- `audio/M01_subtitle_cues.json`：`{duration_seconds, gap_seconds, cues:[{start,end,lines,narration}]}`。
- `audio_manifest.json`：实际长度、来源、字幕事件及峰值检查结果。
- `lesson.voiced.json`：保留输入画面字段，补入各镜头 `audio_file`、`audio_duration_seconds`、`duration_seconds`、`subtitle_events`。

时间单位均为秒，字幕事件相对当前镜头开始。`audio_duration_seconds` 为实测音频长度；`duration_seconds` 为未添加尾停留的镜头基础时长，取输入值与音频长度的较大者。`audio_file` 相对输出配置所在目录解析。

前一句的 `end` 等于下一句的 `start`，句间不会出现空字幕。最后一句在音频侧结束于音轨尾；渲染器将其延续至整镜头末。渲染器统一增加 `video.tail_seconds`（默认 0.35 秒）并向整帧取整，不要在配音脚本里重复加尾停留。

## 离线复用

为每个 `narration_parts` 添加 `source_audio`，指向已有本地分句音频，相对路径仍以 `lesson.json` 所在目录为基准，也可使用绝对路径。使用新的工作目录或镜头 ID，避免源文件与本次生成的输出文件同名。

```json
{
  "text": "先看这朵花的开合。",
  "subtitle_lines": ["先看这朵花的开合。"],
  "source_audio": "source_audio/sentence_01.wav"
}
```

```sh
python <SKILL_DIR>/scripts/synthesize_voice.py --config <WORK_DIR>/lesson.json --reuse-audio --validate-only
python <SKILL_DIR>/scripts/synthesize_voice.py --config <WORK_DIR>/lesson.json --reuse-audio
```

此模式只读取本地音频，由 FFmpeg 统一格式并重新生成合并音轨和字幕时间，不联网，也不导入 `edge_tts`。清单的 `provider` 标为已有本地音频；配置中的预设音色不作为这些源音频实际音色的证明。打包 skill 时只带脚本和说明，不带依赖缓存、用户录音或生成的大量音频。
