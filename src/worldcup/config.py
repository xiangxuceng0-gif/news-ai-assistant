"""
世界杯模块配置 — 数据源、分类、AI Prompt。
"""

# ── ESPN Scoreboard API ─────────────────────────────────
ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"

# ── 体育新闻 RSS（补充深度报道）─────────────────────────
SPORTS_RSS_SOURCES = [
    {
        "name": "ESPN FC",
        "url": "https://www.espn.com/espn/rss/soccer/news",
        "category": "worldcup",
    },
    {
        "name": "BBC Sport Football",
        "url": "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "category": "worldcup",
    },
]

# ── 国旗 Emoji 映射 ─────────────────────────────────────
TEAM_FLAGS = {
    "Argentina": "🇦🇷", "Brazil": "🇧🇷", "Germany": "🇩🇪", "France": "🇫🇷",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Spain": "🇪🇸", "Portugal": "🇵🇹", "Italy": "🇮🇹",
    "Netherlands": "🇳🇱", "Belgium": "🇧🇪", "Croatia": "🇭🇷",
    "Uruguay": "🇺🇾", "Mexico": "🇲🇽", "United States": "🇺🇸",
    "Canada": "🇨🇦", "Japan": "🇯🇵", "South Korea": "🇰🇷",
    "Australia": "🇦🇺", "Morocco": "🇲🇦", "Senegal": "🇸🇳",
    "Ghana": "🇬🇭", "Nigeria": "🇳🇬", "Cameroon": "🇨🇲",
    "Tunisia": "🇹🇳", "Algeria": "🇩🇿", "Egypt": "🇪🇬",
    "South Africa": "🇿🇦", "Ivory Coast": "🇨🇮",
    "Saudi Arabia": "🇸🇦", "Qatar": "🇶🇦", "Iran": "🇮🇷",
    "Denmark": "🇩🇰", "Sweden": "🇸🇪", "Norway": "🇳🇴",
    "Poland": "🇵🇱", "Ukraine": "🇺🇦", "Serbia": "🇷🇸",
    "Switzerland": "🇨🇭", "Austria": "🇦🇹", "Czechia": "🇨🇿",
    "Colombia": "🇨🇴", "Chile": "🇨🇱", "Ecuador": "🇪🇨",
    "Peru": "🇵🇪", "Paraguay": "🇵🇾", "Costa Rica": "🇨🇷",
    "Panama": "🇵🇦", "Jamaica": "🇯🇲", "Honduras": "🇭🇳",
    "New Zealand": "🇳🇿", "Iraq": "🇮🇶", "Uzbekistan": "🇺🇿",
    "Congo DR": "🇨🇩", "Curaçao": "🇨🇼", "Cape Verde": "🇨🇻",
    "Bosnia-Herzegovina": "🇧🇦", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "Russia": "🇷🇺", "Turkey": "🇹🇷",
    "Greece": "🇬🇷", "Ireland": "🇮🇪", "Slovakia": "🇸🇰",
    "Hungary": "🇭🇺", "Romania": "🇷🇴", "Bulgaria": "🇧🇬",
    "Finland": "🇫🇮", "Iceland": "🇮🇸", "Slovenia": "🇸🇮",
    "Venezuela": "🇻🇪", "Bolivia": "🇧🇴",
}

# ── AI 战报生成 Prompt ──────────────────────────────────
WORLDCUP_SYSTEM_PROMPT = """你是一位资深的中文足球评论员，为 ESPN 和 BBC 供稿。你的任务是根据提供的世界杯比赛数据，生成简洁有力的中文赛事报告。

## 要求
1. 为每场已结束的比赛写 1-2 句战报（提及关键球员、比分、精彩瞬间）
2. 标注焦点赛事（强强对话、冷门、纪录被打破、帽子戏法等）
3. 为进行中的比赛标注当前状态
4. 一句话总结本轮/今日最重要的看点
5. 语言风格：简洁、专业、有激情

## 输出格式（严格 JSON）
{
  "matches": [
    {
      "home_team": "球队名",
      "away_team": "球队名",
      "home_score": 比分,
      "away_score": 比分,
      "status": "completed|live|upcoming",
      "match_summary": "1-2句中文字战报",
      "star_player": "最佳球员或 null",
      "key_moment": "关键时刻描述或 null",
      "group": "小组名"
    }
  ],
  "editor_note": "一句话总结"
}"""

# 每批次处理的最大比赛数
MAX_MATCHES_PER_BATCH = 10
