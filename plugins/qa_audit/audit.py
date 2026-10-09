"""The ``/audit-qa`` command: run the fork QA suite and route its artifacts.

Moved out of ``gateway/run_inbound.py`` (the ``/audit_qa`` / ``/qa_audit`` block) and
``gateway/run.py`` (the command parser). The handler is async so the gateway can await it while the
blocking Playwright run and the Telegram uploads execute on worker threads via
``asyncio.to_thread`` — never on the event loop.
"""

from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import os
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from .parser import parse_audit_qa_command
from .skill_bridge import load_skill_module

logger = logging.getLogger(__name__)

DEFAULT_URL = "https://mobospace-sandbox.pancaran-group.co.id"
DEFAULT_MODE = "regression"
DEFAULT_FEATURE = "driver daily meal"
DEFAULT_MODULE = "Uang Makan Driver"

_RUN_MODES = frozenset(
    {"smoke", "regression", "full", "cross_feature", "visual", "negative", "e2e"}
)
_MESSAGE_LIMIT = 3900


def _session_env(name: str, default: str = "") -> str:
    """Read a gateway session variable (``HERMES_SESSION_*``) with an ``os.environ`` fallback.

    The gateway binds these around plugin command dispatch, so a handler invoked from a Telegram
    topic sees that topic's chat/thread ids without the core passing the event through.
    """
    try:
        from gateway.session_context import get_session_env

        value = get_session_env(name, default)
        if value:
            return value
    except Exception:  # gateway not importable (CLI/desktop): fall back to the environment
        logger.debug("session env %s unavailable; using os.environ", name)
    return os.getenv(name, default)


def _split_message(text: str, limit: int = _MESSAGE_LIMIT) -> list[str]:
    """Split *text* into Telegram-sized chunks on line boundaries."""
    chunks: list[str] = []
    if not text:
        return ["-"]
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks


def _tg_post(token: str, api_method: str, fields: dict[str, str], file_path: str | None = None) -> None:
    """POST a Telegram Bot API call; multipart when *file_path* is given, form-encoded otherwise."""
    api_url = f"https://api.telegram.org/bot{token}/{api_method}"

    if file_path is None:
        encoded = urllib.parse.urlencode(fields).encode("utf-8")
        request = urllib.request.Request(api_url, data=encoded, method="POST")
    else:
        boundary = f"----HermesBoundary{uuid.uuid4().hex}"
        path = Path(file_path)
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

        body = bytearray()
        for key, value in fields.items():
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
            body.extend(str(value).encode("utf-8"))
            body.extend(b"\r\n")
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            (
                f'Content-Disposition: form-data; name="document"; filename="{path.name}"\r\n'
                f"Content-Type: {mime_type}\r\n\r\n"
            ).encode()
        )
        body.extend(path.read_bytes())
        body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode())

        request = urllib.request.Request(
            api_url,
            data=bytes(body),
            method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )

    with urllib.request.urlopen(request, timeout=60) as response:
        response_body = response.read().decode("utf-8")

    parsed = json.loads(response_body)
    if not parsed.get("ok"):
        raise RuntimeError(response_body)


