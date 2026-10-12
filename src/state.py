from typing import Annotated, Literal

from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import TypedDict

from src.models import (
    CompleteOrEscalate,
    ToPurchaseSpecialistAssistant,
    ToSalesSpecialistAssistant,
    User,
)
from src.tools import (
    cancel_purchase,
    check_item_status,
    check_sales_record,
    check_validation,
    get_recommendation,
    purchase_product,
    restock,
    update_item_status,
)

DialogState = Literal["customer", "vendor"]


def update_dialog_stack(
    left: list[DialogState], right: DialogState | Literal["pop"] | None
) -> list[DialogState]:
    """Push a specialist state or pop back to the previous state."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return [*left, right]


class State(TypedDict):
    user_info: User | None
    messages: Annotated[list[AnyMessage], add_messages]
    dialog_state: Annotated[list[DialogState], update_dialog_stack]


__all__ = [
    "CompleteOrEscalate",
    "DialogState",
    "State",
    "ToPurchaseSpecialistAssistant",
    "ToSalesSpecialistAssistant",
    "User",
    "cancel_purchase",
    "check_item_status",
    "check_sales_record",
    "check_validation",
    "get_recommendation",
    "purchase_product",
    "restock",
    "update_dialog_stack",
    "update_item_status",
]