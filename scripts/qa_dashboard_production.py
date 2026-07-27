#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Hermes QA Dashboard with one "
            "deterministic production environment."
        ),
    )
    parser.add_argument(
        "--env-file",
        default=(
            "qa_dashboard/.env.production"
        ),
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
    )
    parser.add_argument(
        "--port",
        default=8765,
        type=int,
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help=(
            "Stop a previously running QA "
            "Dashboard process on the same port."
        ),
    )
    return parser.parse_args()


def _listening_pids(
    port: int,
) -> list[int]:
    result = subprocess.run(
        [
            "lsof",
            f"-tiTCP:{port}",
            "-sTCP:LISTEN",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    pids: list[int] = []

    for line in result.stdout.splitlines():
        try:
            pids.append(int(line.strip()))
        except ValueError:
            continue

    return sorted(set(pids))


def _process_table() -> dict[
    int,
    tuple[int, str],
]:
    result = subprocess.run(
        [
            "ps",
            "-axo",
            "pid=,ppid=,command=",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    table: dict[int, tuple[int, str]] = {}

    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 2)

        if len(parts) < 3:
            continue

        try:
            pid = int(parts[0])
            ppid = int(parts[1])
        except ValueError:
            continue

        table[pid] = (
            ppid,
            parts[2],
        )

    return table


def _is_dashboard_process(
    command: str,
) -> bool:
    normalized = command.lower()
    root_text = str(ROOT).lower()

    marker = any(
        value in normalized
        for value in (
            "qa_dashboard_production.py",
            "qa_dashboard.backend.app:app",
            "multiprocessing.spawn",
        )
    )

    return marker and (
        root_text in normalized
        or "qa_dashboard" in normalized
    )


def _descendants(
    roots: set[int],
    table: dict[int, tuple[int, str]],
) -> set[int]:
    collected = set(roots)
    changed = True

    while changed:
        changed = False

        for pid, (ppid, _command) in (
            table.items()
        ):
            if (
                ppid in collected
                and pid not in collected
            ):
                collected.add(pid)
                changed = True

    return collected


def _stop_existing_dashboard(
    port: int,
) -> None:
    listeners = _listening_pids(port)

    if not listeners:
        return

    table = _process_table()
    targets = _descendants(
        set(listeners),
        table,
    )

    for pid in listeners:
        command = table.get(
            pid,
            (0, ""),
        )[1]

        if not _is_dashboard_process(command):
            raise RuntimeError(
                f"Port {port} is used by an "
                "unrecognized process. Nothing "
                f"was stopped. PID {pid}: "
                f"{command or '<unknown>'}"
            )

    for pid in list(targets):
        current = pid

        while current in table:
            ppid, _command = table[current]

            if ppid not in table:
                break

            parent_command = table[ppid][1]

            if not _is_dashboard_process(
                parent_command,
            ):
                break

            targets.add(ppid)
            current = ppid

    for pid in sorted(
        targets,
        reverse=True,
    ):
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    deadline = time.time() + 8

    while (
        time.time() < deadline
        and _listening_pids(port)
    ):
        time.sleep(0.25)

    remaining = _listening_pids(port)

    for pid in remaining:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    time.sleep(0.25)

    if _listening_pids(port):
        raise RuntimeError(
            f"Port {port} could not be cleared."
        )


def main() -> int:
    args = parse_args()

    if args.replace:
        _stop_existing_dashboard(
            args.port,
        )
    elif _listening_pids(args.port):
        raise RuntimeError(
            f"Port {args.port} is already in use. "
            "Run again with --replace after "
            "confirming it is the QA Dashboard."
        )

    from qa_dashboard.backend.environment import (
        load_dashboard_environment,
    )

    env_path = load_dashboard_environment(
        root=ROOT,
        env_file=args.env_file,
    )

    from qa_dashboard.backend.settings import (
        get_settings,
    )

    get_settings.cache_clear()
    settings = get_settings()

    from qa_dashboard.backend.app import app
    from qa_dashboard.backend.auth_diagnostics import (
        verify_password_authentication,
    )

    if settings.auth_required:
        if not settings.auth_password:
            raise RuntimeError(
                "Production startup preflight "
                "requires a plaintext password in "
                "the local, untracked environment "
                "file."
            )

        verify_password_authentication(
            app,
            username=settings.auth_username,
            password=settings.auth_password,
        )

        print(
            "Authentication preflight: PASSED"
        )

    print(f"Environment: {env_path}")
    print(
        "QA Dashboard: "
        f"http://{args.host}:{args.port}/login"
    )
    print(
        "Health: "
        f"http://{args.host}:{args.port}"
        "/api/v1/health/ready"
    )

    import uvicorn

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=False,
        workers=1,
        proxy_headers=True,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
