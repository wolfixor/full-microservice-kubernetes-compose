"""User management endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter()


# Pydantic models for request/response
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str = ""


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str


# In-memory storage (temporary)
users_db = {}


@router.get("/", response_model=List[UserResponse])
async def get_users():
    """Get all users."""
    return list(users_db.values())


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user by ID."""
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_create: UserCreate):
    """Create a new user."""
    import uuid
    
    user_id = str(uuid.uuid4())
    user = UserResponse(
        id=user_id,
        username=user_create.username,
        email=user_create.email,
        full_name=user_create.full_name
    )
    users_db[user_id] = user
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserCreate):
    """Update a user."""
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = UserResponse(
        id=user_id,
        username=user_update.username,
        email=user_update.email,
        full_name=user_update.full_name
    )
    users_db[user_id] = user
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    """Delete a user."""
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    del users_db[user_id]