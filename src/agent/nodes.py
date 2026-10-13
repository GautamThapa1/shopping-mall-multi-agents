from collections.abc import Callable, Sequence
from typing import Any, cast

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda
from langchain_core.tools import BaseTool
from langgraph.graph import END
from langgraph.prebuilt import ToolNode

from src.models import (
    CompleteOrEscalate,
    ToPurchaseSpecialistAssistant,
    ToSalesSpecialistAssistant,
)
from src.state import DialogState, State
from src.tools import check_validation


class Assistant:
    """Invoke a chat runnable and ensure it produces a message or tool call."""

    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(
        self, state: State, config: RunnableConfig | None = None
    ) -> dict[str, BaseMessage]:
        result = cast(AIMessage, self.runnable.invoke(state, config=config))
        if not result.tool_calls and not result.content:
            retry_state = {
                **state,
                "messages": [*state["messages"], ("user", "Please provide a response.")],
            }
            result = cast(AIMessage, self.runnable.invoke(retry_state, config=config))
        return {"messages": result}


def create_entry_node(assistant_name: str, dialog_state: DialogState) -> Callable:
    def entry_node(state: State) -> dict[str, Any]:
        assistant_message = cast(AIMessage, state["messages"][-1])
        return {
            "messages": [
                ToolMessage(
                    content=(
                        f"Request accepted by the {assistant_name}. Continue with the user's "
                        "request using your available tools."
                    ),
                    tool_call_id=call["id"],
                )
                for call in assistant_message.tool_calls
            ],
            "dialog_state": dialog_state,
        }

    return entry_node


def leave_specialist(state: State) -> dict[str, Any]:
    assistant_message = cast(AIMessage, state["messages"][-1])
    messages = [
        ToolMessage(
            content="Returning control to the manager.",
            tool_call_id=call["id"],
        )
        for call in assistant_message.tool_calls
        if call["name"] == CompleteOrEscalate.__name__
    ]
    return {"dialog_state": "pop", "messages": messages}


def route_user(state: State) -> str:
    return "manager" if state.get("user_info") is not None else "unauthorized"


def route_manager(state: State) -> str:
    assistant_message = cast(AIMessage, state["messages"][-1]) # cast = Trust me it is AI or human message
    for call in assistant_message.tool_calls:
        if call["name"] == ToPurchaseSpecialistAssistant.__name__:
            return "enter_purchase_specialist"
        if call["name"] == ToSalesSpecialistAssistant.__name__:
            return "enter_sales_specialist"
    return END


def route_specialist(state: State, tool_node: str) -> str:
    assistant_message = cast(AIMessage, state["messages"][-1])
    if not assistant_message.tool_calls:
        return END
    if any(call["name"] == CompleteOrEscalate.__name__ for call in assistant_message.tool_calls):
        return "leave_specialist"
    return tool_node


def validate_user(state: State, config: RunnableConfig) -> dict[str, Any]:
    return {"user_info": check_validation.invoke({}, config=config)}


def unauthorized(state: State) -> dict[str, list[BaseMessage]]:
    return {
        "messages": [
            AIMessage(
                content="I could not verify your account. Please check your user ID and try again."
            )
        ]
    }


def create_tool_node(tools: Sequence[BaseTool]) -> Runnable:
    return ToolNode(list(tools)).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def handle_tool_error(state: dict[str, Any]) -> dict[str, list[ToolMessage]]:
    error = state.get("error")
    assistant_message = cast(AIMessage, state["messages"][-1])
    return {
        "messages": [
            ToolMessage(
                content=f"The tool could not complete the request: {error}",
                tool_call_id=call["id"],
            )
            for call in assistant_message.tool_calls
        ]
    }
