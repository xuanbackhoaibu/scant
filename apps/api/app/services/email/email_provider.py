from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class EmailMessage(BaseModel):
    to_email: str
    subject: str
    html_body: str
    text_body: str
    metadata: Dict[str, Any] = {}


class BaseEmailProvider(ABC):
    """Abstract Email Service Provider Interface (Launch Phase L16)."""

    @abstractmethod
    async def send_email(self, message: EmailMessage) -> bool:
        pass


class ConsoleEmailProvider(BaseEmailProvider):
    """Logs transactional emails to memory/console for development & testing."""

    def __init__(self):
        self.sent_messages: List[EmailMessage] = []

    async def send_email(self, message: EmailMessage) -> bool:
        self.sent_messages.append(message)
        return True


class EmailService:
    """High-level transactional email dispatcher supporting multiple backend providers."""

    def __init__(self, provider: Optional[BaseEmailProvider] = None):
        self.provider = provider or ConsoleEmailProvider()

    def set_provider(self, provider: BaseEmailProvider):
        self.provider = provider

    async def send_verification_email(self, to_email: str, verify_token: str) -> bool:
        msg = EmailMessage(
            to_email=to_email,
            subject="Xác thực tài khoản AI Report Studio",
            html_body=f"<p>Mã xác thực của bạn là: <strong>{verify_token}</strong></p>",
            text_body=f"Mã xác thực của bạn là: {verify_token}",
            metadata={"type": "verification"}
        )
        return await self.provider.send_email(msg)

    async def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        msg = EmailMessage(
            to_email=to_email,
            subject="Đặt lại mật khẩu AI Report Studio",
            html_body=f"<p>Liên kết đặt lại mật khẩu: https://app.example.com/reset-password?token={reset_token}</p>",
            text_body=f"Liên kết đặt lại mật khẩu: https://app.example.com/reset-password?token={reset_token}",
            metadata={"type": "password_reset"}
        )
        return await self.provider.send_email(msg)

    async def send_report_completed(self, to_email: str, report_title: str, download_url: str) -> bool:
        msg = EmailMessage(
            to_email=to_email,
            subject=f"Báo cáo '{report_title}' đã hoàn tất biên tập",
            html_body=f"<p>Báo cáo của bạn đã sẵn sàng tải về: <a href='{download_url}'>Tải xuống</a></p>",
            text_body=f"Báo cáo của bạn đã sẵn sàng tải về: {download_url}",
            metadata={"type": "report_completed"}
        )
        return await self.provider.send_email(msg)


email_service = EmailService()
