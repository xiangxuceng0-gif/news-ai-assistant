"""
一次性脚本：将 2026 世界杯开幕到现在的所有比赛结果推送到「世界杯」飞书群。
"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.delivery.feishu import _send_to_feishu
from datetime import datetime, timezone, timedelta

BEIJING_TZ = timezone(timedelta(hours=8))
WORLDCUP_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/ee580446-4ce1-4c8f-8ea7-1b4705e4e1b9"

MATCHDAY1 = [
    {"date":"6/11","group":"A","home":"Mexico","home_flag":"🇲🇽","away":"South Africa","away_flag":"🇿🇦","score":"2-0"},
    {"date":"6/11","group":"A","home":"South Korea","home_flag":"🇰🇷","away":"Czechia","away_flag":"🇨🇿","score":"2-1"},
    {"date":"6/12","group":"B","home":"Canada","home_flag":"🇨🇦","away":"Bosnia-Herzegovina","away_flag":"🇧🇦","score":"1-1"},
    {"date":"6/12","group":"D","home":"United States","home_flag":"🇺🇸","away":"Paraguay","away_flag":"🇵🇾","score":"4-1"},
    {"date":"6/13","group":"B","home":"Qatar","home_flag":"🇶🇦","away":"Switzerland","away_flag":"🇨🇭","score":"1-1"},
    {"date":"6/13","group":"C","home":"Brazil","home_flag":"🇧🇷","away":"Morocco","away_flag":"🇲🇦","score":"1-1"},
    {"date":"6/13","group":"C","home":"Haiti","home_flag":"🇭🇹","away":"Scotland","away_flag":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","score":"0-1"},
    {"date":"6/13","group":"D","home":"Australia","home_flag":"🇦🇺","away":"Turkiye","away_flag":"🇹🇷","score":"2-0"},
    {"date":"6/14","group":"E","home":"Germany","home_flag":"🇩🇪","away":"Curacao","away_flag":"🇨🇼","score":"7-1"},
    {"date":"6/14","group":"E","home":"Ivory Coast","home_flag":"🇨🇮","away":"Ecuador","away_flag":"🇪🇨","score":"1-0"},
    {"date":"6/14","group":"F","home":"Netherlands","home_flag":"🇳🇱","away":"Japan","away_flag":"🇯🇵","score":"2-2"},
    {"date":"6/14","group":"F","home":"Sweden","home_flag":"🇸🇪","away":"Tunisia","away_flag":"🇹🇳","score":"5-1"},
    {"date":"6/15","group":"G","home":"Belgium","home_flag":"🇧🇪","away":"Egypt","away_flag":"🇪🇬","score":"1-1"},
    {"date":"6/15","group":"G","home":"Iran","home_flag":"🇮🇷","away":"New Zealand","away_flag":"🇳🇿","score":"2-2"},
    {"date":"6/15","group":"H","home":"Saudi Arabia","home_flag":"🇸🇦","away":"Uruguay","away_flag":"🇺🇾","score":"1-1"},
    {"date":"6/15","group":"H","home":"Spain","home_flag":"🇪🇸","away":"Cape Verde","away_flag":"🇨🇻","score":"0-0"},
    {"date":"6/16","group":"I","home":"France","home_flag":"🇫🇷","away":"Senegal","away_flag":"🇸🇳","score":"3-1","star":"Mbappe 梅开二度"},
    {"date":"6/16","group":"I","home":"Iraq","home_flag":"🇮🇶","away":"Norway","away_flag":"🇳🇴","score":"1-4","star":"Haaland 2球"},
    {"date":"6/16","group":"J","home":"Argentina","home_flag":"🇦🇷","away":"Algeria","away_flag":"🇩🇿","score":"3-0","star":"Messi 帽子戏法!"},
    {"date":"6/16","group":"J","home":"Austria","home_flag":"🇦🇹","away":"Jordan","away_flag":"🇯🇴","score":"3-1"},
    {"date":"6/17","group":"K","home":"Portugal","home_flag":"🇵🇹","away":"Congo DR","away_flag":"🇨🇩","score":"1-1"},
    {"date":"6/17","group":"K","home":"Uzbekistan","home_flag":"🇺🇿","away":"Colombia","away_flag":"🇨🇴","score":"1-3"},
    {"date":"6/17","group":"L","home":"England","home_flag":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","away":"Croatia","away_flag":"🇭🇷","score":"4-2","star":"Kane 2球"},
    {"date":"6/17","group":"L","home":"Ghana","home_flag":"🇬🇭","away":"Panama","away_flag":"🇵🇦","score":"1-0"},
]

MATCHDAY2 = [
    {"date":"6/18","group":"A","home":"Czechia","home_flag":"🇨🇿","away":"South Africa","away_flag":"🇿🇦","score":"1-1","note":"补时点球绝平"},
    {"date":"6/18","group":"A","home":"Mexico","home_flag":"🇲🇽","away":"South Korea","away_flag":"🇰🇷","score":"1-0"},
    {"date":"6/18","group":"B","home":"Switzerland","home_flag":"🇨🇭","away":"Bosnia-Herzegovina","away_flag":"🇧🇦","score":"4-1","star":"Shaqiri 主宰比赛"},
    {"date":"6/18","group":"B","home":"Canada","home_flag":"🇨🇦","away":"Qatar","away_flag":"🇶🇦","score":"6-0","note":"Qatar 2张红牌"},
]


async def push_history():
    now_str = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M")

    # ── Card 1: Matchday 1 ──
    groups = {}
    for m in MATCHDAY1:
        g = m["group"]
        if g not in groups:
            groups[g] = []
        groups[g].append(m)

    elements1 = [
        {"tag": "div", "text": {"tag": "lark_md", "content": f"⚽ **2026 世界杯 — 第一轮 完整战报**\n📅 6月11日 - 6月17日 | 共 24 场比赛 | 12 个小组"}},
        {"tag": "hr"},
    ]

    for g in sorted(groups.keys()):
        ms = groups[g]
        lines = [f"**━━ 小组 {g} ━━**"]
        for m in ms:
            line = f"{m['home_flag']} {m['home']} **{m['score']}** {m['away']} {m['away_flag']}"
            if m.get("star"):
                line += f"  ⭐ {m['star']}"
            lines.append(line)
        elements1.append({"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}})

    elements1.append({"tag": "hr"})
    elements1.append({"tag": "div", "text": {"tag": "lark_md", "content": "🔥 **第一轮亮点**\n🇩🇪 德国 7-1 库拉索 — 最大比分\n🇦🇷 Messi 帽子戏法 — 追平世界杯进球纪录\n🇫🇷 Mbappe 梅开二度 — 法国强势开局\n🇨🇦 加拿大 1-1 波黑 — 队史世界杯首个积分"}})
    elements1.append({"tag": "note", "elements": [{"tag": "plain_text", "content": f"⚽ 数据来源: ESPN | {now_str}"}]})

    card1 = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": "⚽ 2026世界杯 · 第一轮战报"}, "template": "green"},
            "elements": elements1,
        },
    }

    # ── Card 2: Matchday 2 ──
    elements2 = [
        {"tag": "div", "text": {"tag": "lark_md", "content": f"⚽ **2026 世界杯 — 第二轮（截至6月19日）**\n📅 6月18日 | 共 4 场比赛"}},
        {"tag": "hr"},
    ]
    for m in MATCHDAY2:
        lines = [
            f"**{m['home_flag']} {m['home']} {m['score']} {m['away']} {m['away_flag']}**",
            f"  小组 {m['group']} | {m['date']}",
        ]
        if m.get("star"):
            lines.append(f"  ⭐ {m['star']}")
        if m.get("note"):
            lines.append(f"  📌 {m['note']}")
        elements2.append({"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}})

    elements2.append({"tag": "hr"})
    elements2.append({"tag": "div", "text": {"tag": "lark_md", "content": "📅 **后续赛程**\n第二轮: 6/18 - 6/24 | 第三轮: 6/25 - 6/28\n淘汰赛: 6/30 起 | 🏆 决赛: 7/19 纽约"}})
    elements2.append({"tag": "note", "elements": [{"tag": "plain_text", "content": f"⚽ 数据来源: ESPN | {now_str} | 每4小时自动更新"}]})

    card2 = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": "⚽ 2026世界杯 · 第二轮速报"}, "template": "green"},
            "elements": elements2,
        },
    }

    print("Pushing Matchday 1 card...")
    ok1 = await _send_to_feishu(card1, WORLDCUP_WEBHOOK)
    print(f"  Card 1: {'OK' if ok1 else 'FAIL'}")

    print("Pushing Matchday 2 card...")
    ok2 = await _send_to_feishu(card2, WORLDCUP_WEBHOOK)
    print(f"  Card 2: {'OK' if ok2 else 'FAIL'}")

    print("\nDone! Check your Feishu World Cup group.")


if __name__ == "__main__":
    asyncio.run(push_history())
