from datetime import timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.entities import User, Workspace, AuthAccount
from app.repositories.user_repo import user_repo
from app.repositories.base import BaseRepository
from app.schemas.auth import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    GoogleAuthRequest, ProfileUpdateRequest, ChangePasswordRequest
)
from app.api.deps import get_current_user
from app.services.auth.google_auth_service import google_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
workspace_repo = BaseRepository[Workspace](Workspace)
account_repo = BaseRepository[AuthAccount](AuthAccount)


@router.post("/register", response_model=TokenResponse)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await user_repo.get_by_email(db, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
    
    # Create user
    user = await user_repo.create(db, obj_in={
        "email": user_in.email,
        "name": user_in.name,
        "password_hash": get_password_hash(user_in.password),
        "plan": "pro",
        "is_active": True,
        "preferred_locale": "vi",
        "theme": "system",
        "document_language": "vi",
    })

    # Record password auth account
    await account_repo.create(db, obj_in={
        "user_id": user.id,
        "provider": "password",
        "provider_account_id": user.email,
        "email": user.email,
    })

    # Create default personal workspace
    await workspace_repo.create(db, obj_in={
        "user_id": user.id,
        "name": f"{user.name}'s Workspace",
        "slug": f"workspace-{user.id[:8]}",
        "settings_json": {},
        "brand_kit_json": {},
    })

    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await user_repo.get_by_email(db, user_in.email)
    if not user or not user.password_hash or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )

    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/google", response_model=TokenResponse)
async def login_with_google(req: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Authenticates or signs up user via verified Google ID Token."""
    is_valid, user_info, err_msg = await google_auth_service.verify_id_token(req.credential)
    if not is_valid or not user_info:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err_msg or "Google token validation failed")

    # 1. Search user by google_sub first
    stmt = select(User).where(User.google_sub == user_info.google_sub)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user:
        # 2. Search user by email for safe account linking
        user = await user_repo.get_by_email(db, user_info.email)
        if user:
            # Safe link existing account
            user.google_sub = user_info.google_sub
            if user_info.picture and not user.avatar_url:
                user.avatar_url = user_info.picture
            await db.commit()
            await db.refresh(user)
        else:
            # Create new user via Google
            user = await user_repo.create(db, obj_in={
                "email": user_info.email,
                "name": user_info.name,
                "google_sub": user_info.google_sub,
                "avatar_url": user_info.picture,
                "password_hash": None,
                "plan": "pro",
                "is_active": True,
                "preferred_locale": "vi",
                "theme": "system",
                "document_language": "vi",
            })

            # Create default personal workspace
            await workspace_repo.create(db, obj_in={
                "user_id": user.id,
                "name": f"{user.name}'s Workspace",
                "slug": f"workspace-{user.id[:8]}",
                "settings_json": {},
                "brand_kit_json": {},
            })

    # Record Google auth account entry if missing
    stmt_acc = select(AuthAccount).where(
        AuthAccount.user_id == user.id,
        AuthAccount.provider == "google"
    )
    acc_res = await db.execute(stmt_acc)
    if not acc_res.scalars().first():
        await account_repo.create(db, obj_in={
            "user_id": user.id,
            "provider": "google",
            "provider_account_id": user_info.google_sub,
            "email": user.email,
        })

    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates user profile preferences (name, locale, theme, document_language)."""
    if req.name is not None and req.name.strip():
        current_user.name = req.name.strip()
    if req.avatar_url is not None:
        current_user.avatar_url = req.avatar_url
    if req.preferred_locale in ["vi", "en"]:
        current_user.preferred_locale = req.preferred_locale
    if req.theme in ["light", "dark", "system"]:
        current_user.theme = req.theme
    if req.document_language in ["vi", "en", "auto"]:
        current_user.document_language = req.document_language

    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.put("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Securely updates password after verifying old password."""
    if not current_user.password_hash:
        # OAuth user setting password for the first time
        current_user.password_hash = get_password_hash(req.new_password)
    else:
        if not verify_password(req.old_password, current_user.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mật khẩu hiện tại không chính xác")
        current_user.password_hash = get_password_hash(req.new_password)

    await db.commit()
    return {"message": "Mật khẩu đã được thay đổi thành công"}


@router.get("/accounts")
async def list_linked_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists linked authentication methods."""
    stmt = select(AuthAccount).where(AuthAccount.user_id == current_user.id)
    res = await db.execute(stmt)
    accounts = res.scalars().all()
    return [
        {
            "provider": acc.provider,
            "email": acc.email,
            "created_at": acc.created_at.isoformat() if acc.created_at else None
        }
        for acc in accounts
    ]
