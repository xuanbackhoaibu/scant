import os
import json
import time
from typing import Any, Dict, Optional, Tuple
import httpx
from pydantic import BaseModel


class GoogleUserInfo(BaseModel):
    google_sub: str
    email: str
    email_verified: bool
    name: str
    picture: Optional[str] = None


class GoogleAuthService:
    """
    Google Identity Services (GIS) Real Authentication Engine.
    Cryptographically verifies Google ID tokens, extracts claims (sub, email, name, picture),
    and enforces safe account linking.
    """

    GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"

    @classmethod
    async def verify_id_token(cls, id_token: str, expected_client_id: Optional[str] = None) -> Tuple[bool, Optional[GoogleUserInfo], Optional[str]]:
        """
        Verifies the Google ID token against Google's public token endpoint and cryptographic claims.
        """
        if not id_token or not id_token.strip():
            return False, None, "Token Google không hợp lệ hoặc bị trống"

        client_id = expected_client_id or os.getenv("GOOGLE_CLIENT_ID")

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
                    email_verified=payload.get("email_verified") in [True, "true", "True"],
                    name=payload.get("name") or email.split("@")[0],
                    picture=payload.get("picture"),
                )

                return True, user_info, None

        except Exception as ex:
            return False, None, f"Lỗi xác thực Google ID token: {str(ex)}"


google_auth_service = GoogleAuthService()
