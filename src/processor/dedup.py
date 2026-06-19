"""
新闻去重 — 基于标题相似度进行去重，避免同一事件的多家报道重复出现。
"""
import logging
from difflib import SequenceMatcher
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def deduplicate(
    articles: List[Dict[str, Any]],
    threshold: float = 0.65,
) -> List[Dict[str, Any]]:
    """
    对文章列表按标题相似度去重。
    相似度 >= threshold 的两篇文章视为重复，保留先出现的（通常来源更优先）。
    时间复杂度 O(n²)，对于每日几十篇新闻完全可接受。
    """
    if not articles:
        return []

    kept: List[Dict[str, Any]] = []
    kept_titles: List[str] = []

    for article in articles:
        title = _normalize(article.get("title", ""))

        if not title:
            kept.append(article)
            continue

        is_duplicate = False
        for kept_title in kept_titles:
            similarity = SequenceMatcher(None, title, kept_title).ratio()
            if similarity >= threshold:
                is_duplicate = True
                logger.debug(f"去重: 「{title}」≈「{kept_title}」(相似度 {similarity:.2f})")
                break

        if not is_duplicate:
            kept.append(article)
            kept_titles.append(title)

    removed = len(articles) - len(kept)
    if removed > 0:
        logger.info(f"去重完成: {len(articles)} → {len(kept)} 篇（移除 {removed} 篇重复）")
    return kept


def _normalize(title: str) -> str:
    """标准化标题：去除常见噪声，便于比较。"""
    import re
    t = title.lower().strip()
    t = re.sub(r"^(breaking|独家|快讯|just in|update):?\s*", "", t)
    t = re.sub(r"[|｜•·「」『』【】\[\]]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t
