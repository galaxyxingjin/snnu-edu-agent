"""教学 PPT 生成工具：基于 coze-coding-dev-sdk 将 Markdown 内容生成 PPTX 文件。"""
import logging

from langchain.tools import tool
from coze_coding_dev_sdk import DocumentGenerationClient

logger = logging.getLogger(__name__)


@tool
def generate_teaching_pptx(markdown_content: str, title: str) -> str:
    """根据 Markdown 内容生成教学 PPT 文件，返回可下载的 URL 链接。

    适用场景：用户要求制作教学课件、课程 PPT、讲座幻灯片时调用。

    Args:
        markdown_content: PPT 的 Markdown 内容。每页幻灯片之间必须用单独一行 "---" 分隔；
            第一页通常是标题页（# 大标题 + 副标题）；内容页使用 ## 标题 + 列表组织要点。
        title: PPT 文件名（不含扩展名）。必须是英文，不能包含空格，
            单词间用下划线连接，例如 calculus_chapter1、python_basics_lesson。

    Returns:
        str: PPT 下载链接（24 小时内有效），或失败原因说明。
    """
    if not markdown_content or not markdown_content.strip():
        return "PPT 生成失败：markdown_content 内容为空，请先组织好课件内容。"
    if not title or not title.replace("_", "").replace("-", "").isalnum() or not title.isascii():
        return "PPT 生成失败：title 必须是英文且不含空格，请使用下划线连接（如 math_lesson_01）。"

    try:
        client = DocumentGenerationClient()
        url = client.create_pptx_from_markdown(markdown_content, title)
        logger.info("[pptx_tool] PPTX generated, title=%s", title)
        return f"教学 PPT 生成成功！\n下载链接（24小时内有效）：{url}"
    except Exception as e:
        logger.error("[pptx_tool] generate failed: %s", e)
        return f"PPT 生成失败：{str(e)}。请稍后重试，或简化课件内容后重试。"
