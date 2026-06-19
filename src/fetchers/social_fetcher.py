"""
Reddit JSON API 抓取器 — 抓取热门帖子，无需 API Key。
使用 old.reddit.com JSON API，添加浏览器级请求头绕过反爬。
"""
import logging
import httpx
from typing import List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# 模拟浏览器的请求头，Reddit 对非浏览器 UA 会返回 403
REDDIT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}


async def fetch_reddit_source(source: Dict[str, Any], max_items: int = 10) -> List[Dict[str, Any]]:
    """抓取单个 Reddit 社区的热门帖子。"""
    articles = []
    name = source["name"]
    url = source["url"]
    preset_category = source.get("category", "tech")

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=REDDIT_HEADERS)
            logger.debug(f"[{name}] HTTP {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        logger.warning(f"Reddit HTTP {e.response.status_code} [{name}]: 可能需要非中国大陆 IP，GitHub Actions 正常运行")
        return articles
    except httpx.ConnectError as e:
        logger.warning(f"Reddit 连接失败 [{name}]: 可能被网络限制，GitHub Actions 正常运行")
        return articles
    except Exception as e:
        logger.warning(f"Reddit 抓取失败 [{name}]: {type(e).__name__}: {e}")
        return articles

    posts = data.get("data", {}).get("children", [])

    for post_data in posts[:max_items]:
        post = post_data.get("data", {})
        # 跳过置顶帖
        if post.get("stickied") or post.get("pinned"):
            continue

        title = post.get("title", "").strip()
        permalink = post.get("permalink", "")
        full_url = f"https://old.reddit.com{permalink}" if permalink else ""

        if not title:
            continue

        # Reddit 自文本作为摘要
        selftext = post.get("selftext", "")[:300]
        ups = post.get("ups", 0)
        num_comments = post.get("num_comments", 0)

        articles.append({
            "title": title,
            "url": full_url,
            "summary": selftext if selftext else f"{ups} 赞 | {num_comments} 评论",
            "published": datetime.fromtimestamp(
                post.get("created_utc", datetime.now(timezone.utc).timestamp()),
                tz=timezone.utc
            ).isoformat(),
            "source_name": name,
            "source_category": preset_category,
        })

    logger.info(f"[{name}] 抓取到 {len(articles)} 条帖子")
    return articles
