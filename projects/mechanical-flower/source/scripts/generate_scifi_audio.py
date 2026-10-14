"""Original sci-fi sound design, synchronized to the 393-frame mechanical flower."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import wave
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "generated_audio"
OUT.mkdir(parents=True, exist_ok=True)
INPUTS = ROOT / "assets/audio/sources"
SR, N = 48000, 786000
DURATION = N / SR
T = np.arange(N) / SR
RNG = np.random.default_rng(6019366)
CUES = []


def smooth(a, b, t):
    u = np.clip((t - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


def flight_gate(t):
    return (smooth(.62, 1.65, t) * (1 - smooth(9.75, 10.08, t))
            + smooth(13.15, 13.95, t)) * (1 - smooth(15.45, 16.375, t))


def envelope(n, attack=.012, release=.04):
    result = np.ones(n)
    a, r = min(round(SR * attack), n // 2), min(round(SR * release), n // 2)
    result[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    result[-r:] = np.sin(np.linspace(np.pi / 2, 0, r)) ** 2
    return result


def noise(n, low, high):
    frequencies = np.fft.rfftfreq(n, 1 / SR)
    band = (1 - np.exp(-(frequencies / low) ** 4)) * np.exp(-(frequencies / high) ** 4)
    signal = np.fft.irfft(np.fft.rfft(RNG.standard_normal(n)) * band, n=n)
    return signal / max(np.std(signal), 1e-9)


def read_wav(path):
    with wave.open(str(path), "rb") as source:
        assert source.getframerate() == SR and source.getnchannels() == 2
        assert source.getsampwidth() == 2 and source.getnframes() == N
        return np.frombuffer(source.readframes(N), "<i2").reshape(-1, 2).astype(np.float64) / 32768


def add(track, start, signal, gain=1, pan=0):
    index = round(start * SR)
    a, b = max(0, index), min(N, index + len(signal))
    if b > a:
        angle = (pan + 1) * np.pi / 4
        track[a:b] += signal[a - index:b - index, None] * gain * np.array([np.cos(angle), np.sin(angle)])


def sweep(duration, f0, f1, energy=.4, falling=False):
    n = round(duration * SR)
    t = np.arange(n) / SR
    u = t / duration
    bend = smooth(0, 1, u)
    f = f0 + (f1 - f0) * bend + 4.2 * np.sin(2 * np.pi * 13.7 * t)
    phase = np.cumsum(f) * 2 * np.pi / SR
    mod = 2 * np.pi * (41 * t + 8 * t * t / duration)
    field = np.sin(phase + (.58 + .29 * np.sin(np.pi * u)) * np.sin(mod))
    field += .19 * np.sin(phase * 2.17 + .21 * np.sin(mod * .67))
    air = noise(n, 160, 3600)
    sheen = noise(n, 800, 5900)
    form = np.sin(np.pi * np.clip(u, 0, 1)) ** (.72 if falling else .92)
    x = (field * energy + air * .45 + sheen * .13 * u) * form
    return x * envelope(n, .019, .045)


def lock_pulse(duration=.16, pitch=650):
    n = round(duration * SR)
    t = np.arange(n) / SR
    phase = 2 * np.pi * (pitch * t - pitch * .34 * t * t / duration)
    resonant = np.sin(phase + .58 * np.sin(2 * np.pi * 82 * t))
    resonant += .21 * np.sin(phase * 1.63)
    x = resonant * .36 * np.exp(-t * 30) + noise(n, 300, 3700) * .39 * np.exp(-t * 56)
    return x * envelope(n, .003, .04)


source_paths = {
    "glass_air": INPUTS / "A_glass_air_wings.wav",
    "organic_flutter": INPUTS / "C_organic_flutter_wings.wav",
    "petals": INPUTS / "02_petal_mechanism.wav",
    "dock_charge": INPUTS / "03_dock_and_charge.wav",
}
stems = {
    "Wing_SciFi": read_wav(source_paths["glass_air"]) * .43 + read_wav(source_paths["organic_flutter"]) * .36,
    "Petals_SciFi": read_wav(source_paths["petals"]) * .43,
    "Charge_Dock_SciFi": read_wav(source_paths["dock_charge"]) * .45,
}

# Magnetic suspension layer: drifting FM harmonics, asymmetric 3.6 Hz pulses,
# and textured air. The modulation never forms an uninterrupted monotone hum.
near = np.interp(T, [0, 1.55, 3.65, 5.3, 6.65, 10.08, 13.15, 14.6, 16.375],
                 [.5, .75, .70, .86, 1, 1, 1, .90, .42])
pan = np.interp(T, [0, 1.55, 3.65, 5.3, 6.65, 15.45, 16.375], [-.45, -.28, .30, -.27, 0, .06, .17])
knots = np.arange(0, DURATION + .22, .22)
drift = np.interp(T, knots, RNG.uniform(-1, 1, len(knots)))
takeoff = smooth(14.05, 14.65, T) * (1 - smooth(15.0, 16.375, T))
brake = smooth(9.50, 10.08, T) * (1 - smooth(10.08, 10.10, T))
base_frequency = 174 + 11 * np.sin(2 * np.pi * .31 * T) + 8 * drift + 43 * takeoff - 25 * brake
phase = np.cumsum(base_frequency) * 2 * np.pi / SR
mod_phase = np.cumsum(36 + 5 * np.sin(2 * np.pi * .46 * T)) * 2 * np.pi / SR
for side in (-1, 1):
    wing_phase = 2 * np.pi * 3.6 * (T - (0 if side == -1 else .005))
    down = np.maximum(0, np.sin(wing_phase)) ** 1.25
    up = np.maximum(0, -np.sin(wing_phase)) ** 1.80
    pulse = .13 + .75 * down + .32 * up
    field = np.sin(phase + side * .23 + (.55 + .15 * drift) * np.sin(mod_phase + side * .41))
    field += .21 * np.sin(phase * 2.13 + .22 * np.sin(mod_phase * 1.47))
    soft_air = noise(N, 120, 2100)
    flux_air = noise(N, 650, 4300)
    sig = field * .105 * pulse + soft_air * .11 * pulse
    sig += flux_air * .055 * (.42 * down + .70 * up) * (.8 + .2 * drift)
    sig *= flight_gate(T) * near * (.88 + .12 * np.sin(2 * np.pi * .41 * T + .4)) * .18
    angle = (np.clip(pan + side * .17, -.9, .9) + 1) * np.pi / 4
    stems["Wing_SciFi"][:, 0] += sig * np.cos(angle)
    stems["Wing_SciFi"][:, 1] += sig * np.sin(angle)

# Discrete flux surges make changes of flight state audible without a music bed.
for start, duration, f0, f1, gain, stereo in (
    (.88, .65, 150, 320, .019, -.24),
    (8.12, .43, 240, 160, .012, 0),
    (13.18, .72, 105, 310, .040, -.04),
    (14.14, .66, 180, 570, .048, .06),
    (15.51, .71, 350, 110, .020, .15),
):
    add(stems["Wing_SciFi"], start, sweep(duration, f0, f1, .52, f1 < f0), gain, stereo)
CUES.extend([
    {"time": [.62, 10.08], "event": "magnetic suspension, glass air and asymmetric 3.6 Hz wing pulses"},
    {"time": [9.75, 10.08], "event": "drive energy and carrier frequency fall toward docking"},
    {"time": [13.18, 13.95], "event": "magnetic drive progressively restarts"},
    {"time": [14.14, 14.80], "event": "takeoff flux surge"},
    {"time": [15.51, 16.375], "event": "energy recedes into distance"},
])

# Petal servos get short magnetic sweeps, not sustained electronic chords.
for start, duration, closing, level in (
    (7.18, .28, True, .15), (8.53, .59, False, .65),
    (10.06, .53, True, .90), (10.81, .49, False, 1),
    (12.87, .38, True, .25), (14.10, .33, False, .22), (14.52, .43, True, .30),
):
    f0, f1 = (530, 190) if closing else (150, 480)
    for layer, stereo in enumerate((-.22, .22)):
        shift = layer * .024
        add(stems["Petals_SciFi"], start + shift,
            sweep(duration, f0 * (1 + layer * .025), f1 * (1 + layer * .025), .36, closing),
            .044 * level, stereo)
    add(stems["Petals_SciFi"], start + duration - .038, lock_pulse(.105, 590 if closing else 820),
        .025 * level, 0)
    CUES.append({"time": start, "duration": duration, "event": "magnetic petal close" if closing else "magnetic petal open"})

for start, duration, f0, f1, gain in ((8.42, .42, 330, 690, .016), (14.55, .43, 640, 240, .015)):
    add(stems["Charge_Dock_SciFi"], start, sweep(duration, f0, f1, .26), gain)
add(stems["Charge_Dock_SciFi"], 10.075, lock_pulse(.21, 470), .160)
add(stems["Charge_Dock_SciFi"], 10.12, sweep(.28, 300, 105, .30, True), .022)
add(stems["Charge_Dock_SciFi"], 13.98, lock_pulse(.145, 870), .060)
CUES.extend([
    {"time": 8.42, "duration": .42, "event": "pin extension with compact energy servo"},
    {"time": 10.075, "event": "physical contact plus magnetic energy lock"},
    {"time": 13.98, "event": "energy lock release"},
    {"time": 14.55, "duration": .43, "event": "pin retraction with descending servo"},
])

for segment in range(10):
    start = 11.38 + segment * .135
    # A common non-musical flux signature, with irregular inharmonic color rather
    # than a scale. Each pulse has a short attack and a contained soft tail.
    center = 720 + RNG.uniform(-95, 95)
    duration = RNG.uniform(.115, .143)
    n = round(duration * SR)
    local = np.arange(n) / SR
    u = local / duration
    frequency = center + 390 * np.exp(-u * 5) + 90 * u
    p = np.cumsum(frequency) * 2 * np.pi / SR
    electronic = np.sin(p + .44 * np.sin(2 * np.pi * 97 * local)) * .28
    electronic += .09 * np.sin(p * 1.47 + .22)
    texture = noise(n, 540, 3900) * .32
    pulse = (electronic + texture) * np.exp(-u * 3.5) * envelope(n, .004, .024)
    add(stems["Charge_Dock_SciFi"], start, pulse, .110 + .0020 * segment,
        .29 * np.sin(segment * 2 * np.pi / 10))
CUES.append({"time": [11.38, 12.72], "event": "ten clear, soft-edged non-musical energy-segment cues"})

for name, signal in stems.items():
    dry = signal.copy()
    for delay, gain in ((.026, .055), (.061, .028)):
        shift = round(delay * SR)
        signal[shift:] += dry[:-shift, ::-1] * gain
    signal *= envelope(N, .02, .05)[:, None]
# The flying drive must be quiet while docked; no persistent idle hum.
stems["Wing_SciFi"][round(10.30 * SR):round(13.15 * SR)] = 0


def measure(signal):
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-f", "f32le", "-ar", str(SR), "-ac", "2",
         "-i", "pipe:0", "-af", "ebur128=peak=true:framelog=verbose", "-f", "null", "-"],
        input=signal.astype("<f4").tobytes(), capture_output=True, check=True)
    summary = proc.stderr.decode("utf-8", errors="replace").split("Summary:")[-1]
    return {
        "integrated_lufs": float(re.search(r"I:\s+([-\d.]+) LUFS", summary).group(1)),
        "loudness_range_lu": float(re.search(r"LRA:\s+([-\d.]+) LU", summary).group(1)),
        "true_peak_dbfs": float(re.search(r"Peak:\s+([-\d.]+) dBFS", summary).group(1)),
        "sample_peak_dbfs": round(float(20 * np.log10(np.max(np.abs(signal)))), 3),
    }


mix = sum(stems.values())
before = measure(mix)
gain_db = min(-23.0 - before["integrated_lufs"], -3.3 - before["true_peak_dbfs"])
gain = 10 ** (gain_db / 20)
stems = {name: data * gain for name, data in stems.items()}
mix *= gain
final = measure(mix)
assert -24 <= final["integrated_lufs"] <= -22, final
assert final["true_peak_dbfs"] <= -3.0, final


def write_wav(path, signal):
    assert np.max(np.abs(signal)) < .90
    pcm = np.rint(signal * 32768).astype("<i2")
    assert np.sum(np.abs(pcm.astype(np.int32)) >= 32767) == 0
    with wave.open(str(path), "wb") as file:
        file.setnchannels(2)
        file.setsampwidth(2)
        file.setframerate(SR)
        file.writeframes(pcm.tobytes())
    with wave.open(str(path), "rb") as file:
        assert file.getnframes() == N and file.getnchannels() == 2 and file.getframerate() == SR
    return {"duration_seconds": DURATION, "sample_rate": SR, "channels": 2,
            "samples": N, "clipped_samples": 0, **measure(signal)}


files = {f"{name}.wav": write_wav(OUT / f"{name}.wav", data) for name, data in stems.items()}
files["Mix_SciFi.wav"] = write_wav(OUT / "Mix_SciFi.wav", mix)
subprocess.run(
    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(OUT / "Mix_SciFi.wav"),
     "-c:a", "libmp3lame", "-b:a", "320k", str(OUT / "Mix_SciFi_preview.mp3")], check=True)
decoded = subprocess.run(
    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(OUT / "Mix_SciFi_preview.mp3"),
     "-f", "s16le", "-acodec", "pcm_s16le", "-"], capture_output=True, check=True)
assert not decoded.stderr and len(decoded.stdout) == N * 4
report = {
    "origin": "Original procedural sci-fi sound design; uses our previous original wing and mechanical stems; no external audio or music",
    "files": files,
    "common_master_gain_db": round(gain_db, 3),
    "physical_base_gains_before_common_master": {"petals": .43, "dock_charge": .45},
    "sources": {key: {"file": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                for key, path in source_paths.items()},
    "wing_docked_rms_10_30_to_13_15": float(np.sqrt(np.mean(stems["Wing_SciFi"][round(10.30 * SR):round(13.15 * SR)] ** 2))),
    "preview_decode": {"samples": len(decoded.stdout) // 4, "seconds": len(decoded.stdout) / 4 / SR, "errors": False},
    "cues": CUES,
}
(OUT / "audio_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "README.md").write_text(
    "# 科幻机械花音效\n\n"
    "这一版以磨砂玻璃气流与柔软 flutter 为底，加入磁悬浮驱动、频率缓慢漂移的能量谐波与短促磁性锁扣。"
    "主翼拍锁定原片 3.6 Hz，上下拍强弱不同、左右翼相差约 5 ms；亮度与颗粒逐渐变化，避免固定电机包重复。"
    "原花瓣机械声音降到 43%、停靠充电声音降到 45% 后加入新科幻层，最后共用同一母线增益。没有旋律或音乐。\n\n"
    "- `Mix_SciFi.wav`：最终完整混音。\n"
    "- `Mix_SciFi_preview.mp3`：同一混音的完整 16.375 秒试听。\n"
    "- `Wing_SciFi.wav`：玻璃空气、磁悬浮振翅、重启及起飞能量。\n"
    "- `Petals_SciFi.wav`：物理花瓣机构与短促磁性伺服。\n"
    "- `Charge_Dock_SciFi.wav`：接触、能量锁、分段充电与探针。\n\n"
    "三个 WAV 分轨使用同一增益，叠加可还原最终混音。全部 48 kHz / 立体声 / 16-bit PCM，16.375 秒，对应 24 fps、393 帧。\n\n"
    "| 时间（秒） | 声音 |\n|---|---|\n"
    "| 0.62–1.65 | 轻盈飞入，磁悬浮能量逐步建立 |\n"
    "| 1.65–9.75 | 3.6 Hz 空气翼拍、缓慢变化的能量谐波 |\n"
    "| 8.42–8.85 | 伸针能量伺服 |\n"
    "| 8.53–9.15 | 花瓣磁性展开 |\n"
    "| 9.75–10.08 | 能量减弱，停靠刹停 |\n"
    "| 10.075 | 物理接触与低柔能量锁扣 |\n"
    "| 10.06–10.62；10.81–11.32 | 磁性花瓣关闭／展开 |\n"
    "| 10.30–13.15 | 翼声完全留白 |\n"
    "| 11.38–12.72 | 十段能量提示，清楚但不过尖锐 |\n"
    "| 13.15–13.95 | 驱动逐渐重启 |\n"
    "| 13.98；14.14–14.80 | 解锁与起飞增能 |\n"
    "| 14.55–14.98 | 收针伺服 |\n"
    "| 15.51–16.375 | 能量随离场渐远 |\n\n"
    f"最终混音综合响度 {final['integrated_lufs']:.1f} LUFS；真峰值 {final['true_peak_dbfs']:.1f} dBFS；无削波。"
    "MP3 解码长度也准确为 786000 样本／16.375 秒，无解码错误。详细测量与来源校验见 `audio_validation.json`。\n"
    "原始生成脚本：`scripts/generate_scifi_audio.py`。\n", encoding="utf-8")
print(json.dumps({"files": files, "common_master_gain_db": gain_db}, indent=2))
