import logging

from langchain.tools import tool
from coze_coding_dev_sdk import SearchClient
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_utils.log.write_log import request_context

logger = logging.getLogger(__name__)


def _do_web_search(query: str, count: int = 8) -> str:
    """执行联网搜索并格式化结果（公共逻辑，供 tool 调用）"""
    ctx = request_context.get() or new_context(method="web_search")
    client = SearchClient(ctx=ctx)
    response = client.web_search(query=query, count=count, need_summary=True)

    parts = []
    if response.summary:
        parts.append(f"【搜索摘要】\n{response.summary}")

    if response.web_items:
        parts.append("【搜索结果】")
        for i, item in enumerate(response.web_items, 1):
            entry = (
                f"{i}. 标题: {item.title}\n"
                f"   来源: {item.site_name} ({item.url})\n"
                f"   摘要: {item.snippet}"
            )
            if item.publish_time:
                entry += f"\n   发布时间: {item.publish_time}"
            parts.append(entry)

    if not parts:
        return f"未搜索到与「{query}」相关的结果，请换个关键词重试。"
    return "\n\n".join(parts)


@tool
def web_search(query: str) -> str:
    """联网搜索实时信息。当问题涉及陕西师范大学最新通知、校园动态、教育政策、考试安排（四六级/教资/考研报名时间）、最新学术资讯等时效性内容时使用。参数 query 为搜索关键词，应尽量具体（例如"陕西师范大学 2026 开学通知"）。"""
    try:
        logger.info(f"[web_search] query={query}")
        return _do_web_search(query)
    except Exception as e:
        logger.error(f"[web_search] search failed: {e}", exc_info=True)
        return f"搜索暂时不可用（{str(e)}），请稍后重试，或基于你的知识回答并提示用户以官方渠道为准。"
