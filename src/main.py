"""
每日资讯 AI 助手 — 主入口

编排全流程：
  1. 并行抓取 RSS + Reddit 信息源
  2. 合并 & 去重
  3. AI 摘要处理
  4. 飞书推送
"""
import sys
import os

# Windows 编码兼容：强制 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import asyncio
import logging
import sys
import time
from typing import List, Dict, Any

from src.config import (
    RSS_SOURCES,
    REDDIT_SOURCES,
    MAX_ITEMS_PER_SOURCE,
    DEDUP_SIMILARITY_THRESHOLD,
)
from src.fetchers.rss_fetcher import fetch_rss_source
from src.fetchers.social_fetcher import fetch_reddit_source
from src.processor import deduplicate, summarize_articles
from src.delivery import send_report

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("news-ai")


async def fetch_all_sources() -> List[Dict[str, Any]]:
    """并行抓取所有信息源，返回合并后的文章列表。"""
    tasks = []

    # RSS 源
    for source in RSS_SOURCES:
        tasks.append(fetch_rss_source(source, max_items=MAX_ITEMS_PER_SOURCE))

    # Reddit 源
    for source in REDDIT_SOURCES:
        tasks.append(fetch_reddit_source(source, max_items=MAX_ITEMS_PER_SOURCE))

    logger.info(f"开始抓取 {len(tasks)} 个信息源...")
    start_time = time.time()

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_articles: List[Dict[str, Any]] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"信息源 {i} 抓取异常: {result}")
        elif isinstance(result, list):
            all_articles.extend(result)

    elapsed = time.time() - start_time
    logger.info(f"抓取完成: 共 {len(all_articles)} 篇文章，耗时 {elapsed:.1f}s")
    return all_articles


async def run_pipeline() -> bool:
    """执行完整管线。"""
    logger.info("=" * 40)
    logger.info("每日资讯 AI 助手 — 开始运行")
    logger.info("=" * 40)

    try:
        # Step 1: 抓取
        articles = await fetch_all_sources()
        if not articles:
            logger.error("未抓取到任何文章，流程终止")
            return False

        # Step 2: 去重
        unique_articles = deduplicate(articles, threshold=DEDUP_SIMILARITY_THRESHOLD)

        # Step 3: AI 处理
        logger.info(f"开始 AI 处理 {len(unique_articles)} 篇文章...")
        report = await summarize_articles(unique_articles)
        logger.info(f"AI 处理完成: 生成 {len(report.get('briefings', []))} 条简报")

        # Step 4: 飞书推送
        success = await send_report(report)
        if success:
            logger.info("✅ 每日资讯推送成功！")
        else:
            logger.warning("⚠️ 飞书推送未成功，请检查 Webhook 配置")

        # 打印简报摘要到日志
        _print_summary(report)

        return success

    except Exception as e:
        logger.error(f"❌ 流水线执行失败: {e}", exc_info=True)
        return False


def _print_summary(report: Dict[str, Any]) -> None:
    """在日志中打印简报摘要。"""
    briefings = report.get("briefings", [])
    editor_note = report.get("editor_note", "")

    print("\n" + "=" * 50)
    print("📰 今日简报摘要")
    print("=" * 50)

    cat_names = {"ai": "🤖 AI & 科技", "finance": "💰 金融 & 宏观", "markets": "📈 资本市场"}
    for cat_key, cat_label in cat_names.items():
        items = [b for b in briefings if b.get("category") == cat_key]
        if items:
            print(f"\n{cat_label} ({len(items)}):")
            for item in items:
                print(f"  ⭐{item.get('importance', '?')} {item.get('title', '')}")
                key_data = item.get("key_data")
                if key_data and key_data != "null":
                    print(f"       📊 {key_data}")

    if editor_note:
        print(f"\n💡 {editor_note}")

    print("=" * 50)


def main():
    """CLI 入口点。"""
    success = asyncio.run(run_pipeline())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
