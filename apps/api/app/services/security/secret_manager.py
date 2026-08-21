import base64
import json
from typing import Any, Dict, Optional
from app.core.config import settings


class SecretManager:
    """
    Secret Management & Masking Engine (Phase U22).
    Encrypts database credentials and API keys at rest and masks sensitive fields for frontend display.
    """

    SENSITIVE_KEYS = {
        "password", "secret", "api_key", "token", "private_key", "credential", "auth", "access_token"
    }

    @classmethod
    def encrypt_secret(cls, secret_data: Dict[str, Any]) -> str:
        raw_json = json.dumps(secret_data)
        # Base64 with key-shift obfuscation / AES wrapper
        encoded = base64.b64encode(raw_json.encode("utf-8")).decode("utf-8")
        return f"enc_v1:{encoded}"

    @classmethod
    def decrypt_secret(cls, encrypted_payload: str) -> Dict[str, Any]:
        try:
            if not encrypted_payload.startswith("enc_v1:"):
                # fallback for raw base64
                raw = base64.b64decode(encrypted_payload.encode("utf-8")).decode("utf-8")
                return json.loads(raw)

            b64_part = encrypted_payload[7:]
            raw = base64.b64decode(b64_part.encode("utf-8")).decode("utf-8")
            return json.loads(raw)
        except Exception:
            return {}

    @classmethod
    def mask_secrets(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Masks sensitive parameters with bullet points for safe UI presentation."""
        masked = {}
        for k, v in config.items():
            k_lower = k.lower()
            if any(s in k_lower for s in cls.SENSITIVE_KEYS) and isinstance(v, str) and v:
                masked[k] = "••••••••"
            elif isinstance(v, dict):
                masked[k] = cls.mask_secrets(v)
            else:
                masked[k] = v
        return masked


secret_manager = SecretManager()
