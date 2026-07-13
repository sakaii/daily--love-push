#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日微信自动推送 ❤️
—— 从女儿的角度，给爸爸妈妈的早安问候
"""

import sys
import os
import yaml
import requests
import random
from datetime import date, datetime, timedelta
from pathlib import Path

# =============================================
# 配置加载
# =============================================

CONFIG_PATH = Path(__file__).parent / "config.yaml"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    overrides = {
        ("robot", "webhook_url"):  "WEBHOOK_URL",
        ("weather", "city"):       "CITY",
        ("lover", "start_date"):   "START_DATE",
    }
    for (section, key), env in overrides.items():
        val = os.environ.get(env)
        if val:
            cfg[section][key] = val
    return cfg

config = load_config()

# =============================================
# 工具函数
# =============================================

def today():
    return date.today()

def days_until(target_date: date) -> int:
    return (target_date - today()).days

def calc_days_together(start_str: str) -> int:
    start = datetime.strptime(start_str, "%Y-%m-%d").date()
    return (today() - start).days

def get_next_birthday(month: int, day: int) -> date:
    this_year = today().year
    bday = date(this_year, month, day)
    return bday if bday >= today() else date(this_year + 1, month, day)

def parse_mmdd(mmdd: str):
    parts = mmdd.strip().split("-")
    return int(parts[0]), int(parts[1])


# =============================================
# 日期倒计时
# =============================================

def days_until_weekend() -> int:
    w = today().weekday()
    return 0 if w >= 5 else 5 - w

def get_next_national_day() -> date:
    year = today().year
    national = date(year, 10, 1)
    return national if national >= today() else date(year + 1, 10, 1)

SPRING_FESTIVAL_DATES = {
    2024: date(2024, 2, 10),
    2025: date(2025, 1, 29),
    2026: date(2026, 2, 17),
    2027: date(2027, 2, 6),
    2028: date(2028, 1, 26),
    2029: date(2029, 2, 13),
    2030: date(2030, 2, 3),
    2031: date(2031, 1, 23),
    2032: date(2032, 2, 11),
    2033: date(2033, 1, 31),
    2034: date(2034, 2, 19),
    2035: date(2035, 2, 8),
}

def get_next_spring_festival() -> date | None:
    year = today().year
    if year in SPRING_FESTIVAL_DATES and SPRING_FESTIVAL_DATES[year] >= today():
        return SPRING_FESTIVAL_DATES[year]
    if year + 1 in SPRING_FESTIVAL_DATES:
        return SPRING_FESTIVAL_DATES[year + 1]
    return None


# =============================================
# 天气查询（Open-Meteo · 完全免费 · 无需 API Key）
# 遂宁坐标：30.53°N, 105.57°E
# =============================================

LAT, LON = 30.53, 105.57
CITY_DISPLAY = "遂宁"

# WMO 天气代码 → 中文描述
WMO_CODES = {
    0: "☀️ 晴", 1: "🌤 晴间多云", 2: "⛅ 多云", 3: "☁️ 阴天",
    45: "🌫 雾", 48: "🌫 大雾",
    51: "🌦 毛毛雨", 53: "🌦 毛毛雨", 55: "🌦 毛毛雨",
    56: "🌦 冻雨", 57: "🌦 冻雨",
    61: "🌧 小雨", 63: "🌧 中雨", 65: "🌧 大雨",
    66: "🌧 冻雨", 67: "🌧 冻雨",
    71: "🌨 小雪", 73: "🌨 中雪", 75: "🌨 大雪",
    77: "🌨 雪粒",
    80: "🌦 阵雨", 81: "🌧 中阵雨", 82: "🌧 大阵雨",
    85: "🌨 小阵雪", 86: "🌨 大阵雪",
    95: "⛈ 雷暴", 96: "⛈ 雷暴+冰雹", 99: "⛈ 强雷暴+冰雹",
}

RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}
SNOW_CODES = {71, 73, 75, 77, 85, 86}

def get_weather():
    """获取实时天气（Open-Meteo，无需 API Key）"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
        "timezone": "Asia/Shanghai",
        "forecast_days": 1,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if "current" in data:
            curr = data["current"]
            daily = data.get("daily", {})
            code = curr.get("weather_code", 0)
            return {
                "temp":       curr.get("temperature_2m"),
                "feels_like": curr.get("apparent_temperature"),
                "humidity":   curr.get("relative_humidity_2m"),
                "text":       WMO_CODES.get(code, f"未知({code})"),
                "code":       code,
                "temp_max":   daily.get("temperature_2m_max", [None])[0],
                "temp_min":   daily.get("temperature_2m_min", [None])[0],
                "pop":        daily.get("precipitation_probability_max", [0])[0] / 100,
            }
    except Exception as e:
        print(f"获取天气失败: {e}")
    return None

