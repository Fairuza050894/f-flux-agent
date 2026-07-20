from pathlib import Path
from datetime import datetime
import re
import shutil
import sys


ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

CSS_MARKER = "/* QA REMOVE COMPACT FLOW V1.2.2 CSS */"
JS_MARKER = "/* QA REMOVE COMPACT FLOW V1.2.2 JS */"

CLEANUP_MARKER = (
    "<!-- QA DISCARDED COMPACT FLOW V1.2.2 REMOVED -->"
)


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")


stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

backup_path = HTML_PATH.with_name(
    "dashboard.html.backup_before_remove_"
    f"discarded_compact_flow_v1_2_2_{stamp}"
)

shutil.copy2(
    HTML_PATH,
    backup_path
)

text = HTML_PATH.read_text(
    encoding="utf-8"
)


def remove_marked_block(
    source: str,
    marker: str,
    block_type: str,
) -> tuple[str, int]:
    # Remove one QA patch block from its marker until the next
    # QA marker of the same block type or the closing style/script tag.

    if block_type == "css":
        boundary_pattern = (
            r"(?="
            r"/\*\s*QA [^*]* CSS\s*\*/"
            r"|</style>"
            r")"
        )
    elif block_type == "js":
        boundary_pattern = (
            r"(?="
            r"/\*\s*QA [^*]* JS\s*\*/"
            r"|</script>"
            r")"
        )
    else:
        raise ValueError(
            f"Unsupported block type: {block_type}"
        )

    pattern = re.compile(
        re.escape(marker)
        + r".*?"
        + boundary_pattern,
        flags=re.DOTALL,
    )

    return pattern.subn(
        "",
        source,
        count=1,
    )


css_count_before = text.count(
    CSS_MARKER
)

js_count_before = text.count(
    JS_MARKER
)

if css_count_before > 1:
    fail(
        "More than one discarded CSS marker was found. "
        "No changes were made."
    )

if js_count_before > 1:
    fail(
        "More than one discarded JavaScript marker was found. "
        "No changes were made."
    )


if css_count_before == 1:
    text, removed_css = remove_marked_block(
        text,
        CSS_MARKER,
        "css",
    )

    if removed_css != 1:
        shutil.copy2(
            backup_path,
            HTML_PATH
        )

        fail(
            "Could not safely remove the discarded CSS block. "
            "Dashboard restored."
        )

    print(
        "[OK] Removed discarded Compact Flow V1.2.2 CSS"
    )
else:
    print(
        "[SKIP] Discarded Compact Flow V1.2.2 CSS "
        "was not present"
    )


if js_count_before == 1:
    text, removed_js = remove_marked_block(
        text,
        JS_MARKER,
        "js",
    )

    if removed_js != 1:
        shutil.copy2(
            backup_path,
            HTML_PATH
        )

        fail(
            "Could not safely remove the discarded JavaScript block. "
            "Dashboard restored."
        )

    print(
        "[OK] Removed discarded Compact Flow V1.2.2 JavaScript"
    )
else:
    print(
        "[SKIP] Discarded Compact Flow V1.2.2 JavaScript "
        "was not present"
    )


if CLEANUP_MARKER not in text:
    body_match = re.search(
        r"<body\b[^>]*>",
        text,
        flags=re.IGNORECASE,
    )

    if not body_match:
        shutil.copy2(
            backup_path,
            HTML_PATH
        )

        fail(
            "Opening <body> tag was not found. "
            "Dashboard restored."
        )

    insert_at = body_match.end()

    text = (
        text[:insert_at]
        + "\n  "
        + CLEANUP_MARKER
        + text[insert_at:]
    )


remaining = [
    marker
    for marker in (
        CSS_MARKER,
        JS_MARKER,
    )
    if marker in text
]

if remaining:
    shutil.copy2(
        backup_path,
        HTML_PATH
    )

    fail(
        "Verification failed. Dashboard restored. "
        "Remaining discarded markers: "
        + ", ".join(remaining)
    )


required_preserved_markers = [
    "/* QA MAIN DASHBOARD MONITORING BUGFIX V1.2.1 CSS */",
    "/* QA MAIN DASHBOARD MONITORING CLEANUP V1.2 JS */",
]

missing_preserved = [
    marker
    for marker in required_preserved_markers
    if marker not in text
]

if missing_preserved:
    shutil.copy2(
        backup_path,
        HTML_PATH
    )

    fail(
        "Verification failed. Dashboard restored. "
        "Required stable monitoring markers are missing: "
        + ", ".join(missing_preserved)
    )


HTML_PATH.write_text(
    text,
    encoding="utf-8"
)

print(
    f"[OK] Backup created: {backup_path}"
)

print(
    f"[OK] Updated: {HTML_PATH}"
)

print()

print(
    "[SUCCESS] Discarded Compact Flow V1.2.2 removed"
)
