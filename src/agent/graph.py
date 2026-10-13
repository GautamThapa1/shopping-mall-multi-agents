from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from src.agent.nodes import (
    create_entry_node,
    create_tool_node,
    leave_specialist,
    route_manager,
    route_specialist,
    route_user,
    role_restricted,
    unauthorized,
    validate_user,
)
from src.agent.specialists import PURCHASE_TOOLS, SALES_TOOLS, create_assistants
from src.state import State


def build_agent_graph(
    model: BaseChatModel,
    *,
    checkpointer: BaseCheckpointSaver | None = None, # must pass build_agent_graph(my_model, checkpointer=my_saver)
):
    """Build the shopping assistant graph using the application's chat model."""
    manager, purchase_specialist, sales_specialist = create_assistants(model)

    graph = StateGraph(State)
    graph.add_node("validate_user", validate_user)
    graph.add_node("unauthorized", unauthorized)
    graph.add_node("role_restricted", role_restricted)
    graph.add_node("manager", manager)
    graph.add_node(
        "enter_purchase_specialist",
        create_entry_node("Purchase Specialist", "customer"),
    )
    graph.add_node("purchase_specialist", purchase_specialist)
    graph.add_node("purchase_tools", create_tool_node(PURCHASE_TOOLS))
    graph.add_node(
        "enter_sales_specialist",
        create_entry_node("Sales Specialist", "vendor"),
    )
    graph.add_node("sales_specialist", sales_specialist)
    graph.add_node("sales_tools", create_tool_node(SALES_TOOLS))
    graph.add_node("leave_specialist", leave_specialist)

    graph.add_edge(START, "validate_user")
    graph.add_conditional_edges(
        "validate_user",
        route_user,
        {"manager": "manager", "unauthorized": "unauthorized"},
    )
    graph.add_edge("unauthorized", END)
    graph.add_conditional_edges(
        "manager",
        route_manager,
        {
            "enter_purchase_specialist": "enter_purchase_specialist",
            "enter_sales_specialist": "enter_sales_specialist",
            "role_restricted": "role_restricted",
            END: END,
        },
    )
    graph.add_edge("role_restricted", END)
    graph.add_edge("enter_purchase_specialist", "purchase_specialist")
    graph.add_conditional_edges(
        "purchase_specialist",
        lambda state: route_specialist(state, "purchase_tools"),
        {
            "purchase_tools": "purchase_tools",
            "leave_specialist": "leave_specialist",
            END: END,
        },
    )
    graph.add_edge("purchase_tools", "purchase_specialist")
    graph.add_edge("enter_sales_specialist", "sales_specialist")
    graph.add_conditional_edges(
        "sales_specialist",
        lambda state: route_specialist(state, "sales_tools"),
        {
            "sales_tools": "sales_tools",
            "leave_specialist": "leave_specialist",
            END: END,
        },
    )
    graph.add_edge("sales_tools", "sales_specialist")
    graph.add_edge("leave_specialist", "manager")

    return graph.compile(checkpointer=checkpointer)
