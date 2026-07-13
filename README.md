# ❤️ 每日早安推送 —— 给老婆的生日礼物

每天自动在企微群发暖心消息：
- 距离家人生日还有多少天
- 已经在一起多少天
- 今天天气怎么样、需不需要带伞
- 再加一句随机情话 💕

**通过 GitHub Actions 运行，电脑不用开机！**

---

## 📱 最终效果

> ☀️ **早安，宝贝！**
>
> 💕 从 2022年1月1日 到今天
>    我们已经在一起 **1286 天** 啦！
>
> 🎂 **距离家人生日：**
>    · 老婆：还有 **28 天**
>    · 妈妈：还有 **45 天**
>    · 爸爸：还有 **67 天**
>
> 🌤 **今日天气 (北京)**
>    天气：晴  |  温度：28°C（体感 26°C）
>    最高：32°C  /  最低：22°C
>
> ☀️ 今天不用带伞，放心出门吧～
>
> 💌 想牵着你的手，走过春夏秋冬。

---

## 🚀 部署到 GitHub Actions（免开机）

### 前提条件
- 一个 **GitHub 账号**（github.com 免费注册）
- 一个 **OpenWeatherMap API Key**（免费注册：https://openweathermap.org/api）
- 一个 **企业微信群机器人 Webhook 地址**

### 第一步：上传代码到 GitHub

```bash
# 在项目目录打开终端
cd "C:\Users\苗苗的电脑\Desktop\给老婆的生日礼物"

# 初始化 git
git init
git add .
git commit -m "❤️ 每日早安推送 - 给老婆的生日礼物"

# 在 GitHub 新建一个仓库（不要勾选 README），然后 push
git remote add origin https://github.com/你的用户名/你的仓库名.git
git branch -M main
git push -u origin main
```

### 第二步：配置 Secrets（敏感信息）

在 GitHub 仓库页面 → **Settings → Secrets and variables → Actions**，添加以下仓库密钥：

| 名称 | 说明 | 示例 |
|------|------|------|
| `WEBHOOK_URL` | 企业微信群机器人完整地址 | `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx` |
| `WEATHER_API_KEY` | OpenWeatherMap API Key | `abc123def456...` |
| `CITY` | 城市名 | `北京` |
| `NICKNAME` | 称呼 | `宝贝` |
| `START_DATE` | 在一起的日子 | `2022-01-01` |

### 第三步：手动触发测试

仓库里点 **Actions → 每日早安推送 → Run workflow**，群里如果收到消息就成功了 ✅

之后每天早上 7:00（北京时间）会自动发，**电脑关机也不影响**。

---

## 🖥️ 本地测试（可选）

如果想在电脑上先跑一下看看效果：

```bash
pip install requests pyyaml
python send_daily_message.py
```

前提是 `config.yaml` 里填好了 webhook 地址和天气 Key。

---

## 📁 项目结构

```
.github/workflows/daily.yml  ← GitHub Actions 定时任务
send_daily_message.py         ← 主程序
config.yaml                   ← 非敏感配置（生日、纪念日等）
requirements.txt              ← Python 依赖
.gitignore                    ← 忽略敏感文件
README.md                     ← 本文件
```

---

**❤️ 用心做的礼物，她一定会喜欢的！**
