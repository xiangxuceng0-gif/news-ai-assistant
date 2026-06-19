"""
ESPN Scoreboard API 抓取器 — 获取世界杯比赛实时数据。
免费、无需 API Key。
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

import httpx

logger = logging.getLogger(__name__)

BEIJING_TZ = timezone(timedelta(hours=8))
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"


async def fetch_match_data() -> Dict[str, Any]:
    """
    从 ESPN API 获取所有世界杯比赛数据，按状态分类。

    Returns:
        {
            "completed": [...],  # 已结束比赛
            "live": [...],       # 进行中
            "upcoming": [...],   # 未开始
            "last_updated": "ISO时间"
        }
    """
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(ESPN_URL, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error(f"ESPN API 抓取失败: {e}")
        return {"completed": [], "live": [], "upcoming": [], "last_updated": ""}

    events = data.get("events", [])
    logger.info(f"ESPN API: 获取到 {len(events)} 场比赛")

    completed, live, upcoming = [], [], []

    for evt in events:
        match = _parse_match(evt)
        if not match:
            continue

        status = match["status"]
        if status == "completed":
            completed.append(match)
        elif status == "live":
            live.append(match)
        else:
            upcoming.append(match)

    # 预告比赛按开赛时间排序
    upcoming.sort(key=lambda m: m.get("start_time", ""))

    result = {
        "completed": completed,
        "live": live,
        "upcoming": upcoming,
        "last_updated": datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M"),
    }

    logger.info(
        f"比赛分类: {len(completed)} 已结束, "
        f"{len(live)} 进行中, {len(upcoming)} 未开始"
    )
    return result


def _parse_match(evt: Dict) -> Optional[Dict[str, Any]]:
    """解析单场比赛数据。"""
    try:
        status_info = evt.get("status", {}).get("type", {})
        state = status_info.get("state", "pre")
        status_text = status_info.get("description", "")

        # 状态映射
        if state == "post" or status_text in ("Full Time", "Final", "FT"):
            status = "completed"
        elif state == "in":
            status = "live"
        else:
            status = "upcoming"

        # 比赛时间
        start_time = evt.get("date", "")
        if start_time:
            try:
                dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                start_time_display = dt.astimezone(BEIJING_TZ).strftime("%H:%M")
            except Exception:
                start_time_display = ""
        else:
            start_time_display = ""

        # 队伍信息
        comp = evt.get("competitions", [{}])[0]
        competitors = comp.get("competitors", [])

        home_team = home_score = away_team = away_score = None
        for c in competitors:
            team_name = c.get("team", {}).get("displayName", "Unknown")
            score = c.get("score", "")
            if c.get("homeAway") == "home":
                home_team = team_name
                home_score = score
            else:
                away_team = team_name
                away_score = score

        if not home_team or not away_team:
            return None

        # 小组信息
        group = ""
        for detail in comp.get("details", []):
            if "Group" in str(detail.get("type", {}).get("text", "")):
                group = detail["type"]["text"]

        # 比赛阶段
        period = status_info.get("description", "")
        match_clock = status_info.get("shortDetail", "")

        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_score": _safe_int(home_score),
            "away_score": _safe_int(away_score),
            "status": status,
            "start_time": start_time_display,
            "group": group,
            "period": period,
            "match_clock": match_clock,
            "event_id": evt.get("id", ""),
        }
    except Exception as e:
        logger.debug(f"解析比赛数据异常: {e}")
        return None


def _safe_int(val: Any) -> Optional[int]:
    """安全转换为整数。"""
    if val is None or val == "":
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
