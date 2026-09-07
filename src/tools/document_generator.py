import logging
import re

from langchain.tools import tool
from coze_coding_dev_sdk import DocumentGenerationClient, DOCXConfig, PDFConfig

logger = logging.getLogger(__name__)


def _sanitize_title(title):
    """确保文件名符合规范：英文、无空格和特殊字符"""
    if not title:
        return "study_document"
    cleaned = re.sub(r'[^A-Za-z0-9_-]', '_', title).strip('_')
    return cleaned or "study_document"


def _generate(markdown_content, doc_type, title):
    """调用文档生成 SDK 生成文档并返回下载链接（公共逻辑）"""
    client = DocumentGenerationClient(
        docx_config=DOCXConfig(font_name="Noto Sans CJK SC", font_size=11),
        pdf_config=PDFConfig(page_size="A4"),
    )
    safe_title = _sanitize_title(title)
    if doc_type == "pdf":
        url = client.create_pdf_from_markdown(markdown_content, safe_title)
    else:
        url = client.create_docx_from_markdown(markdown_content, safe_title)
    return url


@tool
def generate_study_document(markdown_content: str, doc_type: str = "docx", title: str = "study_plan") -> str:
    """将学习计划、学情诊断报告或理科解题文档生成可下载的文档文件。

参数说明：
- markdown_content: 完整的文档正文，用 # / ## 标题、列表、表格组织。注意：正文中的理科公式必须用 Unicode 下标与纯文本（如 R₁、×、²、E/(R₁+R₂)、G=Mg），禁止使用 $...$ 包裹公式、禁止出现 \\frac、\\sin、\\cdot、^、_、{} 等 LaTeX 原始命令。
- doc_type: 文档格式，"docx"（Word，默认）或 "pdf"
- title: 文件名（必须使用英文，例如 "study_plan"、"learning_report"）

返回：文档的下载链接（24 小时内有效）。仅在用户明确要求「导出/下载/生成文档」学习计划、测评报告、错题本、解题文档时调用。"""
    try:
        if doc_type not in ("docx", "pdf"):
            doc_type = "docx"
        url = _generate(markdown_content, doc_type, title)
        logger.info(f"[generate_study_document] generated {doc_type}, title={title}")
        return f"文档已生成，下载链接（24 小时内有效）：\n{url}"
    except Exception as e:
        logger.error(f"[generate_study_document] failed: {e}", exc_info=True)
        return f"文档生成失败（{str(e)}），请稍后重试。"