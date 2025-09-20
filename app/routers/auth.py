"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth import create_access_token, verify_password, get_password_hash
from app.models import User
from app.schemas import UserResponse
from datetime import timedelta
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    # For demo purposes, we'll use a simple admin/admin login
    if form_data.username == "admin" and form_data.password == "admin":
        access_token = create_access_token(
            data={"sub": "admin", "user_id": 1, "is_admin": True}
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    # In a real implementation, you'd check against the database
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, "hashed_password"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "is_admin": False}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/seed")
async def seed_admin():
    """Seed admin user for development (remove in production)"""
    if settings.environment != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seeding only allowed in development"
        )
    
    # Create admin token
    access_token = create_access_token(
        data={"sub": "admin", "user_id": 1, "is_admin": True}
    )
    return {
        "message": "Admin user seeded",
        "username": "admin",
        "password": "admin",
        "access_token": access_token
    }
