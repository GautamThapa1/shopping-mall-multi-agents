from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import BaseTool

from src.agent.nodes import Assistant
from src.models import (
    CompleteOrEscalate,
    ToPurchaseSpecialistAssistant,
    ToSalesSpecialistAssistant,
)
from src.tools import (
    cancel_purchase,
    check_item_status,
    check_inventory,
    check_sales_record,
    get_recommendation,
    purchase_product,
    restock,
    update_item_status,
)

PURCHASE_TOOLS: list[BaseTool] = [
    get_recommendation,
    purchase_product,
    cancel_purchase,
    check_item_status,
]
SALES_TOOLS: list[BaseTool] = [check_inventory, check_sales_record, restock, update_item_status]

MANAGER_INSTRUCTIONS = (
    "You are the shopping mall manager. The user is already authenticated. "
    "The verified account role is {user_role}. For a customer, delegate product "
    "recommendations, purchases, cancellations, and personal order status to the Purchase "
    "Specialist. For a vendor, delegate inventory, stock, customer order history, sales "
    "records, and shipping updates to the Sales Specialist. In particular, vendor requests "
    "to see recent customer orders are sales-record requests: call ToSalesSpecialistAssistant "
    "instead of answering that you cannot access the records. Always delegate a supported "
    "request before answering; do not claim an action is complete until the specialist has "
    "used the relevant tool."
)
PURCHASE_INSTRUCTIONS = (
    "You are the Purchase Specialist. Recommend products, purchase products, cancel "
    "eligible purchases, and check customer order status using only your tools. "
    "Recommendation results include an inventory_id. When the user selects a numbered "
    "recommendation, use the inventory_id from that exact result when calling "
    "purchase_product; never pass the display number or product ID as inventory_id. "
    "If that listing is no longer in stock, explain that clearly and offer fresh recommendations. "
    "When the task is complete or belongs to another specialist, call CompleteOrEscalate."
)
SALES_INSTRUCTIONS = (
    "You are the Sales Specialist. Check seller inventory and sales records, replenish "
    "stock, and update shipping status using only your tools. Inventory results include "
    "inventory_id and stock; use the exact inventory_id from those results when restocking. "
    "Sales records include purchase_id; use that exact purchase_id when updating one order's "
    "status. Never confuse inventory_id with purchase_id. When the task is complete or "
    "belongs to another specialist, call CompleteOrEscalate."
)

# to create reusable prompt template
def _prompt(instructions: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [("system", instructions), ("placeholder", "{messages}")]
    )


def create_assistants(model: BaseChatModel) -> tuple[Assistant, Assistant, Assistant]:
    """Bind manager and specialist instructions to their respective tool sets."""
    manager = Assistant(
        RunnablePassthrough.assign(
            user_role=lambda state: (
                state["user_info"].type if state.get("user_info") is not None else "unknown"
            )
        )
        .pipe(_prompt(MANAGER_INSTRUCTIONS))
        .pipe(
            model.bind_tools([ToPurchaseSpecialistAssistant, ToSalesSpecialistAssistant])
        )
    )
    purchase_specialist = Assistant(
        _prompt(PURCHASE_INSTRUCTIONS).pipe(
            model.bind_tools([*PURCHASE_TOOLS, CompleteOrEscalate])
        )
    )
    sales_specialist = Assistant(
        _prompt(SALES_INSTRUCTIONS).pipe(model.bind_tools([*SALES_TOOLS, CompleteOrEscalate]))
    )
    return manager, purchase_specialist, sales_specialist
