from pathlib import Path
import ast
import json
import re


ROOT = Path(__file__).resolve().parents[1]

APP_PATH = ROOT / "qa_dashboard" / "backend" / "app.py"
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

PROJECT_ROOT = ROOT / "skills" / "qa_automation" / "projects"

HISTORY_PATH = (
    ROOT
    / "skills"
    / "qa_automation"
    / "artifacts"
    / "history"
    / "qa_run_history.json"
)

STANDARD_JSON_ROOT = (
    ROOT
    / "skills"
    / "qa_automation"
    / "artifacts"
    / "json"
)

OUTPUT_PATH = ROOT / "project_context_integration_audit.txt"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""

    return path.read_text(
        encoding="utf-8",
        errors="replace",
    )


def ast_name(node):
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = ast_name(node.value)

        return (
            f"{parent}.{node.attr}"
            if parent
            else node.attr
        )

    if isinstance(node, ast.Subscript):
        return ast_name(node.value)

    return ""


def function_signature(node):
    arguments = []

    positional = (
        list(node.args.posonlyargs)
        + list(node.args.args)
    )

    defaults = [None] * (
        len(positional)
        - len(node.args.defaults)
    ) + list(node.args.defaults)

    for argument, default in zip(
        positional,
        defaults,
    ):
        item = argument.arg

        if argument.annotation:
            try:
                item += ": " + ast.unparse(
                    argument.annotation
                )
            except Exception:
                pass

        if default is not None:
            try:
                item += " = " + ast.unparse(
                    default
                )
            except Exception:
                item += " = ..."

        arguments.append(item)

    if node.args.vararg:
        arguments.append(
            "*" + node.args.vararg.arg
        )

    for argument, default in zip(
        node.args.kwonlyargs,
        node.args.kw_defaults,
    ):
        item = argument.arg

        if argument.annotation:
            try:
                item += ": " + ast.unparse(
                    argument.annotation
                )
            except Exception:
                pass

        if default is not None:
            try:
                item += " = " + ast.unparse(
                    default
                )
            except Exception:
                item += " = ..."

        arguments.append(item)

    if node.args.kwarg:
        arguments.append(
            "**" + node.args.kwarg.arg
        )

    return (
        f"{node.name}("
        + ", ".join(arguments)
        + ")"
    )


def route_details(path: Path):
    source = read_text(path)

    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [
            f"AST ERROR: {error}"
        ], []

    relevant_prefixes = (
        "/runs",
        "/custom-smoke",
        "/curl-test",
        "/history",
        "/telemetry",
        "/projects",
        "/test-templates",
        "/analysis",
    )

    routes = []
    models = []

    for node in tree.body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            for decorator in node.decorator_list:
                if not isinstance(
                    decorator,
                    ast.Call,
                ):
                    continue

                decorator_name = ast_name(
                    decorator.func
                )

                if not decorator_name.startswith(
                    "app."
                ):
                    continue

                if not decorator.args:
                    continue

                route_path = None

                first_argument = decorator.args[0]

                if isinstance(
                    first_argument,
                    ast.Constant,
                ):
                    route_path = (
                        first_argument.value
                    )

                if not isinstance(
                    route_path,
                    str,
                ):
                    continue

                if not route_path.startswith(
                    relevant_prefixes
                ):
                    continue

                routes.append({
                    "method": (
                        decorator_name.split(
                            "."
                        )[-1].upper()
                    ),
                    "path": route_path,
                    "function": (
                        function_signature(node)
                    ),
                    "line": node.lineno,
                })

        if isinstance(node, ast.ClassDef):
            base_names = {
                ast_name(base)
                for base in node.bases
            }

            if not any(
                "BaseModel" in base
                for base in base_names
            ):
                continue

            fields = []

            for item in node.body:
                if not isinstance(
                    item,
                    ast.AnnAssign,
                ):
                    continue

                if not isinstance(
                    item.target,
                    ast.Name,
                ):
                    continue

                try:
                    annotation = ast.unparse(
                        item.annotation
                    )
                except Exception:
                    annotation = "unknown"

                fields.append(
                    f"{item.target.id}: "
                    f"{annotation}"
                )

            models.append({
                "name": node.name,
                "line": node.lineno,
                "fields": fields,
            })

    return routes, models


