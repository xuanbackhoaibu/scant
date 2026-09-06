import secrets
from datetime import timedelta, datetime, timezone
from typing import List, Optional, Any
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
    GoogleAuthRequest, GoogleCodeAuthRequest, ProfileUpdateRequest, ChangePasswordRequest
)
from app.api.deps import get_current_user
from app.services.auth.google_auth_service import google_auth_service, GoogleUserInfo

router = APIRouter(prefix="/auth", tags=["auth"])
workspace_repo = BaseRepository[Workspace](Workspace)
account_repo = BaseRepository[AuthAccount](AuthAccount)


async def _process_google_user(
    user_info: GoogleUserInfo,
    db: AsyncSession,
    token_data: Optional[Any] = None,
) -> TokenResponse:
    """Helper that creates, links, or returns existing user for Google auth and records OAuth tokens."""
    if not user_info.email_verified:
        raise HTTPException(403,"Google email must be verified")
    # 1. Search user by google_sub first
    stmt = select(User).where(User.google_sub == user_info.google_sub)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user:
        # 2. Search user by email for safe account linking
        user = await user_repo.get_by_email(db, user_info.email)
        if user:
            if not user.is_active:
                raise HTTPException(403,"User account is inactive")
            # Safe link existing account
            user.google_sub = user_info.google_sub
            if user_info.picture and not user.avatar_url:
                user.avatar_url = user_info.picture
            await db.commit()
            await db.refresh(user)
        else:
            from app.services.admin.configuration_service import read_configuration
            registration=(await read_configuration(db,"system"))["values"]
            if not registration["registration_enabled"]:
                raise HTTPException(403,"Đăng ký tài khoản mới đang tạm dừng.")
            # Create new user via Google
            user = await user_repo.create(db, obj_in={
                "email": user_info.email,
                "name": user_info.name,
                "google_sub": user_info.google_sub,
                "avatar_url": user_info.picture,
                "password_hash": f"oauth_google_{secrets.token_hex(24)}",
                "plan": registration["registration_plan"],
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

    if not user.is_active:
        raise HTTPException(403, "User account is inactive")

    # Basic sign-in must never replace an existing Sheets-capable credential
    # with a narrower identity-only token. Dedicated consent uses google_data.
    if token_data and 'https://www.googleapis.com/auth/spreadsheets' not in (getattr(token_data,'scope',None) or '').split():
        token_data=None

    # Record or update Google auth account entry with tokens
    stmt_acc = select(AuthAccount).where(
        AuthAccount.user_id == user.id,
        AuthAccount.provider == "google"
    )
    acc_res = await db.execute(stmt_acc)
    existing_acc = acc_res.scalars().first()

    expiry_dt = None
    if token_data and getattr(token_data, "expires_in", None):
        expiry_dt = datetime.now(timezone.utc) + timedelta(seconds=int(token_data.expires_in))

    if not existing_acc:
        await account_repo.create(db, obj_in={
            "user_id": user.id,
            "provider": "google",
            "provider_account_id": user_info.google_sub,
            "email": user.email,
            "access_token": getattr(token_data, "access_token", None) if token_data else None,
            "refresh_token": getattr(token_data, "refresh_token", None) if token_data else None,
            "token_expiry": expiry_dt,
            "scopes": getattr(token_data, "scope", None) if token_data else None,
        })
    else:
        if token_data:
            if getattr(token_data, "access_token", None):
                existing_acc.access_token = token_data.access_token
            if getattr(token_data, "refresh_token", None):
                existing_acc.refresh_token = token_data.refresh_token
            if expiry_dt:
                existing_acc.token_expiry = expiry_dt
            if getattr(token_data, "scope", None):
                existing_acc.scopes = token_data.scope
            await db.commit()

    from app.services.usage.quota_engine import quota_engine
    await quota_engine.get_or_create_user_quota(db, user.id)

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

    return await _process_google_user(user_info, db)


@router.post("/google/code", response_model=TokenResponse)
async def login_with_google_code(req: GoogleCodeAuthRequest, db: AsyncSession = Depends(get_db)):
    """Exchanges Google OAuth2 authorization code for tokens, then creates or returns session."""
    is_valid, token_data, err_msg = await google_auth_service.exchange_code(req.code, req.redirect_uri)
    if not is_valid or not token_data or not token_data.user_info:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err_msg or "Google code exchange failed")

    return await _process_google_user(token_data.user_info, db, token_data=token_data)


@router.post("/register", response_model=TokenResponse)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await user_repo.get_by_email(db, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
    
    from app.services.admin.configuration_service import read_configuration
    registration=(await read_configuration(db,"system"))["values"]
    if not registration["registration_enabled"]:
        raise HTTPException(403,"Đăng ký tài khoản mới đang tạm dừng.")

    # Create user
    user = await user_repo.create(db, obj_in={
        "email": user_in.email,
        "name": user_in.name,
        "password_hash": get_password_hash(user_in.password),
        "plan": registration["registration_plan"],
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

    from app.services.usage.quota_engine import quota_engine
    await quota_engine.get_or_create_user_quota(db, user.id)

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

    from app.services.usage.quota_engine import quota_engine
    await quota_engine.get_or_create_user_quota(db, user.id)

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
    if not current_user.password_hash or current_user.password_hash.startswith("oauth_"):
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

from app.api.v1.google_connection import router as google_connection_router
router.include_router(google_connection_router)
