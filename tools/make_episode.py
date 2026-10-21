"""幸FM：台本（JSON）から1回分の MP3 を作る。

  python -X utf8 tools/make_episode.py scripts/2026-10-22.json out/        # out/sachi-fm-2026-10-22.mp3

- 声は VOICEVOX ENGINE（~/tools/windows-cpu/run.exe）。動いていなければ、この中で起こして、終わったら止める
- MP3 は ffmpeg（~/tools/ffmpeg-*/bin/ffmpeg.exe）。ポッドキャストの音量（-16 LUFS）にそろえる
- 台本の形は 台本の書き方.md
"""
import json, sys, io, math, struct, wave, time, subprocess, urllib.request, urllib.parse, glob, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
VOICES = json.loads((HERE / 'voices.json').read_text(encoding='utf-8'))
HOME = Path.home()
ENGINE_DIR = Path(os.environ.get('VOICEVOX_DIR', HOME / 'tools' / 'windows-cpu'))
FFMPEG = next(iter(sorted(glob.glob(str(HOME / 'tools' / 'ffmpeg-*' / 'bin' / 'ffmpeg.exe')))), 'ffmpeg')
API = 'http://127.0.0.1:50021'
RATE = 24000


def http(path, data=None, method='GET', timeout=120):
    req = urllib.request.Request(API + path, data=data, method=method, headers={'Content-Type': 'application/json'} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def engine_up():
    try: http('/version', timeout=3); return True
    except Exception: return False


def start_engine():
    if engine_up(): return None
    exe = ENGINE_DIR / 'run.exe'
    if not exe.exists(): sys.exit(f'VOICEVOX ENGINE が見つかりません：{exe}')
    p = subprocess.Popen([str(exe), '--host', '127.0.0.1', '--port', '50021'], cwd=str(ENGINE_DIR),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    for _ in range(180):
        if engine_up(): return p
        time.sleep(1)
    p.terminate(); sys.exit('VOICEVOX ENGINE が起動しませんでした')


def say(text, speaker, speed=1.08):
    q = json.loads(http('/audio_query?' + urllib.parse.urlencode({'text': text, 'speaker': speaker}), data=b'', method='POST'))
    q['speedScale'] = speed
    q['outputSamplingRate'] = RATE
    q['outputStereo'] = False
    q['prePhonemeLength'] = 0.05
    q['postPhonemeLength'] = 0.05
    wav = http('/synthesis?' + urllib.parse.urlencode({'speaker': speaker}), data=json.dumps(q).encode(), method='POST', timeout=600)
    with wave.open(io.BytesIO(wav)) as w:
        assert w.getframerate() == RATE and w.getnchannels() == 1 and w.getsampwidth() == 2, '想定外の WAV'
        return w.readframes(w.getnframes())


def silence(sec):
    return b'\0\0' * int(RATE * sec)


def chime(kind='open'):
    """番組のはじめと終わりの短い音（その場で作る。著作権の心配なし）"""
    notes = [659, 784, 988, 1319] if kind == 'open' else [1319, 988, 784, 659]
    out = bytearray()
    total = int(RATE * 1.6)
    buf = [0.0] * total
    for i, f in enumerate(notes):
        start = int(RATE * 0.16 * i)
        for n in range(int(RATE * 0.9)):
            t = n / RATE
            v = math.sin(2 * math.pi * f * t) * math.exp(-4.2 * t) * 0.22 + math.sin(2 * math.pi * f * 2 * t) * math.exp(-7 * t) * 0.05
            if start + n < total: buf[start + n] += v
    for v in buf: out += struct.pack('<h', int(max(-1, min(1, v)) * 32000))
    return bytes(out)


def build(script, out_dir):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    date = script['date']
    pcm = bytearray(chime('open') + silence(0.3))
    lines = script['lines']
    for i, ln in enumerate(lines):
        if ln.get('pause'):
            pcm += silence(float(ln['pause'])); continue
        v = VOICES[ln['s']]
        pcm += say(ln['t'], v['speaker'], v.get('speed', 1.08))
        pcm += silence(float(ln.get('gap', 0.35)))
        print(f'\r{i + 1}/{len(lines)}', end='', flush=True)
    print()
    pcm += silence(0.4) + chime('close') + silence(0.5)
    wav_p = out_dir / f'sachi-fm-{date}.wav'
    with wave.open(str(wav_p), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(bytes(pcm))
    mp3_p = out_dir / f'sachi-fm-{date}.mp3'
    credit = '、'.join(sorted({'VOICEVOX:' + VOICES[l['s']]['name'] for l in lines if 's' in l}))
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-i', str(wav_p), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '44100', '-ac', '1', '-b:a', '64k',
                    '-metadata', f"title={script['title']}", '-metadata', 'artist=幸FM', '-metadata', 'album=幸FM', '-metadata', f'comment={credit}', str(mp3_p)], check=True)
    wav_p.unlink()  # 中間ファイル（この中で作ったもの）
    secs = len(pcm) / 2 / RATE
    return {'mp3': str(mp3_p), 'seconds': round(secs), 'bytes': mp3_p.stat().st_size, 'credit': credit}


def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    script = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    bad = [l for l in script['lines'] if not l.get('pause') and l.get('s') not in VOICES]
    if bad: sys.exit(f'知らない話し手：{bad[0]}')
    p = start_engine()
    try:
        r = build(script, sys.argv[2])
    finally:
        if p: p.terminate()
    print(json.dumps(r, ensure_ascii=False))


if __name__ == '__main__':
    main()
