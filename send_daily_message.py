#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日微信自动推送 ❤️
给老婆的生日礼物
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
        ("weather", "api_key"):    "WEATHER_API_KEY",
        ("weather", "city"):       "CITY",
        ("lover", "nickname"):     "NICKNAME",
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
    """距离最近周六还有几天（如果已是周末返回0）"""
    w = today().weekday()  # Mon=0, Sun=6
    if w >= 5:  # 周六日
        return 0
    return 5 - w  # 到周六的天数


def get_next_national_day() -> date:
    """下一个国庆节（10月1日）"""
    year = today().year
    national = date(year, 10, 1)
    if national < today():
        national = date(year + 1, 10, 1)
    return national


# 春节公历日期（2024-2035年）
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
    """下一个春节"""
    year = today().year
    # 先看今年春节是否还没过
    if year in SPRING_FESTIVAL_DATES and SPRING_FESTIVAL_DATES[year] >= today():
        return SPRING_FESTIVAL_DATES[year]
    # 看明年
    if year + 1 in SPRING_FESTIVAL_DATES:
        return SPRING_FESTIVAL_DATES[year + 1]
    return None


# =============================================
# 天气查询（OpenWeatherMap）
# =============================================

API_KEY = config["weather"]["api_key"]
CITY = config["weather"]["city"]

def get_weather():
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": CITY, "appid": API_KEY, "units": "metric", "lang": "zh_cn"}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("cod") == 200:
            return {
                "temp":       data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity":   data["main"]["humidity"],
                "text":       data["weather"][0]["description"],
            }
        else:
            print(f"天气API返回: {data.get('message', 'unknown')}")
    except Exception as e:
        print(f"获取天气失败: {e}")
    return None

def get_forecast():
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"q": CITY, "appid": API_KEY, "units": "metric", "lang": "zh_cn"}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("cod") == "200":
            today_entries = [d for d in data["list"]
                             if d["dt_txt"].startswith(today().isoformat())]
            if today_entries:
                pops = [d.get("pop", 0) for d in today_entries]
                temps_max = [d["main"]["temp_max"] for d in today_entries]
                temps_min = [d["main"]["temp_min"] for d in today_entries]
                return {
                    "temp_max": round(max(temps_max)),
                    "temp_min": round(min(temps_min)),
                    "pop": max(pops),
                    "texts": [d["weather"][0]["description"] for d in today_entries],
                }
    except Exception as e:
        print(f"获取预报失败: {e}")
    return None

def need_umbrella(w, f) -> bool:
    kw = ["雨", "雪", "雹", "霰", "drizzle", "rain", "snow"]
    if w:
        for k in kw:
            if k in w.get("text", ""):
                return True
    if f:
        if f.get("pop", 0) >= 0.5:
            return True
        for t in f.get("texts", []):
            for k in kw:
                if k in t:
                    return True
    return False


# =============================================
# 组装消息
# =============================================

def build_message():
    n = config["lover"]["nickname"]
    lines = []

    hour = datetime.now().hour
    greeting = "早安" if hour < 12 else ("下午好" if hour < 18 else "晚上好")
    lines.append(f"☀️ **{greeting}，{n}！**")
    lines.append("")

    # --- 在一起多少天 ---
    start = config["lover"]["start_date"]
    days = calc_days_together(start)
    start_display = datetime.strptime(start, "%Y-%m-%d").strftime("%Y年%m月%d日")
    lines.append(f"💕 从 {start_display} 到现在")
    lines.append(f"   我们已经在一起 **{days} 天** 啦！")
    lines.append("")

    # --- 生日倒计时 ---
    birthdays = config.get("family_birthdays", [])
    if birthdays:
        lines.append("🎂 **距离家人生日：**")
        items = []
        for b in birthdays:
            m, d = parse_mmdd(b["date"])
            remain = days_until(get_next_birthday(m, d))
            if remain == 0:
                items.append((0, b["name"], "🎉 就是今天！生日快乐！"))
            elif remain == 1:
                items.append((1, b["name"], "明天就是啦 🎉"))
            elif remain > 0:
                items.append((remain, b["name"], f"还有 **{remain} 天**"))
        items.sort(key=lambda x: x[0])
        for _, name, text in items:
            lines.append(f"   · {name}：{text}")
        lines.append("")

    # --- 天气 ---
    w = get_weather()
    f = get_forecast()
    if w:
        lines.append(f"🌤 **今日天气 ({CITY})**")
        lines.append(f"   天气：{w['text']}")
        lines.append(f"   温度：{w['temp']}°C（体感 {w['feels_like']}°C）")
        if f:
            lines.append(f"   最高：{f['temp_max']}°C  /  最低：{f['temp_min']}°C")
        lines.append("")
        lines.append("☔ **今天可能要下雨，记得带伞哦～**" if need_umbrella(w, f)
                     else "☀️ 今天不用带伞，放心出门吧～")
    else:
        lines.append("🌤 天气信息暂时获取不到，出门前看一眼窗外吧～")
    lines.append("")

    # --- 周末倒计时 ---
    weekend_days = days_until_weekend()
    weekdays_cn = ["一", "二", "三", "四", "五", "六", "日"]
    today_w = weekdays_cn[today().weekday()]
    if weekend_days == 0:
        lines.append(f"🎉 今天是周{today_w}，好好享受周末吧！")
    elif weekend_days == 1:
        lines.append("🎉 明天就是周末啦！加油最后一天！")
    else:
        lines.append(f"📅 今天是周{today_w}，距离周末还有 **{weekend_days} 天**")
    lines.append("")

    # --- 国庆节倒计时 ---
    national = get_next_national_day()
    nd = days_until(national)
    if nd == 0:
        lines.append("🇨🇳 **国庆节快乐！** 🎉")
    else:
        lines.append(f"🇨🇳 距离国庆节还有 **{nd} 天**")
    lines.append("")

    # --- 春节倒计时 ---
    sf = get_next_spring_festival()
    if sf:
        sd = days_until(sf)
        if sd == 0:
            lines.append("🧧 **新年快乐！春节快乐！** 🎉")
        else:
            lines.append(f"🧧 距离春节还有 **{sd} 天**")
    lines.append("")

    # --- 情话 ---
    quotes = [
        "想你的心，从早上就开始了。",
        "今天也是超喜欢你的一天。",
        "只要有你在，每天都是好天气。",
        "想牵着你的手，走过春夏秋冬。",
        "你是我遇见的所有美好里，最好的那个。",
        "没有什么比你的笑容更治愈了。",
        "今天也要开开心心的！💕",
        "每天醒来，第一件事就是想你。",
        "你永远是我最爱的人。",
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
    print("❤️  每日早安推送")
    print(f"📅  {today()}")
    print("=" * 40)

    message = build_message()
    print("\n" + message + "\n")

    success = push_to_wechat(message)
    print("\n✅ 完成！" if success else "\n❌ 失败")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
