from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "qa_dashboard" / "backend" / "app.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = APP_PATH.with_name(f"app.py.backup_before_curl_masking_{timestamp}")
shutil.copy2(APP_PATH, backup_path)

text = APP_PATH.read_text()

mask_code = r'''

# ============================================================
# Sensitive Data Masking for cURL Test
# ============================================================

def _qa_mask_sensitive_headers(headers):
    masked = {}

    sensitive_keys = [
        "authorization",
        "proxy-authorization",
        "x-api-key",
        "apikey",
        "api-key",
        "cookie",
        "set-cookie",
        "x-auth-token",
        "token",
        "access-token",
        "refresh-token",
    ]

    for key, value in (headers or {}).items():
        lowered = str(key).lower()

        if any(secret_key in lowered for secret_key in sensitive_keys):
            masked[key] = "***MASKED***"
        else:
            masked[key] = value

    return masked


def _qa_mask_sensitive_text(value):
    import re

    text_value = str(value or "")

    patterns = [
        r"(Bearer\s+)[A-Za-z0-9._\-+/=]+",
        r"(authorization['\"]?\s*:\s*['\"]?)[^,'\"\s}]+",
        r"(access_token['\"]?\s*[:=]\s*['\"]?)[^,'\"\s}]+",
        r"(refresh_token['\"]?\s*[:=]\s*['\"]?)[^,'\"\s}]+",
        r"(password['\"]?\s*[:=]\s*['\"]?)[^,'\"\s}]+",
        r"(token['\"]?\s*[:=]\s*['\"]?)[^,'\"\s}]+",
        r"(api_key['\"]?\s*[:=]\s*['\"]?)[^,'\"\s}]+",
    ]

    masked = text_value

    for pattern in patterns:
        masked = re.sub(pattern, r"\1***MASKED***", masked, flags=re.I)

    return masked
'''

if "# Sensitive Data Masking for cURL Test" not in text:
    insert_at = text.find("# ============================================================\n# API cURL Test Endpoint")
    if insert_at != -1:
        text = text[:insert_at] + mask_code + "\n" + text[insert_at:]
    else:
        text = text.rstrip() + "\n" + mask_code + "\n"

    print("Inserted sensitive data masking helpers")
else:
    print("Sensitive data masking helpers already exist")

text = text.replace(
    '"headers": parsed.get("headers"),',
    '"headers": _qa_mask_sensitive_headers(parsed.get("headers")),'
)

text = text.replace(
    '"body": parsed.get("body"),',
    '"body": _qa_mask_sensitive_text(parsed.get("body")),'
)

text = text.replace(
    '"headers": response_data.get("headers"),',
    '"headers": _qa_mask_sensitive_headers(response_data.get("headers")),'
)

text = text.replace(
    'response_preview = str(response_data.get("body") or "")[:5000]',
    'response_preview = _qa_mask_sensitive_text(str(response_data.get("body") or "")[:5000])'
)

APP_PATH.write_text(text)

print(f"Backup created: {backup_path}")
