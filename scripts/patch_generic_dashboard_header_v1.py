from pathlib import Path
from datetime import datetime
import re
import shutil
import sys


ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

MARKER = "<!-- QA GENERIC HEADER V1 -->"

OLD_SUBTITLE = (
    "Local QA Automation Control Panel for Mobospace Sandbox"
)

NEW_SUBTITLE = (
    "Plan, execute, observe, and analyze automated quality checks"
)


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_generic_header_v1_{timestamp}"
)

shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text(
    encoding="utf-8"
)

changes = []


# Replace the exact legacy branding subtitle only.
if OLD_SUBTITLE in text:
    text = text.replace(
        OLD_SUBTITLE,
        NEW_SUBTITLE
    )
    changes.append("legacy Mobospace subtitle")
else:
    print(
        "[INFO] Exact legacy subtitle was not found; "
        "checking known variants."
    )


# Replace a few known static branding variants without touching
# project-aware content, project cards, feature labels, or runner data.
variant_patterns = [
    (
        r"Local\s+QA\s+Automation\s+Control\s+Panel\s+"
        r"for\s+Mobospace\s+Sandbox",
        NEW_SUBTITLE,
    ),
    (
        r"QA\s+Automation\s+Control\s+Panel\s+"
        r"for\s+Mobospace\s+Sandbox",
        NEW_SUBTITLE,
    ),
]

for pattern, replacement in variant_patterns:
    updated, count = re.subn(
        pattern,
        replacement,
        text,
        flags=re.IGNORECASE,
    )

    if count:
        text = updated
        changes.append(
            f"known subtitle variant ({count})"
        )


# Make the browser tab title generic only when it still contains
# Mobospace. Existing generic titles are preserved.
title_pattern = re.compile(
    r"<title>([^<]*Mobospace[^<]*)</title>",
    flags=re.IGNORECASE,
)

text, title_count = title_pattern.subn(
    "<title>QA Autonomous Dashboard</title>",
    text,
)

if title_count:
    changes.append(
        f"browser title ({title_count})"
    )


# Add an inert marker so the patch is easy to audit and idempotent.
if MARKER not in text:
    body_match = re.search(
        r"<body\b[^>]*>",
        text,
        flags=re.IGNORECASE,
    )

    if body_match:
        insert_at = body_match.end()
        text = (
            text[:insert_at]
            + "\n  "
            + MARKER
            + text[insert_at:]
        )
    else:
        fail("Opening <body> tag was not found")


# Verify that the old branding subtitle is gone.
remaining_old_branding = [
    OLD_SUBTITLE,
    "Control Panel for Mobospace Sandbox",
]

remaining = [
    item
    for item in remaining_old_branding
    if item.lower() in text.lower()
]

if remaining:
    shutil.copy2(
        backup_path,
        HTML_PATH
    )

    fail(
        "Verification failed. Dashboard restored. "
        "Remaining static branding: "
        + ", ".join(remaining)
    )


if NEW_SUBTITLE not in text:
    shutil.copy2(
        backup_path,
        HTML_PATH
    )

    fail(
        "Verification failed. Dashboard restored. "
        "Generic subtitle was not found."
    )


HTML_PATH.write_text(
    text,
    encoding="utf-8"
)

print(
    "[OK] Generic dashboard header applied"
)

if changes:
    for change in changes:
        print(f"[OK] Updated: {change}")
else:
    print(
        "[INFO] Header already appeared generic; "
        "the audit marker was added."
    )

print(f"[OK] Backup created: {backup_path}")
print(f"[OK] Updated: {HTML_PATH}")
print()
print(
    "[SUCCESS] Generic Dashboard Header V1 installed"
)
