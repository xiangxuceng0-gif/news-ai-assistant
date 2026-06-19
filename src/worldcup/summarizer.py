"""
世界杯 AI 战报生成器 — 调用 DeepSeek API 生成中文赛事报告。
"""
import json
import logging
from typing import List, Dict, Any

from src.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from src.worldcup.config import WORLDCUP_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def generate_match_report(match_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将比赛数据发送给 AI，生成中文战报。

    Args:
        match_data: espn_fetcher.fetch_match_data() 的输出

    Returns:
        {"matches": [...], "editor_note": "..."}
    """
    completed = match_data.get("completed", [])
    live = match_data.get("live", [])
    upcoming = match_data.get("upcoming", [])

    if not completed and not live and not upcoming:
        logger.info("今日无世界杯比赛数据")
        return {"matches": [], "editor_note": "今日无世界杯比赛"}

    if not ANTHROPIC_API_KEY:
        raise ValueError("未设置 ANTHROPIC_API_KEY")

    # 构建提示文本
    prompt = _build_prompt(completed, live, upcoming)

    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            system=WORLDCUP_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        text_blocks = [b for b in response.content if hasattr(b, "text")]
        if not text_blocks:
            raise ValueError("AI 响应中没有文本内容")

        content = text_blocks[0].text
        result = _parse_json_response(content)

        # 补充原始数据中 AI 可能没有的信息
        result = _enrich_result(result, match_data)

        logger.info(f"AI 战报生成完成: {len(result.get('matches', []))} 场比赛")
        return result

    except Exception as e:
        logger.error(f"AI 战报生成失败: {e}")
        return _fallback_report(match_data)


def _build_prompt(completed: List[Dict], live: List[Dict], upcoming: List[Dict]) -> str:
    """构建发送给 AI 的 prompt。"""
    parts = []

    if completed:
        parts.append(f"## 已结束比赛 ({len(completed)} 场)")
        for m in completed:
            parts.append(
                f"- {m['home_team']} {m.get('home_score', '?')} - "
                f"{m.get('away_score', '?')} {m['away_team']}"
                f" | {m.get('group', '未知小组')} | 状态: {m.get('period', '完赛')}"
            )

    if live:
        parts.append(f"\n## 进行中 ({len(live)} 场)")
        for m in live:
            parts.append(
                f"- {m['home_team']} {m.get('home_score', '?')} - "
                f"{m.get('away_score', '?')} {m['away_team']}"
                f" | {m.get('group', '未知小组')} | {m.get('match_clock', '')}"
            )

    if upcoming:
        parts.append(f"\n## 即将开始 ({len(upcoming)} 场)")
        for m in upcoming[:6]:  # 最多展示 6 场预告
            parts.append(
                f"- {m.get('start_time', '')} {m['home_team']} vs {m['away_team']}"
                f" | {m.get('group', '未知小组')}"
            )

    return "\n".join(parts)


def _enrich_result(result: Dict, match_data: Dict) -> Dict:
    """补充原始数据（国旗、比分、小组等确保准确）。"""
    from src.worldcup.config import TEAM_FLAGS

    # 建立原始数据查找表
    orig_map = {}
    for m in match_data.get("completed", []) + match_data.get("live", []) + match_data.get("upcoming", []):
        key = f"{m['home_team']}_{m['away_team']}"
        orig_map[key] = m

    for match in result.get("matches", []):
        key = f"{match.get('home_team', '')}_{match.get('away_team', '')}"
        orig = orig_map.get(key, {})
        if orig:
            match["home_flag"] = TEAM_FLAGS.get(orig.get("home_team", ""), "")
            match["away_flag"] = TEAM_FLAGS.get(orig.get("away_team", ""), "")
            match["start_time"] = orig.get("start_time", "")
            match["group"] = orig.get("group", match.get("group", ""))
            match["status"] = orig.get("status", match.get("status", ""))
            match["period"] = orig.get("period", "")
            match["match_clock"] = orig.get("match_clock", "")
            # 使用原始比分（更准确）
            if orig.get("home_score") is not None:
                match["home_score"] = orig["home_score"]
            if orig.get("away_score") is not None:
                match["away_score"] = orig["away_score"]

    return result


def _fallback_report(match_data: Dict) -> Dict:
    """AI 失败时的降级报告（纯数据，无战报）。"""
    from src.worldcup.config import TEAM_FLAGS

    matches = []
    for m in match_data.get("completed", []):
        matches.append({
            "home_team": m["home_team"],
            "away_team": m["away_team"],
            "home_score": m.get("home_score"),
            "away_score": m.get("away_score"),
            "home_flag": TEAM_FLAGS.get(m["home_team"], ""),
            "away_flag": TEAM_FLAGS.get(m["away_team"], ""),
            "status": "completed",
            "match_summary": "",
            "star_player": None,
            "key_moment": None,
            "group": m.get("group", ""),
        })

    for m in match_data.get("upcoming", [])[:6]:
        matches.append({
            "home_team": m["home_team"],
            "away_team": m["away_team"],
            "home_score": None, "away_score": None,
            "home_flag": TEAM_FLAGS.get(m["home_team"], ""),
            "away_flag": TEAM_FLAGS.get(m["away_team"], ""),
            "status": "upcoming",
            "match_summary": "",
            "star_player": None, "key_moment": None,
            "group": m.get("group", ""),
            "start_time": m.get("start_time", ""),
        })

    return {
        "matches": matches,
        "editor_note": f"共 {len(match_data.get('completed',[]))} 场比赛结束",
    }


def _parse_json_response(text: str) -> Dict[str, Any]:
    """从 AI 响应中提取 JSON。"""
    import re
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    logger.error(f"无法解析战报 JSON: {text[:300]}")
    return {"matches": [], "editor_note": "解析失败"}
