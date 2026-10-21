"""横浜の今日の天気（Open-Meteo・無料・キー不要）を JSON で出す。台本づくりに使う。

  python -X utf8 tools/weather.py            # 今日
"""
import json, urllib.request, datetime

URL = ('https://api.open-meteo.com/v1/forecast?latitude=35.4437&longitude=139.6380&timezone=Asia%2FTokyo&forecast_days=1'
       '&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max'
       '&hourly=precipitation_probability')
CODE = {0: '快晴', 1: '晴れ', 2: '晴れときどきくもり', 3: 'くもり', 45: '霧', 48: '霧', 51: '霧雨', 53: '霧雨', 55: '霧雨',
        61: '小雨', 63: '雨', 65: '強い雨', 71: '小雪', 73: '雪', 75: '大雪', 80: 'にわか雨', 81: 'にわか雨', 82: '激しいにわか雨',
        95: '雷雨', 96: '雷雨', 99: '雷雨'}


def main():
    d = json.loads(urllib.request.urlopen(URL, timeout=30).read())
    dl = d['daily']
    hp = d['hourly']['precipitation_probability']
    rainy = [i for i, p in enumerate(hp) if p is not None and p >= 50]
    code = dl['weather_code'][0]
    # 雨・雪の記号なのに降水確率が低いときは、確率のほうを信じる
    if code >= 51 and (dl['precipitation_probability_max'][0] or 0) < 30: code = 3
    out = {
        'date': dl['time'][0], 'place': '横浜',
        'weather': CODE.get(code, 'くもり'),
        'max': round(dl['temperature_2m_max'][0]), 'min': round(dl['temperature_2m_min'][0]),
        'rainChance': dl['precipitation_probability_max'][0],
        'rainHours': f'{rainy[0]}時〜{rainy[-1] + 1}時' if rainy else '',
        'windMax': round(dl['wind_speed_10m_max'][0] / 3.6, 1),  # m/s
        'source': 'Open-Meteo'
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
