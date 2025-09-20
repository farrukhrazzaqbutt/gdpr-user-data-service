"""
Dependency injection utilities
"""
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db import get_db
from app.auth import get_current_user, get_admin_user


# Database dependency
def get_database() -> Session:
    """Get database session"""
    return Depends(get_db)


# Authentication dependencies
def get_current_user_dep():
    """Get current authenticated user"""
    return Depends(get_current_user)


def get_admin_user_dep():
    """Get current admin user"""
    return Depends(get_admin_user)
