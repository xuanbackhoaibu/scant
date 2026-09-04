import urllib.parse
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BillingProvider(ABC):
    """Abstract Base Class for SaaS Billing Providers."""

    @abstractmethod
    async def create_checkout_session(
        self,
        user_id: str,
        user_email: str,
        target_plan: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def cancel_subscription(self, subscription_id: str) -> bool:
        pass


class VietQRPayOSBillingProvider(BillingProvider):
    """
    VietQR & PayOS Real Payment Engine.
    Generates dynamic bank transfer QR codes conforming to NAPAS 24/7 VietQR standards.
    """

    PLAN_PRICING = {
        "pro": {"name": "Gói Chuyên Nghiệp (Pro)", "amount": 99000, "tokens": 5000000, "description": "5M Tokens, Xuất DOCX/PDF không giới hạn, Deep Research v2"},
        "enterprise": {"name": "Gói Doanh Nghiệp (Enterprise)", "amount": 299000, "tokens": 50000000, "description": "50M Tokens, Đồ thị & Sơ đồ Mermaid, Batch Generator, Ưu tiên AI tốc độ cao"},
    }

    BANK_CONFIG = {
        "bank_bin": "970422",  # MBBank BIN
        "bank_name": "MBBank (Ngân hàng Quân Đội)",
        "account_no": "0988889999",
        "account_name": "CONG TY AI REPORT STUDIO",
    }

    async def create_checkout_session(
        self,
        user_id: str,
        user_email: str,
        target_plan: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        plan_info = self.PLAN_PRICING.get(target_plan.lower(), self.PLAN_PRICING["pro"])
        amount = plan_info["amount"]
        order_code = f"VIP{user_id[:6].upper()}"
        transfer_content = f"UPGRADE {order_code} {target_plan.upper()}"

        # Generate NAPAS-compliant dynamic VietQR image URL
        encoded_content = urllib.parse.quote(transfer_content)
        encoded_acc_name = urllib.parse.quote(self.BANK_CONFIG["account_name"])
        qr_url = (
            f"https://api.vietqr.io/image/{self.BANK_CONFIG['bank_bin']}-{self.BANK_CONFIG['account_no']}-compact2.png"
            f"?amount={amount}&addInfo={encoded_content}&accountName={encoded_acc_name}"
        )

        return {
            "session_id": f"sess_vietqr_{user_id[:8]}_{target_plan}",
            "order_code": order_code,
            "target_plan": target_plan,
            "plan_name": plan_info["name"],
            "amount_vnd": amount,
            "formatted_amount": f"{amount:,.0f} đ",
            "description": plan_info["description"],
            "bank_name": self.BANK_CONFIG["bank_name"],
            "account_number": self.BANK_CONFIG["account_no"],
            "account_name": self.BANK_CONFIG["account_name"],
            "transfer_content": transfer_content,
            "qr_code_url": qr_url,
            "checkout_url": f"/settings?payment_session=sess_vietqr_{user_id[:8]}_{target_plan}",
            "expires_in_seconds": 900,
            "status": "pending_payment",
        }

    async def cancel_subscription(self, subscription_id: str) -> bool:
        return True


billing_provider: BillingProvider = VietQRPayOSBillingProvider()
