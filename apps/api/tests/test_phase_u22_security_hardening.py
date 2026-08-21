import io
import zipfile
import pytest
from app.services.security.ssrf_validator import ssrf_validator
from app.services.security.upload_validator import upload_validator, MalwareScanner
from app.services.security.secret_manager import secret_manager


def test_ssrf_protection():
    # 1. Block internal addresses & cloud metadata
    blocked_urls = [
        "http://localhost:8080/admin",
        "http://127.0.0.1:5432/query",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5/internal-api",
        "http://192.168.1.1/router",
        "ftp://example.com/file",
    ]
    for url in blocked_urls:
        is_safe, msg = ssrf_validator.is_url_safe(url)
        assert is_safe is False
        assert msg is not None

    # 2. Allow public internet domains
    safe_urls = [
        "https://example.com/api/v1/data",
        "https://api.github.com/repos",
    ]
    for url in safe_urls:
        is_safe, _ = ssrf_validator.is_url_safe(url)
        assert is_safe is True


def test_upload_security_and_magic_bytes():
    # 1. Valid PDF with %PDF header
    valid_pdf = b"%PDF-1.5 \n1 0 obj\n<<>>\nendobj"
    ok, _ = upload_validator.validate_upload(valid_pdf, "document.pdf")
    assert ok is True

    # 2. Fake PDF with wrong header
    fake_pdf = b"This is just a text file pretending to be PDF"
    ok_fake, msg_fake = upload_validator.validate_upload(fake_pdf, "malicious.pdf")
    assert ok_fake is False
    assert "giả mạo" in msg_fake

    # 3. Block executable
    exe_data = b"MZ\x90\x00\x03\x00\x00\x00"
    ok_exe, msg_exe = upload_validator.validate_upload(exe_data, "payload.exe")
    assert ok_exe is False
    assert "bị cấm" in msg_exe

    # 4. Zip with Path Traversal
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("../../etc/passwd", "root:x:0:0:root:/root:/bin/bash")
    ok_zip, msg_zip = upload_validator.validate_upload(zip_buf.getvalue(), "archive.zip")
    assert ok_zip is False
    assert "Path Traversal" in msg_zip


def test_malware_scanner_hook():
    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    ok, msg = MalwareScanner.scan_bytes(eicar, "sample.txt")
    assert ok is False
    assert "mã độc" in msg


def test_secret_management_and_masking():
    raw_creds = {
        "host": "prod-db.internal",
        "database": "sales",
        "password": "SuperSecretPassword123!",
        "api_key": "sk-1234567890abcdef",
        "port": 5432
    }
    # 1. Encrypt and Decrypt
    enc = secret_manager.encrypt_secret(raw_creds)
    assert enc.startswith("enc_v1:")
    dec = secret_manager.decrypt_secret(enc)
    assert dec["password"] == "SuperSecretPassword123!"

    # 2. Masking
    masked = secret_manager.mask_secrets(raw_creds)
    assert masked["password"] == "••••••••"
    assert masked["api_key"] == "••••••••"
    assert masked["host"] == "prod-db.internal"
    assert masked["port"] == 5432
