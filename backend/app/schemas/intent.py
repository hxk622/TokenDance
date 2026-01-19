"""
Intent validation schemas for pre-flight check.
"""
from pydantic import BaseModel, Field


class IntentValidationRequest(BaseModel):
    """Request schema for intent validation."""

    user_input: str = Field(..., description="User's input text to validate", min_length=1)
    context: dict[str, str] | None = Field(
        None, description="Optional context for validation (workspace, previous messages, etc.)"
    )


class IntentValidationResponse(BaseModel):
    """Response schema for intent validation."""

    is_complete: bool = Field(..., description="Whether the intent is complete and actionable")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for the validation (0-1)"
    )
    missing_info: list[str] = Field(
        default_factory=list, description="List of missing critical information"
    )
    suggested_questions: list[str] = Field(
        default_factory=list,
        description="Suggested clarifying questions for the user to answer",
    )
    reasoning: str | None = Field(None, description="Optional explanation of the validation")