def _telegram_targets() -> tuple[str, str, str, str]:
    """``(token, chat_id, testing_thread_id, documentation_thread_id)`` from session/env."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = _session_env("HERMES_SESSION_CHAT_ID") or os.getenv("TELEGRAM_HOME_CHANNEL", "")
    testing_thread_id = (
        _session_env("HERMES_SESSION_THREAD_ID")
        or os.getenv("TELEGRAM_TESTING_THREAD_ID", "")
        or os.getenv("TOPIC_ID_TESTING", "")
    )
    documentation_thread_id = os.getenv("TELEGRAM_DOCUMENTATION_THREAD_ID", "") or os.getenv(
        "TOPIC_ID_DOCUMENTATION", ""
    )
    return token, chat_id, testing_thread_id, documentation_thread_id


async def _send_documentation(
    result: dict, module_name: str, mode: str, token: str, chat_id: str, thread_id: str
) -> str:
    """Send the QA documentation, bug log and evidence files to the Documentation topic."""
    if not token:
        return "⚠️ TELEGRAM_BOT_TOKEN tidak ditemukan di .env."
    if not chat_id:
        return "⚠️ chat_id Telegram tidak ditemukan. Set TELEGRAM_HOME_CHANNEL di .env."
    if not thread_id:
        return "⚠️ TELEGRAM_DOCUMENTATION_THREAD_ID belum di-set di .env."

    documentation_path = result.get("report_path") or "-"
    error_log_path = result.get("error_log_path") or "-"
    spreadsheet_path = result.get("spreadsheet_path") or "-"
    screenshot_path = result.get("screenshot_path") or "-"

    async def _message(text: str) -> None:
        await asyncio.to_thread(
            _tg_post,
            token,
            "sendMessage",
            {
                "chat_id": str(chat_id),
                "message_thread_id": str(thread_id),
                "text": text,
                "disable_web_page_preview": "true",
            },
            None,
        )

    header_message = (
        f"📄 QA Documentation Generated\n\n"
        f"Module: {module_name}\n"
        f"Mode: {mode}\n"
        f"Environment: Sandbox\n"
        f"Status: {result.get('status', '-')}\n\n"
        f"Report file:\n{documentation_path}\n\n"
        f"Screenshot evidence:\n{screenshot_path}"
    )
    await _message(header_message)
    for chunk in _split_message(result.get("documentation_report") or "-"):
        await _message(chunk)

    error_header_message = (
        f"🧾 QA Error / Bug Log\n\n"
        f"Module: {module_name}\n"
        f"Mode: {mode}\n"
        f"Environment: Sandbox\n"
        f"Status: {result.get('status', '-')}\n\n"
        f"Error log file:\n{error_log_path}\n\n"
        f"Spreadsheet file:\n{spreadsheet_path}"
    )
    await _message(error_header_message)
    for chunk in _split_message(result.get("error_log_report") or "-"):
        await _message(chunk)

    for file_path, caption in (
        (documentation_path, "📄 QA Documentation Report"),
        (error_log_path, "🧾 QA Error / Bug Log"),
        (spreadsheet_path, "📊 QA Spreadsheet Report"),
        (screenshot_path, "📸 QA Screenshot Evidence"),
    ):
        if file_path and file_path != "-" and Path(file_path).is_file():
            await asyncio.to_thread(
                _tg_post,
                token,
                "sendDocument",
                {"chat_id": str(chat_id), "message_thread_id": str(thread_id), "caption": caption},
                file_path,
            )

    return "✅ Documentation report, error log, and evidence files sent to Documentation topic."


async def _send_testing_evidence(
    result: dict, token: str, chat_id: str, thread_id: str
) -> str:
    """Send screenshot/log/spreadsheet evidence back to the Testing topic the command came from."""
    if not token:
        return "⚠️ TELEGRAM_BOT_TOKEN tidak ditemukan di .env."
    if not chat_id:
        return "⚠️ chat_id Telegram tidak ditemukan."
    if not thread_id:
        return "⚠️ TELEGRAM_TESTING_THREAD_ID belum ditemukan."

    for file_path, caption in (
        (result.get("screenshot_path") or "-", "📸 QA Screenshot Evidence"),
        (result.get("error_log_path") or "-", "🧾 QA Error / Bug Log"),
        (result.get("spreadsheet_path") or "-", "📊 QA Spreadsheet Report"),
    ):
        if file_path and file_path != "-" and Path(file_path).is_file():
            await asyncio.to_thread(
                _tg_post,
                token,
                "sendDocument",
                {"chat_id": str(chat_id), "message_thread_id": str(thread_id), "caption": caption},
                file_path,
            )

    return "✅ Evidence files and spreadsheet sent to Testing topic."


def _apply_legacy_args(raw_args: str, url: str, module_name: str, mode: str) -> tuple[str, str, str]:
    """Apply the legacy ``url=``/``module_name=``/``mode=``/bare-URL/bare-mode tokens."""
    for part in (raw_args or "").split():
        clean_part = part.strip().strip('"').strip("'")
        clean_lower = clean_part.lower()

        if clean_part.startswith(("http://", "https://")):
            url = clean_part
        elif clean_lower.startswith("url="):
            url = clean_part.split("=", 1)[1].strip().strip('"').strip("'")
        elif clean_lower.startswith("module_name=") or clean_lower.startswith("module="):
            module_name = clean_part.split("=", 1)[1].strip().strip('"').strip("'")
        elif clean_lower.startswith("mode="):
            mode = clean_part.split("=", 1)[1].strip().strip('"').strip("'").lower()
        elif clean_lower in _RUN_MODES:
            mode = clean_lower

    return url, module_name, mode


async def handle_audit_qa(raw_args: str) -> str:
    """Handle ``/audit-qa`` (``/audit_qa``, ``/qa_audit``): run the QA suite and report back."""
    try:
        skill = load_skill_module("qa_automation")

        parsed = parse_audit_qa_command(f"/audit-qa {raw_args}".strip())

        url = os.getenv("QA_DEFAULT_URL", DEFAULT_URL)
        mode = (parsed.get("mode") or os.getenv("QA_DEFAULT_MODE", DEFAULT_MODE) or DEFAULT_MODE)
        mode = mode.strip().lower()
        feature_text = (
            parsed.get("feature")
            or os.getenv("QA_DEFAULT_FEATURE", DEFAULT_FEATURE)
            or DEFAULT_FEATURE
        )

        feature_config = skill.get_feature_config(feature_text)
        module_name = feature_config.get(
            "module_name", os.getenv("QA_DEFAULT_MODULE", DEFAULT_MODULE)
        )

        url, module_name, mode = _apply_legacy_args(raw_args, url, module_name, mode)

        result = await asyncio.to_thread(skill.perform_audit_for_telegram, url, module_name, mode)

        testing_summary = result.get(
            "testing_summary", "QA automation finished, but no summary was generated."
        )
        documentation_path = result.get("report_path") or "-"
        error_log_path = result.get("error_log_path") or "-"
        spreadsheet_path = result.get("spreadsheet_path") or "-"
        screenshot_path = result.get("screenshot_path") or "-"

        token, chat_id, testing_thread_id, documentation_thread_id = _telegram_targets()
        documentation_status = await _send_documentation(
            result, module_name, mode, token, chat_id, documentation_thread_id
        )
        testing_status = await _send_testing_evidence(result, token, chat_id, testing_thread_id)

        return (
            f"{testing_summary}\n\n"
            f"📸 Screenshot evidence:\n"
            f"{screenshot_path}\n\n"
            f"📄 Documentation report generated:\n"
            f"{documentation_path}\n\n"
            f"🧾 Error log generated:\n"
            f"{error_log_path}\n\n"
            f"📊 Spreadsheet report generated:\n"
            f"{spreadsheet_path}\n\n"
            f"{documentation_status}\n"
            f"{testing_status}"
        )
    except Exception as exc:
        logger.exception("QA audit command failed")
        return f"❌ /audit-qa failed: {exc}"
