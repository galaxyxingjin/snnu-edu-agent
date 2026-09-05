"""陕师大智能助学 Agent：学科答疑 + 智能评测 + 教学 PPT 生成。"""
import os
import json
from typing import Annotated

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver

from tools.pptx_tool import generate_teaching_pptx
from tools.web_search_tool import web_search
from tools.document_generator import generate_study_document

LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话 (40 条消息), 可按需调整
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]  # type: ignore


class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


@wrap_tool_call
def handle_tool_errors(request, handler):
    """工具执行异常兜底：返回友好错误信息，避免阻塞 Agent 循环。"""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool execute error: ({str(e)})",
            tool_call_id=request.tool_call["id"],
        )


def build_agent(ctx=None):
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model=cfg["config"].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg["config"].get("temperature", 0.7),
        top_p=cfg["config"].get("top_p", 0.9),
        max_completion_tokens=cfg["config"].get("max_completion_tokens", 16000),
        streaming=True,
        timeout=cfg["config"].get("timeout", 600),
        extra_body={
            "thinking": {
                "type": cfg["config"].get("thinking", "disabled")
            }
        },
        default_headers=default_headers(ctx) if ctx else {},
    )

    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=[generate_teaching_pptx, web_search, generate_study_document],
        middleware=[handle_tool_errors],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
