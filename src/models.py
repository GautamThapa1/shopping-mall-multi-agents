from pydantic import BaseModel, Field


class User(BaseModel):
    id: str
    name: str | None = None
    gender: str | None = None
    type: str | None = None


class ToSalesSpecialistAssistant(BaseModel):
    """Transfer work to a specialist handling seller and sales service."""

    request: str = Field(
        description="Any follow-up questions the sales specialist should clarify before proceeding."
    )


class ToPurchaseSpecialistAssistant(BaseModel):
    """Transfer work to a specialist handling customer purchases."""

    request: str = Field(
        description="Any follow-up questions the purchase specialist should clarify before proceeding."
    )


class CompleteOrEscalate(BaseModel):
    """Mark a task complete or return control to the manager."""

    cancel: bool = True
    reason: str