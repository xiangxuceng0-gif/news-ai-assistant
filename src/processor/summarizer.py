"""
AI 摘要处理器 — 调用 Claude API 分批处理新闻，生成中文简报。
"""
import json
import logging
from typing import List, Dict, Any, Optional

from src.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, SUMMARIZE_SYSTEM_PROMPT, MAX_NEWS_COUNT

logger = logging.getLogger(__name__)

# 每批处理的文章数（避免单次请求 token 溢出或 JSON 截断）
BATCH_SIZE = 15
# 每批的 max_tokens
BATCH_MAX_TOKENS = 8192


async def summarize_articles(
    articles: List[Dict[str, Any]],
    max_count: Optional[int] = None,
) -> Dict[str, Any]:
    """
    将文章列表分批发送给 AI，返回结构化简报。

    Args:
        articles: 待处理的文章列表
        max_count: 最多返回的简报条数，默认使用配置中的 MAX_NEWS_COUNT

    Returns:
        {"briefings": [...], "editor_note": "..."}
    """
    if not articles:
        logger.warning("没有文章需要处理")
        return {"briefings": [], "editor_note": "今日无重要新闻"}

    if not ANTHROPIC_API_KEY:
        raise ValueError("未设置 ANTHROPIC_API_KEY，请检查 .env 文件")

    if max_count is None:
        max_count = MAX_NEWS_COUNT

    # 分批处理
    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    all_briefings: List[Dict] = []
    editor_notes: List[str] = []

    batches = [articles[i:i + BATCH_SIZE] for i in range(0, len(articles), BATCH_SIZE)]
    logger.info(f"AI 处理 {len(articles)} 篇文章，分 {len(batches)} 批")

    for batch_idx, batch in enumerate(batches):
        try:
            result = await _process_batch(client, batch, batch_idx + 1, len(batches))
            briefings = result.get("briefings", [])
            note = result.get("editor_note", "")
            all_briefings.extend(briefings)
            if note:
                editor_notes.append(note)
            logger.info(f"  第 {batch_idx + 1}/{len(batches)} 批完成: {len(briefings)} 条")
        except Exception as e:
            logger.error(f"  第 {batch_idx + 1}/{len(batches)} 批失败: {e}")
            continue

    # 合并去重（跨批次可能有重复）
    seen_titles = set()
    unique_briefings = []
    for b in all_briefings:
        title = b.get("title", "")
        if title not in seen_titles:
            seen_titles.add(title)
            unique_briefings.append(b)

    # 按重要性排序
    unique_briefings.sort(key=lambda x: x.get("importance", 0), reverse=True)
    unique_briefings = unique_briefings[:max_count]

    # 合并编辑点评
    final_note = " | ".join(editor_notes[:3]) if editor_notes else ""

    logger.info(f"AI 处理完成: {len(unique_briefings)} 条简报（去重后）")
    return {
        "briefings": unique_briefings,
        "editor_note": final_note,
        "total_fetched": len(articles),
    }


async def _process_batch(
    client,
    articles: List[Dict],
    batch_num: int,
    total_batches: int,
) -> Dict[str, Any]:
    """处理单个批次的文章。"""
    articles_text = _format_articles_for_prompt(articles)
    user_prompt = f"""以下是一组今日新闻文章（第 {batch_num}/{total_batches} 批，共 {len(articles)} 篇）。

请逐一分析每篇文章，生成中文简报。只返回你认为重要且值得关注的条目（importance >= 6）。

{articles_text}"""

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=BATCH_MAX_TOKENS,
        system=SUMMARIZE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # 过滤 ThinkingBlock，取第一个文本块
    text_blocks = [b for b in response.content if hasattr(b, "text")]
    if not text_blocks:
        raise ValueError("AI 响应中没有文本内容")
    content = text_blocks[0].text
    return _parse_json_response(content)


def _format_articles_for_prompt(articles: List[Dict[str, Any]]) -> str:
    """将文章列表格式化为 prompt 友好的文本。"""
    lines = []
    for i, article in enumerate(articles, 1):
        title = article.get("title", "无标题")
        url = article.get("url", "")
        summary = article.get("summary", "")[:200]
        source = article.get("source_name", "未知来源")
        lines.append(
            f"[{i}] {title}\n"
            f"    来源: {source}\n"
            f"    链接: {url}\n"
            f"    摘要: {summary}\n"
        )
    return "\n".join(lines)


def _parse_json_response(text: str) -> Dict[str, Any]:
    """从 AI 响应中提取 JSON，支持截断修复。"""
    import re

    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试从 markdown code block 中提取
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试找到第一个 { 到最后一个 }
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # JSON 被截断：尝试修复（补全最后一个不完整的条目）
    result = _fix_truncated_json(text)
    if result:
        return result

    logger.error(f"无法解析 AI 响应为 JSON: {text[:500]}")
    return {"briefings": [], "editor_note": "解析失败"}


def _fix_truncated_json(text: str) -> Optional[Dict[str, Any]]:
    """尝试修复被截断的 JSON 响应。"""
    import re

    # 找到最后一个完整的对象 } 之后截断
    # 先尝试找到 briefings 数组中最后一个完整条目
    match = re.search(r"\{[\s\S]*\"briefings\"[\s\S]*\]", text)
    if not match:
        # 尝试找到最后一个完整的 briefing 对象并手动闭合
        last_complete = None
        for m in re.finditer(r'\},\s*\{', text):
            last_complete = m.start() + 1  # position after },
        if last_complete:
            fixed = text[:last_complete] + "]}"
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass

    return None
