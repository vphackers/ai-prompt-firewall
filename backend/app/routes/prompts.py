
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.session import get_db

from app.models.user import User
from app.models.audit_log import PromptAuditLog

from app.schemas.prompt import (
    PromptAnalyzeRequest,
    PromptAnalyzeResponse,
    PromptAuditLogResponse
)

from app.security.prompt_pipeline import inspect_prompt
from app.security.normalizer import normalize_for_detection
from app.security.rate_limiter import check_rate_limit
from app.security.api_key_auth import get_current_user

from app.services.audit_log_service import get_all_audit_logs


router = APIRouter(
    prefix="/api/v1/prompt",
    tags=["Prompt Security"]
)


# ==========================================
# PROMPT SECURITY ANALYSIS
# ==========================================

@router.post(
    "/analyze",
    response_model=PromptAnalyzeResponse
)
def analyze_prompt(
    request: PromptAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Step 1: Apply rate limiting to authenticated user
    check_rate_limit(current_user.id)

    # Step 2: Inspect the submitted prompt
    analysis = inspect_prompt(request.prompt)

    risk_status = analysis["risk_status"]

    # Step 3: Normalize prompt for auditing
    normalized_prompt = normalize_for_detection(
        request.prompt
    )

    # Step 4: Prepare block reason
    block_reason = None

    if risk_status != "SAFE":
        block_reason = json.dumps(
            analysis.get("findings", []),
            ensure_ascii=False,
            default=str
        )

    # Step 5: Create audit log record
    audit_log = PromptAuditLog(
        user_id=current_user.id,
        raw_prompt=request.prompt,
        sanitized_prompt=normalized_prompt,
        risk_status=risk_status,
        block_reason=block_reason,
        ai_response=None
    )

    # Step 6: Save audit log in PostgreSQL
    try:
        db.add(audit_log)
        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save prompt audit log."
        )

    # Step 7: Block unsafe prompts after logging
    if risk_status != "SAFE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Prompt did not pass security checks.",
                **analysis
            }
        )

    # Step 8: Return successful security analysis
    return analysis


# ==========================================
# AUDIT LOG RETRIEVAL
# ==========================================

@router.get(
    "/audit-logs",
    response_model=List[PromptAuditLogResponse],
    status_code=status.HTTP_200_OK
)
def retrieve_audit_logs(
    risk_status: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve audit logs belonging to the authenticated user.
    """

    # Step 1: Validate pagination
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skip cannot be negative."
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100."
        )

    # Step 2: Validate risk status
    if risk_status is not None:
        risk_status = risk_status.upper()

        if risk_status not in ["SAFE", "BLOCKED", "FLAGGED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid risk status."
            )

    # Step 3: Retrieve only authenticated user's records
    logs = get_all_audit_logs(
        db=db,
        user_id=current_user.id,
        risk_status=risk_status,
        skip=skip,
        limit=limit
    )

    return logs
