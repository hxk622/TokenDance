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


class ClarificationOption(BaseModel):
    """A single clarification option with label and value."""

    label: str = Field(..., description="Display label for the option")
    value: str = Field(..., description="Value to append to user input when selected")


class IntentValidationResponse(BaseModel):
    """Response schema for intent validation."""

    is_complete: bool = Field(..., description="Whether the intent is complete and actionable")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for the validation (0-1)"
    )
    # Legacy fields - kept for backward compatibility
    missing_info: list[str] = Field(
        default_factory=list, description="List of missing critical information"
    )
    suggested_questions: list[str] = Field(
        default_factory=list,
        description="Suggested clarifying questions for the user to answer",
    )
    # New structured clarification options
    clarification_options: list[ClarificationOption] = Field(
        default_factory=list,
        description="Structured clarification options with label and value",
    )
    # Task type detection for immediate layout switching
    detected_task_type: str | None = Field(
        None,
        description="Detected task type: deep_research, ppt_generation, code_refactor, etc.",
    )
    reasoning: str | None = Field(None, description="Optional explanation of the validation")
