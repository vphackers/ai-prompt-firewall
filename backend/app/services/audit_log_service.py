
from sqlalchemy.orm import Session

from app.models.audit_log import PromptAuditLog


def get_all_audit_logs(
    db: Session,
    user_id: int,
    risk_status: str | None = None,
    skip: int = 0,
    limit: int = 50
):
    """
    Retrieve audit logs belonging only to the specified user.

    Supports risk-status filtering and pagination.
    """

    # Step 1: Restrict records to the specified user
    query = db.query(PromptAuditLog).filter(
        PromptAuditLog.user_id == user_id
    )

    # Step 2: Filter by risk status if provided
    if risk_status is not None:
        query = query.filter(
            PromptAuditLog.risk_status == risk_status.upper()
        )

    # Step 3: Return newest records first
    query = query.order_by(
        PromptAuditLog.created_at.desc()
    )

    # Step 4: Apply pagination
    return query.offset(skip).limit(limit).all()
