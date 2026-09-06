"""PayOS server adapter. Prices and credentials must be explicitly configured.

API contract: https://payos.vn/docs/api/ . No browser response is payment evidence.
"""
import hashlib
import hmac
import os
import secrets
import httpx
from fastapi import HTTPException


class VietQRPayOSBillingProvider:
    name = "payos"

    @property
    def configured(self):
        return all(os.getenv(key) for key in ("PAYOS_CLIENT_ID", "PAYOS_API_KEY", "PAYOS_CHECKSUM_KEY"))

    def amount_for_plan(self, plan):
        try:
            amount = int(os.getenv(f"PAYOS_PRICE_{plan.upper()}_VND", "0"))
        except ValueError:
            return None
        return amount if 0 < amount <= 2_000_000_000 else None

    async def _request(self, method, path="", payload=None):
        if not self.configured:
            raise HTTPException(503, "Payment provider: Not configured")
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.request(method, "https://api-merchant.payos.vn/v2/payment-requests" + path,
                    headers={"x-client-id": os.environ["PAYOS_CLIENT_ID"], "x-api-key": os.environ["PAYOS_API_KEY"]}, json=payload)
                response.raise_for_status()
                result = response.json()
                if result.get("code") != "00" or not isinstance(result.get("data"), dict):
                    raise ValueError("Provider rejected request")
                return result["data"]
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise HTTPException(502, "Payment provider unavailable or returned invalid data") from exc

    async def create_checkout_session(self, user_id, user_email, target_plan, success_url, cancel_url):
        amount = self.amount_for_plan(target_plan)
        if not self.configured or amount is None:
            raise HTTPException(503, "Payment provider or plan price: Not configured")
        order_code = secrets.randbelow(8_000_000_000_000) + 1_000_000_000_000
        payload = {"amount": amount, "cancelUrl": cancel_url, "description": f"PLAN {target_plan.upper()}", "orderCode": order_code, "returnUrl": success_url}
        signing = "&".join(f"{key}={payload[key]}" for key in sorted(payload))
        payload["signature"] = hmac.new(os.environ["PAYOS_CHECKSUM_KEY"].encode(), signing.encode(), hashlib.sha256).hexdigest()
        data = await self._request("POST", payload=payload)
        if (data.get("amount") != amount or data.get("currency") != "VND" or data.get("orderCode") != order_code
                or not data.get("paymentLinkId") or not str(data.get("checkoutUrl", "")).startswith("https://")):
            raise HTTPException(502, "Payment provider returned inconsistent checkout")
        return {"session_id": data["paymentLinkId"], "order_code": str(order_code), "target_plan": target_plan,
                "amount_vnd": amount, "currency": "VND", "checkout_url": data["checkoutUrl"], "status": "pending_payment"}

    async def verify_payment(self, payment):
        # Fixed provider host and server-stored numeric order code; no user-controlled URL.
        data = await self._request("GET", "/" + payment.order_code)
        transactions = data.get("transactions")
        if not isinstance(transactions, list) or len(transactions) != 1:
            raise HTTPException(409, "Payment requires a single verified bank transaction")
        transaction = transactions[0]
        return {"session_id": data.get("id"), "order_code": str(data.get("orderCode")), "status": data.get("status"),
                "amount": data.get("amount"), "amount_paid": data.get("amountPaid"), "currency": transaction.get("currency"),
                "transaction_amount": transaction.get("amount"), "transaction_id": transaction.get("reference")}


billing_provider = VietQRPayOSBillingProvider()
