
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator


class PromptAnalyzeRequest(BaseModel):

    prompt: str = Field(
        min_length=1,
        max_length=10000,
        description="The prompt submitted for security analysis"
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:

        if not value.strip():
            raise ValueError(
                "Prompt cannot contain only whitespace."
            )

        return value


class PromptAnalyzeResponse(BaseModel):

    is_suspicious: bool
    total_findings: int
    findings: list
    risk_score: int
    risk_status: str
    detected_categories: list[str]


class PromptAuditLogResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    raw_prompt: str
    sanitized_prompt: str | None
    risk_status: str
    block_reason: str | None
    ai_response: str | None
    created_at: datetime
