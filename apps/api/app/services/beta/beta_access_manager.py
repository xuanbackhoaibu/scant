from typing import Any, Dict, List, Optional, Set


class BetaAccessManager:
    """
    Beta Mode & Closed-Testing Access Control (Launch Phase L18).
    Supports invite-only registrations, invite codes, and email allowlists.
    """

    def __init__(self, beta_mode_enabled: bool = False):
        self.beta_mode_enabled = beta_mode_enabled
        self.allowlist_emails: Set[str] = set()
        self.invite_codes: Set[str] = set()

    def set_beta_mode(self, enabled: bool):
        self.beta_mode_enabled = enabled

    def invite_email(self, email: str):
        self.allowlist_emails.add(email.lower().strip())

    def revoke_invite(self, email: str):
        self.allowlist_emails.discard(email.lower().strip())

    def create_invite_code(self, code: str):
        self.invite_codes.add(code.strip())

    def is_access_allowed(self, email: str, invite_code: Optional[str] = None) -> bool:
        if not self.beta_mode_enabled:
            return True  # Open access when Beta Mode is off

        email_clean = email.lower().strip()
        if email_clean in self.allowlist_emails:
            return True

        if invite_code and invite_code.strip() in self.invite_codes:
            return True

        return False


beta_access_manager = BetaAccessManager(beta_mode_enabled=False)
