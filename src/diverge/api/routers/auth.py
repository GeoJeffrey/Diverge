"""
auth.py

Authentication endpoints: signup, login, refresh, me.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..schemas import (
    SignupRequest,
    LoginRequest,
    RefreshTokenRequest,
    AuthTokenResponse,
    UserProfileResponse,
    ErrorResponse,
)
from ...auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from ...db.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
def auth_signup(body: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "EMAIL_EXISTS", "message": "Email already registered."},
        )
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access = create_access_token({"sub": user.id, "email": user.email})
    refresh = create_refresh_token({"sub": user.id})
    return AuthTokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="Bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/login",
    response_model=AuthTokenResponse,
    responses={401: {"model": ErrorResponse}},
)
def auth_login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user."""
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_CREDENTIALS", "message": "Invalid email or password provided."},
        )
    access = create_access_token({"sub": user.id, "email": user.email})
    refresh = create_refresh_token({"sub": user.id})
    return AuthTokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="Bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/refresh",
    response_model=AuthTokenResponse,
    responses={401: {"model": ErrorResponse}},
)
def auth_refresh(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh expired access token."""
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_REFRESH", "message": "Invalid or expired refresh token."},
        )
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "USER_NOT_FOUND", "message": "User not found or inactive."},
        )
    access = create_access_token({"sub": user.id, "email": user.email})
    refresh = create_refresh_token({"sub": user.id})
    return AuthTokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="Bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    responses={401: {"model": ErrorResponse}},
)
def get_auth_me(current_user: User = Depends(get_current_user)):
    """Retrieve authenticated user profile."""
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        created_at=current_user.created_at,
    )