def checker_functions(path: Path):
    source = read_text(path)

    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [
            f"AST ERROR: {error}"
        ]

    exact_names = {
        "perform_audit_for_telegram",
        "perform_custom_smoke_test",
        "_perform_custom_smoke_generic_ui_v2",
        "enrich_qa_result_with_standard_json",
        "append_qa_run_history",
        "perform_audit",
    }

    keyword_parts = (
        "history",
        "standard_json",
        "artifact",
        "telemetry",
        "custom_smoke",
        "audit",
        "curl",
    )

    functions = []

    for node in ast.walk(tree):
        if not isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            continue

        if (
            node.name in exact_names
            or any(
                part in node.name.lower()
                for part in keyword_parts
            )
        ):
            functions.append({
                "name": node.name,
                "signature": (
                    function_signature(node)
                ),
                "line": node.lineno,
                "end_line": getattr(
                    node,
                    "end_lineno",
                    None,
                ),
            })

    functions.sort(
        key=lambda item: item["line"]
    )

    return functions


def frontend_functions(path: Path):
    source = read_text(path)

    names = [
        "applyQaProjectSelection",
        "handleQaProjectChange",
        "loadQaProjectRegistry",
        "qaRenameNavigationButton",
        "startAgentFlow",
        "completeAgentFlow",
        "runRegisteredQA",
        "runCustomSmoke",
        "runCurlTest",
        "loadPaginatedHistory",
        "renderPaginatedHistory",
        "openPaginatedHistoryDetail",
        "startExecutionTelemetry",
        "completeExecutionTelemetry",
        "runAnalysisAgent",
    ]

    result = []

    for name in names:
        pattern = re.compile(
            rf"(?m)^[ \t]*"
            rf"(?:async[ \t]+)?"
            rf"function[ \t]+"
            rf"{re.escape(name)}"
            rf"[ \t]*\("
        )

        match = pattern.search(source)

        if match:
            line = (
                source.count(
                    "\n",
                    0,
                    match.start(),
                )
                + 1
            )

            result.append({
                "name": name,
                "line": line,
            })

    return result


def frontend_ids(path: Path):
    source = read_text(path)

    ids = sorted(
        set(
            re.findall(
                r'\bid=["\']([^"\']+)["\']',
                source,
            )
        )
    )

    interesting_parts = (
        "tab-",
        "Result",
        "result",
        "Feature",
        "feature",
        "History",
        "history",
        "Project",
        "project",
        "runDetail",
        "Telemetry",
        "telemetry",
    )

    return [
        item
        for item in ids
        if any(
            part in item
            for part in interesting_parts
        )
    ]


def project_summary():
    registry_path = (
        PROJECT_ROOT
        / "project_registry.json"
    )

    if not registry_path.exists():
        return []

    registry = json.loads(
        registry_path.read_text(
            encoding="utf-8"
        )
    )

    summaries = []

    for entry in registry.get(
        "projects",
        [],
    ):
        if not isinstance(entry, dict):
            continue

        config_path = (
            PROJECT_ROOT
            / str(entry.get("config_path"))
        )

        if not config_path.exists():
            continue

        config = json.loads(
            config_path.read_text(
                encoding="utf-8"
            )
        )

        project_dir = config_path.parent
        files = config.get("files") or {}

        def count_collection(
            file_key,
            collection_key,
        ):
            relative_path = files.get(
                file_key
            )

            if not relative_path:
                return 0

            path = (
                project_dir
                / relative_path
            )

            if not path.exists():
                return 0

            payload = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

            collection = payload.get(
                collection_key
            )

            return (
                len(collection)
                if isinstance(
                    collection,
                    list,
                )
                else 0
            )

        summaries.append({
            "project_id": config.get(
                "project_id"
            ),
            "name": config.get("name"),
            "environment": config.get(
                "default_environment"
            ),
            "supported_test_types": (
                config.get(
                    "supported_test_types"
                )
            ),
            "features": count_collection(
                "features",
                "features",
            ),
            "regression_suites": (
                count_collection(
                    "regression_suites",
                    "regression_suites",
                )
            ),
            "api_collections": (
                count_collection(
                    "api_collections",
                    "api_collections",
                )
            ),
            "e2e_flows": count_collection(
                "e2e_flows",
                "e2e_flows",
            ),
        })

    return summaries


