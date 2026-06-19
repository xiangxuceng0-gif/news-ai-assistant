"""
飞书推送 — 通过 Webhook 发送交互卡片消息到飞书群/个人。
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta

import httpx

from src.config import FEISHU_WEBHOOK_URL

logger = logging.getLogger(__name__)

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))

# 分类颜色配置
CATEGORY_CONFIG = {
    "ai": {
        "emoji": "🤖",
        "label": "AI & 科技",
        "color": "blue",
        "bg_color": "#E8F4FD",
    },
    "finance": {
        "emoji": "💰",
        "label": "金融 & 宏观",
        "color": "orange",
        "bg_color": "#FFF4E5",
    },
    "markets": {
        "emoji": "📈",
        "label": "资本市场",
        "color": "red",
        "bg_color": "#FFE8E8",
    },
}


async def send_report(report: Dict[str, Any]) -> bool:
    """
    将生成的简报发送到飞书。

    Args:
        report: summarizer 返回的报告 {"briefings": [...], "editor_note": "..."}

    Returns:
        是否发送成功
    """
    if not FEISHU_WEBHOOK_URL:
        logger.error("未设置 FEISHU_WEBHOOK_URL，跳过飞书推送")
        return False

    briefings = report.get("briefings", [])
    editor_note = report.get("editor_note", "")
    total_fetched = report.get("total_fetched", 0)

    if not briefings:
        logger.info("没有简报内容，发送空报告通知")
        return await _send_empty_report()

    # 按分类分组
    categorized = _group_by_category(briefings)

    # 构建飞书卡片
    card = _build_card(categorized, editor_note, total_fetched)

    # 发送
    success = await _send_to_feishu(card)
    return success


def _group_by_category(briefings: List[Dict]) -> Dict[str, List[Dict]]:
    """按分类分组简报。"""
    grouped: Dict[str, List[Dict]] = {"ai": [], "finance": [], "markets": []}
    for item in briefings:
        cat = item.get("category", "ai")
        if cat not in grouped:
            cat = "ai"
        grouped[cat].append(item)
    return grouped


def _build_card(
    categorized: Dict[str, List[Dict]],
    editor_note: str,
    total_fetched: int,
) -> Dict[str, Any]:
    """构建飞书交互卡片消息体。"""
    now_str = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M")
    date_str = datetime.now(BEIJING_TZ).strftime("%Y年%m月%d日")

    elements: List[Dict] = []

    # ── 标题行 ──
    total_briefings = sum(len(v) for v in categorized.values())
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"📰 **每日资讯简报 — {date_str}**\n共抓取 {total_fetched} 条资讯，精选 {total_briefings} 条",
        },
    })
    elements.append({"tag": "hr"})

    # ── 各分类内容 ──
    for cat_key in ["ai", "finance", "markets"]:
        items = categorized.get(cat_key, [])
        cfg = CATEGORY_CONFIG[cat_key]

        if not items:
            continue

        # 分类标题
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"{cfg['emoji']} **{cfg['label']}**（{len(items)} 条）",
            },
        })

        # 每条新闻
        for item in items:
            title = item.get("title", "无标题")
            summary = item.get("summary", "")
            key_data = item.get("key_data")
            source = item.get("source_name", "")
            url = item.get("source_url", "")
            importance = item.get("importance", 5)

            stars = "⭐" * min(5, max(1, importance // 2))

            md_parts = [f"**{title}**"]
            if summary:
                md_parts.append(summary)
            if key_data and key_data != "null":
                md_parts.append(f"📊 {key_data}")
            md_parts.append(f"{stars} [{source}]({url})")

            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "\n".join(md_parts),
                },
            })

        elements.append({"tag": "hr"})

    # ── 编辑点评 ──
    if editor_note:
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"💡 **今日趋势**: {editor_note}",
            },
        })
        elements.append({"tag": "hr"})

    # ── 底部信息 ──
    elements.append({
        "tag": "note",
        "elements": [
            {"tag": "plain_text", "content": f"🤖 AI 自动生成 | {now_str} | 每日 8:00 推送"},
        ],
    })

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"📰 每日资讯简报 · {date_str}",
                },
                "template": "blue",
            },
            "elements": elements,
        },
    }

    return card


async def _send_to_feishu(card: Dict[str, Any]) -> bool:
    """发送卡片到飞书 Webhook。"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                FEISHU_WEBHOOK_URL,
                json=card,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                logger.info("飞书推送成功")
                return True
            else:
                logger.error(f"飞书推送失败: {result}")
                return False
    except Exception as e:
        logger.error(f"飞书推送异常: {e}")
        return False


