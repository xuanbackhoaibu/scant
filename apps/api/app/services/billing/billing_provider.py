from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BillingProvider(ABC):
    """Abstract Base Class for SaaS Billing Providers (Phase U23)."""

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


class MockBillingProvider(BillingProvider):
    """Mock Provider for local testing and zero-lockin development."""

    async def create_checkout_session(
        self,
        user_id: str,
        user_email: str,
        target_plan: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        return {
            "session_id": f"cs_mock_{user_id[:8]}_{target_plan}",
            "checkout_url": f"https://checkout.example.com/pay?plan={target_plan}&uid={user_id}",
            "plan": target_plan,
            "status": "created"
        }

    async def cancel_subscription(self, subscription_id: str) -> bool:
        return True


billing_provider: BillingProvider = MockBillingProvider()
