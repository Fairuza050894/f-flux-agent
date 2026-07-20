from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_custom_smoke_credential_v3_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# Custom Smoke Credential Resolver V3
# Use same credential source pattern as Registered QA config:
# creds.user_env + creds.pass_env
# ============================================================

def _custom_smoke_resolve_credentials_v3():
    import os
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]

    try:
        from dotenv import load_dotenv
        load_dotenv(root / ".env")
        load_dotenv(root / "skills" / "qa_automation" / ".env")
    except Exception:
        pass

    result = {
        "username": "",
        "password": "",
        "workspace": "",
        "username_key": "",
        "password_key": "",
        "workspace_key": "",
        "source": "",
    }

    config_paths = [
        root / "skills" / "qa_automation" / "config.json",
        root / "config.json",
    ]

    def find_credential_pairs(obj, found):
        if isinstance(obj, dict):
            user_env = obj.get("user_env") or obj.get("username_env") or obj.get("email_env")
            pass_env = obj.get("pass_env") or obj.get("password_env")
            workspace_env = obj.get("workspace_env") or obj.get("company_env") or obj.get("tenant_env")

            if user_env and pass_env:
                found.append({
                    "user_env": str(user_env),
                    "pass_env": str(pass_env),
                    "workspace_env": str(workspace_env or ""),
                })

            for value in obj.values():
                find_credential_pairs(value, found)

        elif isinstance(obj, list):
            for item in obj:
                find_credential_pairs(item, found)

    credential_pairs = []

    for config_path in config_paths:
        if not config_path.exists():
            continue

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            find_credential_pairs(data, credential_pairs)
        except Exception:
            pass

    for pair in credential_pairs:
        user_key = pair.get("user_env")
        pass_key = pair.get("pass_env")
        workspace_key = pair.get("workspace_env")

        username = os.getenv(user_key or "", "")
        password = os.getenv(pass_key or "", "")
        workspace = os.getenv(workspace_key or "", "") if workspace_key else ""

        if username and password:
            result.update({
                "username": username,
                "password": password,
                "workspace": workspace,
                "username_key": user_key,
                "password_key": pass_key,
                "workspace_key": workspace_key,
                "source": "config_json_user_env_pass_env",
            })
            return result

    # Explicit fallback only. Jangan pakai fuzzy env scanning karena bisa salah ambil
    # __CF_USER_TEXT_ENCODING, VSCODE_GIT_ASKPASS_NODE, TOPIC_ID_TESTING, dll.
    fallback_pairs = [
        ("QA_USERNAME", "QA_PASSWORD"),
        ("QA_EMAIL", "QA_PASSWORD"),
        ("MOBOSPACE_USERNAME", "MOBOSPACE_PASSWORD"),
        ("MOBOSPACE_EMAIL", "MOBOSPACE_PASSWORD"),
        ("TEST_USERNAME", "TEST_PASSWORD"),
        ("TEST_EMAIL", "TEST_PASSWORD"),
        ("LOGIN_USERNAME", "LOGIN_PASSWORD"),
        ("LOGIN_EMAIL", "LOGIN_PASSWORD"),
    ]

    for user_key, pass_key in fallback_pairs:
        username = os.getenv(user_key, "")
        password = os.getenv(pass_key, "")

        if username and password:
            workspace = (
                os.getenv("QA_WORKSPACE")
                or os.getenv("QA_COMPANY")
                or os.getenv("MOBOSPACE_WORKSPACE")
                or os.getenv("MOBOSPACE_COMPANY")
                or os.getenv("WORKSPACE")
                or os.getenv("COMPANY")
                or ""
            )

            workspace_key = ""
            for key in ["QA_WORKSPACE", "QA_COMPANY", "MOBOSPACE_WORKSPACE", "MOBOSPACE_COMPANY", "WORKSPACE", "COMPANY"]:
                if os.getenv(key):
                    workspace_key = key
                    break

            result.update({
                "username": username,
                "password": password,
                "workspace": workspace,
                "username_key": user_key,
                "password_key": pass_key,
                "workspace_key": workspace_key,
                "source": "explicit_env_fallback",
            })
            return result

    return result


# Override V2 resolver so Generic UI Runner always uses safe V3 resolver.
def _custom_smoke_resolve_credentials_v2():
    return _custom_smoke_resolve_credentials_v3()
'''

if "# Custom Smoke Credential Resolver V3" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted Custom Smoke Credential Resolver V3")
else:
    print("Custom Smoke Credential Resolver V3 already exists")

print(f"Backup created: {backup_path}")
