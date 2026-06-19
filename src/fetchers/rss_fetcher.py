"""
RSS 抓取器 — 基于 feedparser 的通用 RSS/Atom 源抓取。
"""
import logging
import feedparser
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


async def fetch_rss_source(source: Dict[str, Any], max_items: int = 8) -> List[Dict[str, Any]]:
    """抓取单个 RSS 源，返回标准化文章列表。"""
    articles = []
    name = source["name"]
    url = source["url"]
    preset_category = source.get("category", "tech")

    try:
        # 使用 httpx 先获取内容，有些源 feedparser 直接解析会失败
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0; +https://github.com/news-ai-assistant)"
            })
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
    except Exception as e:
        logger.warning(f"RSS 抓取失败 [{name}]: {e}")
        return articles

    if feed.bozo:
        logger.warning(f"RSS 解析警告 [{name}]: {feed.bozo_exception}")

    for entry in feed.entries[:max_items]:
        article = {
            "title": entry.get("title", "").strip(),
            "url": entry.get("link", ""),
            "summary": _clean_html(entry.get("summary", entry.get("description", ""))),
            "published": _parse_date(entry),
            "source_name": name,
            "source_category": preset_category,
        }

        # 跳过空标题或空链接
        if not article["title"] or not article["url"]:
            continue

        articles.append(article)

    logger.info(f"[{name}] 抓取到 {len(articles)} 篇文章")
    return articles


def _clean_html(html_text: str) -> str:
    """去除 HTML 标签，返回纯文本。"""
    import re
    if not html_text:
        return ""
    clean = re.sub(r"<[^>]+>", "", html_text)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()[:500]  # 截取前 500 字符


def _parse_date(entry) -> str:
    """尝试解析文章发布时间，返回 ISO 格式字符串。"""
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)
        if parsed:
            try:
                from time import mktime
                dt = datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
                return dt.isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()
