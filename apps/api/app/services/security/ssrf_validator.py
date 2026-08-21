import ipaddress
import socket
from urllib.parse import urlparse
from typing import Optional, Tuple


class SSRFValidator:
    """
    SSRF Protection Validator (Phase U22).
    Blocks connections to loopback, private IPv4/IPv6 ranges, and cloud metadata endpoints.
    """

    BLOCKED_HOSTNAMES = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "metadata.google.internal",
        "instance-data",
    }

    @classmethod
    def is_url_safe(cls, url: str) -> Tuple[bool, Optional[str]]:
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ["http", "https"]:
                return (False, f"Giao thức URL không an toàn hoặc không được hỗ trợ: {parsed.scheme}")

            hostname = parsed.hostname
            if not hostname:
                return (False, "URL không chứa hostname hợp lệ.")

            hostname_lower = hostname.lower()
            if hostname_lower in cls.BLOCKED_HOSTNAMES:
                return (False, f"Truy cập vào hostname nội bộ bị chặn: {hostname}")

            # Resolve DNS to IP addresses
            try:
                ip_list = socket.getaddrinfo(hostname, None)
            except socket.gaierror:
                return (True, None)  # let downstream handle unresolvable domains

            for item in ip_list:
                ip_str = item[4][0]
                ip = ipaddress.ip_address(ip_str)

                # Check private, loopback, link-local, reserved, multicast
                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_reserved
                    or ip.is_multicast
                    or ip_str == "169.254.169.254"  # Cloud Instance Metadata
                ):
                    return (False, f"Địa chỉ IP mục tiêu thuộc dải mạng nội bộ/metadata bị cấm: {ip_str}")

            return (True, None)
        except Exception as e:
            return (False, f"Lỗi kiểm tra URL an toàn: {str(e)}")


ssrf_validator = SSRFValidator()
