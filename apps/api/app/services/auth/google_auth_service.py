import os
import json
import time
from typing import Any, Dict, Optional, Tuple
import httpx
from pydantic import BaseModel
from app.core.config import settings


class GoogleUserInfo(BaseModel):
    google_sub: str
    email: str
    email_verified: bool
    name: str
    picture: Optional[str] = None


class GoogleTokenData(BaseModel):
    user_info: GoogleUserInfo
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    scope: Optional[str] = None


class GoogleAuthService:
    """
    Google Identity Services (GIS) & OAuth 2.0 Real Authentication Engine.
    Handles cryptographic verification of ID tokens and exchange of authorization codes.
    """

    GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"
    GOOGLE_TOKEN_EXCHANGE_URL = "https://oauth2.googleapis.com/token"

    @classmethod
    def get_client_id(cls) -> str:
        return settings.GOOGLE_CLIENT_ID or os.getenv("GOOGLE_CLIENT_ID", "")

    @classmethod
    def get_client_secret(cls) -> str:
        return settings.GOOGLE_CLIENT_SECRET or os.getenv("GOOGLE_CLIENT_SECRET", "")

    @classmethod
    async def verify_id_token(
        cls, id_token: str, expected_client_id: Optional[str] = None
    ) -> Tuple[bool, Optional[GoogleUserInfo], Optional[str]]:
        """
        Verifies the Google ID token against Google's public token endpoint and cryptographic claims.
        """
        if not id_token or not id_token.strip():
            return False, None, "Token Google không hợp lệ hoặc bị trống"

        client_id = expected_client_id or cls.get_client_id()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{cls.GOOGLE_TOKEN_INFO_URL}?id_token={id_token}")
                if resp.status_code != 200:
                    return False, None, "Google token signature verification failed (Mã thông báo không hợp lệ)"

                payload = resp.json()

                # Validate Issuer
                iss = payload.get("iss")
                if iss not in ["accounts.google.com", "https://accounts.google.com"]:
                    return False, None, "Invalid token issuer"

                # Validate Expiry
                exp = int(payload.get("exp", 0))
                if exp < int(time.time()):
                    return False, None, "Google ID token has expired (Mã thông báo đã hết hạn)"

                # Validate Audience if Client ID configured
                if client_id and payload.get("aud") != client_id:
                    return False, None, "Token audience mismatch (Sai Client ID)"

                # Extract verified user profile
                email = payload.get("email")
                if not email:
                    return False, None, "Email claim missing in token"

                user_info = GoogleUserInfo(
                    google_sub=payload.get("sub"),
                    email=email.lower().strip(),
                    email_verified=payload.get("email_verified") in [True, "true", "True", 1],
                    name=payload.get("name") or email.split("@")[0],
                    picture=payload.get("picture"),
                )

                return True, user_info, None

        except Exception as ex:
            return False, None, f"Lỗi xác thực Google ID token: {str(ex)}"

    @classmethod
    async def exchange_code(
        cls, code: str, redirect_uri: Optional[str] = None
    ) -> Tuple[bool, Optional[GoogleTokenData], Optional[str]]:
        """
        Exchanges an OAuth 2.0 authorization code for Google tokens, then verifies and extracts user info and tokens.
        """
        if not code or not code.strip():
            return False, None, "Authorization code không hợp lệ hoặc bị trống"

        client_id = cls.get_client_id()
        client_secret = cls.get_client_secret()
        target_redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI or "http://localhost:3050/api/auth/callback/google"

        if not client_id or not client_secret:
            return False, None, "GOOGLE_CLIENT_ID hoặc GOOGLE_CLIENT_SECRET chưa được cấu hình"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                token_resp = await client.post(
                    cls.GOOGLE_TOKEN_EXCHANGE_URL,
                    data={
                        "code": code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": target_redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if token_resp.status_code != 200:
                    err_data = token_resp.json() if token_resp.headers.get("content-type", "").startswith("application/json") else {}
                    err_desc = err_data.get("error_description") or err_data.get("error") or token_resp.text
                    return False, None, f"Google OAuth token exchange failed: {err_desc}"

                token_data = token_resp.json()
                id_token = token_data.get("id_token")
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in")
                scope = token_data.get("scope")

                user_info = None
                if id_token:
                    is_valid, uinfo, err = await cls.verify_id_token(id_token, expected_client_id=client_id)
                    if is_valid and uinfo:
                        user_info = uinfo

                # Fallback to userinfo endpoint with access_token if id_token not returned or user_info empty
                if not user_info and access_token:
                    userinfo_resp = await client.get(
                        "https://www.googleapis.com/oauth2/v3/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    if userinfo_resp.status_code == 200:
                        uinfo = userinfo_resp.json()
                        user_info = GoogleUserInfo(
                            google_sub=uinfo.get("sub"),
                            email=uinfo.get("email", "").lower().strip(),
                            email_verified=uinfo.get("email_verified", True),
                            name=uinfo.get("name") or uinfo.get("email", "").split("@")[0],
                            picture=uinfo.get("picture"),
                        )

                if user_info:
                    return True, GoogleTokenData(
                        user_info=user_info,
                        access_token=access_token,
                        refresh_token=refresh_token,
                        expires_in=expires_in,
                        scope=scope,
                    ), None

                return False, None, "Không nhận được ID token hoặc Access token từ Google"

        except Exception as ex:
            return False, None, f"Lỗi trao đổi mã Google OAuth: {str(ex)}"


google_auth_service = GoogleAuthService()