def need_umbrella(w) -> bool:
    if not w:
        return False
    code = w.get("code", 0)
    if code in RAIN_CODES or code in SNOW_CODES:
        return True
    if w.get("pop", 0) >= 0.5:
        return True
    return False


# =============================================
# 组装消息（女儿视角 ❤️）
# =============================================

def build_message():
    lines = []

    # ---- 早安问候 ----
    lines.append("☀️ **早上好，爸爸妈妈！**")
    lines.append("")

    # ---- 在一起多少天 ----
    start = config["lover"]["start_date"]
    days = calc_days_together(start)
    start_display = datetime.strptime(start, "%Y-%m-%d").strftime("%Y年%m月%d日")
    lines.append(f"💕 从 {start_display} 到现在")
    lines.append(f"   爸爸妈妈已经在一起 **{days} 天** 啦！")
    lines.append("")

    # ---- 生日倒计时 ----
    birthdays = config.get("family_birthdays", [])
    if birthdays:
        lines.append("🎂 **距离家人生日：**")
        items = []
        for b in birthdays:
            m, d = parse_mmdd(b["date"])
            remain = days_until(get_next_birthday(m, d))
            label = remain == 0 and "🎉 就是今天！生日快乐！" or (remain == 1 and "明天就是啦 🎉" or (remain > 0 and f"还有 **{remain} 天**" or None))
            if label:
                items.append((remain, b["name"], label))
        items.sort(key=lambda x: x[0])
        for _, name, text in items:
            lines.append(f"   · {name}：{text}")
        lines.append("")

    # ---- 天气 ----
    w = get_weather()
    if w:
        lines.append(f"🌤 **今日天气 ({CITY_DISPLAY})**")
        lines.append(f"   天气：{w['text']}")
        lines.append(f"   温度：{w['temp']}°C（体感 {w['feels_like']}°C）")
        if w["temp_max"] is not None:
            lines.append(f"   最高：{w['temp_max']}°C  /  最低：{w['temp_min']}°C")
        lines.append("")
        lines.append("☔ **今天可能要下雨，出门记得带伞哦～**" if need_umbrella(w)
                     else "☀️ 今天不用带伞，放心出门吧～")
    else:
        lines.append("🌤 天气信息暂时获取不到，出门前看一眼窗外吧～")
    lines.append("")

    # ---- 周末倒计时 ----
    wd = days_until_weekend()
    weekdays_cn = ["一", "二", "三", "四", "五", "六", "日"]
    tw = weekdays_cn[today().weekday()]
    if wd == 0:
        lines.append(f"🎉 今天是周六，好好享受周末吧！" if today().weekday() == 5 else "🎉 今天是周日，好好享受周末吧！")
    elif wd == 1:
        lines.append("🎉 明天就是周末啦！加油最后一天！")
    else:
        lines.append(f"📅 今天是周{tw}，距离周末还有 **{wd} 天**")
    lines.append("")

    # ---- 国庆节 ----
    nd = days_until(get_next_national_day())
    if nd == 0:
        lines.append("🇨🇳 **国庆节快乐！** 🎉")
    else:
        lines.append(f"🇨🇳 距离国庆节还有 **{nd} 天**")
    lines.append("")

    # ---- 春节 ----
    sf = get_next_spring_festival()
    if sf:
        sd = days_until(sf)
        if sd == 0:
            lines.append("🧧 **新年快乐！春节快乐！** 🎉")
        else:
            lines.append(f"🧧 距离春节还有 **{sd} 天**")
    lines.append("")

    # ---- 小情话 ----
    quotes = [
        "爸爸妈妈要一直这么幸福哦！❤️",
        "今天也是爱爸爸妈妈的一天！",
        "有爸爸妈妈的地方就是家 🏠",
        "爸爸妈妈是世界上最好的爸爸妈妈！",
        "你们是我最爱的人 💕",
        "爸爸妈妈要开开心心的哦！",
    ]
    lines.append(f"💌 {random.choice(quotes)}")

    return "\n".join(lines)


# =============================================
# 推送
# =============================================

def push_to_wechat(content: str):
    url = config["robot"]["webhook_url"]
    if not url:
        print("❌ 未配置 webhook_url")
        return False
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content},
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        data = resp.json()
        ok = data.get("errcode") == 0
        print("✅ 推送成功！" if ok else f"❌ 推送失败: {data}")
        return ok
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


# =============================================
# 主函数
# =============================================

def main():
    print("=" * 40)
    print("❤️  每日早安推送（女儿视角）")
    print(f"📅  {today()}")
    print("=" * 40)

    message = build_message()
    print("\n" + message + "\n")

    success = push_to_wechat(message)
    print("\n✅ 完成！" if success else "\n❌ 失败")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
