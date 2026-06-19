"""
全局配置管理 — 从环境变量读取，集中管理所有参数。
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ── API Keys ──────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")

# ── 新闻处理参数 ──────────────────────────────────────
MAX_NEWS_COUNT = int(os.getenv("MAX_NEWS_COUNT", "20"))
MAX_ITEMS_PER_SOURCE = 8  # 每个源最多取多少条

# ── 去重参数 ──────────────────────────────────────────
DEDUP_SIMILARITY_THRESHOLD = 0.65  # 标题相似度阈值 (0-1)

# ── RSS 信息源配置 ────────────────────────────────────
RSS_SOURCES = [
    {
        "name": "36氪",
        "url": "https://36kr.com/feed",
        "category": "finance",  # 预设分类提示
    },
    {
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage",
        "category": "tech",
    },
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "category": "tech",
    },
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
        "category": "ai",
    },
    {
        "name": "ArXiv CS.AI",
        "url": "http://export.arxiv.org/rss/cs.AI",
        "category": "ai",
    },
    {
        "name": "MarketWatch",
        "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "category": "markets",
    },
    {
        "name": "CNBC Tech",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "category": "finance",
    },
]

# ── Reddit 社区配置 ────────────────────────────────────
REDDIT_SOURCES = [
    {
        "name": "r/MachineLearning",
        "url": "https://old.reddit.com/r/MachineLearning/hot.json?limit=10",
        "category": "ai",
    },
    {
        "name": "r/investing",
        "url": "https://old.reddit.com/r/investing/hot.json?limit=10",
        "category": "finance",
    },
    {
        "name": "r/wallstreetbets",
        "url": "https://old.reddit.com/r/wallstreetbets/hot.json?limit=10",
        "category": "markets",
    },
]

# ── AI 摘要 Prompt ─────────────────────────────────────
SUMMARIZE_SYSTEM_PROMPT = """你是一位资深的每日新闻编辑，精通 AI、金融和资本市场。你的任务是将一批新闻文章处理成高质量的中文每日简报。

## 要求
1. 为每篇文章写 2-3 句中文摘要，抓住核心要点
2. 提取关键数据（如涨跌幅、融资金额、技术指标、政策变动等），若无关键数据则填 null
3. 将每篇文章分类到以下三个类别之一：
   - "ai": 🤖 AI & 科技 — 人工智能、前沿科技、学术论文
   - "finance": 💰 金融 & 宏观 — 货币政策、经济数据、行业趋势
   - "markets": 📈 资本市场 — 股市、债市、大宗商品、加密货币
4. 按重要性评分 (1-10)，只返回评分 >= 6 的新闻
5. 忽略低质量的、纯广告性质的内容

## 输出格式
请严格按照以下 JSON 格式输出，只输出 JSON，不要输出其他内容：
{
  "briefings": [
    {
      "title": "原文标题（翻译为中文）",
      "summary": "2-3句中文字摘要",
      "category": "ai|finance|markets",
      "key_data": "关键数据描述，如无可填 null",
      "importance": 8,
      "source_name": "信息来源名称",
      "source_url": "原文链接"
    }
  ],
  "editor_note": "一句话总结今日最重要的趋势"
}"""
