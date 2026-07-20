from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_custom_smoke_credential_resolver_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# Custom Smoke Credential Resolver Override
# ============================================================

def _custom_smoke_read_env_files_flexible():
    from pathlib import Path
    import os

    root = Path(__file__).resolve().parents[2]

    env_paths = [
        root / ".env",
        root / "skills" / "qa_automation" / ".env",
    ]

    data = {}

    for path in env_paths:
        if not path.exists():
            continue

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and value:
                data[key] = value
                os.environ.setdefault(key, value)

    return data


def _custom_smoke_pick_credential(env_data, kind):
    import os

    merged = dict(env_data or {})
    merged.update(os.environ)

    def score_key(key):
        lowered = key.lower()
        score = 0

        if kind == "username":
            if any(token in lowered for token in ["username", "user", "email", "login"]):
                score += 10
            if any(token in lowered for token in ["qa", "mobo", "mobospace", "sandbox", "test"]):
                score += 5
            if any(token in lowered for token in ["telegram", "token", "thread", "bot", "api_key", "secret"]):
                score -= 20

        elif kind == "password":
            if any(token in lowered for token in ["password", "pass", "pwd"]):
                score += 10
            if any(token in lowered for token in ["qa", "mobo", "mobospace", "sandbox", "test"]):
                score += 5
            if any(token in lowered for token in ["telegram", "token", "thread", "bot", "api_key"]):
                score -= 20

        elif kind == "workspace":
            if any(token in lowered for token in ["workspace", "company", "tenant"]):
                score += 10
            if any(token in lowered for token in ["qa", "mobo", "mobospace", "sandbox", "test"]):
                score += 5

        return score

    candidates = []

    for key, value in merged.items():
        if not value:
            continue

        score = score_key(key)
        if score > 0:
            candidates.append((score, key, value))

    candidates.sort(reverse=True)

    if candidates:
        return candidates[0][2], candidates[0][1]

    return "", ""


def _custom_smoke_resolve_credentials_flexible():
    try:
        from dotenv import load_dotenv
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        load_dotenv(root / ".env")
        load_dotenv(root / "skills" / "qa_automation" / ".env")
    except Exception:
        pass

    env_data = _custom_smoke_read_env_files_flexible()

    username, username_key = _custom_smoke_pick_credential(env_data, "username")
    password, password_key = _custom_smoke_pick_credential(env_data, "password")
    workspace, workspace_key = _custom_smoke_pick_credential(env_data, "workspace")

    return {
        "username": username,
        "password": password,
        "workspace": workspace,
        "username_key": username_key,
        "password_key": password_key,
        "workspace_key": workspace_key,
    }


if not globals().get("_CUSTOM_SMOKE_CREDENTIAL_RESOLVER_PATCH_INSTALLED"):
    _CUSTOM_SMOKE_BEFORE_CREDENTIAL_RESOLVER = globals().get("perform_custom_smoke_test")

    def perform_custom_smoke_test(
        url,
        route,
        expected_texts=None,
        feature_name="Custom Smoke Test",
        mode="smoke",
    ):
        import os

        credential = _custom_smoke_resolve_credentials_flexible()

        if credential.get("username"):
            os.environ["QA_USERNAME"] = credential["username"]

        if credential.get("password"):
            os.environ["QA_PASSWORD"] = credential["password"]

        if credential.get("workspace"):
            os.environ["QA_WORKSPACE"] = credential["workspace"]

        if _CUSTOM_SMOKE_BEFORE_CREDENTIAL_RESOLVER is None:
            raise RuntimeError("Previous perform_custom_smoke_test not found")

        result = _CUSTOM_SMOKE_BEFORE_CREDENTIAL_RESOLVER(
            url=url,
            route=route,
            expected_texts=expected_texts,
            feature_name=feature_name,
            mode=mode,
        )

        if isinstance(result, dict):
            result["credential_keys_used"] = {
                "username_key": credential.get("username_key"),
                "password_key": credential.get("password_key"),
                "workspace_key": credential.get("workspace_key"),
            }

        return result

    _CUSTOM_SMOKE_CREDENTIAL_RESOLVER_PATCH_INSTALLED = True
'''

if "# Custom Smoke Credential Resolver Override" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted Custom Smoke credential resolver override")
else:
    print("Custom Smoke credential resolver override already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
