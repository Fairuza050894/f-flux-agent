from __future__ import annotations

import csv
import io
import json
import os
import re
import tempfile
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parents[2]
QA_AUTOMATION_DIR = (
    ROOT
    / "skills"
    / "qa_automation"
)
RUNTIME_DIR = (
    QA_AUTOMATION_DIR
    / "artifacts"
    / "runtime"
)
DELIVERY_STORE_PATH = (
    RUNTIME_DIR
    / "report_deliveries.json"
)

RUNTIME_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

load_dotenv(
    QA_AUTOMATION_DIR / ".env",
    override=True,
)

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["QA Reports"],
)

LOCK = RLock()

ReportFormat = Literal[
    "json",
    "csv",
    "pdf",
]

ReportDestination = Literal[
    "testing",
    "documentation",
    "both",
]


class ReportPayloadRequest(BaseModel):
    report: Dict[str, Any]


class ReportDeliveryRequest(BaseModel):
    report: Dict[str, Any]
    destination: ReportDestination = "both"
    formats: List[ReportFormat] = Field(
        default_factory=lambda: [
            "json",
            "csv",
            "pdf",
        ],
    )


def _utc_now() -> str:
    return datetime.now(
        timezone.utc,
    ).isoformat()


def _safe_text(
    value: Any,
    fallback: str = "",
) -> str:
    if value is None:
        return fallback

    text = str(value).strip()
    return text or fallback


def _safe_filename(
    value: Any,
    fallback: str = "qa-report",
) -> str:
    normalized = re.sub(
        r"[^a-zA-Z0-9._-]+",
        "-",
        _safe_text(
            value,
            fallback,
        ),
    ).strip("-._")

    return normalized or fallback


def _report_value(
    report: Dict[str, Any],
    *path: str,
    fallback: Any = "",
) -> Any:
    current: Any = report

    for key in path:
        if not isinstance(
            current,
            dict,
        ):
            return fallback

        current = current.get(key)

        if current is None:
            return fallback

    return current


def _read_delivery_store() -> List[Dict[str, Any]]:
    if not DELIVERY_STORE_PATH.exists():
        return []

    try:
        payload = json.loads(
            DELIVERY_STORE_PATH.read_text(
                encoding="utf-8",
            ),
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return []

    return (
        payload
        if isinstance(payload, list)
        else []
    )


def _write_delivery_store(
    records: List[Dict[str, Any]],
) -> None:
    DELIVERY_STORE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with LOCK:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=DELIVERY_STORE_PATH.parent,
            delete=False,
            prefix="report-deliveries-",
            suffix=".tmp",
        ) as handle:
            json.dump(
                records,
                handle,
                ensure_ascii=False,
                indent=2,
            )
            handle.write("\n")
            temporary_path = Path(
                handle.name,
            )

        os.replace(
            temporary_path,
            DELIVERY_STORE_PATH,
        )


def _append_delivery_record(
    record: Dict[str, Any],
) -> None:
    with LOCK:
        records = _read_delivery_store()
        records.insert(
            0,
            record,
        )
        _write_delivery_store(
            records[:500],
        )


def _public_delivery_record(
    record: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        key: value
        for key, value in record.items()
        if key != "request"
    }


def _first_environment_value(
    *names: str,
) -> str:
    for name in names:
        value = os.getenv(name)

        if value and value.strip():
            return value.strip()

    return ""