async def _send_empty_report() -> bool:
    """发送无新闻时的空报告。"""
    now_str = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M")
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "📰 每日资讯简报 · 无更新"},
                "template": "grey",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "今日未抓取到符合条件的新闻，请稍后重试。",
                    },
                },
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": f"🤖 AI 自动生成 | {now_str}"},
                    ],
                },
            ],
        },
    }
    return await _send_to_feishu(card)


async def send_worldcup_report(report: Dict[str, Any]) -> bool:
    """
    将世界杯战报推送到飞书。

    Args:
        report: summarizer 返回的 {"matches": [...], "editor_note": "..."}
    """
    if not FEISHU_WEBHOOK_URL:
        logger.error("未设置 FEISHU_WEBHOOK_URL")
        return False

    matches = report.get("matches", [])
    editor_note = report.get("editor_note", "")
    last_updated = report.get("last_updated", datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M"))

    if not matches:
        return await _send_to_feishu({
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": "⚽ 世界杯日报 · 今日无比赛"},
                    "template": "grey",
                },
                "elements": [{
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": "今日没有世界杯比赛安排。"},
                }],
            },
        })

    # 分类
    completed = [m for m in matches if m.get("status") == "completed"]
    live = [m for m in matches if m.get("status") == "live"]
    upcoming = [m for m in matches if m.get("status") == "upcoming"]

    date_str = datetime.now(BEIJING_TZ).strftime("%Y年%m月%d日")
    elements = []

    # ── 标题 ──
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"⚽ **2026 世界杯日报 · {date_str}**\n更新时间: {last_updated}",
        },
    })
    elements.append({"tag": "hr"})

    # ── 最新赛果 ──
    if completed:
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"🏁 **最新赛果**（{len(completed)} 场）"},
        })
        for m in completed:
            hf = m.get("home_flag", "")
            af = m.get("away_flag", "")
            group = m.get("group", "")
            summary = m.get("match_summary", "")
            star = m.get("star_player") or ""
            key = m.get("key_moment") or ""

            lines = [
                f"**{hf} {m['home_team']} {m.get('home_score', '-')} - {m.get('away_score', '-')} {m['away_team']} {af}**",
            ]
            if summary:
                lines.append(f"  {summary}")
            if star and star != "null":
                lines.append(f"  ⭐ {star}")
            if key and key != "null":
                lines.append(f"  🔥 {key}")
            if group:
                lines.append(f"  _{group}_")

            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "\n".join(lines)},
            })

        elements.append({"tag": "hr"})

    # ── 进行中 ──
    if live:
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"🔴 **进行中**（{len(live)} 场）"},
        })
        for m in live:
            hf = m.get("home_flag", "")
            af = m.get("away_flag", "")
            clock = m.get("match_clock", "")
            lines = [
                f"**{hf} {m['home_team']} {m.get('home_score', '-')} - {m.get('away_score', '-')} {m['away_team']} {af}**",
                f"  ⏱ {clock}"
            ]
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "\n".join(lines)},
            })
        elements.append({"tag": "hr"})

    # ── 赛事预告 ──
    if upcoming:
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"📅 **赛事预告**（{len(upcoming)} 场）"},
        })
        for m in upcoming[:6]:
            hf = m.get("home_flag", "")
            af = m.get("away_flag", "")
            start = m.get("start_time", "待定")
            group = m.get("group", "")
            lines = [f"**{start}** {hf} {m['home_team']} vs {m['away_team']} {af}"]
            if group:
                lines.append(f"  _{group}_")
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "\n".join(lines)},
            })
        elements.append({"tag": "hr"})

    # ── AI 点评 ──
    if editor_note:
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"💡 **AI 点评**: {editor_note}"},
        })
        elements.append({"tag": "hr"})

    # ── 底部 ──
    elements.append({
        "tag": "note",
        "elements": [
            {"tag": "plain_text", "content": f"⚽ 数据来源: ESPN | AI 自动生成 | {last_updated}"},
        ],
    })

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"⚽ 2026 世界杯日报 · {date_str}",
                },
                "template": "green",
            },
            "elements": elements,
        },
    }

    return await _send_to_feishu(card)
