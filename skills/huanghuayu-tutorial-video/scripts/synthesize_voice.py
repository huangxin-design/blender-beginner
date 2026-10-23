"""Build narration and subtitle timing; importing this module never uses the network."""
import argparse
import array
import asyncio
import json
import math
import re
import subprocess
import sys
import wave
from pathlib import Path

SAMPLE_RATE = 48000
DEFAULTS = {'voice': 'zh-CN-XiaoxiaoNeural', 'rate': '+12%', 'pitch': '-2Hz',
            'gap_seconds': 0.15}


def read_config(path, reuse_audio=False):
    config = json.loads(path.read_text(encoding='utf-8-sig'))
    settings = DEFAULTS | config.get('voice_settings', {})
    if not isinstance(settings['voice'], str) or not settings['voice'].strip():
        raise ValueError('voice_settings.voice must be a voice name')
    for key, pattern in [('rate', r'[+-]\d+%'), ('pitch', r'[+-]\d+Hz')]:
        if not isinstance(settings[key], str) or not re.fullmatch(pattern, settings[key]):
            raise ValueError(f'voice_settings.{key} requires a signed value, e.g. {DEFAULTS[key]}')
    gap = settings['gap_seconds']
    if not isinstance(gap, (int, float)) or not math.isfinite(gap) or gap < 0:
        raise ValueError('voice_settings.gap_seconds must be a finite nonnegative number')
    shots = config.get('shots')
    if not isinstance(shots, list) or not shots:
        raise ValueError('shots must be a nonempty list')
    seen = set()
    for shot in shots:
        shot_id = shot.get('id', '')
        if not isinstance(shot_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', shot_id) or shot_id in seen:
            raise ValueError('Each shot needs a unique filename-safe id')
        seen.add(shot_id)
        parts = shot.get('narration_parts', [])
        if not isinstance(parts, list):
            raise ValueError(f'{shot_id}: narration_parts must be a list')
        for part in parts:
            if not isinstance(part.get('text'), str) or not part['text'].strip():
                raise ValueError(f'{shot_id}: each narration part needs text')
            lines = part.get('subtitle_lines')
            if not isinstance(lines, list) or not lines or not all(isinstance(s, str) and s.strip() for s in lines):
                raise ValueError(f'{shot_id}: each narration part needs nonempty subtitle_lines')
            if reuse_audio and not (path.parent / part.get('source_audio', '')).is_file():
                raise ValueError(f'{shot_id}: --reuse-audio requires an existing source_audio for each part')
        duration = shot.get('duration_seconds', 0)
        if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration < 0:
            raise ValueError(f'{shot_id}: duration_seconds must be a finite nonnegative number')
    if reuse_audio:
        generated = set()
        for shot in shots:
            generated.add((path.parent / 'audio' / f'{shot["id"]}.wav').resolve())
            generated.update((path.parent / 'audio' / f'{shot["id"]}_part_{i:02}.wav').resolve()
                             for i in range(1, len(shot.get('narration_parts', [])) + 1))
        if any((path.parent / part['source_audio']).resolve() in generated
               for shot in shots for part in shot.get('narration_parts', [])):
            raise ValueError('source_audio overlaps generated output; use a new working directory or shot id')
    config['voice_settings'] = settings
    return config


def read_pcm(path):
    with wave.open(str(path), 'rb') as source:
        if (source.getframerate(), source.getnchannels(), source.getsampwidth()) != (SAMPLE_RATE, 1, 2):
            raise ValueError(f'Expected 48000 Hz mono PCM s16le: {path}')
        data = source.readframes(source.getnframes())
    samples = array.array('h', data)
    if sys.byteorder != 'little':
        samples.byteswap()
    peak = max((abs(s) for s in samples), default=0)
    clipped = sum(s in (-32768, 32767) for s in samples)
    if peak <= 100 or clipped:
        raise ValueError(f'Silent or clipped audio: {path}')
    return data, {'pcm_format': '48000 Hz mono s16le', 'non_silent': True,
                  'peak_dbfs': round(20 * math.log10(peak / 32768), 2), 'clipped_samples': clipped}


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


async def synthesize(config_path, config, reuse_audio=False):
    # Only explicit synthesis imports the online client. Offline reuse has no TTS dependency.
    if not reuse_audio:
        import edge_tts
    root = config_path.parent
    audio_dir = root / 'audio'
    audio_dir.mkdir(exist_ok=True)
    settings = config['voice_settings']
    gap_frames = round(settings['gap_seconds'] * SAMPLE_RATE)
    records = []
    for shot in config['shots']:
        parts = shot.get('narration_parts', [])
        if not parts:
            continue
        shot_id = shot['id']
        pcm, cues, sources = bytearray(), [], []
        for index, part in enumerate(parts, 1):
            raw = (root / part['source_audio']).resolve() if reuse_audio else audio_dir / f'{shot_id}_source_{index:02}.mp3'
            normalized = audio_dir / f'{shot_id}_part_{index:02}.wav'
            if not reuse_audio:
                await edge_tts.Communicate(part['text'], settings['voice'],
                                          rate=settings['rate'], pitch=settings['pitch']).save(str(raw))
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(raw),
                            '-af', 'loudnorm=I=-18:TP=-2:LRA=9', '-ar', str(SAMPLE_RATE),
                            '-ac', '1', '-c:a', 'pcm_s16le', str(normalized)], check=True)
            data, _ = read_pcm(normalized)
            start = len(pcm) / (2 * SAMPLE_RATE)
            pcm.extend(data)
            cues.append({'start': round(start, 6), 'end': round(len(pcm) / (2 * SAMPLE_RATE), 6),
                         'lines': part['subtitle_lines'], 'narration': part['text']})
            sources.append(str(raw) if reuse_audio else raw.relative_to(root).as_posix())
            if index < len(parts):
                pcm.extend(bytes(gap_frames * 2))
        duration = len(pcm) / (2 * SAMPLE_RATE)
        for current, following in zip(cues, cues[1:]):
            current['end'] = following['start']
        output = audio_dir / f'{shot_id}.wav'
        with wave.open(str(output), 'wb') as target:
            target.setnchannels(1)
            target.setsampwidth(2)
            target.setframerate(SAMPLE_RATE)
            target.writeframes(pcm)
        _, verification = read_pcm(output)
        shot['audio_file'] = output.relative_to(root).as_posix()
        shot['audio_duration_seconds'] = round(duration, 6)
        shot['duration_seconds'] = max(shot.get('duration_seconds', 0), round(duration, 6))
        shot['subtitle_events'] = cues
        cue_path = audio_dir / f'{shot_id}_subtitle_cues.json'
        write_json(cue_path, {'duration_seconds': round(duration, 6),
                             'gap_seconds': gap_frames / SAMPLE_RATE, 'cues': cues})
        records.append({'id': shot_id, 'file': shot['audio_file'], 'source_files': sources,
                        'narration': ''.join(p['text'] for p in parts),
                        'duration_seconds': round(duration, 6), 'subtitle_events': cues,
                        'subtitle_cues_file': cue_path.relative_to(root).as_posix(),
                        'verification': verification})
        print(f'{shot_id}: {duration:.3f}s', flush=True)
    manifest = {'schema_version': 1, 'voice_settings': settings,
                'provider': 'Existing local audio' if reuse_audio else 'Microsoft Edge online neural speech via edge-tts',
                'sample_rate': SAMPLE_RATE, 'channels': 1, 'format': 'PCM s16le WAV',
                'normalization': 'FFmpeg loudnorm I=-18 LUFS, TP=-2 dBTP, LRA=9',
                'audio_played_during_production': False, 'segments': records,
                'total_narration_seconds': round(sum(r['duration_seconds'] for r in records), 6)}
    write_json(root / 'audio_manifest.json', manifest)
    voiced_path = config_path.with_name(config_path.stem + '.voiced.json')
    write_json(voiced_path, config)
    print(f'READY {voiced_path}', flush=True)
    return voiced_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path, help='Lesson JSON; relative media paths resolve beside it')
    parser.add_argument('--validate-only', action='store_true', help='Validate configuration without network or file writes')
    parser.add_argument('--reuse-audio', action='store_true', help='Use local narration_parts[].source_audio, without network')
    args = parser.parse_args()
    path = args.config.resolve()
    config = read_config(path, args.reuse_audio)
    if args.validate_only:
        print(f'VALID {path}: {len(config["shots"])} shots; no synthesis or network')
    else:
        asyncio.run(synthesize(path, config, args.reuse_audio))


if __name__ == '__main__':
    main()
