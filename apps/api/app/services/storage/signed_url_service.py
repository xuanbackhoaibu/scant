import hmac
import hashlib
import time
import base64
import json
from typing import Any, Dict, Optional, Tuple
from app.core.config import settings


class SignedURLService:
    """
    Time-Limited Signed URL Service (Phase U21).
    Generates and verifies tamper-proof HMAC signatures for private file downloads.
    """

    def __init__(self, secret_key: Optional[str] = None):
        self.secret = (secret_key or settings.JWT_SECRET).encode("utf-8")

    def generate_signed_token(
        self,
        storage_key: str,
        user_id: str,
        expires_in_seconds: int = 3600
    ) -> str:
        expires_at = int(time.time()) + expires_in_seconds
        payload = {
            "key": storage_key,
            "uid": user_id,
            "exp": expires_at,
        }
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        signature = hmac.new(self.secret, payload_bytes, hashlib.sha256).hexdigest()

        token_data = {
            "p": base64.urlsafe_b64encode(payload_bytes).decode("utf-8"),
            "s": signature,
        }
        return base64.urlsafe_b64encode(json.dumps(token_data).encode("utf-8")).decode("utf-8")

    def verify_and_decode_token(self, token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates signed download token.
        Returns: (is_valid, storage_key, error_message)
        """
        try:
            raw_token = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
            token_dict = json.loads(raw_token)
            payload_b64 = token_dict.get("p", "")
            received_sig = token_dict.get("s", "")

            payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
            expected_sig = hmac.new(self.secret, payload_bytes, hashlib.sha256).hexdigest()

            if not hmac.compare_digest(received_sig, expected_sig):
                return (False, None, "Chữ ký xác thực file không hợp lệ hoặc đã bị thay đổi.")

            payload = json.loads(payload_bytes.decode("utf-8"))
            if int(time.time()) > payload.get("exp", 0):
                return (False, None, "Liên kết tải file đã hết hạn sử dụng.")

            return (True, payload.get("key"), None)
        except Exception:
            return (False, None, "Mã token không hợp lệ.")


signed_url_service = SignedURLService()
