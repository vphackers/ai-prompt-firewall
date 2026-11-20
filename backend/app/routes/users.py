
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db

from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserListResponse,
    UserUpdate
)

from app.services.user_service import (
    create_user,
    get_all_users,
    get_user_by_id,
    update_user,
    delete_user
)





# ==========================================
# CREATE ROUTER
# ==========================================

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# ==========================================
# 1. REGISTER USER
# ==========================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):

    new_user, api_key = create_user(
        db=db,
        name=user_data.name,
        email=user_data.email
    )

    if new_user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered."
        )

    return {
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "api_key": api_key,
        "created_at": new_user.created_at
    }


# ==========================================
# 2. GET ALL USERS
# ==========================================

@router.get(
    "/",
    response_model=List[UserListResponse]
)
def list_users(
    db: Session = Depends(get_db)
):

    users = get_all_users(db)

    return users


# ==========================================
# 3. GET USER BY ID
# ==========================================

@router.get(
    "/{user_id}",
    response_model=UserListResponse
)
def retrieve_user(
    user_id: int,
    db: Session = Depends(get_db)
):

    user = get_user_by_id(
        db=db,
        user_id=user_id
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    return user

# ==========================================
# 4. UPDATE USER
# ==========================================

@router.put(
    "/{user_id}",
    response_model=UserListResponse
)
def update_existing_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):

    # Call the update service
    updated_user, error = update_user(
        db=db,
        user_id=user_id,
        name=user_data.name,
        email=user_data.email
    )

    # Handle user not found
    if error == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Handle duplicate email
    if error == "email_exists":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered."
        )

    return updated_user
@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_existing_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    result = delete_user(db=db, user_id=user_id)

    if result == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    if result == "has_audit_logs":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User cannot be deleted because audit records are associated with this account."
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)