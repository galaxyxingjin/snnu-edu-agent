"""教学 PPT 生成工具：基于 coze-coding-dev-sdk 将结构化内容生成带配色与版式的 PPTX 文件。

设计说明（Classic Blue 教学主题）：
- 封面页：深蓝底 + 白色大标题 + 副标题 + 橙色装饰线
- 内容页：顶部深蓝标题栏（白色标题）+ 浅灰内容区（深色正文）+ 底部灰色教师备注区 + 页码
- 考点/易错点用 **加粗** 标记，渲染为橙色加粗文字
- 所有元素使用 left/top/width/height 绝对定位，确保标题与内容不重叠
"""

import json
import logging
import re

from langchain.tools import tool
from coze_coding_dev_sdk import DocumentGenerationClient

logger = logging.getLogger(__name__)

# —— 教学主题配色（Classic Blue，专业清晰） ——
HEADER_BG = "#1C2833"   # 标题栏 / 封面深蓝
PAGE_BG = "#F4F6F6"     # 内容页浅灰底
TEXT = "#1C2833"        # 正文深色
SUB = "#5D6D7E"         # 次要文字
WHITE = "#FFFFFF"
GREY = "#AAB7B8"        # 封面辅助文字
HL = "#E67E22"          # 考点 / 易错点高亮（橙色）

SLIDE_W, SLIDE_H = 960, 540  # 16:9 像素


def _escape(s: str) -> str:
    """转义 HTML 特殊字符。"""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _render_bold(s: str) -> str:
    """把 Markdown 加粗 **xxx** 转为 <strong>xxx</strong>（用于考点高亮）。"""
    s = _escape(s)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def _cover_html(spec: dict) -> str:
    """生成封面页 HTML。"""
    title = _escape(spec.get("title", "课件标题"))
    subtitle = _escape(spec.get("subtitle", ""))
    notes = _escape(spec.get("notes", ""))

    subtitle_html = ""
    if subtitle:
        subtitle_html = (
            f'<p style="left:80px;top:260px;width:800px;height:40px;'
            f'color:{GREY};font-size:20px;text-align:center;">{subtitle}</p>'
        )
    notes_html = ""
    if notes:
        notes_html = (
            f'<p style="left:60px;top:480px;width:840px;height:36px;'
            f'color:{GREY};font-size:13px;text-align:center;">{notes}</p>'
        )

    return (
        f'<html><body style="background-color:{HEADER_BG};">'
        f'<div style="left:0;top:0;width:{SLIDE_W}px;height:{SLIDE_H}px;'
        f'background-color:{HEADER_BG};"></div>'
        f'<h1 style="left:80px;top:170px;width:800px;height:80px;color:{WHITE};'
        f'font-size:38px;text-align:center;">{title}</h1>'
        f'{subtitle_html}'
        f'<div style="left:380px;top:325px;width:200px;height:6px;background-color:{HL};"></div>'
        f'{notes_html}'
        f'</body></html>'
    )


def _content_html(spec: dict, no: int, total: int) -> str:
    """生成内容页 HTML。no 为内容页序号（从 1 开始）。"""
    title = _escape(spec.get("title", f"第 {no} 页"))
    points = spec.get("points", [])
    notes = _escape(spec.get("notes", ""))

    # 要点越多字号越小，避免溢出
    n = max(len(points), 1)
    fs = 22 if n <= 3 else (20 if n <= 5 else 17)

    items = "".join(f"<li>{_render_bold(str(p))}</li>" for p in points)

    ul_top, ul_height = 95, 370 if not notes else 300

    notes_html = ""
    if notes:
        notes_html = (
            f'<div style="left:40px;top:410px;width:880px;height:58px;'
            f'background-color:#E8EAED;"></div>'
            f'<p style="left:52px;top:417px;width:856px;height:44px;color:{SUB};font-size:12px;">'
            f'教师备注：{notes}</p>'
        )

    return (
        f'<html><body style="background-color:{PAGE_BG};">'
        f'<div style="left:0;top:0;width:{SLIDE_W}px;height:70px;'
        f'background-color:{HEADER_BG};"></div>'
        f'<h2 style="left:40px;top:14px;width:760px;height:42px;color:{WHITE};'
        f'font-size:26px;">{title}</h2>'
        f'<p style="left:840px;top:20px;width:90px;height:30px;color:{GREY};'
        f'font-size:14px;text-align:right;">{no}/{total}</p>'
        f'<ul style="left:50px;top:{ul_top}px;width:860px;height:{ul_height}px;'
        f'color:{TEXT};font-size:{fs}px;">{items}</ul>'
        f'{notes_html}'
        f'</body></html>'
    )


def _build_slides(slides: list) -> list:
    """把结构化 slides 转成 HTML 页面列表。"""
    htmls = []
    total = len(slides)
    content_no = 0
    for spec in slides:
        if "subtitle" in spec:
            htmls.append(_cover_html(spec))
        else:
            content_no += 1
            htmls.append(_content_html(spec, content_no, total))
    return htmls


@tool
def generate_teaching_pptx(slides_spec: str, title: str) -> str:
    """把教学内容制作成带配色与版式的教学 PPT（PPTX）文件，返回下载链接。

    适用场景：用户要求制作教学课件 / 课程 PPT / 讲座幻灯片时调用。

    Args:
        slides_spec: 幻灯片内容，JSON 字符串，是一个数组（每页一个对象）：
            - 封面页：{"title": "课件主标题", "subtitle": "副标题", "notes": "教师备注(可选)"}
            - 内容页：{"title": "页面标题", "points": ["要点1", "要点2"], "notes": "教师备注(可选)"}
            硬性要求：每页只放一个主题；要点为短句（3~6 个）；大段讲解、推导全部写进
            notes（教师备注）；重点、考点、易错点用 **加粗** 标记。
        title: PPT 文件名（不含扩展名），必须为英文，单词间用下划线连接，如 newton_law。

    Returns:
        str: PPT 下载链接（24 小时内有效），或失败原因。
    """
    if not slides_spec or not slides_spec.strip():
        return "PPT 生成失败：slides_spec 内容为空。"
    if (
        not title
        or not title.isascii()
        or not title.replace("_", "").replace("-", "").isalnum()
    ):
        return "PPT 生成失败：title 必须是英文且不含空格，如 newton_third_law。"

    try:
        slides = json.loads(slides_spec)
        if not isinstance(slides, list) or not slides:
            return "PPT 生成失败：slides_spec 必须是 JSON 数组，且至少包含一页。"
        for s in slides:
            if not isinstance(s, dict):
                return "PPT 生成失败：每一页都必须是 JSON 对象（包含 title 等字段）。"
            if "title" not in s:
                return "PPT 生成失败：每一页都必须包含 title 字段。"

        htmls = _build_slides(slides)
        client = DocumentGenerationClient()
        url = client.create_pptx_from_html(htmls, title)
        logger.info("[pptx_tool] generated title=%s slides=%d", title, len(htmls))
        return (
            f"教学 PPT 生成成功！共 {len(htmls)} 页。\n"
            f"下载链接（24 小时内有效）：{url}"
        )
    except json.JSONDecodeError as e:
        return (
            f"PPT 生成失败：slides_spec 不是合法 JSON（{e}）。"
            f"请用 JSON 数组格式提供幻灯片内容，例如 "
            f'[{{"title":"学习目标","points":["理解...","掌握..."]}}]。'
        )
    except Exception as e:  # noqa: BLE001
        logger.error("[pptx_tool] generate failed: %s", e)
        return f"PPT 生成失败：{str(e)}"