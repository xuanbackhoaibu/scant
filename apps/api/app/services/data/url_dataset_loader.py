import base64
import ipaddress
import re
import socket
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import parse_qs, quote, unquote, urlparse

import httpx


class UrlDatasetLoader:
    MAX_BYTES = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".xlsm"}
    BLOCKED_HOSTNAMES = {"localhost", "0.0.0.0", "127.0.0.1", "::1", "metadata.google.internal"}

    @classmethod
    def is_google_sheets(cls, url: str) -> bool:
        parsed = urlparse((url or "").strip())
        netloc = parsed.netloc.lower()
        return any(
            netloc == domain or netloc.endswith("." + domain)
            for domain in ["docs.google.com", "drive.google.com", "spreadsheets.google.com"]
        )

    @classmethod
    def get_google_sheet_candidates(cls, url: str, sheet_range: Optional[str] = None) -> List[str]:
        trimmed = (url or "").strip()
        parsed = urlparse(trimmed)
        path = parsed.path

        # 1. Published web spreadsheet: /spreadsheets/d/e/{pub_id}/pubhtml or /pub
        m_pub = re.search(r"/d/e/([a-zA-Z0-9-_]+)", path)
        if m_pub:
            pub_id = m_pub.group(1)
            return [
                f"https://docs.google.com/spreadsheets/d/e/{quote(pub_id)}/pub?output=xlsx",
                f"https://docs.google.com/spreadsheets/d/e/{quote(pub_id)}/pub?output=csv",
            ]

        # 2. Extract sheet_id from /d/{id} or query id={id}
        sheet_id = None
        m_id = re.search(r"/d/([a-zA-Z0-9-_]+)", path)
        if m_id:
            sheet_id = m_id.group(1)
        else:
            q = parse_qs(parsed.query)
            if "id" in q:
                sheet_id = q["id"][0]

        if not sheet_id:
            return [trimmed]

        query_params = parse_qs(parsed.query)
        fragment_params = parse_qs(parsed.fragment) if parsed.fragment else {}
        raw_gid = (
            query_params.get("gid", [None])[0]
            or fragment_params.get("gid", [None])[0]
            or "0"
        )
        gid = raw_gid if (raw_gid and raw_gid.isdigit()) else "0"

        sheet_name = ""
        a1_range = ""
        if sheet_range and sheet_range.strip():
            sr = sheet_range.strip()
            if "!" in sr:
                sheet_name, a1_range = sr.split("!", 1)
            elif re.fullmatch(r"[A-Za-z]{1,3}\d+:[A-Za-z]{1,3}\d+", sr):
                a1_range = sr
            else:
                sheet_name = sr

        sheet_name = sheet_name.strip().strip("'\"")
        a1_range = a1_range.strip().upper()

        candidates: List[str] = []

        if sheet_name:
            range_param = f"&range={quote(a1_range)}" if a1_range else ""
            candidates.append(
                f"https://docs.google.com/spreadsheets/d/{quote(sheet_id)}/gviz/tq?tqx=out:csv&sheet={quote(sheet_name)}{range_param}"
            )
            candidates.append(
                f"https://docs.google.com/spreadsheets/d/{quote(sheet_id)}/export?format=xlsx"
            )
            candidates.append(
                f"https://docs.google.com/spreadsheets/d/{quote(sheet_id)}/export?format=csv&gid={quote(gid)}"
            )
        elif a1_range:
            candidates.append(
                f"https://docs.google.com/spreadsheets/d/{quote(sheet_id)}/gviz/tq?tqx=out:csv&gid={quote(gid)}&range={quote(a1_range)}"
            )
            candidates.append(
                f"https://docs.google.com/spreadsheets/d/{quote(sheet_id)}/export?format=xlsx"
            )
            candidates.append(
                f"https://docs.google.com/spreadsheets/d/{quote(sheet_id)}/export?format=csv&gid={quote(gid)}"
            )
        else:
            candidates.append(
                f"https://docs.google.com/spreadsheets/d/{quote(sheet_id)}/export?format=xlsx"
            )
            candidates.append(
                f"https://docs.google.com/spreadsheets/d/{quote(sheet_id)}/export?format=csv&gid={quote(gid)}"
            )
            candidates.append(
                f"https://docs.google.com/spreadsheets/d/{quote(sheet_id)}/gviz/tq?tqx=out:csv&gid={quote(gid)}"
            )
            candidates.append(
                f"https://docs.google.com/spreadsheets/d/{quote(sheet_id)}/gviz/tq?tqx=out:csv"
            )

        return candidates

    @classmethod
    def normalize_url(cls, url: str, sheet_range: Optional[str] = None) -> str:
        candidates = cls.get_google_sheet_candidates(url, sheet_range=sheet_range)
        return candidates[0] if candidates else (url or "").strip()

    @classmethod
    def filename_from_url(cls, url: str, content_type: str = "", sheet_range: Optional[str] = None) -> str:
        parsed = urlparse(url)
        path_name = Path(unquote(parsed.path)).name
        ct = (content_type or "").lower()

        if cls.is_google_sheets(url) or "spreadsheet" in parsed.netloc:
            clean_name = "google_sheet"
            if sheet_range and sheet_range.strip():
                safe_range = re.sub(r"[^a-zA-Z0-9_\-]", "_", sheet_range.strip())
                clean_name = f"google_sheet_{safe_range}"
            if "spreadsheetml" in ct or "openxmlformats" in ct or "excel" in ct or "format=xlsx" in url or "output=xlsx" in url:
                return f"{clean_name}.xlsx"
            return f"{clean_name}.csv"

        if Path(path_name).suffix.lower() in cls.ALLOWED_EXTENSIONS:
            return path_name

        if "spreadsheetml" in ct or "openxmlformats" in ct or "excel" in ct:
            return path_name if path_name.endswith(".xlsx") else f"{path_name or 'linked_dataset'}.xlsx"
        if "csv" in ct or "text/plain" in ct:
            return path_name if path_name.endswith(".csv") else f"{path_name or 'linked_dataset'}.csv"

        return path_name or "linked_dataset.xlsx"

    @classmethod
    def _validate_public_host(cls, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Chỉ hỗ trợ liên kết http/https công khai.")

        host = parsed.hostname
        if not host:
            raise ValueError("Đường dẫn liên kết không hợp lệ.")

        lowered_host = host.lower()
        if lowered_host in cls.BLOCKED_HOSTNAMES or lowered_host.endswith(".local") or lowered_host.endswith(".internal"):
            raise ValueError("Không cho phép tải dữ liệu từ địa chỉ máy chủ nội bộ (SSRF Protection).")

        try:
            addr_info = socket.getaddrinfo(host, None)
        except socket.gaierror:
            raise ValueError(f"Không thể phân giải tên miền: {host}. Vui lòng kiểm tra lại URL.")

        for info in addr_info:
            raw_ip = info[4][0]
            ip = ipaddress.ip_address(raw_ip)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
                or ip.is_unspecified
                or str(ip).startswith("169.254.")
            ):
                raise ValueError("Không cho phép tải dữ liệu từ địa chỉ IP mạng nội bộ/private (SSRF Protection).")

    @classmethod
    def _load_data_url(cls, url: str) -> Tuple[bytes, str, str]:
        header, payload = url.split(",", 1)
        mime = header[5:].split(";")[0] or "text/csv"
        contents = base64.b64decode(payload) if ";base64" in header else unquote(payload).encode("utf-8")
        if len(contents) > cls.MAX_BYTES:
            raise ValueError("Dữ liệu vượt quá giới hạn dung lượng 50MB.")
        filename = "linked_dataset.csv" if "csv" in mime or "text/plain" in mime else "linked_dataset.xlsx"
        return contents, filename, mime

    @classmethod
    def _is_html_content(cls, contents: bytes, content_type: str) -> bool:
        sample_bytes = contents[:600].lower()
        return (
            b"<!doctype html" in sample_bytes
            or b"<html" in sample_bytes
            or b"<head" in sample_bytes
            or "text/html" in (content_type or "").lower()
        )

    @classmethod
    async def load(cls, url: str, sheet_range: Optional[str] = None) -> Tuple[bytes, str, str]:
        raw_url = (url or "").strip()
        if not raw_url:
            raise ValueError("Vui lòng nhập đường liên kết dữ liệu.")

        if raw_url.startswith("data:"):
            raise ValueError("Chỉ hỗ trợ liên kết http/https công khai.")

        timeout = httpx.Timeout(20.0, connect=8.0)
        headers = {
            "User-Agent": "Mozilla/5.0 (AI Report Studio Dataset Loader; compatible)",
            "Accept": "text/csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel, */*",
        }

        # 1. Google Sheets with Candidate Fallbacks
        if cls.is_google_sheets(raw_url):
            candidates = cls.get_google_sheet_candidates(raw_url, sheet_range=sheet_range)
            last_status = 0
            had_html = False

            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, max_redirects=4) as client:
                for candidate_url in candidates:
                    cls._validate_public_host(candidate_url)
                    try:
                        resp = await client.get(candidate_url, headers=headers)
                        if resp.history:
                            for redirect_resp in resp.history:
                                cls._validate_public_host(str(redirect_resp.url))
                        cls._validate_public_host(str(resp.url))

                        last_status = resp.status_code
                        if resp.status_code == 200:
                            content_type = resp.headers.get("content-type", "").lower()
                            if not cls._is_html_content(resp.content, content_type) and len(resp.content.strip()) > 0:
                                filename = cls.filename_from_url(raw_url, content_type, sheet_range=sheet_range)
                                return resp.content, filename, content_type or "text/csv"
                            else:
                                had_html = True
                    except (httpx.TimeoutException, httpx.RequestError):
                        continue

            if last_status == 404:
                raise ValueError(
                    "Không tìm thấy Google Sheet tại liên kết này (HTTP 404). Vui lòng kiểm tra lại URL hoặc ID bảng tính."
                )
            if last_status in (401, 403):
                raise ValueError(
                    "Không có quyền truy cập Google Sheet (HTTP 403). Hãy mở quyền chia sẻ ở chế độ 'Bất kỳ ai có đường liên kết đều có thể xem'."
                )
            if had_html or last_status == 400:
                raise ValueError(
                    "Không thể đọc dữ liệu từ Google Sheet này. Hãy kiểm tra quyền chia sẻ (đặt thành 'Bất kỳ ai có đường liên kết đều có thể xem') hoặc kiểm tra tên sheet/range."
                )
            raise ValueError(
                "Không thể kết nối hoặc tải dữ liệu từ Google Sheet. Vui lòng kiểm tra lại liên kết."
            )

        # 2. General Public URL
        cls._validate_public_host(raw_url)
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, max_redirects=4) as client:
                response = await client.get(raw_url, headers=headers)
                if response.history:
                    for redirect_resp in response.history:
                        cls._validate_public_host(str(redirect_resp.url))
                cls._validate_public_host(str(response.url))

                if response.status_code in (401, 403):
                    raise ValueError(
                        f"Không có quyền truy cập liên kết (HTTP {response.status_code}). Vui lòng đảm bảo tệp được đặt ở chế độ công khai."
                    )
                elif response.status_code == 404:
                    raise ValueError(f"Không tìm thấy tệp tại liên kết này (HTTP 404). Vui lòng kiểm tra lại URL.")
                elif response.status_code == 400:
                    raise ValueError("Liên kết trả về mã lỗi 400 (Bad Request). Vui lòng kiểm tra lại đường dẫn.")
                elif response.status_code == 429:
                    raise ValueError("Quá nhiều yêu cầu tới liên kết (HTTP 429). Vui lòng thử lại sau ít phút.")
                elif response.status_code >= 400:
                    raise ValueError(f"Máy chủ trả về mã lỗi HTTP {response.status_code}.")

                contents = response.content
        except httpx.TimeoutException:
            raise ValueError("Kết nối tới liên kết quá thời gian chờ (Timeout). Vui lòng kiểm tra lại mạng hoặc liên kết.")
        except httpx.RequestError as req_err:
            raise ValueError(f"Lỗi khi kết nối tới liên kết dữ liệu: {str(req_err)}")

        if not contents or len(contents.strip()) == 0:
            raise ValueError("Dữ liệu tải về từ liên kết bị trống.")

        if len(contents) > cls.MAX_BYTES:
            raise ValueError("Dung lượng tệp từ liên kết vượt quá giới hạn 50MB.")

        content_type = response.headers.get("content-type", "").lower()
        if cls._is_html_content(contents, content_type):
            raise ValueError(
                "Không thể đọc dữ liệu từ liên kết này. Liên kết trả về trang web HTML thay vì tệp dữ liệu CSV/Excel."
            )

        filename = cls.filename_from_url(str(response.url), content_type, sheet_range=sheet_range)
        ext = Path(filename).suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise ValueError("Liên kết phải trỏ tới tệp CSV, XLSX, XLS hoặc Google Sheet công khai.")

        return contents, filename, content_type or "application/octet-stream"


url_dataset_loader = UrlDatasetLoader()
