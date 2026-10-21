# 幸FM

白さんの通学のおともに、毎朝10分のラジオ。2人の幸（ひなた・みお）が、横浜の天気・ニュース3本・基本情報の1問・今日のインプットを話す。

- 聴く：https://nusag1.github.io/sachi-fm/ ／ Podcast アプリ：https://nusag1.github.io/sachi-fm/feed.xml （itunes:block で検索には出さない）
- 声：VOICEVOX:春日部つむぎ（ひなた）、VOICEVOX:冥鳴ひまり（みお）。エンジンは PC3 の `~/tools/windows-cpu/run.exe`（使うときだけ起こす）
- MP3 は GitHub のリリース（タグ `fm-<日付>`）。ページと feed は `docs/`（GitHub Pages）
- 個人の情報（予定など）は入れない（2026-10-22 白さん決定）

## 毎朝（PC3 の幸）
`台本の書き方.md` のとおり `scripts/<日付>.json` を書いて：
```
python -X utf8 tools/make_episode.py scripts/<日付>.json <作業フォルダ>
python -X utf8 tools/publish.py scripts/<日付>.json <作業フォルダ>/sachi-fm-<日付>.mp3 <秒数>
```
