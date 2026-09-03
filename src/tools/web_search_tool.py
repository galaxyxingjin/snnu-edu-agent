"""联网搜索工具：基于 coze-coding-dev-sdk 检索实时网络信息。"""
import logging

from langchain.tools import tool
from coze_coding_dev_sdk import SearchClient
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context

logger = logging.getLogger(__name__)


@tool
def web_search(query: str) -> str:
    """联网搜索最新的教育资讯、考试政策、学术动态、校园通知等时效性信息。

    适用场景：用户询问最新政策、近期新闻、考试安排、实时资讯等需要联网核实的内容。

    Args:
        query: 搜索关键词，应简洁准确地描述要查询的内容。

    Returns:
        str: 搜索结果摘要与来源列表，或未找到相关信息的说明。
    """
    if not query or not query.strip():
        return "搜索失败：查询关键词不能为空。"

    ctx = request_context.get() or new_context(method="web_search")
    try:
        client = SearchClient(ctx=ctx)
        response = client.web_search(query=query.strip(), count=5, need_summary=True)

        parts = []
        if response.summary:
            parts.append(f"【搜索摘要】\n{response.summary}")

        if response.web_items:
            parts.append("【参考来源】")
            for i, item in enumerate(response.web_items, 1):
                publish = f"（{item.publish_time}）" if item.publish_time else ""
                parts.append(
                    f"{i}. {item.title}{publish}\n   来源：{item.site_name or '未知'}\n   链接：{item.url}"
                )
        if not parts:
            return f"未搜索到与「{query}」相关的有效信息，请尝试更换关键词。"
        return "\n\n".join(parts)
    except Exception as e:
        logger.error("[web_search_tool] search failed: %s", e)
        return f"搜索服务暂时不可用：{str(e)}。请稍后重试。"
