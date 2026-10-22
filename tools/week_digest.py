"""幸FM：日曜のふり返り回のための、その週（月〜土）の台本のまとめを出す。
台本を全部読み直さずにすむように、題・章・見出し・基本情報の1問だけを短く並べる。
使い方：python -X utf8 tools/week_digest.py <日曜の日付 YYYY-MM-DD>
"""
import json, os, sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sun = date.fromisoformat(sys.argv[1])
out = []
for i in range(6, 0, -1):
    d = sun - timedelta(days=i)
    p = os.path.join(HERE, 'scripts', f'{d}.json')
    if not os.path.exists(p):
        out.append(f'## {d}（なし）')
        continue
    s = json.load(open(p, encoding='utf-8'))
    out.append(f"## {d} {s.get('title', '')}")
    out.append('章：' + ' / '.join(s.get('chapters', [])))
    for src in s.get('sources', []):
        out.append('見出し：' + src['title'])
    qs = s.get('quiz') or []
    for q in (qs if isinstance(qs, list) else [qs]):
        ch = '　'.join(f'{k}、{c}' for k, c in zip('アイウエ', q['choices']))
        out.append(f"基本情報（{q['cat']}）：{q['q']}　{ch}　正解{q['a']}：{q['ex']}")
print('\n'.join(out))