def history_summary():
    if not HISTORY_PATH.exists():
        return {
            "available": False,
        }

    history = json.loads(
        HISTORY_PATH.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(history, list):
        return {
            "available": True,
            "root_type": type(history).__name__,
        }

    latest = (
        history[0]
        if history
        and isinstance(history[0], dict)
        else {}
    )

    project_count = sum(
        1
        for item in history
        if isinstance(item, dict)
        and item.get("project_id")
    )

    return {
        "available": True,
        "count": len(history),
        "latest_keys": sorted(
            latest.keys()
        ),
        "latest_execution_id": (
            latest.get("execution_id")
        ),
        "runs_with_project_id": (
            project_count
        ),
    }


def standard_json_summary():
    if not STANDARD_JSON_ROOT.exists():
        return {
            "available": False,
        }

    files = list(
        STANDARD_JSON_ROOT.glob("*.json")
    )

    if not files:
        return {
            "available": True,
            "count": 0,
        }

    latest = max(
        files,
        key=lambda path: (
            path.stat().st_mtime
        ),
    )

    payload = json.loads(
        latest.read_text(
            encoding="utf-8"
        )
    )

    execution = payload.get(
        "execution"
    )

    artifacts = payload.get(
        "artifacts"
    )

    return {
        "available": True,
        "file": str(latest),
        "root_keys": sorted(
            payload.keys()
        ),
        "execution_keys": sorted(
            execution.keys()
        ) if isinstance(
            execution,
            dict,
        ) else [],
        "artifact_keys": sorted(
            artifacts.keys()
        ) if isinstance(
            artifacts,
            dict,
        ) else [],
        "has_project_id": bool(
            isinstance(execution, dict)
            and execution.get(
                "project_id"
            )
        ),
    }


routes, models = route_details(
    APP_PATH
)

checker = checker_functions(
    CHECKER_PATH
)

frontend = frontend_functions(
    HTML_PATH
)

html_ids = frontend_ids(
    HTML_PATH
)

projects = project_summary()
history = history_summary()
standard_json = (
    standard_json_summary()
)


lines = []

lines.append(
    "QA PROJECT CONTEXT INTEGRATION AUDIT"
)
lines.append("=" * 72)
lines.append("")

lines.append("1. BACKEND ROUTES")
lines.append("-" * 72)

for item in routes:
    if isinstance(item, str):
        lines.append(item)
        continue

    lines.append(
        f'{item["method"]:6} '
        f'{item["path"]:32} '
        f'line={item["line"]} '
        f'function={item["function"]}'
    )

lines.append("")
lines.append("2. PYDANTIC REQUEST MODELS")
lines.append("-" * 72)

for model in models:
    lines.append(
        f'{model["name"]} '
        f'(line {model["line"]})'
    )

    for field in model["fields"]:
        lines.append(
            f"  - {field}"
        )

lines.append("")
lines.append("3. CHECKER FUNCTIONS")
lines.append("-" * 72)

for item in checker:
    if isinstance(item, str):
        lines.append(item)
        continue

    lines.append(
        f'line={item["line"]}'
        f'..{item["end_line"]} '
        f'{item["signature"]}'
    )

lines.append("")
lines.append("4. FRONTEND FUNCTIONS")
lines.append("-" * 72)

for item in frontend:
    lines.append(
        f'line={item["line"]} '
        f'{item["name"]}'
    )

lines.append("")
lines.append("5. RELEVANT FRONTEND ELEMENT IDS")
lines.append("-" * 72)

for item in html_ids:
    lines.append(f"- {item}")

lines.append("")
lines.append("6. PROJECT REGISTRY")
lines.append("-" * 72)
lines.append(
    json.dumps(
        projects,
        indent=2,
        ensure_ascii=False,
    )
)

lines.append("")
lines.append("7. HISTORY SCHEMA")
lines.append("-" * 72)
lines.append(
    json.dumps(
        history,
        indent=2,
        ensure_ascii=False,
    )
)

lines.append("")
lines.append("8. STANDARD JSON SCHEMA")
lines.append("-" * 72)
lines.append(
    json.dumps(
        standard_json,
        indent=2,
        ensure_ascii=False,
    )
)

OUTPUT_PATH.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)

print(f"Audit saved: {OUTPUT_PATH}")
print()
print("\n".join(lines))
