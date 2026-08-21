import io
import zipfile
from typing import Optional, Tuple
from pathlib import Path


class MalwareScanner:
    """Pluggable Malware Scanner Hook (Phase U22)."""

    @classmethod
    def scan_bytes(cls, data: bytes, filename: str) -> Tuple[bool, str]:
        # Production hook for ClamAV / VirusTotal API
        # By default, perform heuristic signature check
        if b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*" in data:
            return (False, "Phát hiện mã độc (EICAR Antivirus Test Signature).")
        return (True, "Tập tin an toàn.")


class UploadSecurityValidator:
    """
    Advanced Upload Security & Archive Inspection (Phase U22).
    Enforces Magic Bytes inspection, ZIP bomb mitigation, Path Traversal protection, and Malware Scanning.
    """

    MAGIC_SIGNATURES = {
        ".pdf": b"%PDF",
        ".zip": b"PK\x03\x04",
        ".docx": b"PK\x03\x04",
        ".xlsx": b"PK\x03\x04",
        ".pptx": b"PK\x03\x04",
        ".png": b"\x89PNG\r\n\x1a\n",
        ".jpg": b"\xff\xd8\xff",
        ".jpeg": b"\xff\xd8\xff",
    }

    DANGEROUS_EXTENSIONS = {
        ".exe", ".bat", ".cmd", ".sh", ".bash", ".bin", ".elf",
        ".vbs", ".ps1", ".msi", ".dll", ".so", ".dylib", ".scr"
    }

    MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES = 100 * 1024 * 1024  # 100MB
    MAX_ZIP_COMPRESSION_RATIO = 100.0

    @classmethod
    def validate_upload(
        cls,
        data: bytes,
        filename: str
    ) -> Tuple[bool, Optional[str]]:
        ext = Path(filename).suffix.lower()

        # 1. Malware Scan Hook
        is_clean, scan_msg = MalwareScanner.scan_bytes(data, filename)
        if not is_clean:
            return (False, scan_msg)

        # 2. Dangerous Extension Check
        if ext in cls.DANGEROUS_EXTENSIONS:
            return (False, f"Định dạng tập tin bị cấm vì lý do an ninh: {ext}")

        # 3. Magic Bytes Validation
        if ext in cls.MAGIC_SIGNATURES:
            expected_sig = cls.MAGIC_SIGNATURES[ext]
            if not data.startswith(expected_sig):
                return (False, f"Tập tin giả mạo phần mở rộng {ext} (Header không khớp magic bytes).")

        # 4. ZIP & Office Archive Deep Inspection
        if ext in [".zip", ".docx", ".xlsx", ".pptx"]:
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    total_uncompressed = 0
                    for info in zf.infolist():
                        # Path Traversal Check
                        if info.filename.startswith("/") or ".." in info.filename or "\\" in info.filename:
                            return (False, f"Phát hiện tấn công Path Traversal trong archive: {info.filename}")

                        # Executable inside archive
                        entry_ext = Path(info.filename).suffix.lower()
                        if entry_ext in cls.DANGEROUS_EXTENSIONS:
                            return (False, f"Tập tin nén chứa mã thực thi nguy hiểm: {info.filename}")

                        total_uncompressed += info.file_size

                        # Ratio check per file
                        if info.compress_size > 0:
                            ratio = info.file_size / float(info.compress_size)
                            if ratio > cls.MAX_ZIP_COMPRESSION_RATIO and info.file_size > 5 * 1024 * 1024:
                                return (False, f"Phát hiện Zip Bomb (Tỷ lệ nén bất thường: {ratio:.1f}x)")

                    # Total uncompressed size limit
                    if total_uncompressed > cls.MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES:
                        return (False, f"Dung lượng sau giải nén vượt quá hạn mức an toàn ({total_uncompressed / (1024*1024):.1f}MB / 100MB)")

            except zipfile.BadZipFile:
                if ext == ".zip":
                    return (False, "Tập tin ZIP bị hỏng hoặc không đúng định dạng.")

        return (True, None)


upload_validator = UploadSecurityValidator()