def _telegram_configuration() -> Dict[str, Any]:
    token = _first_environment_value(
        "TELEGRAM_BOT_TOKEN",
        "HERMES_TELEGRAM_BOT_TOKEN",
        "TELEGRAM_TOKEN",
        "BOT_TOKEN",
    )

    chat_id = _first_environment_value(
        "TELEGRAM_CHAT_ID",
        "HERMES_TELEGRAM_CHAT_ID",
        "CHAT_ID",
    )

    testing_thread_id = (
        _first_environment_value(
            "TELEGRAM_TESTING_THREAD_ID",
            "TESTING_THREAD_ID",
            "TELEGRAM_TESTING_TOPIC_ID",
        )
    )

    documentation_thread_id = (
        _first_environment_value(
            "TELEGRAM_DOCUMENTATION_THREAD_ID",
            "DOCUMENTATION_THREAD_ID",
            "TELEGRAM_DOCUMENTATION_TOPIC_ID",
        )
    )

    return {
        "token": token,
        "chat_id": chat_id,
        "testing_thread_id":
            testing_thread_id,
        "documentation_thread_id":
            documentation_thread_id,
        "configured":
            bool(token and chat_id),
    }


def _validate_telegram_destination(
    configuration: Dict[str, Any],
    destination: str,
) -> None:
    if not configuration["token"]:
        raise RuntimeError(
            "Telegram bot token is not configured. "
            "Set TELEGRAM_BOT_TOKEN in "
            "skills/qa_automation/.env.",
        )

    if not configuration["chat_id"]:
        raise RuntimeError(
            "Telegram chat ID is not configured. "
            "Set TELEGRAM_CHAT_ID in "
            "skills/qa_automation/.env.",
        )

    if (
        destination in {
            "testing",
            "both",
        }
        and not configuration[
            "testing_thread_id"
        ]
    ):
        raise RuntimeError(
            "Testing topic ID is not configured. "
            "Set TELEGRAM_TESTING_THREAD_ID.",
        )

    if (
        destination in {
            "documentation",
            "both",
        }
        and not configuration[
            "documentation_thread_id"
        ]
    ):
        raise RuntimeError(
            "Documentation topic ID is not configured. "
            "Set TELEGRAM_DOCUMENTATION_THREAD_ID.",
        )


def _telegram_api_url(
    token: str,
    method: str,
) -> str:
    return (
        "https://api.telegram.org/bot"
        f"{token}/{method}"
    )


def _read_telegram_response(
    response: Any,
) -> Dict[str, Any]:
    raw = response.read()
    payload = json.loads(
        raw.decode(
            "utf-8",
            errors="replace",
        ),
    )

    if not payload.get("ok"):
        raise RuntimeError(
            _safe_text(
                payload.get(
                    "description",
                ),
                "Telegram request failed.",
            ),
        )

    return payload.get(
        "result",
        {},
    )


