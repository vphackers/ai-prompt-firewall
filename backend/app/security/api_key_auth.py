
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.services.user_service import hash_api_key


# Read API key from request headers
api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)


def get_current_user(
    api_key: str | None = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> User:
    """
    Authenticate a user using their API key.
    """

    # Step 1: Check whether API key was provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required."
        )

    # Step 2: Hash the received API key
    hashed_key = hash_api_key(api_key)

    # Step 3: Find the user using the hashed API key
    user = db.query(User).filter(
        User.api_key == hashed_key
    ).first()

    # Step 4: Reject invalid API keys
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key."
        )

    # Step 5: Return authenticated user
    return user
