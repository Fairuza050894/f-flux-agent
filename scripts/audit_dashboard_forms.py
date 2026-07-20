from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]

HTML_PATH = (
    ROOT
    / "qa_dashboard"
    / "frontend"
    / "dashboard.html"
)

OUTPUT_PATH = (
    ROOT
    / "dashboard_forms_audit.txt"
)

text = HTML_PATH.read_text(
    encoding="utf-8",
    errors="replace",
)


TAB_IDS = [
    "tab-registered",
    "tab-custom",
    "tab-curl",
    "tab-planning",
    "tab-history",
]

FUNCTION_NAMES = [
    "runRegisteredQA",
    "runCustomSmoke",
    "runCurlTest",
    "generateTestPlan",
    "runAnalysisAgent",
    "renderPaginatedHistory",
]


def find_balanced_element(
    source: str,
    element_id: str,
):
    id_match = re.search(
        rf'\bid=["\']{re.escape(element_id)}["\']',
        source,
    )

    if not id_match:
        return None

    opening_start = source.rfind(
        "<",
        0,
        id_match.start(),
    )

    opening_end = source.find(
        ">",
        id_match.end(),
    )

    if opening_start == -1 or opening_end == -1:
        return None

    opening_tag = source[
        opening_start:opening_end + 1
    ]

    tag_match = re.match(
        r"<([a-zA-Z0-9_-]+)\b",
        opening_tag,
    )

    if not tag_match:
        return None

    tag_name = tag_match.group(1)

    token_pattern = re.compile(
        rf"</?{re.escape(tag_name)}\b[^>]*>",
        flags=re.IGNORECASE,
    )

    depth = 0

    for token in token_pattern.finditer(
        source,
        opening_start,
    ):
        token_text = token.group(0)

        is_closing = token_text.startswith(
            "</"
        )

        is_self_closing = token_text.rstrip().endswith(
            "/>"
        )

        if is_closing:
            depth -= 1

            if depth == 0:
                return source[
                    opening_start:token.end()
                ]
        elif not is_self_closing:
            depth += 1

    return None


def find_function_block(
    source: str,
    function_name: str,
):
    pattern = re.compile(
        rf"(?m)^[ \t]*"
        rf"(?:async[ \t]+)?"
        rf"function[ \t]+"
        rf"{re.escape(function_name)}"
        rf"[ \t]*\("
    )

    match = pattern.search(source)

    if not match:
        return None

    opening_brace = source.find(
        "{",
        match.end(),
    )

    if opening_brace == -1:
        return None

    depth = 0
    quote = None
    escaped = False
    template_depth = 0

    for index in range(
        opening_brace,
        len(source),
    ):
        character = source[index]

        if escaped:
            escaped = False
            continue

        if character == "\\":
            escaped = True
            continue

        if quote:
            if character == quote:
                quote = None
            continue

        if character in (
            "'",
            '"',
            "`",
        ):
            quote = character
            continue

        if character == "{":
            depth += 1

        elif character == "}":
            depth -= 1

            if depth == 0:
                return source[
                    match.start():index + 1
                ]

    return None


def extract_controls(block: str):
    controls = []

    control_pattern = re.compile(
        r"<(input|select|textarea|button)\b"
        r"([^>]*)>",
        flags=re.IGNORECASE | re.DOTALL,
    )

    for match in control_pattern.finditer(
        block
    ):
        tag = match.group(1).lower()
        attributes = match.group(2)

        def attr(name):
            value_match = re.search(
                rf'\b{name}=["\']([^"\']*)["\']',
                attributes,
                flags=re.IGNORECASE,
            )

            return (
                value_match.group(1)
                if value_match
                else None
            )

        controls.append({
            "tag": tag,
            "id": attr("id"),
            "name": attr("name"),
            "type": attr("type"),
            "placeholder": attr(
                "placeholder"
            ),
            "onclick": attr("onclick"),
            "required": bool(
                re.search(
                    r"\brequired\b",
                    attributes,
                    flags=re.IGNORECASE,
                )
            ),
            "disabled": bool(
                re.search(
                    r"\bdisabled\b",
                    attributes,
                    flags=re.IGNORECASE,
                )
            ),
        })

    return controls


lines = []

lines.append(
    "QA DASHBOARD FORM AUDIT"
)
lines.append("=" * 78)
lines.append("")

for tab_id in TAB_IDS:
    lines.append(
        f"TAB: {tab_id}"
    )
    lines.append("-" * 78)

    block = find_balanced_element(
        text,
        tab_id,
    )

    if not block:
        lines.append(
            "STATUS: NOT FOUND"
        )
        lines.append("")
        continue

    controls = extract_controls(
        block
    )

    lines.append(
        f"BLOCK LENGTH: {len(block)}"
    )

    lines.append(
        f"CONTROL COUNT: {len(controls)}"
    )

    lines.append("")

    for control in controls:
        lines.append(
            "- "
            + " | ".join([
                f'tag={control["tag"]}',
                f'id={control["id"]}',
                f'name={control["name"]}',
                f'type={control["type"]}',
                (
                    "required="
                    + str(
                        control["required"]
                    )
                ),
                (
                    "disabled="
                    + str(
                        control["disabled"]
                    )
                ),
                (
                    "placeholder="
                    + str(
                        control["placeholder"]
                    )
                ),
                (
                    "onclick="
                    + str(
                        control["onclick"]
                    )
                ),
            ])
        )

    lines.append("")
    lines.append("HTML BLOCK")
    lines.append("~" * 78)
    lines.append(block)
    lines.append("")
    lines.append("")


lines.append(
    "JAVASCRIPT SUBMIT FUNCTIONS"
)
lines.append("=" * 78)
lines.append("")

for function_name in FUNCTION_NAMES:
    lines.append(
        f"FUNCTION: {function_name}"
    )
    lines.append("-" * 78)

    block = find_function_block(
        text,
        function_name,
    )

    if block:
        lines.append(block)
    else:
        lines.append("NOT FOUND")

    lines.append("")
    lines.append("")


OUTPUT_PATH.write_text(
    "\n".join(lines),
    encoding="utf-8",
)

print(f"Audit saved: {OUTPUT_PATH}")
print()
print(
    "Tabs audited:",
    ", ".join(TAB_IDS),
)
print(
    "Functions audited:",
    ", ".join(FUNCTION_NAMES),
)