def _send_telegram_message(
    *,
    token: str,
    chat_id: str,
    thread_id: str,
    text: str,
) -> Dict[str, Any]:
    fields = {
        "chat_id": chat_id,
        "text": text[:4000],
        "disable_web_page_preview":
            "true",
    }

    if thread_id:
        fields["message_thread_id"] = (
            thread_id
        )

    request = urllib.request.Request(
        _telegram_api_url(
            token,
            "sendMessage",
        ),
        data=urllib.parse.urlencode(
            fields,
        ).encode("utf-8"),
        headers={
            "Content-Type":
                "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:
            return _read_telegram_response(
                response,
            )
    except urllib.error.HTTPError as error:
        detail = error.read().decode(
            "utf-8",
            errors="replace",
        )
        raise RuntimeError(
            f"Telegram sendMessage failed: {detail}",
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(
            "Telegram sendMessage network error: "
            f"{error.reason}",
        ) from error


def _multipart_body(
    *,
    fields: Dict[str, str],
    filename: str,
    file_bytes: bytes,
    mime_type: str,
) -> tuple[bytes, str]:
    boundary = (
        "----HermesQAReport"
        + uuid4().hex
    )

    chunks: List[bytes] = []

    for key, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(
                    "utf-8",
                ),
                (
                    "Content-Disposition: "
                    f'form-data; name="{key}"'
                    "\r\n\r\n"
                ).encode("utf-8"),
                str(value).encode(
                    "utf-8",
                ),
                b"\r\n",
            ],
        )

    chunks.extend(
        [
            f"--{boundary}\r\n".encode(
                "utf-8",
            ),
            (
                "Content-Disposition: "
                'form-data; name="document"; '
                f'filename="{filename}"'
                "\r\n"
            ).encode("utf-8"),
            (
                f"Content-Type: {mime_type}"
                "\r\n\r\n"
            ).encode("utf-8"),
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode(
                "utf-8",
            ),
        ],
    )

    return (
        b"".join(chunks),
        boundary,
    )


def _send_telegram_document(
    *,
    token: str,
    chat_id: str,
    thread_id: str,
    filename: str,
    file_bytes: bytes,
    mime_type: str,
    caption: str,
) -> Dict[str, Any]:
    fields = {
        "chat_id": chat_id,
        "caption": caption[:1000],
    }

    if thread_id:
        fields["message_thread_id"] = (
            thread_id
        )

    body, boundary = _multipart_body(
        fields=fields,
        filename=filename,
        file_bytes=file_bytes,
        mime_type=mime_type,
    )

    request = urllib.request.Request(
        _telegram_api_url(
            token,
            "sendDocument",
        ),
        data=body,
        headers={
            "Content-Type":
                "multipart/form-data; "
                f"boundary={boundary}",
            "Content-Length":
                str(len(body)),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=60,
        ) as response:
            return _read_telegram_response(
                response,
            )
    except urllib.error.HTTPError as error:
        detail = error.read().decode(
            "utf-8",
            errors="replace",
        )
        raise RuntimeError(
            f"Telegram sendDocument failed: {detail}",
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(
            "Telegram sendDocument network error: "
            f"{error.reason}",
        ) from error


def _report_file_base_name(
    report: Dict[str, Any],
) -> str:
    configured = _report_value(
        report,
        "fileBaseName",
    )

    if configured:
        return _safe_filename(
            configured,
        )

    cycle_id = _report_value(
        report,
        "cycle",
        "id",
        fallback="cycle",
    )

    return _safe_filename(
        f"qa-report-{cycle_id}",
    )


def _report_json_bytes(
    report: Dict[str, Any],
) -> bytes:
    return (
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def _execution_metric(
    execution: Dict[str, Any],
    key: str,
) -> Any:
    metrics = execution.get(
        "metrics",
        {},
    )

    return (
        metrics.get(key, 0)
        if isinstance(metrics, dict)
        else 0
    )


def _report_csv_bytes(
    report: Dict[str, Any],
) -> bytes:
    output = io.StringIO(
        newline="",
    )

    writer = csv.writer(output)

    writer.writerow(
        [
            "cycle_id",
            "cycle_name",
            "project",
            "environment",
            "release_decision",
            "run_id",
            "scope",
            "status",
            "attempt",
            "execution_reason",
            "target_asset_count",
            "passed",
            "failed",
            "need_review",
            "skipped",
            "blocked",
            "bugs_found",
            "warnings",
            "started_at",
            "completed_at",
        ],
    )

    cycle = report.get(
        "cycle",
        {},
    )
    project = report.get(
        "project",
        {},
    )
    environment = report.get(
        "environment",
        {},
    )
    release_decision = report.get(
        "releaseDecision",
        {},
    )

    executions = report.get(
        "executions",
        [],
    )

    if not isinstance(executions, list):
        executions = []

    if not executions:
        writer.writerow(
            [
                cycle.get("id", ""),
                cycle.get("name", ""),
                project.get("name", ""),
                environment.get("name", ""),
                release_decision.get(
                    "status",
                    "",
                ),
            ],
        )

    for execution in executions:
        if not isinstance(
            execution,
            dict,
        ):
            continue

        target_ids = execution.get(
            "targetAssetIds",
            [],
        )

        writer.writerow(
            [
                cycle.get("id", ""),
                cycle.get("name", ""),
                project.get("name", ""),
                environment.get(
                    "name",
                    "",
                ),
                release_decision.get(
                    "status",
                    "",
                ),
                execution.get(
                    "runId",
                    "",
                ),
                execution.get(
                    "scopeLabel",
                    "",
                ),
                execution.get(
                    "statusLabel",
                    execution.get(
                        "status",
                        "",
                    ),
                ),
                execution.get(
                    "attemptNumber",
                    1,
                ),
                execution.get(
                    "executionReasonLabel",
                    "",
                ),
                (
                    len(target_ids)
                    if isinstance(
                        target_ids,
                        list,
                    )
                    else 0
                ),
                _execution_metric(
                    execution,
                    "passed",
                ),
                _execution_metric(
                    execution,
                    "failed",
                ),
                _execution_metric(
                    execution,
                    "needReview",
                ),
                _execution_metric(
                    execution,
                    "skipped",
                ),
                _execution_metric(
                    execution,
                    "blocked",
                ),
                _execution_metric(
                    execution,
                    "bugsFound",
                ),
                _execution_metric(
                    execution,
                    "warnings",
                ),
                execution.get(
                    "startedAt",
                    "",
                ),
                execution.get(
                    "completedAt",
                    "",
                ),
            ],
        )

    return output.getvalue().encode(
        "utf-8-sig",
    )


def _report_text_lines(
    report: Dict[str, Any],
) -> List[str]:
    cycle = report.get(
        "cycle",
        {},
    )
    project = report.get(
        "project",
        {},
    )
    environment = report.get(
        "environment",
        {},
    )
    summary = report.get(
        "summary",
        {},
    )
    decision = report.get(
        "releaseDecision",
        {},
    )

    lines = [
        _safe_text(
            report.get("title"),
            "QA Consolidated Report",
        ),
        "",
        f"Report ID: {_safe_text(report.get('reportId'), 'Not available')}",
        f"Generated: {_safe_text(report.get('generatedAt'), 'Not available')}",
        f"Cycle: {_safe_text(cycle.get('name'), 'Untitled')} ({_safe_text(cycle.get('id'), 'N/A')})",
        f"Project: {_safe_text(project.get('name'), 'Unknown project')}",
        f"Environment: {_safe_text(environment.get('name'), 'Unknown environment')}",
        f"Release: {_safe_text(cycle.get('releaseVersion'), 'Not specified')}",
        "",
        "RELEASE DECISION",
        f"Status: {_safe_text(decision.get('label'), decision.get('status', 'Unknown'))}",
        f"Reason: {_safe_text(decision.get('reason'), 'No decision reason.')}",
        "",
        "EXECUTIVE SUMMARY",
    ]

    executive_summary = report.get(
        "executiveSummary",
        [],
    )

    if isinstance(
        executive_summary,
        list,
    ):
        lines.extend(
            f"- {_safe_text(item)}"
            for item in executive_summary
        )

    lines.extend(
        [
            "",
            "RESULT METRICS",
            (
                "Passed: "
                f"{summary.get('passed', 0)} | "
                "Failed: "
                f"{summary.get('failed', 0)} | "
                "Need Review: "
                f"{summary.get('needReview', 0)}"
            ),
            (
                "Skipped: "
                f"{summary.get('skipped', 0)} | "
                "Blocked: "
                f"{summary.get('blocked', 0)} | "
                "Warnings: "
                f"{summary.get('warnings', 0)}"
            ),
            (
                "Pass Rate: "
                f"{summary.get('passRateLabel', 'Not available')} | "
                "Execution Attempts: "
                f"{summary.get('executionAttemptCount', 0)}"
            ),
            (
                "New Failures: "
                f"{summary.get('newFailureCount', 0)} | "
                "Resolved Failures: "
                f"{summary.get('resolvedFailureCount', 0)}"
            ),
            "",
            "RELEASE CHECKLIST",
        ],
    )

    checklist = decision.get(
        "checklist",
        [],
    )

    if isinstance(checklist, list):
        for item in checklist:
            if not isinstance(
                item,
                dict,
            ):
                continue

            lines.append(
                "["
                f"{_safe_text(item.get('status'), 'unknown').upper()}"
                "] "
                f"{_safe_text(item.get('label'), 'Checklist item')}: "
                f"{_safe_text(item.get('detail'), '')}",
            )

    lines.extend(
        [
            "",
            "EXECUTIONS",
        ],
    )

    executions = report.get(
        "executions",
        [],
    )

    if isinstance(executions, list):
        for execution in executions:
            if not isinstance(
                execution,
                dict,
            ):
                continue

            metrics = execution.get(
                "metrics",
                {},
            )

            lines.append(
                "- "
                f"{_safe_text(execution.get('scopeLabel'), 'Execution')} | "
                f"{_safe_text(execution.get('runId'), 'N/A')} | "
                f"{_safe_text(execution.get('statusLabel'), 'Unknown')} | "
                f"Attempt {execution.get('attemptNumber', 1)} | "
                f"P {metrics.get('passed', 0)} "
                f"F {metrics.get('failed', 0)} "
                f"R {metrics.get('needReview', 0)}",
            )

    lines.extend(
        [
            "",
            "EXECUTION COMPARISONS",
        ],
    )

    comparisons = report.get(
        "comparisons",
        [],
    )

    if isinstance(comparisons, list):
        for comparison in comparisons:
            if not isinstance(
                comparison,
                dict,
            ):
                continue

            failure_delta = comparison.get(
                "failureDelta",
                {},
            )

            lines.append(
                "- "
                f"{_safe_text(comparison.get('scopeLabel'), 'Scope')} | "
                f"{_safe_text(comparison.get('baselineRunId'), 'N/A')} -> "
                f"{_safe_text(comparison.get('candidateRunId'), 'N/A')} | "
                f"New {len(failure_delta.get('newFailures', []))} | "
                f"Resolved {len(failure_delta.get('resolvedFailures', []))}",
            )

    asset_summary = report.get(
        "assetTraceability",
        {},
    )

    lines.extend(
        [
            "",
            "TEST ASSET TRACEABILITY",
            (
                "Total: "
                f"{asset_summary.get('total', 0)} | "
                "Captured: "
                f"{asset_summary.get('captured', 0)} | "
                "Current: "
                f"{asset_summary.get('current', 0)} | "
                "Outdated: "
                f"{asset_summary.get('outdated', 0)} | "
                "Missing: "
                f"{asset_summary.get('missing', 0)} | "
                "No Snapshot: "
                f"{asset_summary.get('unsnapshotted', 0)}"
            ),
            "",
            "ARTIFACTS AND LOGS",
            (
                "Artifacts: "
                f"{summary.get('artifactCount', 0)} | "
                "Log records: "
                f"{summary.get('logCount', 0)}"
            ),
        ],
    )

    wrapped: List[str] = []

    for line in lines:
        if not line:
            wrapped.append("")
            continue

        wrapped.extend(
            textwrap.wrap(
                line,
                width=92,
                replace_whitespace=True,
                drop_whitespace=True,
            )
            or [""],
        )

    return wrapped


def _pdf_escape(
    value: str,
) -> str:
    latin = value.encode(
        "latin-1",
        errors="replace",
    ).decode("latin-1")

    return (
        latin
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def _build_pdf_bytes(
    report: Dict[str, Any],
) -> bytes:
    report_lines = _report_text_lines(
        report,
    )

    lines_per_page = 52
    pages = [
        report_lines[index:index + lines_per_page]
        for index in range(
            0,
            len(report_lines),
            lines_per_page,
        )
    ] or [["QA Consolidated Report"]]

    objects: Dict[int, bytes] = {}

    page_ids = [
        4 + index * 2
        for index in range(
            len(pages),
        )
    ]

    objects[1] = (
        b"<< /Type /Catalog /Pages 2 0 R >>"
    )

    kids = " ".join(
        f"{page_id} 0 R"
        for page_id in page_ids
    )

    objects[2] = (
        "<< /Type /Pages "
        f"/Kids [{kids}] "
        f"/Count {len(page_ids)} >>"
    ).encode("ascii")

    objects[3] = (
        b"<< /Type /Font /Subtype /Type1 "
        b"/BaseFont /Helvetica >>"
    )

    for index, page_lines in enumerate(
        pages,
    ):
        page_id = page_ids[index]
        content_id = page_id + 1

        printable_lines = list(
            page_lines,
        )

        printable_lines.extend(
            [
                "",
                (
                    "Page "
                    f"{index + 1} of {len(pages)}"
                ),
            ],
        )

        commands = [
            "BT",
            "/F1 9 Tf",
            "12 TL",
            "50 792 Td",
        ]

        for line in printable_lines:
            commands.append(
                f"({_pdf_escape(line)}) Tj",
            )
            commands.append("T*")

        commands.append("ET")

        stream = "\n".join(
            commands,
        ).encode(
            "latin-1",
            errors="replace",
        )

        objects[page_id] = (
            "<< /Type /Page "
            "/Parent 2 0 R "
            "/MediaBox [0 0 612 842] "
            "/Resources << "
            "/Font << /F1 3 0 R >> "
            ">> "
            f"/Contents {content_id} 0 R "
            ">>"
        ).encode("ascii")

        objects[content_id] = (
            f"<< /Length {len(stream)} >>\n"
            "stream\n"
        ).encode("ascii") + (
            stream
        ) + b"\nendstream"

    max_object_id = max(
        objects,
    )

    output = bytearray(
        b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n",
    )

    offsets = {
        0: 0,
    }

    for object_id in range(
        1,
        max_object_id + 1,
    ):
        offsets[object_id] = len(
            output,
        )

        output.extend(
            f"{object_id} 0 obj\n".encode(
                "ascii",
            ),
        )
        output.extend(
            objects[object_id],
        )
        output.extend(
            b"\nendobj\n",
        )

    xref_offset = len(
        output,
    )

    output.extend(
        (
            "xref\n"
            f"0 {max_object_id + 1}\n"
            "0000000000 65535 f \n"
        ).encode("ascii"),
    )

    for object_id in range(
        1,
        max_object_id + 1,
    ):
        output.extend(
            (
                f"{offsets[object_id]:010d} "
                "00000 n \n"
            ).encode("ascii"),
        )

    output.extend(
        (
            "trailer\n"
            "<< "
            f"/Size {max_object_id + 1} "
            "/Root 1 0 R "
            ">>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii"),
    )

    return bytes(output)


def _telegram_summary(
    report: Dict[str, Any],
) -> str:
    cycle = report.get(
        "cycle",
        {},
    )
    project = report.get(
        "project",
        {},
    )
    environment = report.get(
        "environment",
        {},
    )
    summary = report.get(
        "summary",
        {},
    )
    decision = report.get(
        "releaseDecision",
        {},
    )

    return "\n".join(
        [
            "QA Consolidated Report",
            "",
            (
                "Cycle: "
                f"{_safe_text(cycle.get('name'), 'Untitled')}"
            ),
            (
                "Project: "
                f"{_safe_text(project.get('name'), 'Unknown')}"
            ),
            (
                "Environment: "
                f"{_safe_text(environment.get('name'), 'Unknown')}"
            ),
            (
                "Release Decision: "
                f"{_safe_text(decision.get('label'), decision.get('status', 'Unknown'))}"
            ),
            (
                "Passed / Failed / Need Review: "
                f"{summary.get('passed', 0)} / "
                f"{summary.get('failed', 0)} / "
                f"{summary.get('needReview', 0)}"
            ),
            (
                "New / Resolved Failures: "
                f"{summary.get('newFailureCount', 0)} / "
                f"{summary.get('resolvedFailureCount', 0)}"
            ),
            (
                "Pass Rate: "
                f"{summary.get('passRateLabel', 'Not available')}"
            ),
            "",
            _safe_text(
                decision.get("reason"),
                "No release-decision reason.",
            ),
            "",
            (
                "Report ID: "
                f"{_safe_text(report.get('reportId'), 'Not available')}"
            ),
        ],
    )


def _build_export_files(
    report: Dict[str, Any],
    formats: List[str],
) -> List[Dict[str, Any]]:
    base_name = _report_file_base_name(
        report,
    )

    files = []

    for report_format in dict.fromkeys(
        formats,
    ):
        if report_format == "json":
            files.append(
                {
                    "filename":
                        f"{base_name}.json",
                    "bytes":
                        _report_json_bytes(
                            report,
                        ),
                    "mime_type":
                        "application/json",
                },
            )
        elif report_format == "csv":
            files.append(
                {
                    "filename":
                        f"{base_name}.csv",
                    "bytes":
                        _report_csv_bytes(
                            report,
                        ),
                    "mime_type":
                        "text/csv",
                },
            )
        elif report_format == "pdf":
            files.append(
                {
                    "filename":
                        f"{base_name}.pdf",
                    "bytes":
                        _build_pdf_bytes(
                            report,
                        ),
                    "mime_type":
                        "application/pdf",
                },
            )

    return files


def _deliver_report(
    request: ReportDeliveryRequest,
    *,
    attempt: int = 1,
    retry_of: Optional[str] = None,
) -> Dict[str, Any]:
    delivery_id = (
        "delivery-"
        + uuid4().hex
    )
    created_at = _utc_now()

    report = request.report
    cycle_id = _safe_text(
        _report_value(
            report,
            "cycle",
            "id",
        ),
    )
    cycle_name = _safe_text(
        _report_value(
            report,
            "cycle",
            "name",
        ),
        "Untitled Test Cycle",
    )

    record: Dict[str, Any] = {
        "id": delivery_id,
        "report_id":
            _safe_text(
                report.get(
                    "reportId",
                ),
            ),
        "cycle_id": cycle_id,
        "cycle_name": cycle_name,
        "destination":
            request.destination,
        "formats":
            list(
                dict.fromkeys(
                    request.formats,
                ),
            ),
        "status": "sending",
        "attempt": attempt,
        "retry_of": retry_of,
        "created_at": created_at,
        "updated_at": created_at,
        "sent_at": None,
        "error": "",
        "telegram_message_ids": [],
        "request":
            (
                request.model_dump()
                if hasattr(
                    request,
                    "model_dump",
                )
                else request.dict()
            ),
    }

    try:
        configuration = (
            _telegram_configuration()
        )

        _validate_telegram_destination(
            configuration,
            request.destination,
        )

        summary = _telegram_summary(
            report,
        )

        message_ids: List[int] = []

        if request.destination in {
            "testing",
            "both",
        }:
            testing_message = (
                _send_telegram_message(
                    token=configuration[
                        "token"
                    ],
                    chat_id=configuration[
                        "chat_id"
                    ],
                    thread_id=configuration[
                        "testing_thread_id"
                    ],
                    text=summary,
                )
            )

            message_id = (
                testing_message.get(
                    "message_id",
                )
            )

            if isinstance(
                message_id,
                int,
            ):
                message_ids.append(
                    message_id,
                )

        if request.destination in {
            "documentation",
            "both",
        }:
            documentation_message = (
                _send_telegram_message(
                    token=configuration[
                        "token"
                    ],
                    chat_id=configuration[
                        "chat_id"
                    ],
                    thread_id=configuration[
                        "documentation_thread_id"
                    ],
                    text=summary,
                )
            )

            message_id = (
                documentation_message.get(
                    "message_id",
                )
            )

            if isinstance(
                message_id,
                int,
            ):
                message_ids.append(
                    message_id,
                )

            for export_file in (
                _build_export_files(
                    report,
                    request.formats,
                )
            ):
                document_message = (
                    _send_telegram_document(
                        token=configuration[
                            "token"
                        ],
                        chat_id=configuration[
                            "chat_id"
                        ],
                        thread_id=configuration[
                            "documentation_thread_id"
                        ],
                        filename=export_file[
                            "filename"
                        ],
                        file_bytes=export_file[
                            "bytes"
                        ],
                        mime_type=export_file[
                            "mime_type"
                        ],
                        caption=(
                            f"{cycle_name} · "
                            f"{export_file['filename']}"
                        ),
                    )
                )

                document_message_id = (
                    document_message.get(
                        "message_id",
                    )
                )

                if isinstance(
                    document_message_id,
                    int,
                ):
                    message_ids.append(
                        document_message_id,
                    )

        sent_at = _utc_now()

        record.update(
            {
                "status": "sent",
                "updated_at": sent_at,
                "sent_at": sent_at,
                "telegram_message_ids":
                    message_ids,
            },
        )
    except Exception as error:
        failed_at = _utc_now()

        record.update(
            {
                "status": "failed",
                "updated_at": failed_at,
                "error": _safe_text(
                    error,
                    "Report delivery failed.",
                ),
            },
        )

    _append_delivery_record(
        record,
    )

    return _public_delivery_record(
        record,
    )


@router.get("/configuration")
def get_report_delivery_configuration() -> Dict[str, Any]:
    configuration = _telegram_configuration()

    return {
        "configured":
            configuration[
                "configured"
            ],
        "chat_configured":
            bool(
                configuration[
                    "chat_id"
                ],
            ),
        "testing_topic_configured":
            bool(
                configuration[
                    "testing_thread_id"
                ],
            ),
        "documentation_topic_configured":
            bool(
                configuration[
                    "documentation_thread_id"
                ],
            ),
        "required_environment_variables":
            [
                "TELEGRAM_BOT_TOKEN",
                "TELEGRAM_CHAT_ID",
                "TELEGRAM_TESTING_THREAD_ID",
                "TELEGRAM_DOCUMENTATION_THREAD_ID",
            ],
    }


@router.post("/pdf")
def export_report_pdf(
    request: ReportPayloadRequest,
) -> StreamingResponse:
    report = request.report

    if not report:
        raise HTTPException(
            status_code=422,
            detail="Report payload is required.",
        )

    filename = (
        _report_file_base_name(
            report,
        )
        + ".pdf"
    )

    return StreamingResponse(
        io.BytesIO(
            _build_pdf_bytes(
                report,
            ),
        ),
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"',
        },
    )


@router.get("/deliveries")
def list_report_deliveries(
    cycle_id: Optional[str] = Query(
        default=None,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
) -> Dict[str, Any]:
    records = _read_delivery_store()

    if cycle_id:
        records = [
            record
            for record in records
            if record.get(
                "cycle_id",
            ) == cycle_id
        ]

    visible = [
        _public_delivery_record(
            record,
        )
        for record in records[:limit]
    ]

    return {
        "items": visible,
        "count": len(visible),
    }


@router.post("/deliveries")
def create_report_delivery(
    request: ReportDeliveryRequest,
) -> Dict[str, Any]:
    if not request.report:
        raise HTTPException(
            status_code=422,
            detail="Report payload is required.",
        )

    if not request.formats:
        raise HTTPException(
            status_code=422,
            detail=(
                "Select at least one "
                "report format."
            ),
        )

    return _deliver_report(
        request,
    )


@router.post(
    "/deliveries/{delivery_id}/retry",
)
def retry_report_delivery(
    delivery_id: str,
) -> Dict[str, Any]:
    records = _read_delivery_store()

    source = next(
        (
            record
            for record in records
            if record.get("id")
            == delivery_id
        ),
        None,
    )

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Report delivery not found.",
        )

    request_payload = source.get(
        "request",
    )

    if not isinstance(
        request_payload,
        dict,
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "The original delivery request "
                "is not available for retry."
            ),
        )

    request = ReportDeliveryRequest(
        **request_payload,
    )

    return _deliver_report(
        request,
        attempt=int(
            source.get(
                "attempt",
                1,
            )
        ) + 1,
        retry_of=delivery_id,
    )
