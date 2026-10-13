from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
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
SALES_TOOLS: list[BaseTool] = [check_sales_record, restock, update_item_status]

MANAGER_INSTRUCTIONS = (
    "You are the shopping mall manager. The user is already authenticated. "
    "Route product recommendations, purchases, cancellations, and customer order status "
    "to the Purchase Specialist. Route seller sales records, stock replenishment, and "
    "shipping updates to the Sales Specialist. Do not claim an action is complete unless "
    "the specialist has used the relevant tool."
)
PURCHASE_INSTRUCTIONS = (
    "You are the Purchase Specialist. Recommend products, purchase products, cancel "
    "eligible purchases, and check customer order status using only your tools. "
    "When the task is complete or belongs to another specialist, call CompleteOrEscalate."
)
SALES_INSTRUCTIONS = (
    "You are the Sales Specialist. Check sales records, replenish seller inventory, and "
    "update shipping status using only your tools. When the task is complete or belongs "
    "to another specialist, call CompleteOrEscalate."
)

# to create reusable prompt template
def _prompt(instructions: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [("system", instructions), ("placeholder", "{messages}")]
    )


def create_assistants(model: BaseChatModel) -> tuple[Assistant, Assistant, Assistant]:
    """Bind manager and specialist instructions to their respective tool sets."""
    manager = Assistant(
        _prompt(MANAGER_INSTRUCTIONS).pipe(
            model.bind_tools(
                [ToPurchaseSpecialistAssistant, ToSalesSpecialistAssistant]
            )
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
