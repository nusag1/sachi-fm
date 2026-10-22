"""幸FM：できた MP3 を公開する。

  python -X utf8 tools/publish.py scripts/2026-10-22.json out/sachi-fm-2026-10-22.mp3 <秒数>

- MP3 は GitHub のリリース（nusag1/sachi-fm、タグ fm-<日付>）に置く（リポジトリが重くならない）
- docs/episodes.json に足して、docs/feed.xml（Podcast アプリ用）と docs/index.html（ブラウザで聴くページ）を作り直し、push する
- feed は itunes:block で Apple の検索には出さない（URL を知っている人だけ）
"""
import json, sys, subprocess, datetime, html
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
REPO = 'nusag1/sachi-fm'
SITE = 'https://nusag1.github.io/sachi-fm/'
KEEP = 30  # feed に載せる回数（古いリリースは消さずに残す）
WD = '月火水木金土日'


def run(*a, **k):
    return subprocess.run(a, check=True, text=True, capture_output=True, cwd=ROOT, **k)


def notes_html(ep):
    h = f"<p>{html.escape(ep['summary'])}</p>"
    if ep.get('chapters'):
        h += '<ul>' + ''.join(f'<li>{html.escape(c)}</li>' for c in ep['chapters']) + '</ul>'
    if ep.get('sources'):
        h += '<p>出てきた話題</p><ul>' + ''.join(f'<li><a href="{html.escape(s["url"])}">{html.escape(s["title"])}</a></li>' for s in ep['sources']) + '</ul>'
    h += f"<p>{html.escape(ep['credit'])}</p>"
    return h


def feed(eps):
    items = []
    for e in eps[:KEEP]:
        dt = datetime.datetime.fromisoformat(e['date'] + 'T06:30:00+09:00')
        items.append(f"""  <item>
   <title>{html.escape(e['title'])}</title>
   <description><![CDATA[{notes_html(e)}]]></description>
   <pubDate>{format_datetime(dt)}</pubDate>
   <enclosure url="{html.escape(e['url'])}" length="{e['bytes']}" type="audio/mpeg"/>
   <guid isPermaLink="false">sachi-fm-{e['date']}</guid>
   <itunes:duration>{e['seconds']}</itunes:duration>
   <itunes:explicit>false</itunes:explicit>
  </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
 <channel>
  <title>幸FM</title>
  <link>{SITE}</link>
  <atom:link href="{SITE}feed.xml" rel="self" type="application/rss+xml"/>
  <description>通学のおともに、毎朝10分（または20分）。2人の幸が、今日のニュース・天気・基本情報の1問・今日のインプットを話します。日曜は1週間のふり返り回。</description>
  <language>ja</language>
  <itunes:author>幸</itunes:author>
  <itunes:image href="{SITE}cover.png"/>
  <itunes:category text="Education"/>
  <itunes:explicit>false</itunes:explicit>
  <itunes:block>Yes</itunes:block>
  <itunes:type>episodic</itunes:type>
{chr(10).join(items)}
 </channel>
</rss>
"""


def page(eps):
    rows = []
    for e in eps[:KEEP]:
        rows.append(f"""<article class="ep">
  <div class="d">{html.escape(e['title'])}</div>
  <audio controls preload="none" src="{html.escape(e['url'])}"></audio>
  <details><summary>この回の内容</summary>{notes_html(e)}</details>
</article>""")
    tpl = (DOCS / 'template.html').read_text(encoding='utf-8')
    return tpl.replace('{{EPISODES}}', '\n'.join(rows) or '<p class="muted">まだ放送はありません。</p>').replace('{{FEED}}', SITE + 'feed.xml')


def main():
    if len(sys.argv) < 4: sys.exit(__doc__)
    script = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    mp3 = Path(sys.argv[2]); secs = int(sys.argv[3])
    date = script['date']; tag = 'fm-' + date
    credit = sorted({l['s'] for l in script['lines'] if 's' in l})
    voices = json.loads((ROOT / 'tools' / 'voices.json').read_text(encoding='utf-8'))
    credit = '声：' + '、'.join('VOICEVOX:' + voices[s]['name'] for s in credit)
    exists = subprocess.run(['gh', 'release', 'view', tag, '--repo', REPO], capture_output=True).returncode == 0
    if exists: run('gh', 'release', 'upload', tag, str(mp3), '--clobber', '--repo', REPO)
    else: run('gh', 'release', 'create', tag, str(mp3), '--repo', REPO, '--title', script['title'], '--notes', script['summary'] + '\n\n' + credit)
    url = f'https://github.com/{REPO}/releases/download/{tag}/{mp3.name}'
    eps_p = DOCS / 'episodes.json'
    eps = json.loads(eps_p.read_text(encoding='utf-8')) if eps_p.exists() else []
    eps = [e for e in eps if e['date'] != date]
    eps.insert(0, {'date': date, 'title': script['title'], 'summary': script['summary'], 'chapters': script.get('chapters', []), 'sources': script.get('sources', []),
                   'url': url, 'bytes': mp3.stat().st_size, 'seconds': secs, 'credit': credit})
    eps.sort(key=lambda e: e['date'], reverse=True)
    eps_p.write_text(json.dumps(eps, ensure_ascii=False, indent=1), encoding='utf-8')
    (DOCS / 'feed.xml').write_text(feed(eps), encoding='utf-8')
    (DOCS / 'index.html').write_text(page(eps), encoding='utf-8')
    run('git', 'add', 'docs', 'scripts')
    run('git', 'commit', '-m', f'幸FM {date}')
    run('git', 'push', '-q')
    print(json.dumps({'tag': tag, 'url': url, 'episodes': len(eps)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
