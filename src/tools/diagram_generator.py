"""知识点图解生成工具：基于 coze-coding-dev-sdk 生成示意图、概念图、实验装置图、原子模型图等。"""
import logging

from langchain.tools import tool
from coze_coding_dev_sdk import ImageGenerationClient
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context

logger = logging.getLogger(__name__)


@tool
def generate_diagram(description: str, size: str = "2K") -> str:
    """根据文字描述生成知识点图解/示意图，返回图片链接。

    适用场景：
    - 知识点图解（概念关系图、知识框架图、思维导图）
    - 物理实验装置示意图（斜面小车、电路连接图、弹簧测力计等）
    - 原子结构/原子模型示意图（如玻尔模型、电子云模型）
    - 几何图形、函数图像等可视化辅助

    Args:
        description: 需要生成图片的详细中文描述。要明确图片类型（示意图/图解/思维导图）、
            应包含的关键元素和文字标注。例如"中学物理斜面实验装置示意图，标注木块、斜面、
            滑轮、砝码、弹簧测力计等器材，白底简洁风格"。
        size: 图片尺寸，可选 "2K" 或 "4K"，默认 "2K"。

    Returns:
        str: 图片链接（可直接查看），或失败原因说明。
    """
    if not description or not description.strip():
        return "图解生成失败：描述内容不能为空。"

    if size not in ("2K", "4K"):
        size = "2K"

    ctx = request_context.get() or new_context(method="generate_diagram")
    try:
        client = ImageGenerationClient(ctx=ctx)
        response = client.generate(prompt=description.strip(), size=size)
        if response.success and response.image_urls:
            urls = response.image_urls
            lines = [f"图解生成成功！共 {len(urls)} 张图片："]
            for i, u in enumerate(urls, 1):
                lines.append(f"{i}. {u}")
            return "\n".join(lines)
        return f"图解生成失败：{getattr(response, 'error_messages', '未知错误')}"
    except Exception as e:
        logger.error("[diagram_generator] generate failed: %s", e)
        return f"图解生成失败：{str(e)}。请稍后重试，或简化图片描述后重试。"