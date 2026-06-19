"""
世界杯资讯报告 — 主入口

编排全流程：
  1. 从 ESPN API 抓取比赛数据
  2. AI 生成中文战报
  3. 飞书推送世界杯卡片
"""
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from src.worldcup.espn_fetcher import fetch_match_data
from src.worldcup.summarizer import generate_match_report
from src.delivery.feishu import send_worldcup_report

BEIJING_TZ = timezone(timedelta(hours=8))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("worldcup")


async def run_pipeline() -> bool:
    """执行世界杯资讯管线。"""
    logger.info("=" * 40)
    logger.info("⚽ 世界杯资讯报告 — 开始运行")
    logger.info("=" * 40)

    try:
        # Step 1: 抓取比赛数据
        match_data = await fetch_match_data()

        total = len(match_data.get("completed", [])) + \
                len(match_data.get("live", [])) + \
                len(match_data.get("upcoming", []))
        if total == 0:
            logger.info("今日无世界杯比赛")
            return True

        # Step 2: AI 生成战报
        logger.info(f"开始 AI 生成战报 ({total} 场比赛)...")
        report = await generate_match_report(match_data)
        report["last_updated"] = match_data.get("last_updated", "")

        logger.info(f"战报生成完成: {len(report.get('matches', []))} 场比赛")

        # Step 3: 飞书推送
        success = await send_worldcup_report(report)
        if success:
            logger.info("✅ 世界杯战报推送成功！")
        else:
            logger.warning("⚠️ 世界杯推送未成功")

        _print_summary(report)
        return success

    except Exception as e:
        logger.error(f"❌ 世界杯流水线失败: {e}", exc_info=True)
        return False


def _print_summary(report: dict) -> None:
    """日志打印摘要。"""
    matches = report.get("matches", [])
    completed = [m for m in matches if m.get("status") == "completed"]
    live = [m for m in matches if m.get("status") == "live"]
    upcoming = [m for m in matches if m.get("status") == "upcoming"]

    print("\n" + "=" * 50)
    print(f"⚽ 世界杯日报 | {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    if completed:
        print(f"\n🏁 赛果 ({len(completed)}):")
        for m in completed:
            print(f"  {m.get('home_flag','')} {m['home_team']} {m.get('home_score','-')}-{m.get('away_score','-')} {m['away_team']} {m.get('away_flag','')}")

    if live:
        print(f"\n🔴 进行中 ({len(live)}):")
        for m in live:
            print(f"  {m['home_team']} {m.get('home_score','-')}-{m.get('away_score','-')} {m['away_team']} ({m.get('match_clock','')})")

    if upcoming:
        print(f"\n📅 预告 ({len(upcoming)}):")
        for m in upcoming:
            print(f"  {m.get('start_time','')} {m['home_team']} vs {m['away_team']}")

    note = report.get("editor_note", "")
    if note:
        print(f"\n💡 {note}")
    print("=" * 50)


def main():
    success = asyncio.run(run_pipeline())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
