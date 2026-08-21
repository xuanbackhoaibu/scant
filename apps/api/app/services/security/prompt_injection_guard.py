import re
from typing import Tuple, List, Dict, Any


class PromptInjectionGuard:
    """
    Prompt Injection Defense Engine (Launch Phase L4).
    Guards AI pipelines against adversarial prompt injection embedded in
    uploaded documents, web research, OCR extracts, and codebase comments.
    Enforces the UNTRUSTED CONTENT boundary.
    """

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
        r"reveal\s+(the\s+)?system\s+prompt",
        r"print\s+(the\s+)?system\s+prompt",
        r"delete\s+(the\s+)?(report|database|project|all\s+files)",
        r"drop\s+table",
        r"send\s+(project\s+)?data\s+to\s+https?://",
        r"disregard\s+(all\s+)?instructions?",
        r"you\s+are\s+now\s+in\s+dan\s+mode",
        r"bypass\s+(safety|content)\s+filters?",
        r"override\s+system\s+directive",
    ]

    COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

    @classmethod
    def sanitize_untrusted_input(cls, content: str, source_label: str = "document") -> Tuple[str, bool, List[str]]:
        """
        Sanitizes untrusted text by wrapping it in strict XML data boundaries
        and neutralizing active jailbreak phrases.
        Returns: (sanitized_content, is_flagged, detected_attacks)
        """
        detected = []
        for pattern in cls.COMPILED_PATTERNS:
            matches = pattern.findall(content)
            if matches:
                detected.append(pattern.pattern)

        is_flagged = len(detected) > 0

        # Neutralize dangerous phrases in the untrusted text
        cleaned = content
        for pattern in cls.COMPILED_PATTERNS:
            cleaned = pattern.sub("[REDACTED_UNTRUSTED_INSTRUCTION]", cleaned)

        # Enforce strict untrusted data isolation framing
        framed = f"""<{source_label.upper()}_DATA_UNTRUSTED>
{cleaned}
</{source_label.upper()}_DATA_UNTRUSTED>"""

        return framed, is_flagged, detected


prompt_injection_guard = PromptInjectionGuard()
