
from pydantic import BaseModel, Field
from datetime import datetime


# Input schema: information received from the user
class UserCreate(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=100
    )

    email: str = Field(
        min_length=5,
        max_length=254
    )


# Output schema: information returned after registration
class UserResponse(BaseModel):

    id: int
    name: str
    email: str
    api_key: str
    created_at: datetime

class UserListResponse(BaseModel):

    id: int
    name: str
    email: str
    created_at: datetime

# Input schema: information used to update a user
class UserUpdate(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=100
    )

    email: str = Field(
        min_length=5,
        max_length=254
    )
