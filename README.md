# 📰 每日资讯 AI 助手

每天自动抓取全球最新 AI、金融、资本市场资讯，经 AI 提炼后通过飞书 Bot 推送到手机。

## 功能

- **多源抓取**: RSS (36氪、Hacker News、TechCrunch、MIT Tech Review、ArXiv、Reuters) + Reddit 热门社区
- **AI 处理**: Claude 自动摘要、分类、提取关键数据、重要性评分
- **飞书推送**: 精美的交互卡片消息，按 🤖 AI / 💰 金融 / 📈 资本市场 分类展示
- **定时运行**: GitHub Actions 每天北京时间 8:00 自动执行

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 填写你的 API Key：

```env
ANTHROPIC_API_KEY=sk-ant-你的密钥
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/你的Webhook地址
```

### 3. 本地测试

```bash
python -m src.main
```

### 4. 部署到 GitHub Actions

1. Push 到 GitHub 仓库
2. 在 Settings → Secrets and variables → Actions 中添加：
   - `ANTHROPIC_API_KEY`
   - `FEISHU_WEBHOOK_URL`
3. Actions 将每天 UTC 0:00（北京时间 8:00）自动运行
4. 也可在 Actions 页面手动触发测试

## 获取 API Key

| 服务 | 地址 |
|------|------|
| Anthropic API | https://console.anthropic.com |
| 飞书机器人 Webhook | 飞书开放平台 → 创建应用 → 机器人 → 添加 Webhook |

## 项目结构

```
news-ai-assistant/
├── .github/workflows/daily-news.yml   # GitHub Actions 定时任务
├── src/
│   ├── config.py          # 配置管理
│   ├── main.py            # 主入口
│   ├── fetchers/          # 信息源抓取
│   │   ├── rss_fetcher.py
│   │   └── social_fetcher.py
│   ├── processor/         # AI 处理
│   │   ├── dedup.py
│   │   └── summarizer.py
│   └── delivery/          # 飞书推送
│       └── feishu.py
├── requirements.txt
└── .env.example
```
