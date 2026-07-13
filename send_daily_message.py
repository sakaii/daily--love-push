#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日微信自动推送 ❤️
给老婆的生日礼物 —— 每天自动在企微群发暖心消息

支持本地运行（config.yaml）和 GitHub Actions（环境变量）两种模式
"""

import sys
import os
import yaml
import requests
import random
from datetime import date, datetime
from pathlib import Path

# =============================================
# 配置加载（环境变量优先，兼容 GitHub Actions）
# =============================================

CONFIG_PATH = Path(__file__).parent / "config.yaml"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # 以下环境变量会覆盖 config.yaml（GitHub Actions 时使用）
    env_overrides = {
        ("robot", "webhook_url"):          "WEBHOOK_URL",
        ("weather", "api_key"):            "WEATHER_API_KEY",
        ("weather", "city"):               "CITY",
        ("lover", "nickname"):             "NICKNAME",
        ("lover", "start_date"):           "START_DATE",
    }
    for (section, key), env_name in env_overrides.items():
        val = os.environ.get(env_name)
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
# 天气查询（OpenWeatherMap · 免费）
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
    except Exception as e:
        print(f"获取天气失败: {e}")
    return None


def get_forecast():
    """获取今天降水概率，判断是否需要带伞"""
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


def need_umbrella(now_weather, forecast) -> bool:
    rain_keywords = ["雨", "雪", "雹", "霰", "drizzle", "rain", "snow"]
    if now_weather:
        for kw in rain_keywords:
            if kw in now_weather.get("text", ""):
                return True
    if forecast:
        if forecast.get("pop", 0) >= 0.5:
            return True
        for t in forecast.get("texts", []):
            for kw in rain_keywords:
                if kw in t:
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

    # 在一起多少天
    start = config["lover"]["start_date"]
    days = calc_days_together(start)
    start_display = datetime.strptime(start, "%Y-%m-%d").strftime("%Y年%m月%d日")
    lines.append(f"💕 从 {start_display} 到今天")
    lines.append(f"   我们已经在一起 **{days} 天** 啦！")
    lines.append("")

    # 生日倒计时
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
            elif remain < 0:
                continue
            else:
                items.append((remain, b["name"], f"还有 **{remain} 天**"))
        items.sort(key=lambda x: x[0])
        for _, name, text in items:
            lines.append(f"   · {name}：{text}")
        lines.append("")

    # 天气
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

    # 随机情话
    quotes = [
        "想你的心，从早上就开始了。",
        "今天也是超喜欢你的一天。",
        "只要有你在，每天都是好天气。",
        "想牵着你的手，走过春夏秋冬。",
        "你是我遇见的所有美好里，最好的那个。",
        "没有什么比你的笑容更治愈了。",
        "你的存在，就是我每天醒来的理由。",
        "今天也要开开心心的！💕",
    ]
    lines.append(f"💌 {random.choice(quotes)}")

    return "\n".join(lines)


# =============================================
# 推送到企业微信群
# =============================================

def push_to_wechat(content: str):
    url = config["robot"]["webhook_url"]
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content},
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        result = resp.json()
        if result.get("errcode") == 0:
            print("✅ 企业微信推送成功！")
            return True
        else:
            print(f"❌ 推送失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


# =============================================
# 主函数
# =============================================

def main():
    print("=" * 40)
    print("❤️  每日自动推送")
    print(f"📅  {today()}")
    print("=" * 40)

    message = build_message()
    print("\n" + message + "\n")

    success = push_to_wechat(message)
    print("\n✅ 完成！" if success else "\n❌ 失败")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
