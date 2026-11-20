
import secrets
import hashlib

from sqlalchemy.orm import Session

from app.models.user import User
from sqlalchemy.exc import IntegrityError


# ==========================================
# 1. API KEY GENERATION
# ==========================================

def generate_api_key() -> str:
    """
    Generate a cryptographically secure API key.
    """
    return "pf_" + secrets.token_urlsafe(32)


# ==========================================
# 2. API KEY HASHING
# ==========================================

def hash_api_key(api_key: str) -> str:
    """
    Convert API key into SHA-256 hash.
    """
    return hashlib.sha256(
        api_key.encode("utf-8")
    ).hexdigest()


# ==========================================
# 3. CREATE USER
# ==========================================

def create_user(db: Session, name: str, email: str):

    # Check whether email already exists
    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        return None, None

    # Generate a new API key
    api_key = generate_api_key()

    # Hash the API key before storing it
    hashed_key = hash_api_key(api_key)

    # Create user object
    new_user = User(
        name=name,
        email=email,
        api_key=hashed_key
    )

    try:
        # Add user to database session
        db.add(new_user)

        # Save transaction to PostgreSQL
        db.commit()

        # Retrieve generated database values
        db.refresh(new_user)

        # Return user and original API key
        return new_user, api_key

    except Exception:
        db.rollback()
        raise


# ==========================================
# 4. READ ALL USERS
# ==========================================

def get_all_users(db: Session):
    """
    Retrieve all registered users.
    """

    return db.query(User).order_by(
        User.id
    ).all()


# ==========================================
# 5. READ USER BY ID
# ==========================================

def get_user_by_id(db: Session, user_id: int):
    """
    Retrieve a specific user using ID.
    """

    return db.query(User).filter(
        User.id == user_id
    ).first()

def update_user(db: Session, user_id: int, name: str, email: str):
    """
    Update an existing user's name and email.
    """

    # Step 1: Find the user
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        return None, "not_found"

    # Step 2: Check whether another user owns this email
    existing_user = db.query(User).filter(
        User.email == email,
        User.id != user_id
    ).first()

    if existing_user:
        return None, "email_exists"

    try:
        # Step 3: Update user information
        user.name = name
        user.email = email

        # Step 4: Save changes to PostgreSQL
        db.commit()

        # Step 5: Refresh updated database values
        db.refresh(user)

        return user, None

    except Exception:
        db.rollback()
        raise
def delete_user(db: Session, user_id: int):
    """
    Delete a user if no audit records are associated.
    """

    # Step 1: Find the user
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        return "not_found"

    try:
        # Step 2: Delete the user
        db.delete(user)

        # Step 3: Save deletion to PostgreSQL
        db.commit()

        return "deleted"

    except IntegrityError:
        # Foreign key RESTRICT prevented deletion
        db.rollback()
        return "has_audit_logs"

    except Exception:
        db.rollback()
        raise
