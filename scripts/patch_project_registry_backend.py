from pathlib import Path
from datetime import datetime
import shutil


ROOT = Path(__file__).resolve().parents[1]

APP_PATH = (
    ROOT
    / "qa_dashboard"
    / "backend"
    / "app.py"
)

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

backup_path = APP_PATH.with_name(
    "app.py.backup_before_project_registry_"
    + timestamp
)

shutil.copy2(
    APP_PATH,
    backup_path,
)

text = APP_PATH.read_text(
    encoding="utf-8"
)


project_api_code = r'''

# ============================================================
# QA Project Registry API
# ============================================================

def _qa_project_root():
    from pathlib import Path

    return (
        Path(__file__).resolve()
        .parents[2]
        / "skills"
        / "qa_automation"
        / "projects"
    )


def _qa_project_read_json(
    path,
    default=None,
):
    import json

    if default is None:
        default = {}

    if not path.exists() or not path.is_file():
        return default

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return default


def _qa_project_safe_id(project_id):
    import re

    value = str(
        project_id or ""
    ).strip().lower()

    if not re.fullmatch(
        r"[a-z0-9][a-z0-9_-]{0,63}",
        value,
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid project ID",
        )

    return value


def _qa_project_resolve_file(
    base_path,
    relative_path,
):
    from pathlib import Path

    if not relative_path:
        return None

    root = _qa_project_root().resolve()

    try:
        path = (
            Path(base_path)
            / str(relative_path)
        ).resolve()

        path.relative_to(root)
    except Exception:
        return None

    if not path.exists() or not path.is_file():
        return None

    return path


def _qa_project_environment_name(
    project_dir,
    project_config,
):
    files = project_config.get("files")

    if not isinstance(files, dict):
        files = {}

    environment_path = (
        _qa_project_resolve_file(
            project_dir,
            files.get("environments"),
        )
    )

    environment_data = (
        _qa_project_read_json(
            environment_path,
            {},
        )
        if environment_path
        else {}
    )

    environments = environment_data.get(
        "environments"
    )

    if not isinstance(environments, list):
        environments = []

    default_environment = str(
        project_config.get(
            "default_environment"
        )
        or ""
    )

    for environment in environments:
        if not isinstance(
            environment,
            dict,
        ):
            continue

        if str(
            environment.get(
                "environment_id"
            )
            or ""
        ) == default_environment:
            return str(
                environment.get("name")
                or default_environment
                or "Custom"
            )

    return (
        default_environment.title()
        if default_environment
        else "Custom"
    )


def _qa_project_count_items(
    project_dir,
    project_config,
    file_key,
    collection_key,
):
    files = project_config.get("files")

    if not isinstance(files, dict):
        files = {}

    path = _qa_project_resolve_file(
        project_dir,
        files.get(file_key),
    )

    if not path:
        return 0

    data = _qa_project_read_json(
        path,
        {},
    )

    items = data.get(collection_key)

    return (
        len(items)
        if isinstance(items, list)
        else 0
    )


def _qa_project_registry_entries():
    root = _qa_project_root()

    registry_path = (
        root
        / "project_registry.json"
    )

    registry = _qa_project_read_json(
        registry_path,
        {
            "projects": [],
        },
    )

    entries = registry.get("projects")

    if not isinstance(entries, list):
        return []

    return [
        item
        for item in entries
        if isinstance(item, dict)
    ]


def _qa_project_load_entry(entry):
    root = _qa_project_root()

    config_path = _qa_project_resolve_file(
        root,
        entry.get("config_path"),
    )

    if not config_path:
        return None

    config = _qa_project_read_json(
        config_path,
        {},
    )

    if not isinstance(config, dict):
        return None

    project_dir = config_path.parent

    return {
        "project_id": str(
            config.get("project_id")
            or entry.get("project_id")
            or ""
        ),
        "name": str(
            config.get("name")
            or entry.get("name")
            or ""
        ),
        "description": str(
            config.get("description")
            or entry.get("description")
            or ""
        ),
        "status": str(
            config.get("status")
            or entry.get("status")
            or "unknown"
        ),
        "default_environment": (
            config.get(
                "default_environment"
            )
        ),
        "default_environment_name": (
            _qa_project_environment_name(
                project_dir,
                config,
            )
        ),
        "supported_test_types": (
            config.get(
                "supported_test_types"
            )
            if isinstance(
                config.get(
                    "supported_test_types"
                ),
                list,
            )
            else []
        ),
        "runner_adapter": config.get(
            "runner_adapter"
        ),
        "feature_count": (
            _qa_project_count_items(
                project_dir,
                config,
                "features",
                "features",
            )
        ),
        "regression_suite_count": (
            _qa_project_count_items(
                project_dir,
                config,
                "regression_suites",
                "regression_suites",
            )
        ),
    }


@app.get("/projects")
def list_qa_projects():
    projects = []

    for entry in (
        _qa_project_registry_entries()
    ):
        project = _qa_project_load_entry(
            entry
        )

        if project:
            projects.append(project)

    return {
        "ok": True,
        "count": len(projects),
        "projects": projects,
    }


@app.get("/projects/{project_id}")
def get_qa_project(project_id: str):
    safe_project_id = (
        _qa_project_safe_id(
            project_id
        )
    )

    matched_entry = None

    for entry in (
        _qa_project_registry_entries()
    ):
        if str(
            entry.get("project_id") or ""
        ).lower() == safe_project_id:
            matched_entry = entry
            break

    if not matched_entry:
        raise HTTPException(
            status_code=404,
            detail=(
                "Project not found: "
                + safe_project_id
            ),
        )

    root = _qa_project_root()

    config_path = _qa_project_resolve_file(
        root,
        matched_entry.get(
            "config_path"
        ),
    )

    if not config_path:
        raise HTTPException(
            status_code=404,
            detail=(
                "Project configuration "
                "was not found"
            ),
        )

    config = _qa_project_read_json(
        config_path,
        {},
    )

    project_dir = config_path.parent
    files = config.get("files")

    if not isinstance(files, dict):
        files = {}

    detail = {
        "project": _qa_project_load_entry(
            matched_entry
        ),
        "environments": [],
        "features": [],
        "regression_suites": [],
        "api_collections": [],
        "e2e_flows": [],
    }

    file_mapping = {
        "environments": "environments",
        "features": "features",
        "regression_suites": (
            "regression_suites"
        ),
        "api_collections": (
            "api_collections"
        ),
        "e2e_flows": "e2e_flows",
    }

    for file_key, collection_key in (
        file_mapping.items()
    ):
        path = _qa_project_resolve_file(
            project_dir,
            files.get(file_key),
        )

        if not path:
            continue

        payload = _qa_project_read_json(
            path,
            {},
        )

        collection = payload.get(
            collection_key
        )

        if isinstance(collection, list):
            detail[collection_key] = (
                collection
            )

    return {
        "ok": True,
        **detail,
    }
'''


if '@app.get("/projects")' not in text:
    text = (
        text.rstrip()
        + "\n"
        + project_api_code
        + "\n"
    )

    print(
        "Inserted Project Registry API"
    )
else:
    print(
        "Project Registry API already exists"
    )


APP_PATH.write_text(
    text,
    encoding="utf-8",
)

print(f"Backup created: {backup_path}")
