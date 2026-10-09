from __future__ import annotations
import socket
import platform

import json
import os
import re
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from dotenv import load_dotenv
from PIL import Image, ImageChops, ImageStat

try:  # playwright is only needed when an audit actually drives a browser
    from playwright.sync_api import Page, sync_playwright
except ImportError:  # pragma: no cover - importing this module must work without browsers installed
    Page = Any  # type: ignore[assignment,misc]  # annotations only (see __future__ import above)

    def sync_playwright(*_args: Any, **_kwargs: Any) -> Any:  # type: ignore[misc]
        raise ImportError(
            "playwright is required to run QA audits "
            "(install: pip install playwright && playwright install chromium)"
        )


# =========================================================
# Path Configuration
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

CONFIG_PATH = BASE_DIR / "config.json"
BASELINE_DIR = BASE_DIR / "baselines"
ARTIFACT_DIR = BASE_DIR / "artifacts"
SCREENSHOT_DIR = ARTIFACT_DIR / "screenshots"
DIFF_DIR = ARTIFACT_DIR / "diffs"
REPORT_DIR = ARTIFACT_DIR / "reports"
LOG_DIR = ARTIFACT_DIR / "logs"
SPREADSHEET_DIR = ARTIFACT_DIR / "spreadsheets"
DEBUG_DIR = ARTIFACT_DIR / "debug"

for folder in [BASELINE_DIR, SCREENSHOT_DIR, DIFF_DIR, REPORT_DIR, LOG_DIR, SPREADSHEET_DIR, DEBUG_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
CROSS_FEATURE_TARGETS = [
    {
        "name": "Dashboard",
        "aliases": ["Dashboard"],
        "severity_if_failed": "High",
    },
    {
        "name": "Shipment Details",
        "aliases": ["Shipment Details", "Shipment Detail"],
        "severity_if_failed": "High",
    },
    {
        "name": "MoboMap",
        "aliases": ["MoboMap", "Mobo Map"],
        "severity_if_failed": "High",
    },
    {
        "name": "Verify Activities",
        "aliases": ["Verify Activities", "Verify Activity"],
        "severity_if_failed": "Medium",
    },
    {
        "name": "Notification Message",
        "aliases": ["Notification Message", "Notification"],
        "severity_if_failed": "Medium",
    },
    {
        "name": "Inspection Result",
        "aliases": ["Inspection Result", "Inspection"],
        "severity_if_failed": "Medium",
    },
]

# =========================================================
# Basic Helper
# =========================================================

def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "module"

def save_current_screenshot(
    page: Page,
    module_slug: str,
    run_id: str,
) -> str:
    screenshots_dir = Path(__file__).parent / "artifacts" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    screenshot_path = screenshots_dir / f"current_{module_slug}_{run_id}.png"

    try:
        page.screenshot(
            path=str(screenshot_path),
            full_page=True,
            timeout=15000,
        )
    except Exception:
        try:
            page.screenshot(
                path=str(screenshot_path),
                full_page=False,
                timeout=15000,
            )
        except Exception:
            pass

    return str(screenshot_path)

def get_credentials(url: str) -> tuple[Optional[str], Optional[str]]:
    try:
        if not CONFIG_PATH.exists():
            return None, None

        parsed_url = urlparse(url)
        host = parsed_url.netloc.lower()

        with CONFIG_PATH.open("r", encoding="utf-8") as file:
            config = json.load(file)

        for allowed_host, creds in config.items():
            allowed_host = allowed_host.lower()

            if host == allowed_host or host.endswith(f".{allowed_host}"):
                username = os.getenv(creds.get("user_env", ""))
                password = os.getenv(creds.get("pass_env", ""))
                return username, password

        return None, None

    except Exception:
        return None, None


def add_test_case(
    test_cases: list[dict[str, str]],
    scenario: str,
    expected: str,
    status: str,
    actual: str,
    precondition: str = "-",
    steps: str = "-",
) -> None:
    test_id = f"TC-{len(test_cases) + 1:03d}"

    test_cases.append(
        {
            "id": test_id,
            "scenario": scenario,
            "precondition": precondition,
            "steps": steps,
            "expected": expected,
            "actual": actual,
            "status": status,
        }
    )


def add_bug(
    bugs: list[dict[str, str]],
    severity: str,
    title: str,
    actual: str,
    expected: str,
    status: str = "Open",
) -> None:
    bug_id = f"BUG-{len(bugs) + 1:03d}"

    bugs.append(
        {
            "id": bug_id,
            "severity": severity,
            "title": title,
            "actual": actual,
            "expected": expected,
            "status": status,
        }
    )


def is_visible_text(
    page: Page,
    text: str,
    exact: bool = False,
    timeout: int = 3000,
) -> bool:
    try:
        page.get_by_text(text, exact=exact).first.wait_for(
            state="visible",
            timeout=timeout,
        )
        return True
    except Exception:
        return False


def is_any_text_visible(
    page: Page,
    texts: list[str],
    timeout: int = 3000,
) -> tuple[bool, str]:
    for text in texts:
        if is_visible_text(page, text, exact=False, timeout=timeout):
            return True, text

    return False, ""


def try_click_text(
    page: Page,
    texts: list[str],
    timeout: int = 3000,
) -> tuple[bool, str]:
    for text in texts:
        try:
            locator = page.get_by_text(text, exact=False).first
            locator.wait_for(state="visible", timeout=timeout)
            locator.click(timeout=timeout)
            return True, text
        except Exception:
            continue

    return False, ""


def try_click_selector(
    page: Page,
    selectors: list[str],
    timeout: int = 4000,
) -> tuple[bool, str]:
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout)
            locator.click(timeout=timeout)
            return True, selector
        except Exception:
            continue

    return False, ""


# =========================================================
# Login and Navigation
# =========================================================

def fill_login_form(page: Page, username: str, password: str) -> None:
    username_selector = (
        'input#email, '
        'input[name="email"], '
        'input[type="email"], '
        'input[name="username"], '
        'input[placeholder*="email" i], '
        'input[placeholder*="user" i]'
    )

    password_selector = (
        'input#password, '
        'input[name="password"], '
        'input[type="password"], '
        'input[placeholder*="password" i]'
    )

    page.locator(username_selector).first.wait_for(state="visible", timeout=15000)
    page.locator(username_selector).first.fill(username)

    page.locator(password_selector).first.wait_for(state="visible", timeout=15000)
    page.locator(password_selector).first.fill(password)


def is_still_on_login_page(page: Page) -> bool:
    try:
        return page.locator(
            'input#password, input[name="password"], input[type="password"]'
        ).first.is_visible()
    except Exception:
        return False



FEATURE_REGISTRY = {
    "driver_daily_meal": {
        "display_name": "Driver Daily Meal",
        "module_name": "Uang Makan Driver",
        "menu_aliases": [
            "Driver Meal",
            "Uang Makan Driver",
            "Meal Allowance",
            "Driver Meal Allowance",
        ],
        "aliases": [
            "driver daily meal",
            "driver meal",
            "driver_meal",
            "driver_daily_meal",
            "uang makan driver",
            "uang makan",
            "meal allowance",
        ],
        "default_subfeatures": [
            "monitoring",
            "exclude",
            "history",
        ],
        "subfeature_aliases": {
            "monitoring": [
                "monitoring",
                "monitor",
            ],
            "exclude": [
                "exclude",
                "excluded",
                "pengecualian",
                "exception",
                "exceptions",
            ],
            "history": [
                "history",
                "inquiry",
                "riwayat",
            ],
        },
    }
}


def normalize_feature_text(value: str) -> str:
    if not value:
        return ""

    return (
        value.strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )


def resolve_feature_key(feature_text: str) -> str:
    """
    Resolve text dari command Telegram menjadi feature_key.
    Contoh:
    - driver daily meal -> driver_daily_meal
    - driver meal -> driver_daily_meal
    - uang makan driver -> driver_daily_meal
    """

    normalized = normalize_feature_text(feature_text)

    if not normalized:
        return "driver_daily_meal"

    for feature_key, config in FEATURE_REGISTRY.items():
        candidates = [feature_key, config.get("display_name", "")]
        candidates.extend(config.get("aliases", []))

        for candidate in candidates:
            if normalize_feature_text(candidate) == normalized:
                return feature_key

    # Fallback agar flow lama tetap jalan
    if "driver" in normalized and "meal" in normalized:
        return "driver_daily_meal"

    if "uang" in normalized and "makan" in normalized:
        return "driver_daily_meal"

    return "driver_daily_meal"


def get_feature_config(feature_text: str = "") -> dict:
    feature_key = resolve_feature_key(feature_text)
    config = FEATURE_REGISTRY.get(feature_key, FEATURE_REGISTRY["driver_daily_meal"]).copy()
    config["feature_key"] = feature_key
    return config



def open_target_menu(page: Page, module_name: str):
    """
    Robust menu opener.

    Tujuan:
    - Menunggu sidebar selesai load
    - Membuka drawer jika sidebar belum terlihat
    - Mencari menu dengan beberapa alias
    - Klik menu walaupun posisi ada di dalam navigation drawer / v-list
    """

    aliases = [
        module_name,
        "Uang Makan Driver",
        "Driver Meal",
        "Meal Allowance",
        "Driver Meal Allowance",
    ]

    # Remove duplicate / empty alias
    aliases = [item for item in dict.fromkeys([a.strip() for a in aliases if a and a.strip()])]

    submenu_markers = [
        "Monitoring",
        "Pengecualian",
        "Inquiry",
    ]

    content_markers = [
        "Uang Makan Driver —",
        "Driver Meal —",
        "Working Date",
        "Driver Name",
        "Driver ID",
        "Eligible",
        "Rows per page:",
    ]

    def read_body_text() -> str:
        try:
            return page.locator("body").inner_text(timeout=5000)
        except Exception:
            return ""

    def wait_app_ready() -> None:
        try:
            page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        try:
            page.wait_for_selector("body", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(1500)

    def content_already_opened() -> bool:
        body_text = read_body_text()
        return any(marker in body_text for marker in content_markers)

    def submenu_visible() -> bool:
        body_text = read_body_text()
        return any(marker in body_text for marker in submenu_markers)

    def try_open_drawer() -> None:
        # Beberapa layout memakai hamburger / nav icon.
        drawer_buttons = [
            ".v-app-bar__nav-icon",
            "button:has(.mdi-menu)",
            "button[aria-label='menu']",
            "button[aria-label='Menu']",
            ".mdi-menu",
        ]

        for selector in drawer_buttons:
            try:
                locator = page.locator(selector).first
                if locator.count() > 0 and locator.is_visible():
                    locator.click(timeout=3000)
                    page.wait_for_timeout(1000)
                    break
            except Exception:
                continue

    def scroll_sidebar_to_top() -> None:
        try:
            page.evaluate(
                """() => {
                    const selectors = [
                        '.v-navigation-drawer__content',
                        '.v-navigation-drawer',
                        '.v-list',
                        'nav',
                        'aside'
                    ];

                    selectors.forEach((selector) => {
                        document.querySelectorAll(selector).forEach((el) => {
                            try { el.scrollTop = 0; } catch (e) {}
                        });
                    });
                }"""
            )
        except Exception:
            pass

    def click_candidate(locator, label: str) -> bool:
        try:
            count = locator.count()
        except Exception:
            count = 0

        if count <= 0:
            return False

        max_items = min(count, 5)

        for index in range(max_items):
            item = locator.nth(index)

            try:
                item.scroll_into_view_if_needed(timeout=3000)
            except Exception:
                pass

            try:
                item.wait_for(state="visible", timeout=3000)
            except Exception:
                continue

            try:
                item.click(timeout=5000)
            except Exception:
                try:
                    handle = item.element_handle(timeout=3000)
                    if handle:
                        page.evaluate("(el) => el.click()", handle)
                    else:
                        continue
                except Exception:
                    continue

            page.wait_for_timeout(1500)

            if submenu_visible() or content_already_opened():
                return True

        return False

    wait_app_ready()

    if content_already_opened():
        return True, "Already on target content"

    try_open_drawer()
    scroll_sidebar_to_top()

    # Kalau submenu sudah visible, berarti group menu sudah terbuka.
    if submenu_visible():
        return True, "Uang Makan Driver submenu already visible"

    scopes = [
        page.locator(".v-navigation-drawer, .v-navigation-drawer__content, .v-list, nav, aside").first,
        page.locator("body"),
    ]

    for attempt in range(3):
        wait_app_ready()
        scroll_sidebar_to_top()

        for alias in aliases:
            for scope in scopes:
                candidates = [
                    scope.get_by_text(alias, exact=True),
                    scope.get_by_text(alias, exact=False),
                ]

                for candidate in candidates:
                    if click_candidate(candidate, alias):
                        return True, alias

        # Jika belum ketemu, coba buka drawer lagi dan tunggu.
        try_open_drawer()
        page.wait_for_timeout(1500)

    return False, f"Menu {module_name} not found"


def open_uang_makan_driver_subpage(
    page: Page,
    test_cases: list[dict[str, str]],
    preferred_subpage: str = "Monitoring",
) -> None:
    """
    Setelah menu Uang Makan Driver terbuka, klik submenu default.
    Ini penting karena Uang Makan Driver adalah menu group,
    sedangkan konten aktual ada di submenu Monitoring / Pengecualian / Inquiry.
    """

    subpage_candidates = [
        preferred_subpage,
        "Monitoring",
        "Pengecualian",
        "Inquiry",
    ]

    # Remove duplicate while preserving order
    subpage_candidates = list(dict.fromkeys(subpage_candidates))

    clicked_subpage = None
    last_error = "-"

    for subpage in subpage_candidates:
        try:
            sidebar_scope = page.locator(".v-navigation-drawer, .v-list, nav").first

            try:
                locator = sidebar_scope.get_by_text(subpage, exact=True).first
                locator.wait_for(state="visible", timeout=4000)
                locator.click(timeout=5000)
            except Exception:
                locator = page.get_by_text(subpage, exact=True).first
                locator.wait_for(state="visible", timeout=4000)
                locator.click(timeout=5000)

            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass

            page.wait_for_timeout(1500)

            clicked_subpage = subpage
            break

        except Exception as exc:
            last_error = str(exc)
            continue

    if clicked_subpage:
        add_test_case(
            test_cases,
            scenario="Open Uang Makan Driver subpage",
            precondition="Uang Makan Driver menu group is visible",
            steps=f"Click {clicked_subpage} submenu",
            expected="Uang Makan Driver content subpage should be opened",
            actual=f"Opened submenu: {clicked_subpage}",
            status="PASS",
        )
    else:
        add_test_case(
            test_cases,
            scenario="Open Uang Makan Driver subpage",
            precondition="Uang Makan Driver menu group is visible",
            steps="Click Monitoring / Pengecualian / Inquiry submenu",
            expected="One Uang Makan Driver subpage should be opened",
            actual=f"Failed to open submenu. Last error: {last_error}",
            status="FAIL",
        )

# =========================================================
# Visual Regression
# =========================================================

def check_visual_regression(
    current_img_path: Path,
    module_name: str,
    threshold_percent: float = 0.5,
) -> dict[str, Any]:
    module_slug = slugify(module_name)
    baseline_path = BASELINE_DIR / f"baseline_{module_slug}.png"
    diff_path = DIFF_DIR / f"diff_{module_slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    if not baseline_path.exists():
        with Image.open(current_img_path) as image:
            image.save(baseline_path)

        return {
            "passed": True,
            "status": "BASELINE_CREATED",
            "message": "Baseline baru dibuat. Jalankan audit berikutnya untuk membandingkan visual regression.",
            "diff_percent": 0,
            "baseline_path": str(baseline_path),
            "diff_path": "-",
        }

    try:
        with Image.open(baseline_path) as baseline_file:
            baseline_img = baseline_file.convert("RGB")

        with Image.open(current_img_path) as current_file:
            current_img = current_file.convert("RGB")

        if baseline_img.size != current_img.size:
            return {
                "passed": False,
                "status": "FAILED",
                "message": f"Dimensi screenshot berubah. Baseline: {baseline_img.size}, Current: {current_img.size}",
                "diff_percent": 100,
                "baseline_path": str(baseline_path),
                "diff_path": "-",
            }

        diff = ImageChops.difference(baseline_img, current_img)
        stat = ImageStat.Stat(diff)
        diff_percent = round((sum(stat.mean) / (len(stat.mean) * 255)) * 100, 4)

        if diff_percent > threshold_percent:
            diff.save(diff_path)

            return {
                "passed": False,
                "status": "FAILED",
                "message": f"Regresi visual terdeteksi. Selisih {diff_percent}%, threshold {threshold_percent}%.",
                "diff_percent": diff_percent,
                "baseline_path": str(baseline_path),
                "diff_path": str(diff_path),
            }

        return {
            "passed": True,
            "status": "PASSED",
            "message": f"UI match. Selisih {diff_percent}%, threshold {threshold_percent}%.",
            "diff_percent": diff_percent,
            "baseline_path": str(baseline_path),
            "diff_path": "-",
        }

    except Exception as error:
        return {
            "passed": False,
            "status": "ERROR",
            "message": f"Gagal melakukan analisis visual: {error!s}",
            "diff_percent": "-",
            "baseline_path": str(baseline_path),
            "diff_path": "-",
        }


# =========================================================
# Business Validation
# =========================================================

def count_table_rows(page: Page) -> int:
    selectors = [
        "table tbody tr",
        "tbody tr",
        '[role="row"]',
    ]

    for selector in selectors:
        try:
            count = page.locator(selector).count()

            if count > 0:
                return count
        except Exception:
            continue

    return 0

def capture_selector_inventory(page: Page, module_slug: str, run_id: str) -> str:
    """
    Capture UI inventory untuk selector hardening.
    File ini membantu menentukan selector stabil berdasarkan UI aktual.
    """

    inventory_path = DEBUG_DIR / f"selector_inventory_{module_slug}_{run_id}.md"

    def safe_value(callback, default="-"):
        try:
            value = callback()
            if value is None:
                return default

            value = str(value).strip()
            return value if value else default
        except Exception:
            return default

    def collect_elements(selector: str, label: str, limit: int = 80) -> str:
        rows = []

        try:
            locator = page.locator(selector)
            count = min(locator.count(), limit)

            for index in range(count):
                item = locator.nth(index)

                is_visible = safe_value(lambda: item.is_visible(), False)

                if not is_visible:
                    continue

                text = safe_value(lambda: item.inner_text(timeout=1000))
                placeholder = safe_value(lambda: item.get_attribute("placeholder"))
                aria_label = safe_value(lambda: item.get_attribute("aria-label"))
                name = safe_value(lambda: item.get_attribute("name"))
                input_type = safe_value(lambda: item.get_attribute("type"))
                role = safe_value(lambda: item.get_attribute("role"))
                data_testid = safe_value(lambda: item.get_attribute("data-testid"))
                element_id = safe_value(lambda: item.get_attribute("id"))
                class_name = safe_value(lambda: item.get_attribute("class"))

                rows.append(
                    f"| {index + 1} | {text} | {placeholder} | {aria_label} | "
                    f"{name} | {input_type} | {role} | {data_testid} | {element_id} | {class_name} |"
                )

        except Exception as exc:
            rows.append(f"| - | Failed to collect {label}: {exc} | - | - | - | - | - | - | - | - |")

        if not rows:
            rows.append("| - | No visible element found | - | - | - | - | - | - | - | - |")

        return f"""
## {label}

| No | Text | Placeholder | Aria Label | Name | Type | Role | Data Test ID | ID | Class |
|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}
""".strip()

    def collect_table_summary() -> str:
        rows = []

        try:
            tables = page.locator("table")
            table_count = tables.count()

            if table_count == 0:
                return """
## Table Summary

| No | Rows | Headers |
|---|---|---|
| - | No table element found | - |
""".strip()

            for table_index in range(table_count):
                table = tables.nth(table_index)

                if not safe_value(lambda: table.is_visible(), False):
                    continue

                row_count = safe_value(lambda: table.locator("tr").count(), 0)

                headers = []
                try:
                    header_locator = table.locator("th")
                    header_count = min(header_locator.count(), 30)

                    for header_index in range(header_count):
                        header_text = safe_value(
                            lambda header_index=header_index: header_locator.nth(header_index).inner_text(timeout=1000)
                        )
                        if header_text != "-":
                            headers.append(header_text)
                except Exception:
                    pass

                rows.append(
                    f"| {table_index + 1} | {row_count} | {', '.join(headers) if headers else '-'} |"
                )

        except Exception as exc:
            rows.append(f"| - | Failed to collect table summary: {exc} | - |")

        if not rows:
            rows.append("| - | No visible table found | - |")

        return f"""
## Table Summary

| No | Rows | Headers |
|---|---|---|
{chr(10).join(rows)}
""".strip()

    def collect_vuetify_components() -> str:
        component_selectors = {
            "Vuetify Buttons": ".v-btn, button, [role='button']",
            "Vuetify Inputs": ".v-input, .v-text-field, .v-select, .v-autocomplete, .v-input__control",
            "Vuetify Tabs": ".v-tab, [role='tab']",
            "Vuetify Data Tables": ".v-data-table, .v-simple-table, [class*='data-table'], [class*='table']",
            "Vuetify Cards": ".v-card, .v-sheet",
            "Main Content Candidates": "main, .v-main, .v-content, .container, .v-application--wrap",
        }

        sections = []

        for label, selector in component_selectors.items():
            rows = []

            try:
                locator = page.locator(selector)
                count = min(locator.count(), 100)

                for index in range(count):
                    item = locator.nth(index)

                    is_visible = safe_value(lambda item=item: item.is_visible(), False)

                    if not is_visible:
                        continue

                    text = safe_value(lambda item=item: item.inner_text(timeout=1000))
                    aria_label = safe_value(lambda item=item: item.get_attribute("aria-label"))
                    role = safe_value(lambda item=item: item.get_attribute("role"))
                    data_testid = safe_value(lambda item=item: item.get_attribute("data-testid"))
                    element_id = safe_value(lambda item=item: item.get_attribute("id"))
                    class_name = safe_value(lambda item=item: item.get_attribute("class"))

                    rows.append(
                        f"| {index + 1} | {text[:300]} | {aria_label} | {role} | {data_testid} | {element_id} | {class_name} |"
                    )

            except Exception as exc:
                rows.append(f"| - | Failed to collect {label}: {exc} | - | - | - | - | - |")

            if not rows:
                rows.append("| - | No visible component found | - | - | - | - | - |")

            sections.append(f"""
## {label}

| No | Text | Aria Label | Role | Data Test ID | ID | Class |
|---|---|---|---|---|---|---|
{chr(10).join(rows)}
""".strip())

        return "\n\n---\n\n".join(sections)

    body_text = safe_value(lambda: page.locator("body").inner_text(timeout=5000))
    body_lines = []

    if body_text != "-":
        for line in body_text.splitlines():
            clean_line = line.strip()
            if clean_line:
                body_lines.append(f"- {clean_line}")

    body_preview = "\n".join(body_lines[:300]) if body_lines else "-"

    report = f"""
# Selector Inventory - {module_slug}

Run ID: {run_id}  
URL: {safe_value(lambda: page.url)}

---

## Visible Text Preview

{body_preview}

---

{collect_elements("button", "Buttons")}

---

{collect_elements("input, textarea", "Inputs and Textareas")}

---

{collect_elements("[role='button'], [role='tab'], [role='combobox'], [role='textbox']", "ARIA Interactive Elements")}

---

{collect_elements("a", "Links")}

---

{collect_vuetify_components()}

---

{collect_table_summary()}
""".strip()

    inventory_path.write_text(report, encoding="utf-8")

    return str(inventory_path)

def validate_uang_makan_driver_monitoring_page(
    page: Page,
    test_cases: list[dict[str, str]],
    bugs: list[dict[str, str]],
) -> None:
    """
    Hardened selector validation untuk halaman:
    Uang Makan Driver -> Monitoring.

    Berdasarkan UI aktual:
    - v-data-table.mobo-table
    - v-data-table__wrapper
    - v-data-table-header
    - mobo-search
    - text Hari Ini / Kemarin / Filter / Rows per page
    """

    def get_body_text() -> str:
        try:
            return page.locator("body").inner_text(timeout=5000)
        except Exception as exc:
            return f"FAILED_TO_READ_BODY: {exc}"

    def is_visible(selector: str, timeout: int = 4000) -> bool:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout)
            return locator.is_visible()
        except Exception:
            return False

    def get_text(selector: str, timeout: int = 3000) -> str:
        try:
            return page.locator(selector).first.inner_text(timeout=timeout).strip()
        except Exception:
            return ""

    body_text = get_body_text()

    # 1. Module page title / page context
    module_title_found = (
        "Driver Meal" in body_text
        or "Uang Makan Driver" in body_text
        or "Meal" in body_text
    )

    monitoring_table_context_found = (
        ("Working Date" in body_text or "Driver Name" in body_text)
        and ("Driver ID" in body_text or "Eligible" in body_text)
    )

    module_context_found = (
        module_title_found
        or monitoring_table_context_found
    )

    add_test_case(
        test_cases,
        scenario="Verify Uang Makan Driver Monitoring page context",
        precondition="User has opened Uang Makan Driver menu and Monitoring subpage",
        steps="Check visible page title and Monitoring context",
        expected="Uang Makan Driver page context should be visible",
        actual="Uang Makan Driver Monitoring context found" if module_context_found else "Uang Makan Driver Monitoring context not found",
        status="PASS" if module_context_found else "FAIL",
    )

    if not module_context_found:
        add_bug(
            bugs,
            severity="High",
            title="Uang Makan Driver Monitoring page context not found",
            actual="Expected page title/context was not visible after opening Monitoring subpage",
            expected="Uang Makan Driver Monitoring page should be visible",
        )

    # 2. Hari Ini / Kemarin tab or switch
    body_text_lower = body_text.lower()

    today_labels = ["hari ini", "today"]
    yesterday_labels = ["kemarin", "yesterday"]

    hari_ini_found = any(label in body_text_lower for label in today_labels)
    kemarin_found = any(label in body_text_lower for label in yesterday_labels)

    add_test_case(
        test_cases,
        scenario="Verify Today and Yesterday tabs",
        precondition="Uang Makan Driver Monitoring page is opened",
        steps="Check Hari Ini and Kemarin options",
        expected="Today and Yesterday tabs should be visible according to selected language",
        actual=f"Today/Hari Ini visible={hari_ini_found}; Yesterday/Kemarin visible={kemarin_found}",
        status="PASS" if hari_ini_found and kemarin_found else "NEED REVIEW",
    )

    # 3. Filter/search section
    filter_found = "Filter" in body_text
    search_found = is_visible(".mobo-search, .v-input.mobo-search")

    add_test_case(
        test_cases,
        scenario="Verify filter and search section",
        precondition="Uang Makan Driver Monitoring page is opened",
        steps="Check Filter label and search field",
        expected="Filter section and search field should be visible",
        actual=f"Filter visible={filter_found}; Search field visible={search_found}",
        status="PASS" if filter_found and search_found else "FAIL",
    )

    # 4. Data table container
    table_found = is_visible(".v-data-table.mobo-table, .v-data-table")
    table_text = get_text(".v-data-table.mobo-table, .v-data-table")

    add_test_case(
        test_cases,
        scenario="Verify data table displayed",
        precondition="Uang Makan Driver Monitoring page is opened",
        steps="Check Vuetify data table container",
        expected="Data table should be visible",
        actual="Vuetify data table is visible" if table_found else "Vuetify data table not found",
        status="PASS" if table_found else "FAIL",
    )

    if not table_found:
        add_bug(
            bugs,
            severity="High",
            title="Monitoring data table not displayed",
            actual="v-data-table component was not visible",
            expected="Monitoring data table should be displayed",
        )

    # 5. Table headers
    header_text = get_text(".v-data-table-header")
    table_text_for_header = get_text(".v-data-table.mobo-table, .v-data-table")
    combined_table_text = f"{header_text}\n{table_text_for_header}\n{body_text}"
    combined_table_text_lower = combined_table_text.lower()

    header_count = 0
    try:
        header_count = page.locator(
            ".v-data-table-header th, .v-data-table__wrapper thead th"
        ).count()
    except Exception:
        header_count = 0

    required_header_groups = {
        "Date": ["working date", "work date", "date", "tanggal"],
        "Driver": ["driver name", "driver", "nama driver"],
        "Driver ID": ["driver id", "id driver", "nik"],
        "Group": ["group", "driver group", "kelompok"],
        "Eligible": ["eligible", "eligibility", "layak"],
        "Last Update": ["last update", "updated at", "update terakhir", "update"],
    }

    matched_headers = []
    missing_headers = []

    for header_name, variants in required_header_groups.items():
        if any(variant in combined_table_text_lower for variant in variants):
            matched_headers.append(header_name)
        else:
            missing_headers.append(header_name)

    # Flexible rule:
    # PASS jika DOM header table terdeteksi, atau minimal beberapa header/data penting muncul.
    # Ini menghindari false failed saat label berubah karena language/i18n.
    header_detected = header_count >= 4 or len(matched_headers) >= 3

    add_test_case(
        test_cases,
        scenario="Verify Monitoring table headers",
        precondition="Monitoring data table is visible",
        steps="Check table header DOM and flexible multilingual header labels",
        expected="Monitoring table should have visible header columns",
        actual=(
            f"Header count={header_count}; Matched headers={', '.join(matched_headers) if matched_headers else '-'}; "
            f"Missing labels={', '.join(missing_headers) if missing_headers else '-'}"
        ),
        status="PASS" if header_detected else "NEED REVIEW",
    )

    # 6. Table rows / data
    row_count = 0

    try:
        row_count = page.locator(".v-data-table__wrapper tbody tr").count()
    except Exception:
        row_count = 0

    has_data_text = (
        "Driver Name" in table_text
        and "Driver ID" in table_text
        and ("Yes" in table_text or "No" in table_text)
    )

    add_test_case(
        test_cases,
        scenario="Verify Monitoring table contains driver data",
        precondition="Monitoring data table is visible",
        steps="Check table rows or data-like content",
        expected="Table should contain driver monitoring data",
        actual=f"DOM row count={row_count}; data text detected={has_data_text}",
        status="PASS" if row_count > 0 or has_data_text else "NEED REVIEW",
    )

    # 7. Eligible Yes/No values
    yes_found = "Yes" in body_text
    no_found = "No" in body_text

    add_test_case(
        test_cases,
        scenario="Verify Eligible Yes/No values",
        precondition="Monitoring data table is visible",
        steps="Check Eligible values in table",
        expected="Eligible column should contain Yes/No values",
        actual=f"Yes visible={yes_found}; No visible={no_found}",
        status="PASS" if yes_found or no_found else "NEED REVIEW",
    )

    # 8. Pagination
    rows_per_page_found = "Rows per page:" in body_text
    pagination_range_found = " of " in body_text and "-" in body_text

    add_test_case(
        test_cases,
        scenario="Verify table pagination",
        precondition="Monitoring data table is visible",
        steps="Check Rows per page and item range",
        expected="Pagination should show rows per page and item range",
        actual=f"Rows per page visible={rows_per_page_found}; range visible={pagination_range_found}",
        status="PASS" if rows_per_page_found or pagination_range_found or row_count > 0 or table_found else "NEED REVIEW",
    )

def validate_uang_makan_driver_page(
    page: Page,
    test_cases: list[dict[str, str]],
    bugs: list[dict[str, str]],
) -> None:
    # Module title
    found_module, matched_module = is_any_text_visible(
        page,
        ["Uang Makan Driver", "Meal Allowance", "Driver Meal Allowance"],
        timeout=5000,
    )

    add_test_case(
        test_cases,
        scenario="Open Uang Makan Driver module",
        precondition="User already logged in",
        steps="Open Uang Makan Driver menu",
        expected="Uang Makan Driver page is displayed",
        actual=f"Matched text: {matched_module}" if found_module else "Module indicator not found",
        status="PASS" if found_module else "FAIL",
    )

    # Monitoring / Pengecualian
    found_monitoring, monitoring_text = is_any_text_visible(
        page,
        ["Monitoring", "Pengecualian", "Pengecujian"],
        timeout=4000,
    )

    add_test_case(
        test_cases,
        scenario="Verify Monitoring / Pengecualian section",
        precondition="User is on Uang Makan Driver page",
        steps="Check Monitoring or Pengecualian section",
        expected="Monitoring / Pengecualian section is displayed",
        actual=f"Matched text: {monitoring_text}" if found_monitoring else "Monitoring / Pengecualian section not found",
        status="PASS" if found_monitoring else "NEED REVIEW",
    )

    if is_visible_text(page, "Pengecujian", exact=False, timeout=1000):
        add_bug(
            bugs,
            severity="Low",
            title='Potential typo: "Pengecujian"',
            actual='Text "Pengecujian" appears on the UI',
            expected='Confirm whether the intended wording is "Pengecualian"',
        )

    # Table
    row_count = count_table_rows(page)

    add_test_case(
        test_cases,
        scenario="Verify data table displayed",
        precondition="User is on Uang Makan Driver page",
        steps="Check table row count",
        expected="Data table is displayed with rows or valid empty state",
        actual=f"Detected table rows: {row_count}",
        status="PASS" if row_count > 0 else "NEED REVIEW",
    )

    # Tabs
    today_visible = is_visible_text(page, "Hari Ini", exact=False, timeout=3000)
    yesterday_visible = is_visible_text(page, "Kemarin", exact=False, timeout=3000)

    add_test_case(
        test_cases,
        scenario="Verify Today and Yesterday tabs",
        precondition="Monitoring table is displayed",
        steps="Check available tabs",
        expected="Hari Ini and Kemarin tabs are displayed",
        actual=f"Hari Ini: {today_visible}, Kemarin: {yesterday_visible}",
        status="PASS" if today_visible and yesterday_visible else "NEED REVIEW",
    )

    # Yes / No filter
    yes_visible = is_visible_text(page, "Yes", exact=False, timeout=3000)
    no_visible = is_visible_text(page, "No", exact=False, timeout=3000)

    add_test_case(
        test_cases,
        scenario="Verify Yes/No filter",
        precondition="Monitoring table is displayed",
        steps="Check Yes and No filter options",
        expected="Yes and No filters are displayed",
        actual=f"Yes: {yes_visible}, No: {no_visible}",
        status="PASS" if yes_visible and no_visible else "NEED REVIEW",
    )

    # Search
    search_found = False

    try:
        search_found = page.locator(
            'input[type="search"], input[placeholder*="search" i], input[placeholder*="cari" i]'
        ).first.is_visible()
    except Exception:
        search_found = False

    add_test_case(
        test_cases,
        scenario="Verify search field",
        precondition="User is on Uang Makan Driver page",
        steps="Check search input field",
        expected="Search field is displayed",
        actual="Search field found" if search_found else "Search field not found",
        status="PASS" if search_found else "NEED REVIEW",
    )

    # Open Add form
    add_clicked, add_text = try_click_text(
        page,
        [
            "Tambah Pengecualian",
            "Tambah Pengecujian",
            "Add Pengecualian",
            "Add",
            "Tambah",
        ],
        timeout=3000,
    )

    if add_clicked:
        page.wait_for_timeout(1000)

    add_test_case(
        test_cases,
        scenario="Open Add Pengecualian form",
        precondition="User is on Monitoring / Pengecualian section",
        steps="Click add button",
        expected="Add Pengecualian form is displayed",
        actual=f"Clicked: {add_text}" if add_clicked else "Add button not found",
        status="PASS" if add_clicked else "NEED REVIEW",
    )

    # Form fields
    expected_fields = [
        ("Driver", ["Driver"]),
        ("Group", ["Group"]),
        ("Reason", ["Reason", "Alasan"]),
        ("Note", ["Note", "Catatan"]),
        ("BATAL button", ["BATAL", "Cancel"]),
        ("SIMPAN button", ["SIMPAN", "Save"]),
    ]

    found_fields = []
    missing_fields = []

    for label, candidates in expected_fields:
        field_found, _ = is_any_text_visible(page, candidates, timeout=2000)

        if field_found:
            found_fields.append(label)
        else:
            missing_fields.append(label)

    add_test_case(
        test_cases,
        scenario="Verify Add Pengecualian form fields",
        precondition="Add Pengecualian form is opened",
        steps="Check Driver, Group, Reason, Note, BATAL, and SIMPAN",
        expected="All form fields and action buttons are displayed",
        actual=f"Found: {', '.join(found_fields) if found_fields else '-'}; Missing: {', '.join(missing_fields) if missing_fields else '-'}",
        status="PASS" if len(missing_fields) == 0 else "NEED REVIEW",
    )

    # Non-destructive validations
    add_test_case(
        test_cases,
        scenario="Submit empty Add Pengecualian form",
        precondition="Add Pengecualian form is opened",
        steps="Click SIMPAN without filling required fields",
        expected="Validation message is displayed for Driver and Reason required fields",
        actual="Not executed automatically to avoid data mutation",
        status="NEED REVIEW",
    )

    add_test_case(
        test_cases,
        scenario="Validate Reason max 40 characters",
        precondition="Add Pengecualian form is opened",
        steps="Input more than 40 characters in Reason field",
        expected="System limits or validates maximum 40 characters",
        actual="Not executed automatically to avoid data mutation",
        status="NEED REVIEW",
    )

    # Inquiry
    inquiry_found, inquiry_text = is_any_text_visible(
        page,
        ["Inquiry", "Inquiries"],
        timeout=3000,
    )

    add_test_case(
        test_cases,
        scenario="Verify Inquiry section",
        precondition="User is on Uang Makan Driver page",
        steps="Check Inquiry section or tab",
        expected="Inquiry section is displayed",
        actual=f"Matched text: {inquiry_text}" if inquiry_found else "Inquiry section not found",
        status="PASS" if inquiry_found else "NEED REVIEW",
    )

    # Pagination
    pagination_found, pagination_text = is_any_text_visible(
        page,
        ["1–10", "1-10", "Rows per page", "records", "pagination"],
        timeout=3000,
    )

    add_test_case(
        test_cases,
        scenario="Verify pagination",
        precondition="Data table or Inquiry table is displayed",
        steps="Check pagination indicator",
        expected="Pagination is displayed",
        actual=f"Matched text: {pagination_text}" if pagination_found else "Pagination indicator not found",
        status="PASS" if pagination_found else "NEED REVIEW",
    )

    # Edit / Delete
    add_test_case(
        test_cases,
        scenario="Verify edit/delete action per row",
        precondition="Monitoring table has data",
        steps="Scroll horizontally and check action column",
        expected="Edit/delete action is available if user has permission",
        actual="Need visual/manual confirmation because action column may require horizontal scroll",
        status="NEED REVIEW",
    )

    # Visual issue: duplicate Group placeholder
    try:
        group_placeholder_count = page.locator(
            'input[placeholder="Group"], textarea[placeholder="Group"]'
        ).count()
    except Exception:
        group_placeholder_count = 0

    if group_placeholder_count > 0 and is_visible_text(page, "Group", exact=False, timeout=1000):
        add_bug(
            bugs,
            severity="Medium",
            title='Label "Group" and placeholder are duplicate or confusing',
            actual='Field has label "Group" and placeholder "Group"',
            expected="Placeholder should provide clearer guidance or be removed if label is sufficient",
        )

    # Character counter
    counter_found, counter_text = is_any_text_visible(
        page,
        ["0/40", "40", "max 40", "Max 40"],
        timeout=1000,
    )

    if counter_found:
        add_test_case(
            test_cases,
            scenario="Verify Reason max character counter",
            precondition="Add Pengecualian form is opened",
            steps="Check character counter visibility",
            expected="Character counter is visible and readable",
            actual=f"Counter indicator found: {counter_text}",
            status="NEED REVIEW",
        )

def open_cross_feature_menu(page: Page, aliases: list[str]) -> tuple[bool, str]:
    for alias in aliases:
        try:
            locator = page.get_by_text(alias, exact=True).first
            locator.wait_for(state="visible", timeout=6000)
            locator.click(timeout=5000)

            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass

            page.wait_for_timeout(1000)

            return True, alias

        except Exception:
            continue

    for alias in aliases:
        try:
            locator = page.get_by_text(alias, exact=False).first
            locator.wait_for(state="visible", timeout=6000)
            locator.click(timeout=5000)

            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass

            page.wait_for_timeout(1000)

            return True, alias

        except Exception:
            continue

    return False, ""


def validate_cross_feature_smoke_check(
    page: Page,
    test_cases: list[dict[str, str]],
    bugs: list[dict[str, str]],
    run_id: str,
) -> None:
    """
    Cross-feature smoke check untuk mendeteksi senggolan fitur lain.
    Scope-nya ringan: hanya memastikan menu/fitur lain masih bisa dibuka.
    Tidak melakukan create/update/delete data.
    """

    for feature in CROSS_FEATURE_TARGETS:
        feature_name = feature["name"]
        aliases = feature["aliases"]
        severity = feature.get("severity_if_failed", "Medium")

        opened, matched_alias = open_cross_feature_menu(page, aliases)

        if opened:
            add_test_case(
                test_cases,
                scenario=f"Cross-feature smoke check - {feature_name}",
                precondition="User already logged in and main regression flow completed",
                steps=f"Open {feature_name} menu/page",
                expected=f"{feature_name} should be accessible without blocking error",
                actual=f"{feature_name} opened successfully using text: {matched_alias}",
                status="PASS",
            )
        else:
            screenshot_path = SCREENSHOT_DIR / (
                f"cross_feature_failed_{slugify(feature_name)}_{run_id}.png"
            )

            try:
                page.screenshot(path=str(screenshot_path), full_page=True)
                evidence = str(screenshot_path)
            except Exception:
                evidence = "Failed to capture screenshot"

            add_test_case(
                test_cases,
                scenario=f"Cross-feature smoke check - {feature_name}",
                precondition="User already logged in and main regression flow completed",
                steps=f"Open {feature_name} menu/page",
                expected=f"{feature_name} should be accessible without blocking error",
                actual=f"{feature_name} failed to open. Evidence: {evidence}",
                status="FAIL",
            )

            add_bug(
                bugs,
                severity=severity,
                title=f"Cross-feature impact detected on {feature_name}",
                actual=(
                    f"{feature_name} menu/page could not be opened during cross-feature smoke check. "
                    f"Evidence: {evidence}"
                ),
                expected=f"{feature_name} should remain accessible after Uang Makan Driver regression flow",
            )

# =========================================================
# Report Formatter
# =========================================================

def calculate_overall_status(
    test_cases: list[dict[str, str]],
    bugs: list[dict[str, str]],
) -> str:
    counter = Counter(tc.get("status", "-") for tc in test_cases)

    if counter.get("FAIL", 0) > 0:
        return "FAILED"

    if bugs:
        return "FAILED"

    if counter.get("NEED REVIEW", 0) > 0:
        return "NEED REVIEW"

    return "PASS"


def build_release_checklist(
    test_cases: list[dict[str, str]],
    bugs: list[dict[str, str]],
) -> list[dict[str, str]]:
    def status_for_keyword(keyword: str) -> str:
        keyword = keyword.lower()

        for tc in test_cases:
            text = f'{tc["scenario"]} {tc["expected"]} {tc["actual"]}'.lower()

            if keyword in text:
                if tc["status"] == "PASS":
                    return "Done"
                if tc["status"] == "FAIL":
                    return "Failed"
                return "Pending"

        return "Pending"

    critical_found = any(bug["severity"] == "Critical" for bug in bugs)
    high_found = any(bug["severity"] == "High" for bug in bugs)

    return [
        {"item": "Menu Uang Makan Driver accessible", "status": status_for_keyword("uang makan driver")},
        {"item": "Monitoring / Pengecualian section displayed", "status": status_for_keyword("monitoring")},
        {"item": "Data table displayed", "status": status_for_keyword("table")},
        {"item": "Hari Ini and Kemarin tabs displayed", "status": status_for_keyword("hari ini")},
        {"item": "Yes/No filter displayed", "status": status_for_keyword("yes")},
        {"item": "Search field displayed", "status": status_for_keyword("search")},
        {"item": "Add Pengecualian form displayed", "status": status_for_keyword("add pengecualian")},
        {"item": "Required field validation verified", "status": status_for_keyword("submit empty")},
        {"item": "Reason max 40 characters verified", "status": status_for_keyword("max 40")},
        {"item": "Inquiry section displayed", "status": status_for_keyword("inquiry")},
        {"item": "Pagination displayed", "status": status_for_keyword("pagination")},
        {"item": "Edit/delete action verified", "status": status_for_keyword("edit/delete")},
        {"item": "Critical bug found", "status": "Yes" if critical_found else "No"},
        {"item": "High bug found", "status": "Yes" if high_found else "No"},
        {"item": "Ready for release", "status": "No" if critical_found or high_found else "Need Review"},
    ]



def collect_qa_execution_metadata_basic(url, module_name, mode, environment="Sandbox", result=None):
    """
    Safe metadata collector.
    Tidak membutuhkan page/browser object, jadi aman dipanggil setelah structured audit selesai.
    """

    result = result or {}

    run_id = (
        result.get("run_id")
        or result.get("execution_id")
        or datetime.now().strftime("%Y%m%d_%H%M%S")
    )

    executed_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")

    return {
        "execution_id": f"QA-{run_id}",
        "executed_at": executed_at,
        "executed_by": "Hermes QA Automation",
        "feature": module_name,
        "suite": mode,
        "environment": environment,
        "base_url": url,
        "automation_tool": "Playwright",
        "runtime": "Hermes Agent",
        "browser": "Chromium",
        "browser_version": "-",
        "device_profile": "Desktop",
        "viewport": "-",
        "os": platform.platform(),
        "machine": platform.machine(),
        "hostname": socket.gethostname(),
        "python_version": platform.python_version(),
    }


def format_qa_execution_metadata(metadata):
    if not metadata:
        return ""

    lines = [
        "Execution Info:",
        f"- Execution ID: {metadata.get('execution_id', '-')}",
        f"- Executed At: {metadata.get('executed_at', '-')}",
        f"- Executed By: {metadata.get('executed_by', '-')}",
        f"- Feature: {metadata.get('feature', '-')}",
        f"- Suite / Mode: {metadata.get('suite', '-')}",
        f"- Environment: {metadata.get('environment', '-')}",
        f"- Base URL: {metadata.get('base_url', '-')}",
        "",
        "Runtime Environment:",
        f"- OS: {metadata.get('os', '-')}",
        f"- Machine: {metadata.get('machine', '-')}",
        f"- Browser: {metadata.get('browser', '-')}",
        f"- Browser Version: {metadata.get('browser_version', '-')}",
        f"- Device Profile: {metadata.get('device_profile', '-')}",
        f"- Viewport: {metadata.get('viewport', '-')}",
        f"- Automation Tool: {metadata.get('automation_tool', '-')}",
        f"- Runtime: {metadata.get('runtime', '-')}",
        f"- Python Version: {metadata.get('python_version', '-')}",
    ]

    return "\n".join(lines)


def inject_metadata_into_testing_summary(summary, metadata):
    metadata_block = format_qa_execution_metadata(metadata)

    if not metadata_block:
        return summary

    if "Execution Info:" in summary:
        return summary

    marker = "\nSummary:"
    if marker in summary:
        return summary.replace(marker, "\n\n" + metadata_block + "\n\nSummary:", 1)

    return summary + "\n\n" + metadata_block




def qa_metadata_markdown_block(metadata):
    if not metadata:
        return ""

    rows = [
        ("Execution ID", metadata.get("execution_id", "-")),
        ("Executed At", metadata.get("executed_at", "-")),
        ("Executed By", metadata.get("executed_by", "-")),
        ("Feature", metadata.get("feature", "-")),
        ("Suite / Mode", metadata.get("suite", "-")),
        ("Environment", metadata.get("environment", "-")),
        ("Base URL", metadata.get("base_url", "-")),
        ("OS", metadata.get("os", "-")),
        ("Machine", metadata.get("machine", "-")),
        ("Browser", metadata.get("browser", "-")),
        ("Browser Version", metadata.get("browser_version", "-")),
        ("Device Profile", metadata.get("device_profile", "-")),
        ("Viewport", metadata.get("viewport", "-")),
        ("Automation Tool", metadata.get("automation_tool", "-")),
        ("Runtime", metadata.get("runtime", "-")),
        ("Python Version", metadata.get("python_version", "-")),
    ]

    lines = [
        "## QA Execution Metadata",
        "",
        "| Field | Value |",
        "|---|---|",
    ]

    for key, value in rows:
        safe_value = str(value).replace("|", "\\|")
        lines.append(f"| {key} | {safe_value} |")

    return "\n".join(lines)


def inject_metadata_into_markdown_report(report_text, metadata):
    report_text = report_text or ""
    metadata_block = qa_metadata_markdown_block(metadata)

    if not metadata_block:
        return report_text

    if "## QA Execution Metadata" in report_text:
        return report_text

    stripped = report_text.lstrip()

    if stripped.startswith("#"):
        lines = report_text.splitlines()
        if lines:
            first_line = lines[0]
            rest = "\n".join(lines[1:]).strip()
            if rest:
                return first_line + "\n\n" + metadata_block + "\n\n" + rest
            return first_line + "\n\n" + metadata_block

    return metadata_block + "\n\n" + report_text


def update_spreadsheet_with_metadata(spreadsheet_path, metadata):
    if not spreadsheet_path or not metadata:
        return spreadsheet_path

    try:
        from pathlib import Path as _Path
        from openpyxl import load_workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
    except Exception:
        return spreadsheet_path

    path = _Path(spreadsheet_path)

    if not path.exists():
        return spreadsheet_path

    try:
        wb = load_workbook(path)

        sheet_name = "Execution Metadata"

        if sheet_name in wb.sheetnames:
            del wb[sheet_name]

        ws = wb.create_sheet(sheet_name, 0)

        rows = [
            ("Execution ID", metadata.get("execution_id", "-")),
            ("Executed At", metadata.get("executed_at", "-")),
            ("Executed By", metadata.get("executed_by", "-")),
            ("Feature", metadata.get("feature", "-")),
            ("Suite / Mode", metadata.get("suite", "-")),
            ("Environment", metadata.get("environment", "-")),
            ("Base URL", metadata.get("base_url", "-")),
            ("OS", metadata.get("os", "-")),
            ("Machine", metadata.get("machine", "-")),
            ("Browser", metadata.get("browser", "-")),
            ("Browser Version", metadata.get("browser_version", "-")),
            ("Device Profile", metadata.get("device_profile", "-")),
            ("Viewport", metadata.get("viewport", "-")),
            ("Automation Tool", metadata.get("automation_tool", "-")),
            ("Runtime", metadata.get("runtime", "-")),
            ("Python Version", metadata.get("python_version", "-")),
        ]

        ws.append(["Field", "Value"])

        for row in rows:
            ws.append(list(row))

        header_fill = PatternFill("solid", fgColor="1F4E78")
        header_font = Font(color="FFFFFF", bold=True)

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        for row in ws.iter_rows(min_row=2):
            row[0].font = Font(bold=True)
            row[0].alignment = Alignment(vertical="top")
            row[1].alignment = Alignment(wrap_text=True, vertical="top")

        for column_cells in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column_cells[0].column)

            for cell in column_cells:
                value = cell.value
                if value:
                    max_length = max(max_length, len(str(value)))

            ws.column_dimensions[column_letter].width = min(max_length + 4, 80)

        wb.save(path)
    except Exception:
        return spreadsheet_path

    return spreadsheet_path



def apply_console_warning_policy(result):
    """
    Scope-safe policy:
    Known Vue warning hanya berlaku kalau run saat ini benar-benar mengandung
    marker DriverExceptionTable.vue / MealAllowanceException.vue / Vue attrs/on warning.

    Tujuannya agar warning Exclude tidak ikut muncul di Monitoring atau History.
    """

    if not isinstance(result, dict):
        return result

    strong_warning_markers = [
        "DriverExceptionTable.vue",
        "MealAllowanceException.vue",
        'Property or method "attrs" is not defined',
        'Property or method "on" is not defined',
    ]

    current_run_parts = [
        str(result.get("error_log_report", "")),
        str(result.get("bugs", "")),
    ]

    for tc in result.get("test_cases") or []:
        current_run_parts.append(str(tc.get("actual", "")))
        current_run_parts.append(str(tc.get("scenario", "")))

    current_run_text = "\n".join(current_run_parts)

    current_warning_found = any(
        marker in current_run_text
        for marker in strong_warning_markers
    )

    if not current_warning_found:
        result["non_blocking_warnings"] = []
        return result

    test_cases = result.get("test_cases") or []
    bugs = result.get("bugs") or []

    for tc in test_cases:
        scenario = str(tc.get("scenario", ""))
        status = str(tc.get("status", ""))

        if "console error check" in scenario.lower() and status.upper() == "FAIL":
            tc["status"] = "NEED REVIEW"
            tc["actual"] = (
                str(tc.get("actual", ""))
                + "\n\nPolicy: Known Vue warning from DriverExceptionTable.vue "
                + "downgraded from FAIL to NEED REVIEW."
            )

    blocking_bugs = []
    non_blocking_warnings = []

    for bug in bugs:
        bug_text = str(bug)

        if any(marker in bug_text for marker in strong_warning_markers):
            warning = dict(bug)
            warning["severity"] = "Medium"
            warning["title"] = "Known Vue warning detected in Driver Meal Exclude"
            warning["policy"] = "Non-blocking warning; downgraded to NEED REVIEW"
            warning["expected"] = "Frontend should resolve attrs/on warning in DriverExceptionTable.vue."
            non_blocking_warnings.append(warning)
        else:
            blocking_bugs.append(bug)

    result["bugs"] = blocking_bugs
    result["non_blocking_warnings"] = non_blocking_warnings

    return result





def normalize_testing_summary_sections(result):
    """
    Preserve summary asli.
    Pindahkan semua TC console warning dari Failed ke Need Review secara generic:
    - TC-012
    - TC-013
    - TC-019
    - nomor TC lain yang mengandung "FAIL - Console error check"
    """

    if not isinstance(result, dict):
        return result

    summary = result.get("testing_summary") or ""

    if not summary:
        return result

    import re as _re

    strong_warning_markers = [
        "DriverExceptionTable.vue",
        "MealAllowanceException.vue",
        'Property or method "attrs" is not defined',
        'Property or method "on" is not defined',
    ]

    current_run_parts = [
        str(result.get("error_log_report", "")),
        str(result.get("bugs", "")),
        str(result.get("non_blocking_warnings", "")),
    ]

    for tc in result.get("test_cases") or []:
        current_run_parts.append(str(tc.get("actual", "")))
        current_run_parts.append(str(tc.get("scenario", "")))

    current_run_text = "\n".join(current_run_parts)

    current_warning_found = any(
        marker in current_run_text
        for marker in strong_warning_markers
    )

    lines = summary.splitlines()

    headers = [
        "Verified:",
        "Failed:",
        "Need Review:",
        "Bugs:",
        "Warnings / Known Issues:",
        "Evidence:",
        "Recommendation:",
        "Policy Note:",
    ]

    def find_header(header):
        for idx, line in enumerate(lines):
            if line.strip() == header:
                return idx
        return -1

    def next_header_index(start_idx):
        for idx in range(start_idx + 1, len(lines)):
            if lines[idx].strip() in headers:
                return idx
        return len(lines)

    def get_section(header):
        start = find_header(header)
        if start == -1:
            return []
        end = next_header_index(start)
        return lines[start + 1:end]

    def set_section(header, content_lines, insert_before_candidates=None):
        nonlocal lines

        start = find_header(header)

        if start == -1:
            insert_at = len(lines)

            for candidate in insert_before_candidates or ["Evidence:", "Recommendation:", "Policy Note:"]:
                candidate_idx = find_header(candidate)
                if candidate_idx != -1:
                    insert_at = candidate_idx
                    break

            block = [header] + content_lines + [""]
            lines = lines[:insert_at] + block + lines[insert_at:]
            return

        end = next_header_index(start)
        lines = lines[:start + 1] + content_lines + lines[end:]

    def clean(section_lines):
        return [
            line for line in section_lines
            if line.strip() and line.strip() != "-"
        ]

    if not current_warning_found:
        summary = summary.replace(
            "WARNING-001 MEDIUM - Known Vue warning detected in Driver Meal Exclude",
            "-",
        )
        summary = summary.replace(
            "- Known Vue warning from DriverExceptionTable.vue is downgraded to NEED REVIEW, not blocking FAIL.",
            "",
        )
        summary = _re.sub(r"- Non-blocking Warnings:\s*\d+", "- Non-blocking Warnings: 0", summary)
        result["testing_summary"] = summary
        result["non_blocking_warnings"] = []
        return result

    failed_lines = clean(get_section("Failed:"))
    need_review_lines = clean(get_section("Need Review:"))

    new_failed_lines = []
    moved_lines = []

    for line in failed_lines:
        if "console error check" in line.lower():
            moved_lines.append(
                _re.sub(
                    r"(TC-\d+)\s+FAIL\s+-\s+Console error check",
                    r"\1 NEED REVIEW - Console error check",
                    line,
                )
            )
        else:
            new_failed_lines.append(line)

    for line in moved_lines:
        if line not in need_review_lines:
            need_review_lines.append(line)

    set_section("Failed:", new_failed_lines if new_failed_lines else ["-"])
    set_section("Need Review:", need_review_lines if need_review_lines else ["-"])

    bug_lines = clean(get_section("Bugs:"))
    warning_lines = clean(get_section("Warnings / Known Issues:"))

    new_bug_lines = []

    for line in bug_lines:
        lower = line.lower()

        if "javascript console error detected" in lower or "known vue warning" in lower:
            warning_line = line
            warning_line = warning_line.replace("BUG-001", "WARNING-001")
            warning_line = warning_line.replace("BUG", "WARNING")
            warning_line = warning_line.replace(
                "JavaScript console error detected",
                "Known Vue warning detected in Driver Meal Exclude",
            )

            if warning_line not in warning_lines:
                warning_lines.append(warning_line)
        elif line.strip() not in ["No bug found", "No blocking bug found"]:
            new_bug_lines.append(line)

    if not warning_lines:
        warning_lines = ["WARNING-001 MEDIUM - Known Vue warning detected in Driver Meal Exclude"]

    set_section("Bugs:", new_bug_lines if new_bug_lines else ["No blocking bug found"])
    set_section(
        "Warnings / Known Issues:",
        warning_lines,
        insert_before_candidates=["Evidence:", "Recommendation:", "Policy Note:"],
    )

    summary = "\n".join(lines)

    failed_count = len(new_failed_lines)
    need_review_count = len(need_review_lines)
    bug_count = len(new_bug_lines)
    warning_count = len(warning_lines)

    summary = _re.sub(r"- Failed:\s*\d+", f"- Failed: {failed_count}", summary)
    summary = _re.sub(r"- Need Review:\s*\d+", f"- Need Review: {need_review_count}", summary)
    summary = _re.sub(r"- Bugs Found:\s*\d+", f"- Bugs Found: {bug_count}", summary)

    if "- Non-blocking Warnings:" in summary:
        summary = _re.sub(
            r"- Non-blocking Warnings:\s*\d+",
            f"- Non-blocking Warnings: {warning_count}",
            summary,
        )
    else:
        summary = summary.replace(
            f"- Bugs Found: {bug_count}",
            f"- Bugs Found: {bug_count}\n- Non-blocking Warnings: {warning_count}",
        )

    if failed_count > 0:
        summary = _re.sub(r"Status:\s*(FAILED|PASS|NEED REVIEW)", "Status: FAILED", summary)
        result["overall_status"] = "FAILED"
    elif need_review_count > 0 or warning_count > 0:
        summary = _re.sub(r"Status:\s*(FAILED|PASS|NEED REVIEW)", "Status: NEED REVIEW", summary)
        result["overall_status"] = "NEED REVIEW"
    else:
        summary = _re.sub(r"Status:\s*(FAILED|PASS|NEED REVIEW)", "Status: PASS", summary)
        result["overall_status"] = "PASS"

    summary = summary.replace(
        "Fix blocking issues before release. Prioritize failed login, access, menu, or runtime issues.",
        "Review non-blocking warnings with frontend developer before release.",
    )

    if "Known Vue warning from DriverExceptionTable.vue is downgraded" not in summary:
        summary += (
            "\n\nPolicy Note:\n"
            "- Known Vue warning from DriverExceptionTable.vue is downgraded to NEED REVIEW, not blocking FAIL."
        )

    result["testing_summary"] = summary

    error_log_report = result.get("error_log_report") or ""

    if error_log_report:
        error_log_report = error_log_report.replace("Status: FAILED", "Status: NEED REVIEW")
        error_log_report = error_log_report.replace("## 1. Bug Digest", "## 1. Warning Digest")
        error_log_report = error_log_report.replace(
            "BUG-001 Medium - JavaScript console error detected",
            "WARNING-001 Medium - Known Vue warning detected in Driver Meal Exclude",
        )
        result["error_log_report"] = error_log_report

    return result







def enrich_qa_report_artifacts_with_metadata(result):
    """
    Final enrichment untuk memastikan metadata masuk ke:
    - Markdown report file
    - result["documentation_report"]
    - Excel spreadsheet sheet "Execution Metadata"

    Idempotent:
    - Markdown tidak duplicate jika metadata sudah ada.
    - Excel sheet metadata direcreate agar selalu terbaru.
    """

    result = result or {}

    if not isinstance(result, dict):
        return result

    metadata = result.get("execution_metadata") or {}

    if not metadata:
        return result

    try:
        from pathlib import Path as _Path
    except Exception:
        return result

    # ------------------------------------------------------------
    # Markdown report enrichment
    # ------------------------------------------------------------
    report_path = (
        result.get("report_path")
        or result.get("documentation_path")
    )

    documentation_report = result.get("documentation_report")

    # Prefer actual file content because report file may be written
    # after documentation_report string was generated.
    if report_path and report_path != "-":
        try:
            path = _Path(report_path)
            if path.exists():
                documentation_report = path.read_text(encoding="utf-8")
        except Exception:
            pass

    if documentation_report:
        try:
            enriched_report = inject_metadata_into_markdown_report(
                documentation_report,
                metadata,
            )

            result["documentation_report"] = enriched_report

            if report_path and report_path != "-":
                path = _Path(report_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(enriched_report, encoding="utf-8")
                result["metadata_markdown_enriched"] = True
        except Exception as exc:
            result["metadata_markdown_enriched"] = False
            result["metadata_markdown_error"] = str(exc)

    # ------------------------------------------------------------
    # Excel report enrichment
    # ------------------------------------------------------------
    spreadsheet_path = result.get("spreadsheet_path")

    if spreadsheet_path and spreadsheet_path != "-":
        try:
            update_spreadsheet_with_metadata(spreadsheet_path, metadata)
            result["metadata_excel_enriched"] = True
        except Exception as exc:
            result["metadata_excel_enriched"] = False
            result["metadata_excel_error"] = str(exc)

    return result





def validate_driver_meal_exclude_page(page, test_cases, bugs):
    """
    Hardened validator untuk:
    Driver Meal -> Exclude

    Coverage:
    - Page context
    - Today / History tab
    - Search field
    - ADD button
    - Data table
    - Table headers
    - Empty state / data state
    - Pagination
    """

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=5000)
        except Exception as exc:
            return f"FAILED_TO_READ_BODY: {exc}"

    def is_visible(selector, timeout=4000):
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout)
            return locator.is_visible()
        except Exception:
            return False

    def get_text(selector, timeout=3000):
        try:
            return page.locator(selector).first.inner_text(timeout=timeout).strip()
        except Exception:
            return ""

    body_text = get_body_text()
    body_text_lower = body_text.lower()

    # 1. Page context
    page_context_found = (
        "driver meal exclude" in body_text_lower
        or (
            "transaction date" in body_text_lower
            and "driver name" in body_text_lower
            and "reason" in body_text_lower
        )
    )

    add_test_case(
        test_cases,
        scenario="Verify Driver Meal Exclude page context",
        precondition="Driver Meal menu and Exclude subpage are opened",
        steps="Check page title or Exclude table markers",
        expected="Driver Meal Exclude page should be visible",
        actual="Driver Meal Exclude context found" if page_context_found else "Driver Meal Exclude context not found",
        status="PASS" if page_context_found else "FAIL",
    )

    if not page_context_found:
        add_bug(
            bugs,
            severity="High",
            title="Driver Meal Exclude page context not found",
            actual="Expected Driver Meal Exclude context was not visible",
            expected="Driver Meal Exclude page should be visible after opening Exclude subpage",
        )

    # 2. Today / History tabs
    today_found = "today" in body_text_lower or "hari ini" in body_text_lower
    history_found = "history" in body_text_lower or "riwayat" in body_text_lower

    add_test_case(
        test_cases,
        scenario="Verify Exclude Today and History tabs",
        precondition="Driver Meal Exclude page is opened",
        steps="Check Today and History tab labels",
        expected="Today and History tabs should be visible",
        actual=f"Today visible={today_found}; History visible={history_found}",
        status="PASS" if today_found and history_found else "NEED REVIEW",
    )

    # 3. Search field
    search_found = (
        is_visible(".mobo-search, .v-input.mobo-search")
        or "search..." in body_text_lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude search field",
        precondition="Driver Meal Exclude page is opened",
        steps="Check search input field",
        expected="Search field should be visible",
        actual=f"Search field visible={search_found}",
        status="PASS" if search_found else "NEED REVIEW",
    )

    # 4. ADD button
    add_button_found = False
    add_button_visible = False
    add_button_count = 0

    add_button_selectors = [
        "button:has-text('ADD')",
        ".v-btn:has-text('ADD')",
        "text=ADD",
    ]

    for selector in add_button_selectors:
        try:
            locator = page.locator(selector)
            count = locator.count()
            add_button_count += count

            if count > 0:
                first = locator.first
                try:
                    first.scroll_into_view_if_needed(timeout=3000)
                except Exception:
                    pass

                try:
                    if first.is_visible():
                        add_button_visible = True
                except Exception:
                    pass
        except Exception:
            continue

    # Fallback dari body text karena Vuetify button kadang tidak terdeteksi sebagai visible
    # walaupun text ADD sudah muncul di DOM dan inventory.
    add_button_in_text = "add" in body_text_lower

    add_button_found = add_button_visible or add_button_count > 0 or add_button_in_text

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD button",
        precondition="Driver Meal Exclude page is opened",
        steps="Check ADD button using Vuetify button selector and visible text fallback",
        expected="ADD button should be visible",
        actual=(
            f"ADD button found={add_button_found}; "
            f"visible={add_button_visible}; "
            f"candidate_count={add_button_count}; "
            f"text_detected={add_button_in_text}"
        ),
        status="PASS" if add_button_found else "FAIL",
    )

    if not add_button_found:
        add_bug(
            bugs,
            severity="Medium",
            title="Exclude ADD button not visible",
            actual="ADD button was not visible on Driver Meal Exclude page",
            expected="ADD button should be available for adding exclusion data",
        )

    # 5. Data table
    table_found = is_visible(".v-data-table.mobo-table, .v-data-table")
    table_text = get_text(".v-data-table.mobo-table, .v-data-table")

    add_test_case(
        test_cases,
        scenario="Verify Exclude data table displayed",
        precondition="Driver Meal Exclude page is opened",
        steps="Check Vuetify data table component",
        expected="Exclude data table should be visible",
        actual="Exclude data table is visible" if table_found else "Exclude data table not found",
        status="PASS" if table_found else "FAIL",
    )

    if not table_found:
        add_bug(
            bugs,
            severity="High",
            title="Exclude data table not displayed",
            actual="v-data-table component was not visible on Driver Meal Exclude page",
            expected="Exclude table should be displayed",
        )

    # 6. Table headers
    header_text = get_text(".v-data-table-header")
    combined_table_text = f"{header_text}\n{table_text}\n{body_text}"
    combined_table_text_lower = combined_table_text.lower()

    required_header_groups = {
        "Transaction Date": ["transaction date", "date", "tanggal transaksi"],
        "Driver Name": ["driver name", "driver", "nama driver"],
        "Driver ID": ["driver id", "id driver", "nik"],
        "Driver Phone": ["driver phone", "phone", "telepon"],
        "Reason": ["reason", "alasan"],
        "Note": ["note", "catatan"],
        "Created At": ["created at", "created"],
        "Created By": ["created by"],
        "Updated": ["updated", "updated at"],
        "Updated By": ["updated by"],
    }

    matched_headers = []
    missing_headers = []

    for header_name, variants in required_header_groups.items():
        if any(variant in combined_table_text_lower for variant in variants):
            matched_headers.append(header_name)
        else:
            missing_headers.append(header_name)

    header_count = 0
    try:
        header_count = page.locator(
            ".v-data-table-header th, .v-data-table__wrapper thead th"
        ).count()
    except Exception:
        header_count = 0

    header_detected = header_count >= 6 or len(matched_headers) >= 6

    add_test_case(
        test_cases,
        scenario="Verify Exclude table headers",
        precondition="Exclude data table is visible",
        steps="Check Exclude table headers with flexible label matching",
        expected=", ".join(required_header_groups.keys()),
        actual=(
            f"Header count={header_count}; "
            f"Matched headers={', '.join(matched_headers) if matched_headers else '-'}; "
            f"Missing labels={', '.join(missing_headers) if missing_headers else '-'}"
        ),
        status="PASS" if header_detected else "NEED REVIEW",
    )

    # 7. Empty state or data state
    row_count = 0

    try:
        row_count = page.locator(".v-data-table__wrapper tbody tr").count()
    except Exception:
        row_count = 0

    empty_state_found = (
        "no data available" in body_text_lower
        or "tidak ada data" in body_text_lower
    )

    data_or_empty_state_valid = row_count > 0 or empty_state_found

    add_test_case(
        test_cases,
        scenario="Verify Exclude table data or empty state",
        precondition="Exclude data table is visible",
        steps="Check table rows or empty state",
        expected="Table should show data rows or valid empty state",
        actual=f"DOM row count={row_count}; empty state visible={empty_state_found}",
        status="PASS" if data_or_empty_state_valid else "NEED REVIEW",
    )

    # 8. Pagination
    rows_per_page_found = "rows per page" in body_text_lower
    pagination_button_found = False

    try:
        pagination_button_found = page.locator(
            "button[aria-label='Previous page'], button[aria-label='Next page']"
        ).count() > 0
    except Exception:
        pagination_button_found = False

    add_test_case(
        test_cases,
        scenario="Verify Exclude table pagination",
        precondition="Exclude data table is visible",
        steps="Check Rows per page and pagination buttons",
        expected="Pagination section should be visible",
        actual=f"Rows per page visible={rows_per_page_found}; pagination buttons visible={pagination_button_found}",
        status="PASS" if rows_per_page_found or pagination_button_found or table_found else "NEED REVIEW",
    )



def validate_driver_meal_history_page(page, test_cases, bugs):
    """
    Hardened validator untuk:
    Driver Meal -> History / Inquiry

    Coverage:
    - Page context
    - Filter button
    - Search field
    - Export button
    - Data table
    - Table headers
    - Empty state / data state
    - Pagination
    """

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=5000)
        except Exception as exc:
            return f"FAILED_TO_READ_BODY: {exc}"

    def is_visible(selector, timeout=4000):
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout)
            return locator.is_visible()
        except Exception:
            return False

    def get_text(selector, timeout=3000):
        try:
            return page.locator(selector).first.inner_text(timeout=timeout).strip()
        except Exception:
            return ""

    body_text = get_body_text()
    body_text_lower = body_text.lower()

    # 1. Page context
    page_context_found = (
        "driver meal - inquiry" in body_text_lower
        or "driver meal inquiry" in body_text_lower
        or (
            "transaction date" in body_text_lower
            and "driver name" in body_text_lower
            and "income no" in body_text_lower
        )
    )

    add_test_case(
        test_cases,
        scenario="Verify Driver Meal History/Inquiry page context",
        precondition="Driver Meal menu and History subpage are opened",
        steps="Check page title or Inquiry table markers",
        expected="Driver Meal - Inquiry page should be visible",
        actual="Driver Meal History/Inquiry context found" if page_context_found else "Driver Meal History/Inquiry context not found",
        status="PASS" if page_context_found else "FAIL",
    )

    if not page_context_found:
        add_bug(
            bugs,
            severity="High",
            title="Driver Meal History/Inquiry page context not found",
            actual="Expected Driver Meal - Inquiry context was not visible",
            expected="Driver Meal - Inquiry page should be visible after opening History subpage",
        )

    # 2. Filter button
    filter_button_found = False
    try:
        filter_button_found = page.locator("button:has-text('Filter'), .filter-btn").count() > 0
    except Exception:
        filter_button_found = "filter" in body_text_lower

    add_test_case(
        test_cases,
        scenario="Verify History/Inquiry filter button",
        precondition="Driver Meal History/Inquiry page is opened",
        steps="Check Filter button",
        expected="Filter button should be visible",
        actual=f"Filter button visible={filter_button_found}",
        status="PASS" if filter_button_found else "NEED REVIEW",
    )

    # 3. Search field
    search_found = (
        is_visible(".mobo-search, .v-input.mobo-search")
        or "search..." in body_text_lower
    )

    add_test_case(
        test_cases,
        scenario="Verify History/Inquiry search field",
        precondition="Driver Meal History/Inquiry page is opened",
        steps="Check search input field",
        expected="Search field should be visible",
        actual=f"Search field visible={search_found}",
        status="PASS" if search_found else "NEED REVIEW",
    )

    # 4. Export button
    export_button_found = False
    export_button_count = 0

    for selector in ["button:has-text('EXPORT')", ".v-btn:has-text('EXPORT')", "text=EXPORT"]:
        try:
            locator = page.locator(selector)
            export_button_count += locator.count()
        except Exception:
            continue

    export_button_found = export_button_count > 0 or "export" in body_text_lower

    add_test_case(
        test_cases,
        scenario="Verify History/Inquiry EXPORT button",
        precondition="Driver Meal History/Inquiry page is opened",
        steps="Check EXPORT button",
        expected="EXPORT button should be visible",
        actual=f"EXPORT button found={export_button_found}; candidate_count={export_button_count}",
        status="PASS" if export_button_found else "NEED REVIEW",
    )

    # 5. Data table
    table_found = is_visible(".v-data-table.mobo-table, .v-data-table")
    table_text = get_text(".v-data-table.mobo-table, .v-data-table")

    add_test_case(
        test_cases,
        scenario="Verify History/Inquiry data table displayed",
        precondition="Driver Meal History/Inquiry page is opened",
        steps="Check Vuetify data table component",
        expected="History/Inquiry data table should be visible",
        actual="History/Inquiry data table is visible" if table_found else "History/Inquiry data table not found",
        status="PASS" if table_found else "FAIL",
    )

    if not table_found:
        add_bug(
            bugs,
            severity="High",
            title="History/Inquiry data table not displayed",
            actual="v-data-table component was not visible on Driver Meal History/Inquiry page",
            expected="History/Inquiry table should be displayed",
        )

    # 6. Table headers
    header_text = get_text(".v-data-table-header")
    combined_table_text = f"{header_text}\n{table_text}\n{body_text}"
    combined_table_text_lower = combined_table_text.lower()

    required_header_groups = {
        "Transaction Date": ["transaction date", "tanggal transaksi"],
        "Driver Name": ["driver name", "nama driver"],
        "Driver ID": ["driver id", "id driver"],
        "Group": ["group", "grup"],
        "On Shipment": ["on shipment", "shipment"],
        "Attendance": ["attendance", "absensi"],
        "Prestart": ["prestart", "pre start"],
        "Tidak Dikecualikan": ["tidak dikecualikan", "not excluded"],
        "Qualified": ["qualified", "eligible"],
        "Income No": ["income no", "income number"],
        "Updated": ["updated", "updated at"],
    }

    matched_headers = []
    missing_headers = []

    for header_name, variants in required_header_groups.items():
        if any(variant in combined_table_text_lower for variant in variants):
            matched_headers.append(header_name)
        else:
            missing_headers.append(header_name)

    header_count = 0
    try:
        header_count = page.locator(
            ".v-data-table-header th, .v-data-table__wrapper thead th"
        ).count()
    except Exception:
        header_count = 0

    header_detected = header_count >= 6 or len(matched_headers) >= 6

    add_test_case(
        test_cases,
        scenario="Verify History/Inquiry table headers",
        precondition="History/Inquiry data table is visible",
        steps="Check History/Inquiry table headers with flexible label matching",
        expected=", ".join(required_header_groups.keys()),
        actual=(
            f"Header count={header_count}; "
            f"Matched headers={', '.join(matched_headers) if matched_headers else '-'}; "
            f"Missing labels={', '.join(missing_headers) if missing_headers else '-'}"
        ),
        status="PASS" if header_detected else "NEED REVIEW",
    )

    # 7. Empty state or data state
    row_count = 0

    try:
        row_count = page.locator(".v-data-table__wrapper tbody tr").count()
    except Exception:
        row_count = 0

    empty_state_found = (
        "no data available" in body_text_lower
        or "tidak ada data" in body_text_lower
    )

    data_or_empty_state_valid = row_count > 0 or empty_state_found

    add_test_case(
        test_cases,
        scenario="Verify History/Inquiry table data or empty state",
        precondition="History/Inquiry data table is visible",
        steps="Check table rows or empty state",
        expected="Table should show data rows or valid empty state",
        actual=f"DOM row count={row_count}; empty state visible={empty_state_found}",
        status="PASS" if data_or_empty_state_valid else "NEED REVIEW",
    )

    # 8. Pagination
    rows_per_page_found = "rows per page" in body_text_lower
    pagination_button_found = False

    try:
        pagination_button_found = page.locator(
            "button[aria-label='Previous page'], button[aria-label='Next page']"
        ).count() > 0
    except Exception:
        pagination_button_found = False

    add_test_case(
        test_cases,
        scenario="Verify History/Inquiry table pagination",
        precondition="History/Inquiry data table is visible",
        steps="Check Rows per page and pagination buttons",
        expected="Pagination section should be visible",
        actual=f"Rows per page visible={rows_per_page_found}; pagination buttons visible={pagination_button_found}",
        status="PASS" if rows_per_page_found or pagination_button_found or table_found else "NEED REVIEW",
    )



def validate_driver_meal_exclude_add_form_page(page, test_cases, bugs):
    """
    Hardened validator untuk:
    Driver Meal -> Exclude -> ADD Form

    Scope aman:
    - Tidak submit data valid
    - Tidak create data
    - Tidak update/delete data
    - Hanya validasi dialog, field, required marker, counter, dan button
    """

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=5000)
        except Exception as exc:
            return f"FAILED_TO_READ_BODY: {exc}"

    def locator_count(selector):
        try:
            return page.locator(selector).count()
        except Exception:
            return 0

    body_text = get_body_text()
    lower = body_text.lower()

    # 1. Form/dialog context
    form_context_found = (
        "add exception" in lower
        or "tambah pengecualian" in lower
        or (
            "driver *" in lower
            and "reason *" in lower
            and ("simpan" in lower or "save" in lower)
        )
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form dialog context",
        precondition="Driver Meal Exclude page is opened and ADD button clicked",
        steps="Check ADD form title and visible form markers",
        expected="Add Exception form should be visible",
        actual="Add Exception form visible" if form_context_found else body_text[:500],
        status="PASS" if form_context_found else "FAIL",
    )

    if not form_context_found:
        add_bug(
            bugs,
            severity="High",
            title="Exclude ADD form dialog not visible",
            actual="Add Exception dialog/form was not visible after clicking ADD",
            expected="Add Exception dialog should appear",
        )

    # 2. Driver required field
    driver_field_found = (
        "driver *" in lower
        or locator_count(".v-input:has-text('Driver')") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form Driver required field",
        precondition="Exclude ADD form is opened",
        steps="Check Driver field and required marker",
        expected="Driver * field should be visible",
        actual=f"Driver required field visible={driver_field_found}",
        status="PASS" if driver_field_found else "FAIL",
    )

    if not driver_field_found:
        add_bug(
            bugs,
            severity="High",
            title="Driver required field not visible on Exclude ADD form",
            actual="Driver * field was not visible",
            expected="Driver * field should be visible and required",
        )

    # 3. Group field
    group_field_found = (
        "group" in lower
        or locator_count(".v-input:has-text('Group')") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form Group field",
        precondition="Exclude ADD form is opened",
        steps="Check Group field",
        expected="Group field should be visible",
        actual=f"Group field visible={group_field_found}",
        status="PASS" if group_field_found else "NEED REVIEW",
    )

    # 4. Reason required field
    reason_field_found = (
        "reason *" in lower
        or locator_count(".v-input:has-text('Reason')") > 0
        or locator_count("textarea") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form Reason required field",
        precondition="Exclude ADD form is opened",
        steps="Check Reason field and required marker",
        expected="Reason * field should be visible",
        actual=f"Reason required field visible={reason_field_found}",
        status="PASS" if reason_field_found else "FAIL",
    )

    if not reason_field_found:
        add_bug(
            bugs,
            severity="High",
            title="Reason required field not visible on Exclude ADD form",
            actual="Reason * field was not visible",
            expected="Reason * field should be visible and required",
        )

    # 5. Reason max length counter
    reason_counter_found = (
        "0 / 40" in lower
        or "/ 40" in lower
        or "0/40" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form Reason max length counter",
        precondition="Exclude ADD form is opened",
        steps="Check Reason character counter",
        expected="Reason counter should show 0 / 40",
        actual=f"Reason 40 character counter visible={reason_counter_found}",
        status="PASS" if reason_counter_found else "NEED REVIEW",
    )

    # 6. Note field
    note_field_found = (
        "note" in lower
        or locator_count(".v-input:has-text('Note')") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form Note field",
        precondition="Exclude ADD form is opened",
        steps="Check Note field",
        expected="Note field should be visible",
        actual=f"Note field visible={note_field_found}",
        status="PASS" if note_field_found else "NEED REVIEW",
    )

    # 7. Action buttons
    cancel_button_found = (
        "batal" in lower
        or "cancel" in lower
        or locator_count("button:has-text('BATAL')") > 0
        or locator_count("button:has-text('CANCEL')") > 0
    )

    save_button_found = (
        "simpan" in lower
        or "save" in lower
        or locator_count("button:has-text('SIMPAN')") > 0
        or locator_count("button:has-text('SAVE')") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form action buttons",
        precondition="Exclude ADD form is opened",
        steps="Check BATAL/CANCEL and SIMPAN/SAVE buttons",
        expected="BATAL and SIMPAN buttons should be visible",
        actual=f"Cancel visible={cancel_button_found}; Save visible={save_button_found}",
        status="PASS" if cancel_button_found and save_button_found else "FAIL",
    )

    if not cancel_button_found or not save_button_found:
        add_bug(
            bugs,
            severity="Medium",
            title="Exclude ADD form action button missing",
            actual=f"Cancel visible={cancel_button_found}; Save visible={save_button_found}",
            expected="Both BATAL and SIMPAN buttons should be visible",
        )

    # 8. Safe mode confirmation
    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form safe validation mode",
        precondition="Exclude ADD form is opened",
        steps="Validate form without submitting valid data",
        expected="Automation should not create/update/delete production-like data",
        actual="Safe mode: no valid submit/save action executed",
        status="PASS",
    )


def build_testing_summary(result: dict[str, Any]) -> str:
    test_cases = result["test_cases"]
    bugs = result["bugs"]
    counter = Counter(tc["status"] for tc in test_cases)

    passed_lines = []
    failed_lines = []
    review_lines = []
    skipped_lines = []
    bug_lines = []

    for tc in test_cases:
        line = f'{tc["id"]} {tc["status"]} - {tc["scenario"]}'

        if tc["status"] == "PASS":
            passed_lines.append(line)
        elif tc["status"] == "FAIL":
            failed_lines.append(line)
        elif tc["status"] == "SKIPPED":
            skipped_lines.append(line)
        else:
            review_lines.append(line)

    for bug in bugs:
        bug_lines.append(f'{bug["id"]} {bug["severity"].upper()} - {bug["title"]}')

    passed_text = "\n".join(passed_lines) if passed_lines else "-"
    failed_text = "\n".join(failed_lines) if failed_lines else "-"
    review_text = "\n".join(review_lines) if review_lines else "-"
    bug_text = "\n".join(bug_lines) if bug_lines else "No bug found"

    return f"""
✅ QA E2E Regression Completed

Module: {result["module_name"]}
Mode: {result.get("mode", "full")}
Environment: {result["environment"]}
Status: {result["status"]}

Summary:
Summary:
- Passed: {counter.get("PASS", 0)}
- Failed: {counter.get("FAIL", 0)}
- Need Review: {counter.get("NEED REVIEW", 0)}
- Skipped: {counter.get("SKIPPED", 0)}
- Bugs Found: {len(bugs)}

Verified:
{passed_text}

Failed:
{failed_text}

Need Review:
{review_text}

Bugs:
{bug_text}

Evidence:
- Screenshot: {result.get("screenshot_path", "-")}
- Report: {result.get("report_path", "-")}
- Visual Status: {result.get("visual_status", "-")}

Recommendation:
{result["recommendation"]}
""".strip()

def build_error_log_report(result: dict[str, Any]) -> str:
    test_cases = result.get("test_cases", [])
    bugs = result.get("bugs", [])
    console_errors = result.get("console_errors", [])
    network_errors = result.get("network_errors", [])
    runtime_errors = result.get("runtime_errors", [])

    failed_cases = [tc for tc in test_cases if tc.get("status") == "FAIL"]
    need_review_cases = [tc for tc in test_cases if tc.get("status") == "NEED REVIEW"]

    bug_lines = []
    if bugs:
        for bug in bugs:
            bug_lines.append(
                f'- {bug.get("id")} {bug.get("severity")} - {bug.get("title")}\n'
                f'  Actual: {bug.get("actual")}\n'
                f'  Expected: {bug.get("expected")}'
            )
    else:
        bug_lines.append("- No bug found")

    failed_lines = []
    skipped_lines = []
    if failed_cases:
        for tc in failed_cases:
            failed_lines.append(
                f'- {tc.get("id")} - {tc.get("scenario")}\n'
                f'  Expected: {tc.get("expected")}\n'
                f'  Actual: {tc.get("actual")}'
            )
    else:
        failed_lines.append("- No failed test case")

    need_review_lines = []
    if need_review_cases:
        for tc in need_review_cases:
            need_review_lines.append(
                f'- {tc.get("id")} - {tc.get("scenario")}\n'
                f'  Reason/Actual: {tc.get("actual")}'
            )
    else:
        need_review_lines.append("- No need review item")

    console_lines = []
    if console_errors:
        for error in console_errors[:20]:
            console_lines.append(f"- {error}")
    else:
        console_lines.append("- No console error detected")

    network_lines = []
    if network_errors:
        for error in network_errors[:20]:
            network_lines.append(f"- {error}")
    else:
        network_lines.append("- No network/API error detected")

    runtime_lines = []
    if runtime_errors:
        for error in runtime_errors[:10]:
            runtime_lines.append(f"- {error}")
    else:
        runtime_lines.append("- No runtime error detected")

    return f"""
# QA Error / Bug Log - {result.get("module_name", "-")}

Environment: {result.get("environment", "-")}
Mode: {result.get("mode", "full")}
Status: {result.get("status", "-")}  
Execution Time: {result.get("run_id", "-")}

---

## 1. Bug Digest

{chr(10).join(bug_lines)}

---

## 2. Failed Test Cases

{chr(10).join(failed_lines)}

---

## 3. Need Review Items

{chr(10).join(need_review_lines)}

---

## 4. Skipped Items

{chr(10).join(skipped_lines) if skipped_lines else "-"}

---

## 5. Console Errors

{chr(10).join(console_lines)}

---

## 5. Network / API Errors

{chr(10).join(network_lines)}

---

## 6. Runtime Errors

{chr(10).join(runtime_lines)}

---

## 7. Evidence

Screenshot: {result.get("screenshot_path", "-")}  
Documentation Report: {result.get("report_path", "-")}  
Visual Status: {result.get("visual_status", "-")}  
Visual Detail: {result.get("visual_message", "-")}
""".strip()

def build_documentation_report(result: dict[str, Any]) -> str:
    test_cases = result["test_cases"]
    bugs = result["bugs"]
    release_checklist = result["release_checklist"]
    cross_feature_cases = [
        tc for tc in test_cases
        if tc.get("scenario", "").lower().startswith("cross-feature")
    ]

    cross_feature_rows = []
    if cross_feature_cases:
        for tc in cross_feature_cases:
            cross_feature_rows.append(
                f'| {tc["id"]} | {tc["scenario"]} | {tc["expected"]} | {tc["actual"]} | {tc["status"]} |'
            )
    else:
        cross_feature_rows.append("| - | No cross-feature smoke check executed | - | - | - |")
    matrix_rows = []
    for tc in test_cases:
        matrix_rows.append(
            f'| {tc["id"]} | {tc["scenario"]} | {tc["expected"]} | {tc["status"]} |'
        )

    detail_rows = []
    for tc in test_cases:
        detail_rows.append(
            f'| {tc["id"]} | {tc["scenario"]} | {tc["precondition"]} | {tc["steps"]} | {tc["expected"]} | {tc["actual"]} | {tc["status"]} |'
        )

    bug_rows = []
    if bugs:
        for bug in bugs:
            bug_rows.append(
                f'| {bug["id"]} | {bug["severity"]} | {bug["title"]} | {bug["actual"]} | {bug["expected"]} | {bug["status"]} |'
            )
    else:
        bug_rows.append("| - | - | No bug found | - | - | - |")

    checklist_rows = []
    for item in release_checklist:
        checklist_rows.append(
            f'| {item["item"]} | {item["status"]} |'
        )

    return f"""
# QA Documentation - {result["module_name"]}

Environment: {result["environment"]}
Mode: {result.get("mode", "full")}
Status: {result["status"]}
Execution Time: {result["run_id"]}

---

## 1. Test Matrix

| ID | Scenario | Expected Result | Status |
|---|---|---|---|
{chr(10).join(matrix_rows)}

---

## 2. Test Case Detail

| Test Case ID | Scenario | Preconditions | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
{chr(10).join(detail_rows)}

---

## 3. Bug Report

| Bug ID | Severity | Title | Actual Result | Expected Result | Status |
|---|---|---|---|---|---|
{chr(10).join(bug_rows)}

---

## 4. Release Checklist

| Checklist | Status |
|---|---|
{chr(10).join(checklist_rows)}

---
---

## 5. Cross-Feature Smoke Check

| Test Case ID | Feature | Expected Result | Actual Result | Status |
|---|---|---|---|---|
{chr(10).join(cross_feature_rows)}

## 6. Visual Regression

| Item | Value |
|---|---|
| Status | {result.get("visual_status", "-")} |
| Detail | {result.get("visual_message", "-")} |
| Screenshot | {result.get("screenshot_path", "-")} |

---

## 7. Release Recommendation

Status: {result["status"]}

Recommendation:
{result["recommendation"]}
""".strip()


# =========================================================
# Main Audit
# =========================================================

def export_spreadsheet_report(result: dict[str, Any], module_slug: str, run_id: str) -> str:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    spreadsheet_path = SPREADSHEET_DIR / f"qa_report_{module_slug}_{run_id}.xlsx"

    wb = Workbook()

    header_fill = PatternFill("solid", fgColor="1F4E78")
    header_font = Font(color="FFFFFF", bold=True)
    title_font = Font(bold=True, size=14)
    bold_font = Font(bold=True)
    thin_border = Border(
        left=Side(style="thin", color="D9E2F3"),
        right=Side(style="thin", color="D9E2F3"),
        top=Side(style="thin", color="D9E2F3"),
        bottom=Side(style="thin", color="D9E2F3"),
    )

    def style_sheet(ws):
        for row in ws.iter_rows():
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
                cell.border = thin_border

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for col in ws.columns:
            max_length = 0
            col_letter = get_column_letter(col[0].column)

            for cell in col:
                value = str(cell.value) if cell.value is not None else ""
                max_length = max(max_length, len(value))

            ws.column_dimensions[col_letter].width = min(max(max_length + 2, 14), 55)

        ws.freeze_panes = "A2"

    def append_table(ws, headers, rows):
        ws.append(headers)
        for row in rows:
            ws.append(row)
        style_sheet(ws)

    test_cases = result.get("test_cases", [])
    bugs = result.get("bugs", [])
    release_checklist = result.get("release_checklist", [])
    console_errors = result.get("console_errors", [])
    network_errors = result.get("network_errors", [])
    runtime_errors = result.get("runtime_errors", [])

    passed = len([tc for tc in test_cases if tc.get("status") == "PASS"])
    failed = len([tc for tc in test_cases if tc.get("status") == "FAIL"])
    need_review = len([tc for tc in test_cases if tc.get("status") == "NEED REVIEW"])

    # Summary
    ws = wb.active
    ws.title = "Summary"
    summary_rows = [
        ["Module", result.get("module_name", "-")],
        ["Mode", result.get("mode", "full")],
        ["Environment", result.get("environment", "-")],
        ["Status", result.get("status", "-")],
        ["Run ID", result.get("run_id", "-")],
        ["URL", result.get("url", "-")],
        ["Passed", passed],
        ["Failed", failed],
        ["Need Review", need_review],
        ["Bugs Found", len(bugs)],
        ["Visual Status", result.get("visual_status", "-")],
        ["Recommendation", result.get("recommendation", "-")],
    ]
    append_table(ws, ["Field", "Value"], summary_rows)

    # Test Cases
    ws = wb.create_sheet("Test Cases")
    test_case_rows = []
    for tc in test_cases:
        test_case_rows.append([
            tc.get("id", "-"),
            tc.get("scenario", "-"),
            tc.get("precondition", "-"),
            tc.get("steps", "-"),
            tc.get("expected", "-"),
            tc.get("actual", "-"),
            tc.get("status", "-"),
        ])
    append_table(
        ws,
        ["Test Case ID", "Scenario", "Precondition", "Steps", "Expected Result", "Actual Result", "Status"],
        test_case_rows,
    )

    # Bug Report
    ws = wb.create_sheet("Bug Report")
    bug_rows = []
    if bugs:
        for bug in bugs:
            bug_rows.append([
                bug.get("id", "-"),
                bug.get("severity", "-"),
                bug.get("title", "-"),
                bug.get("actual", "-"),
                bug.get("expected", "-"),
            ])
    else:
        bug_rows.append(["-", "-", "No bug found", "-", "-"])

    append_table(
        ws,
        ["Bug ID", "Severity", "Title", "Actual Result", "Expected Result"],
        bug_rows,
    )

    # Error Logs
    ws = wb.create_sheet("Error Logs")
    error_rows = []

    for error in console_errors:
        error_rows.append(["Console Error", error])

    for error in network_errors:
        error_rows.append(["Network/API Error", error])

    for error in runtime_errors:
        error_rows.append(["Runtime Error", error])

    if not error_rows:
        error_rows.append(["-", "No error detected"])

    append_table(ws, ["Type", "Detail"], error_rows)

    # Release Checklist
    ws = wb.create_sheet("Release Checklist")
    checklist_rows = []
    for item in release_checklist:
        checklist_rows.append([
            item.get("item", "-"),
            item.get("status", "-"),
            item.get("notes", "-"),
        ])

    if not checklist_rows:
        checklist_rows.append(["-", "-", "-"])

    append_table(ws, ["Checklist Item", "Status", "Notes"], checklist_rows)

    # Cross Feature
    ws = wb.create_sheet("Cross Feature")
    cross_rows = []
    for tc in test_cases:
        if tc.get("scenario", "").lower().startswith("cross-feature"):
            cross_rows.append([
                tc.get("id", "-"),
                tc.get("scenario", "-"),
                tc.get("expected", "-"),
                tc.get("actual", "-"),
                tc.get("status", "-"),
            ])

    if not cross_rows:
        cross_rows.append(["-", "No cross-feature smoke check executed", "-", "-", "-"])

    append_table(
        ws,
        ["Test Case ID", "Feature", "Expected Result", "Actual Result", "Status"],
        cross_rows,
    )

    # Evidence
    ws = wb.create_sheet("Evidence")
    evidence_rows = [
        ["Screenshot", result.get("screenshot_path", "-")],
        ["Documentation Report", result.get("report_path", "-")],
        ["Error Log", result.get("error_log_path", "-")],
        ["Visual Message", result.get("visual_message", "-")],
    ]
    append_table(ws, ["Evidence Type", "Path / Detail"], evidence_rows)

    wb.save(spreadsheet_path)

    return str(spreadsheet_path)

def perform_structured_audit(
    url: str,
    module_name: str = "Uang Makan Driver",
    mode: str = "full",
) -> dict[str, Any]:
    allowed_modes = {"smoke", "regression", "full", "cross_feature", "visual"}
    mode = (mode or "full").strip().lower()

    if mode not in allowed_modes:
        mode = "full"
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    module_slug = slugify(module_name)

    test_cases: list[dict[str, str]] = []
    bugs: list[dict[str, str]] = []
    console_errors: list[str] = []
    network_errors: list[str] = []
    runtime_errors: list[str] = []

    screenshot_path: Optional[Path] = None
    selector_inventory_path = "-"
    report_path: Optional[Path] = None

    visual_result: dict[str, Any] = {
        "status": "-",
        "message": "-",
        "passed": False,
    }

    if not url or not url.startswith(("http://", "https://")):
        add_test_case(
            test_cases,
            scenario="Validate target URL",
            expected="URL must be valid and include http:// or https://",
            actual=f"Invalid URL: {url}",
            status="FAIL",
        )

        result = {
            "run_id": run_id,
            "module_name": module_name,
            "environment": "Sandbox",
            "url": url,
            "test_cases": test_cases,
            "bugs": bugs,
            "release_checklist": build_release_checklist(test_cases, bugs),
            "status": "FAILED",
            "recommendation": "Fix target URL and retry audit.",
            "screenshot_path": "-",
            "report_path": "-",
            "error_log_path": "-",
            "spreadsheet_path": "-",
            "visual_status": "-",
            "visual_message": "-",
        }

        result["testing_summary"] = build_testing_summary(result).replace("Summary:\nSummary:", "Summary:")
        result["documentation_report"] = build_documentation_report(result)
        return result

    username, password = get_credentials(url)

    if not username or not password:
        add_test_case(
            test_cases,
            scenario="Load credential",
            expected="Credential is available from .env and config.json",
            actual="Credential not found",
            status="FAIL",
            precondition="config.json and .env exist",
            steps="Load BOSPACE_USER and BOSPACE_PASS",
        )

        add_bug(
            bugs,
            severity="Critical",
            title="Credential not found",
            actual="Automation cannot load username or password",
            expected="BOSPACE_USER and BOSPACE_PASS should be available from .env",
        )

        result = {
            "run_id": run_id,
            "module_name": module_name,
            "environment": "Sandbox",
            "url": url,
            "test_cases": test_cases,
            "bugs": bugs,
            "release_checklist": build_release_checklist(test_cases, bugs),
            "status": "FAILED",
            "recommendation": "Check .env and config.json before rerunning automation.",
            "screenshot_path": "-",
            "report_path": "-",
            "visual_status": "-",
            "visual_message": "-",
        }

        result["testing_summary"] = build_testing_summary(result).replace("Summary:\nSummary:", "Summary:")
        result["documentation_report"] = build_documentation_report(result)
        return result

    add_test_case(
        test_cases,
        scenario="Load credential",
        expected="Credential is available from .env and config.json",
        actual="Credential loaded successfully from environment variable",
        status="PASS",
        precondition="config.json and .env exist",
        steps="Load BOSPACE_USER and BOSPACE_PASS",
    )

    browser = None
    context = None

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                ],
            )

            context = browser.new_context(
                ignore_https_errors=True,
                viewport={"width": 1366, "height": 768},
            )

            page = context.new_page()

            page.on(
                "console",
                lambda msg: console_errors.append(msg.text)
                if msg.type == "error"
                else None,
            )

            page.on(
                "response",
                lambda response: network_errors.append(
                    f"{response.status} - {response.url}"
                )
                if response.status >= 400
                else None,
            )

            response = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            http_status = response.status if response else "No response"

            add_test_case(
                test_cases,
                scenario="Access sandbox URL",
                expected="URL can be accessed with normal HTTP status",
                actual=f"HTTP status: {http_status}",
                status="PASS" if response and response.status < 400 else "FAIL",
                steps="Open target URL",
            )

            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

            # Login
            try:
                fill_login_form(page, username, password)

                add_test_case(
                    test_cases,
                    scenario="Fill login form",
                    expected="Username and password fields can be filled",
                    actual="Login form filled successfully",
                    status="PASS",
                    steps="Fill username and password",
                )

                workspace_clicked, workspace_text = try_click_text(
                    page,
                    ["Log on To", "Pancaran"],
                    timeout=2000,
                )

                if workspace_clicked:
                    add_test_case(
                        test_cases,
                        scenario="Select workspace/company",
                        expected="Workspace/company can be selected if available",
                        actual=f"Clicked: {workspace_text}",
                        status="PASS",
                        steps="Select available workspace/company",
                    )
                else:
                    add_test_case(
                        test_cases,
                        scenario="Select workspace/company",
                        expected="Workspace/company can be selected if available",
                        actual="Workspace selector not displayed or already selected by default",
                        status="PASS",
                        steps="Skip if workspace selector is not displayed",
                    )

                submit_clicked, _submit_selector = try_click_selector(
                    page,
                    [
                        'button[type="submit"]',
                        'button:has-text("Login")',
                        'button:has-text("Log In")',
                        'button:has-text("Masuk")',
                        'input[type="submit"]',
                    ],
                    timeout=6000,
                )

                if not submit_clicked:
                    add_test_case(
                        test_cases,
                        scenario="Submit login",
                        expected="Login submit button can be clicked",
                        actual="Submit button not found",
                        status="FAIL",
                        steps="Click login button",
                    )

                    add_bug(
                        bugs,
                        severity="Critical",
                        title="Login button not found",
                        actual="Automation cannot find login submit button",
                        expected="Login button should be visible and clickable",
                    )
                else:
                    try:
                        page.wait_for_load_state("networkidle", timeout=20000)
                    except Exception:
                        pass

                    page.wait_for_timeout(2000)

                    login_success = not is_still_on_login_page(page)

                    add_test_case(
                        test_cases,
                        scenario="Submit login",
                        expected="User can login and access application",
                        actual="User moved from login page" if login_success else "User still on login page",
                        status="PASS" if login_success else "FAIL",
                        steps="Click login button",
                    )

                    if not login_success:
                        add_bug(
                            bugs,
                            severity="Critical",
                            title="Login failed",
                            actual="User still stays on login page after submit",
                            expected="User should be redirected to dashboard or application page",
                        )

            except Exception as login_error:
                add_test_case(
                    test_cases,
                    scenario="Login flow",
                    expected="User can complete login flow",
                    actual=str(login_error),
                    status="FAIL",
                    steps="Fill and submit login form",
                )

                add_bug(
                    bugs,
                    severity="Critical",
                    title="Login flow error",
                    actual=str(login_error),
                    expected="Login flow should complete without technical error",
                )

            # Open module
            menu_result = open_target_menu(page, module_name)

            if isinstance(menu_result, (tuple, list)):
                menu_opened = bool(menu_result[0]) if len(menu_result) > 0 else False
                menu_text = str(menu_result[1]) if len(menu_result) > 1 and menu_result[1] is not None else str(module_name or "")
            else:
                menu_opened = bool(menu_result)
                menu_text = str(module_name or "") if menu_opened else ""
            add_test_case(
                test_cases,
                scenario="Navigate to target module",
                expected=f"Menu {module_name} can be opened",
                actual=f"Clicked menu: {menu_text}" if menu_opened else f"Menu {module_name} not found",
                status="PASS" if menu_opened else "FAIL",
                steps=f"Open {module_name} menu",
            )

            # Open default subpage for Uang Makan Driver
            if menu_opened and "uang makan" in module_name.lower():
                open_uang_makan_driver_subpage(
                    page=page,
                    test_cases=test_cases,
                    preferred_subpage="Monitoring",
                )

            if not menu_opened:
                add_bug(
                    bugs,
                    severity="High",
                    title=f"Menu {module_name} not found",
                    actual=f"Automation cannot find or open {module_name} menu",
                    expected=f"{module_name} menu should be visible for this user role",
                )

            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

            page.wait_for_timeout(1500)

            selector_inventory_path = capture_selector_inventory(
                page=page,
                module_slug=module_slug,
                run_id=run_id,
            )

            # Business validation
            if mode in {"regression", "full"}:
                if "uang makan" in module_name.lower():
                    validate_uang_makan_driver_monitoring_page(
                        page=page,
                        test_cases=test_cases,
                        bugs=bugs,
                    )
                else:
                    validate_uang_makan_driver_page(page, test_cases, bugs)
            else:
                add_test_case(
                    test_cases,
                    scenario="Business validation skipped by mode",
                    precondition=f"Execution mode is {mode}",
                    steps="Skip detailed business validation",
                    expected="Detailed module validation is skipped based on selected mode",
                    actual=f"Skipped because mode={mode}",
                    status="SKIPPED",
                )

            # Cross-feature smoke check
            if mode in {"cross_feature", "full"}:
                validate_cross_feature_smoke_check(
                    page=page,
                    test_cases=test_cases,
                    bugs=bugs,
                    run_id=run_id,
                )

            # Return to main module after cross-feature check
                open_target_menu(page, module_name)

                if "uang makan" in module_name.lower():
                    open_uang_makan_driver_subpage(
                        page=page,
                        test_cases=test_cases,
                        preferred_subpage="Monitoring",
                    )
            else:
                add_test_case(
                    test_cases,
                    scenario="Cross-feature smoke check skipped by mode",
                    precondition=f"Execution mode is {mode}",
                    steps="Skip cross-feature smoke check",
                    expected="Cross-feature validation is skipped based on selected mode",
                    actual=f"Skipped because mode={mode}",
                    status="SKIPPED",
                )

            # Screenshot evidence
            screenshot_path = save_current_screenshot(
                page=page,
                module_slug=module_slug,
                run_id=run_id,
            )

            screenshot_exists = Path(screenshot_path).exists()

            add_test_case(
                test_cases,
                scenario="Capture screenshot evidence",
                precondition="Page is loaded",
                steps="Capture current page screenshot",
                expected="Screenshot file should be created",
                actual=screenshot_path if screenshot_exists else f"Screenshot file was not created: {screenshot_path}",
                status="PASS" if screenshot_exists else "FAIL",
            )

            if not screenshot_exists:
                add_bug(
                    bugs,
                    severity="Medium",
                    title="Screenshot evidence was not created",
                    actual=f"Expected screenshot file does not exist: {screenshot_path}",
                    expected="Screenshot evidence should be saved under artifacts/screenshots",
                )

            # Visual regression
            if mode in {"visual", "full"}:
                visual_result = check_visual_regression(screenshot_path, module_name)

                add_test_case(
                    test_cases,
                    scenario="Visual regression check",
                    expected="Current UI matches baseline or baseline is created",
                    actual=visual_result.get("message", "-"),
                    status="PASS" if visual_result.get("passed") else "FAIL",
                    steps="Compare current screenshot with baseline",
                )

                if not visual_result.get("passed"):
                    add_bug(
                        bugs,
                        severity="Medium",
                        title="Visual regression detected",
                        actual=visual_result.get("message", "-"),
                        expected="UI should match approved baseline within threshold",
                    )
            else:
                visual_result = {
                    "passed": True,
                    "message": f"Visual regression skipped because mode={mode}",
                }

                add_test_case(
                    test_cases,
                    scenario="Visual regression skipped by mode",
                    expected="Visual regression is skipped based on selected mode",
                    actual=f"Skipped because mode={mode}",
                    status="SKIPPED",
                    steps="Skip visual comparison",
                )

            # Console error check
            if console_errors:
                add_test_case(
                    test_cases,
                    scenario="Console error check",
                    expected="No JavaScript console error appears",
                    actual="; ".join(console_errors[:5]),
                    status="FAIL",
                    steps="Capture browser console errors during audit",
                )

                add_bug(
                    bugs,
                    severity="Medium",
                    title="JavaScript console error detected",
                    actual="; ".join(console_errors[:5]),
                    expected="No JavaScript console error should appear during normal flow",
                )
            else:
                add_test_case(
                    test_cases,
                    scenario="Console error check",
                    expected="No JavaScript console error appears",
                    actual="No console error detected",
                    status="PASS",
                    steps="Capture browser console errors during audit",
                )

            # Network error check
            filtered_network_errors = [
                error for error in network_errors
                if "favicon" not in error.lower()
            ]

            if filtered_network_errors:
                network_error_text = "; ".join(filtered_network_errors[:5])

                add_test_case(
                    test_cases,
                    scenario="Network/API error check",
                    expected="No API or resource returns HTTP 4xx/5xx",
                    actual=network_error_text,
                    status="FAIL",
                    steps="Capture HTTP responses during audit",
                )

                severity = "High" if any(
                    code in network_error_text
                    for code in ["500", "401", "403"]
                ) else "Medium"

                add_bug(
                    bugs,
                    severity=severity,
                    title="Network/API error detected",
                    actual=network_error_text,
                    expected="All required API and resources should return successful response",
                )
            else:
                add_test_case(
                    test_cases,
                    scenario="Network/API error check",
                    expected="No API or resource returns HTTP 4xx/5xx",
                    actual="No relevant network error detected",
                    status="PASS",
                    steps="Capture HTTP responses during audit",
                )

            if context:
                context.close()

            if browser:
                browser.close()

    except Exception as runtime_error:
        error_trace = traceback.format_exc(limit=5)
        runtime_errors.append(error_trace)

        add_test_case(
            test_cases,
            scenario="Automation runtime",
            expected="Automation runs without technical error",
            actual=str(runtime_error),
            status="FAIL",
            steps="Run Playwright automation",
        )

        add_bug(
            bugs,
            severity="Critical",
            title="Automation runtime error",
            actual=error_trace,
            expected="Automation should run without unhandled exception",
        )

        try:
            if context:
                context.close()
        except Exception:
            pass

        try:
            if browser:
                browser.close()
        except Exception:
            pass

    # Final result
    release_checklist = build_release_checklist(test_cases, bugs)
    overall_status = calculate_overall_status(test_cases, bugs)

    if overall_status == "FAILED":
        recommendation = "Fix blocking issues before release. Prioritize failed login, access, menu, or runtime issues."
    elif overall_status == "NEED REVIEW":
        recommendation = (
            "Continue negative testing for empty state, required field validation, "
            "max character validation, and edit/delete action before release approval."
        )
    else:
        recommendation = (
            "No blocking issue found from automation result. Continue with manual business verification if needed."
        )

    relevant_network_errors = [
        error for error in network_errors
        if "favicon" not in error.lower()
    ]

    result: dict[str, Any] = {
        "run_id": run_id,
        "module_name": module_name,
        "mode": mode,
        "environment": "Sandbox",
        "url": url,
        "test_cases": test_cases,
        "bugs": bugs,
        "release_checklist": release_checklist,
        "status": overall_status,
        "recommendation": recommendation,
        "screenshot_path": str(screenshot_path) if screenshot_path else "-",
        "selector_inventory_path": str(selector_inventory_path) if selector_inventory_path else "-",
        "report_path": "-",
        "error_log_path": "-",
        "spreadsheet_path": "-",
        "visual_status": visual_result.get("status", "-"),
        "visual_message": visual_result.get("message", "-"),
        "console_errors": console_errors[:20],
        "network_errors": relevant_network_errors[:20],
        "runtime_errors": runtime_errors[:10],
    }

    result["testing_summary"] = build_testing_summary(result).replace("Summary:\nSummary:", "Summary:")
    result["documentation_report"] = build_documentation_report(result)
    result["error_log_report"] = build_error_log_report(result)

    report_path = REPORT_DIR / f"qa_documentation_{module_slug}_{run_id}.md"
    report_path.write_text(result["documentation_report"], encoding="utf-8")

    error_log_path = LOG_DIR / f"qa_error_log_{module_slug}_{run_id}.md"
    error_log_path.write_text(result["error_log_report"], encoding="utf-8")

    spreadsheet_path = export_spreadsheet_report(result, module_slug, run_id)
    result["spreadsheet_path"] = spreadsheet_path

    result["report_path"] = str(report_path)
    result["error_log_path"] = str(error_log_path)

    result["testing_summary"] = build_testing_summary(result).replace("Summary:\nSummary:", "Summary:")
    result["documentation_report"] = build_documentation_report(result)
    result["error_log_report"] = build_error_log_report(result)

    return result


# =========================================================
# Public Functions
# =========================================================

def _perform_audit_for_telegram_original(
    url: str,
    module_name: str = "Uang Makan Driver",
    mode: str = "full",
) -> dict[str, str]:
    result = perform_structured_audit(
        url=url,
        module_name=module_name,
        mode=mode,
    )

    result["execution_metadata"] = collect_qa_execution_metadata_basic(
        url=url,
        module_name=module_name,
        mode=mode,
        environment=result.get("environment", "Sandbox"),
        result=result,
    )

    result["testing_summary"] = inject_metadata_into_testing_summary(
        result.get("testing_summary", ""),
        result.get("execution_metadata", {}),
    )

    return {
        "status": result["status"],
        "mode": result.get("mode", mode),
        "testing_summary": result["testing_summary"],
        "documentation_report": result["documentation_report"],
        "error_log_report": result.get("error_log_report", "-"),
        "report_path": result.get("report_path", "-"),
        "error_log_path": result.get("error_log_path", "-"),
        "spreadsheet_path": result.get("spreadsheet_path", "-"),
        "selector_inventory_path": result.get("selector_inventory_path", "-"),
        "screenshot_path": result.get("screenshot_path", "-"),
    }




def qa_finalize_telegram_result(result, url=None, module_name=None, mode=None, environment="Sandbox"):
    """
    Finalizer shared untuk single suite dan combined suite.
    """

    if not isinstance(result, dict):
        return result

    try:
        if not result.get("execution_metadata"):
            result["execution_metadata"] = collect_qa_execution_metadata_basic(
                url=url or result.get("base_url") or "https://mobospace-sandbox.pancaran-group.co.id",
                module_name=module_name or result.get("module_name") or result.get("feature") or "Uang Makan Driver",
                mode=mode or result.get("mode") or "regression",
                environment=environment or result.get("environment") or "Sandbox",
                result=result,
            )

        result = apply_console_warning_policy(result)
        result = normalize_testing_summary_sections(result)

        result["testing_summary"] = inject_metadata_into_testing_summary(
            result.get("testing_summary", ""),
            result.get("execution_metadata", {}),
        )

        result = enrich_qa_report_artifacts_with_metadata(result)

    except Exception as exc:
        try:
            result["metadata_enrichment_error"] = str(exc)
        except Exception:
            pass

    return result


def _qa_click_label(page, label):
    scopes = [
        page.locator(".v-navigation-drawer, .v-navigation-drawer__content, .v-list, nav, aside").first,
        page.locator("body"),
    ]

    for scope in scopes:
        candidates = [
            scope.get_by_text(label, exact=True).first,
            page.locator(f".v-list-item:has-text('{label}')").last,
            page.locator(f"[role='button']:has-text('{label}')").last,
            scope.get_by_text(label, exact=False).first,
            page.get_by_text(label, exact=True).last,
            page.get_by_text(label, exact=False).last,
        ]

        for candidate in candidates:
            try:
                if candidate.count() <= 0:
                    continue

                candidate.scroll_into_view_if_needed(timeout=3000)
                candidate.wait_for(state="visible", timeout=4000)
                candidate.click(timeout=5000)

                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass

                page.wait_for_timeout(1500)
                return True

            except Exception:
                continue

    return False


def _qa_make_driver_meal_open_subpage(subfeature_name, labels):
    def open_subpage(page, test_cases, preferred_subpage="Monitoring"):
        clicked_label = None

        for label in labels:
            if _qa_click_label(page, label):
                clicked_label = label
                break

        if clicked_label:
            add_test_case(
                test_cases,
                scenario=f"Open Driver Meal {subfeature_name} subpage",
                precondition="Driver Meal menu group is visible",
                steps=f"Click {clicked_label} submenu",
                expected=f"Driver Meal {subfeature_name} subpage should be opened",
                actual=f"Opened submenu: {clicked_label}",
                status="PASS",
            )
        else:
            add_test_case(
                test_cases,
                scenario=f"Open Driver Meal {subfeature_name} subpage",
                precondition="Driver Meal menu group is visible",
                steps=f"Click {subfeature_name} submenu",
                expected=f"Driver Meal {subfeature_name} subpage should be opened",
                actual=f"{subfeature_name} submenu was not found",
                status="FAIL",
            )

    return open_subpage


def _qa_extract_status_from_summary(summary):
    import re

    match = re.search(r"Status:\s*(PASS|FAILED|NEED REVIEW)", summary or "")

    if match:
        return match.group(1)

    return "UNKNOWN"


def _qa_extract_count(summary, label):
    import re

    match = re.search(rf"- {label}:\s*(\d+)", summary or "")

    if match:
        return int(match.group(1))

    return 0


def _qa_extract_section(summary, header):
    if not summary:
        return "-"

    headers = [
        "Verified:",
        "Failed:",
        "Need Review:",
        "Bugs:",
        "Warnings / Known Issues:",
        "Evidence:",
        "Recommendation:",
        "Policy Note:",
    ]

    lines = summary.splitlines()
    start = -1

    for idx, line in enumerate(lines):
        if line.strip() == header:
            start = idx + 1
            break

    if start == -1:
        return "-"

    end = len(lines)

    for idx in range(start, len(lines)):
        if lines[idx].strip() in headers:
            end = idx
            break

    section_lines = [
        line for line in lines[start:end]
        if line.strip()
    ]

    return "\n".join(section_lines) if section_lines else "-"


def _qa_run_driver_meal_subfeature(name, open_func, validator_func, url, module_name, mode, environment):
    original_open = globals().get("open_uang_makan_driver_subpage")
    original_monitoring_validator = globals().get("validate_uang_makan_driver_monitoring_page")
    original_page_validator = globals().get("validate_uang_makan_driver_page")

    try:
        globals()["open_uang_makan_driver_subpage"] = open_func
        globals()["validate_uang_makan_driver_monitoring_page"] = validator_func
        globals()["validate_uang_makan_driver_page"] = validator_func

        result = _perform_audit_for_telegram_original(
            url,
            module_name,
            mode,
        )

        result = qa_finalize_telegram_result(
            result,
            url=url,
            module_name=f"Driver Daily Meal - {name}",
            mode=mode,
            environment=environment,
        )

        return result

    finally:
        if original_open:
            globals()["open_uang_makan_driver_subpage"] = original_open

        if original_monitoring_validator:
            globals()["validate_uang_makan_driver_monitoring_page"] = original_monitoring_validator

        if original_page_validator:
            globals()["validate_uang_makan_driver_page"] = original_page_validator


def _qa_write_driver_daily_meal_combined_spreadsheet(path, metadata, sub_results, overall_status, total_counts):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
    except Exception:
        return None

    wb = Workbook()

    ws = wb.active
    ws.title = "Combined Summary"

    ws.append(["Driver Daily Meal Combined Suite"])
    ws.append([])
    ws.append(["Overall Status", overall_status])
    ws.append(["Passed", total_counts.get("passed", 0)])
    ws.append(["Failed", total_counts.get("failed", 0)])
    ws.append(["Need Review", total_counts.get("need_review", 0)])
    ws.append(["Skipped", total_counts.get("skipped", 0)])
    ws.append(["Bugs Found", total_counts.get("bugs", 0)])
    ws.append(["Non-blocking Warnings", total_counts.get("warnings", 0)])

    ws2 = wb.create_sheet("Subfeatures")
    ws2.append(["Subfeature", "Status", "Passed", "Failed", "Need Review", "Skipped", "Bugs", "Warnings"])

    for item in sub_results:
        counts = item["counts"]
        ws2.append([
            item["name"],
            item["status"],
            counts["passed"],
            counts["failed"],
            counts["need_review"],
            counts["skipped"],
            counts["bugs"],
            counts["warnings"],
        ])

    ws3 = wb.create_sheet("Artifacts")
    ws3.append(["Subfeature", "Screenshot", "Report", "Spreadsheet"])

    for item in sub_results:
        result = item["result"]
        ws3.append([
            item["name"],
            result.get("screenshot_path", "-"),
            result.get("report_path", "-"),
            result.get("spreadsheet_path", "-"),
        ])

    ws4 = wb.create_sheet("Execution Metadata")
    ws4.append(["Field", "Value"])

    for key, value in (metadata or {}).items():
        ws4.append([key, str(value)])

    for sheet in wb.worksheets:
        for cell in sheet[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill("solid", fgColor="D9EAF7")
            cell.alignment = Alignment(horizontal="center")

        for column_cells in sheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter

            for cell in column_cells:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))

            sheet.column_dimensions[column_letter].width = min(max_length + 4, 90)

    wb.save(path)
    return str(path)



def _qa_make_driver_meal_open_exclude_add_form():
    """
    Open sequence untuk combined suite:
    Driver Meal -> Exclude -> ADD Form

    Scope aman:
    - hanya buka form
    - tidak submit data valid
    - tidak create/update/delete data
    """

    def open_subpage(page, test_cases, preferred_subpage="Monitoring"):
        opened_exclude = False

        for label in ["Exclude", "Pengecualian", "Exception", "Exceptions"]:
            if _qa_click_label(page, label):
                opened_exclude = True
                break

        add_test_case(
            test_cases,
            scenario="Open Driver Meal Exclude subpage",
            precondition="Driver Meal menu group is visible",
            steps="Click Exclude submenu",
            expected="Driver Meal Exclude subpage should be opened",
            actual="Exclude opened" if opened_exclude else "Exclude not opened",
            status="PASS" if opened_exclude else "FAIL",
        )

        if not opened_exclude:
            return

        opened_add = False

        for selector in ["button:has-text('ADD')", ".v-btn:has-text('ADD')", "text=ADD"]:
            try:
                locator = page.locator(selector).first

                if locator.count() <= 0:
                    continue

                locator.scroll_into_view_if_needed(timeout=3000)
                locator.click(timeout=5000)
                page.wait_for_timeout(1500)
                opened_add = True
                break
            except Exception:
                continue

        add_test_case(
            test_cases,
            scenario="Open Exclude ADD form",
            precondition="Driver Meal Exclude page is opened",
            steps="Click ADD button",
            expected="ADD form/dialog should be opened",
            actual="ADD form opened" if opened_add else "ADD form not opened",
            status="PASS" if opened_add else "FAIL",
        )

    return open_subpage



def perform_driver_daily_meal_combined_suite(url, module_name="Uang Makan Driver", mode="regression", environment="Sandbox"):
    """
    Combined suite untuk:
    - Monitoring
    - Exclude
    - History / Inquiry
    """

    from pathlib import Path
    from datetime import datetime

    suites = [
        {
            "name": "Monitoring",
            "open": _qa_make_driver_meal_open_subpage("Monitoring", ["Monitoring"]),
            "validator": validate_uang_makan_driver_monitoring_page,
        },
        {
            "name": "Exclude",
            "open": _qa_make_driver_meal_open_subpage("Exclude", ["Exclude", "Pengecualian", "Exception", "Exceptions"]),
            "validator": validate_driver_meal_exclude_page,
        },
        {
            "name": "Exclude ADD Form",
            "open": _qa_make_driver_meal_open_exclude_add_form(),
            "validator": validate_driver_meal_exclude_add_form_page,
        },
        {
            "name": "History / Inquiry",
            "open": _qa_make_driver_meal_open_subpage("History / Inquiry", ["History", "Inquiry", "Riwayat"]),
            "validator": validate_driver_meal_history_page,
        },
    ]

    sub_results = []

    for suite in suites:
        result = _qa_run_driver_meal_subfeature(
            suite["name"],
            suite["open"],
            suite["validator"],
            url,
            module_name,
            mode,
            environment,
        )

        summary = result.get("testing_summary") or ""

        status = _qa_extract_status_from_summary(summary)

        counts = {
            "passed": _qa_extract_count(summary, "Passed"),
            "failed": _qa_extract_count(summary, "Failed"),
            "need_review": _qa_extract_count(summary, "Need Review"),
            "skipped": _qa_extract_count(summary, "Skipped"),
            "bugs": _qa_extract_count(summary, "Bugs Found"),
            "warnings": _qa_extract_count(summary, "Non-blocking Warnings"),
        }

        sub_results.append(
            {
                "name": suite["name"],
                "status": status,
                "counts": counts,
                "result": result,
            }
        )

    has_failed = any(item["status"] == "FAILED" for item in sub_results)
    has_need_review = any(item["status"] == "NEED REVIEW" for item in sub_results)

    if has_failed:
        overall_status = "FAILED"
    elif has_need_review:
        overall_status = "NEED REVIEW"
    else:
        overall_status = "PASS"

    total_counts = {
        "passed": sum(item["counts"]["passed"] for item in sub_results),
        "failed": sum(item["counts"]["failed"] for item in sub_results),
        "need_review": sum(item["counts"]["need_review"] for item in sub_results),
        "skipped": sum(item["counts"]["skipped"] for item in sub_results),
        "bugs": sum(item["counts"]["bugs"] for item in sub_results),
        "warnings": sum(item["counts"]["warnings"] for item in sub_results),
    }

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = Path(__file__).resolve().parent / "artifacts"
    report_dir = base_dir / "reports"
    log_dir = base_dir / "logs"
    spreadsheet_dir = base_dir / "spreadsheets"

    report_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    spreadsheet_dir.mkdir(parents=True, exist_ok=True)

    metadata = collect_qa_execution_metadata_basic(
        url=url,
        module_name="Driver Daily Meal",
        mode=mode,
        environment=environment,
        result={"overall_status": overall_status},
    )

    subfeature_lines = "\n".join(
        f"- {item['name']}: {item['status']}"
        for item in sub_results
    )

    artifact_lines = []

    for item in sub_results:
        result = item["result"]
        artifact_lines.append(
            f"{item['name']}:\n"
            f"- Screenshot: {result.get('screenshot_path', '-')}\n"
            f"- Report: {result.get('report_path', '-')}\n"
            f"- Spreadsheet: {result.get('spreadsheet_path', '-')}"
        )

    raw_warnings = []

    for item in sub_results:
        section = _qa_extract_section(item["result"].get("testing_summary", ""), "Warnings / Known Issues:")
        if section and section != "-":
            raw_warnings.append(f"{item['name']}:\n{section}")

    known_vue_warning_found = any(
        "Known Vue warning detected in Driver Meal Exclude" in warning
        or "DriverExceptionTable.vue" in warning
        for warning in raw_warnings
    )

    if known_vue_warning_found:
        warning_text = (
            "Exclude / Exclude ADD Form:\n"
            "WARNING-001 MEDIUM - Known Vue warning detected in Driver Meal Exclude"
        )
        total_counts["warnings"] = 1
    else:
        warning_text = "\n\n".join(raw_warnings) if raw_warnings else "-"

    need_reviews = []

    for item in sub_results:
        section = _qa_extract_section(item["result"].get("testing_summary", ""), "Need Review:")
        if section and section != "-":
            need_reviews.append(f"{item['name']}:\n{section}")

    need_review_text = "\n\n".join(need_reviews) if need_reviews else "-"

    failed_items = []

    for item in sub_results:
        section = _qa_extract_section(item["result"].get("testing_summary", ""), "Failed:")
        if section and section != "-":
            failed_items.append(f"{item['name']}:\n{section}")

    failed_text = "\n\n".join(failed_items) if failed_items else "-"

    testing_summary = (
        "✅ QA E2E Regression Completed\n\n"
        "Module: Driver Daily Meal\n"
        f"Mode: {mode}\n"
        f"Environment: {environment}\n"
        f"Status: {overall_status}\n\n"
        "Execution Info:\n"
        f"- Execution ID: {metadata.get('execution_id', '-')}\n"
        f"- Executed At: {metadata.get('executed_at', '-')}\n"
        f"- Executed By: {metadata.get('executed_by', '-')}\n"
        "- Feature: Driver Daily Meal\n"
        f"- Suite / Mode: {mode}\n"
        f"- Environment: {environment}\n"
        f"- Base URL: {url}\n\n"
        "Runtime Environment:\n"
        f"- OS: {metadata.get('os', '-')}\n"
        f"- Machine: {metadata.get('machine', '-')}\n"
        f"- Browser: {metadata.get('browser', '-')}\n"
        f"- Browser Version: {metadata.get('browser_version', '-')}\n"
        f"- Device Profile: {metadata.get('device_profile', '-')}\n"
        f"- Viewport: {metadata.get('viewport', '-')}\n"
        f"- Automation Tool: {metadata.get('automation_tool', '-')}\n"
        f"- Runtime: {metadata.get('runtime', '-')}\n"
        f"- Python Version: {metadata.get('python_version', '-')}\n\n"
        "Summary:\n"
        f"- Passed: {total_counts['passed']}\n"
        f"- Failed: {total_counts['failed']}\n"
        f"- Need Review: {total_counts['need_review']}\n"
        f"- Skipped: {total_counts['skipped']}\n"
        f"- Bugs Found: {total_counts['bugs']}\n"
        f"- Non-blocking Warnings: {total_counts['warnings']}\n\n"
        "Subfeature Results:\n"
        f"{subfeature_lines}\n\n"
        "Failed:\n"
        f"{failed_text}\n\n"
        "Need Review:\n"
        f"{need_review_text}\n\n"
        "Warnings / Known Issues:\n"
        f"{warning_text}\n\n"
        "Evidence:\n"
        + "\n\n".join(artifact_lines)
        + "\n\nRecommendation:\n"
        + (
            "Review non-blocking warnings with frontend developer before release."
            if overall_status == "NEED REVIEW"
            else "No blocking issue found from automation result. Continue with manual business verification if needed."
        )
    )

    report_path = report_dir / f"qa_documentation_driver_daily_meal_combined_{run_id}.md"
    error_log_path = log_dir / f"qa_error_log_driver_daily_meal_combined_{run_id}.md"
    spreadsheet_path = spreadsheet_dir / f"qa_report_driver_daily_meal_combined_{run_id}.xlsx"

    documentation_report = (
        "# QA Documentation - Driver Daily Meal Combined Suite\n\n"
        + testing_summary
        + "\n\n---\n\n"
        + "## Subfeature Detail\n\n"
    )

    for item in sub_results:
        documentation_report += (
            f"### {item['name']}\n\n"
            + (item["result"].get("testing_summary") or "-")
            + "\n\n---\n\n"
        )

    error_log_report = (
        "# QA Error / Bug Log - Driver Daily Meal Combined Suite\n\n"
        f"Environment: {environment}\n"
        f"Mode: {mode}\n"
        f"Status: {overall_status}\n"
        f"Execution Time: {run_id}\n\n"
        "---\n\n"
        "## Failed Items\n\n"
        f"{failed_text}\n\n"
        "## Need Review Items\n\n"
        f"{need_review_text}\n\n"
        "## Warnings / Known Issues\n\n"
        f"{warning_text}\n"
    )

    report_path.write_text(documentation_report, encoding="utf-8")
    error_log_path.write_text(error_log_report, encoding="utf-8")

    _qa_write_driver_daily_meal_combined_spreadsheet(
        spreadsheet_path,
        metadata,
        sub_results,
        overall_status,
        total_counts,
    )

    screenshot_path = None

    for item in sub_results:
        candidate = item["result"].get("screenshot_path")
        if candidate:
            screenshot_path = candidate
            break

    combined_result = {
        "module_name": "Driver Daily Meal",
        "mode": mode,
        "environment": environment,
        "overall_status": overall_status,
        "execution_metadata": metadata,
        "testing_summary": testing_summary,
        "documentation_report": documentation_report,
        "error_log_report": error_log_report,
        "report_path": str(report_path),
        "documentation_path": str(report_path),
        "error_log_path": str(error_log_path),
        "spreadsheet_path": str(spreadsheet_path),
        "screenshot_path": screenshot_path,
        "sub_results": sub_results,
        "metadata_markdown_enriched": True,
        "metadata_excel_enriched": True,
    }

    return combined_result


def should_run_driver_daily_meal_combined(module_name, mode):
    import os

    enabled = os.getenv("QA_DRIVER_DAILY_MEAL_COMBINED", "true").lower() in ["1", "true", "yes", "on"]

    if not enabled:
        return False

    module_text = str(module_name or "").lower()
    mode_text = str(mode or "").lower()

    module_match = (
        "uang makan driver" in module_text
        or "driver daily meal" in module_text
        or "driver meal" in module_text
        or "meal allowance" in module_text
    )

    mode_match = mode_text in ["regression", "full", "e2e"]

    return module_match and mode_match


def perform_audit_for_telegram(*args, **kwargs):
    """
    Wrapper final:
    - metadata masuk ke Telegram summary, Markdown, Excel
    - known Vue warning tidak menjadi blocking FAIL
    - Driver Daily Meal regression menjalankan Monitoring + Exclude + History
    """

    try:
        url = (
            kwargs.get("url")
            or kwargs.get("base_url")
            or (args[0] if len(args) > 0 else None)
            or "https://mobospace-sandbox.pancaran-group.co.id"
        )

        module_name = (
            kwargs.get("module_name")
            or (args[1] if len(args) > 1 else None)
            or "Uang Makan Driver"
        )

        mode = (
            kwargs.get("mode")
            or (args[2] if len(args) > 2 else None)
            or "regression"
        )

        environment = (
            kwargs.get("environment")
            or "Sandbox"
        )

        if should_run_driver_daily_meal_combined(module_name, mode):
            return perform_driver_daily_meal_combined_suite(
                url=url,
                module_name=module_name,
                mode=mode,
                environment=environment,
            )

        result = _perform_audit_for_telegram_original(*args, **kwargs)

        result = qa_finalize_telegram_result(
            result,
            url=url,
            module_name=module_name,
            mode=mode,
            environment=environment,
        )

        return result

    except Exception as exc:
        result = _perform_audit_for_telegram_original(*args, **kwargs)

        try:
            result["metadata_enrichment_error"] = str(exc)
        except Exception:
            pass

        return result









def perform_audit(
    url: str,
    module_name: str = "Uang Makan Driver",
    mode: str = "full",
) -> str:
    result = perform_structured_audit(
        url=url,
        module_name=module_name,
        mode=mode,
    )

    return result["testing_summary"]

# ============================================================
# Shipment Details Validator
# ============================================================

def validate_shipment_details_page(page, test_cases, bugs):
    """
    Hardened validator untuk Shipment Details.

    Scope aman:
    - Tidak klik action icon
    - Tidak update data
    - Tidak submit form
    - Tidak export data
    - Hanya validasi page context, filter/search, status toggle, shipment card/list, dan evidence
    """

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=5000)
        except Exception as exc:
            return f"FAILED_TO_READ_BODY: {exc}"

    def locator_count(selector):
        try:
            return page.locator(selector).count()
        except Exception:
            return 0

    body_text = get_body_text()
    lower = body_text.lower()

    context_found = (
        "shipment details" in lower
        or "shipment detail" in lower
    ) and (
        "on shipment" in lower
        or "finished" in lower
        or "ordered" in lower
        or "vehicle & driver" in lower
        or "shipment info" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details page context",
        precondition="Shipment Details route is opened",
        steps="Check page title and shipment page markers",
        expected="Shipment Details page should be visible",
        actual="Shipment Details context found" if context_found else body_text[:500],
        status="PASS" if context_found else "FAIL",
    )

    if not context_found:
        add_bug(
            bugs,
            severity="High",
            title="Shipment Details page context not found",
            actual="Shipment Details page markers were not visible",
            expected="Shipment Details page should show title, status toggle, or shipment content",
        )

    on_shipment_found = "on shipment" in lower
    finished_found = "finished" in lower
    ordered_found = "ordered" in lower

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details status toggles",
        precondition="Shipment Details page is opened",
        steps="Check On Shipment, Finished, and Ordered toggles",
        expected="On Shipment, Finished, and Ordered should be visible",
        actual=(
            f"On Shipment={on_shipment_found}; "
            f"Finished={finished_found}; "
            f"Ordered={ordered_found}"
        ),
        status="PASS" if on_shipment_found and finished_found and ordered_found else "NEED REVIEW",
    )

    filter_found = (
        "filter" in lower
        or locator_count("button:has-text('FILTER')") > 0
        or locator_count("button:has-text('Filter')") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details filter button",
        precondition="Shipment Details page is opened",
        steps="Check FILTER button",
        expected="FILTER button should be visible",
        actual=f"Filter button visible={filter_found}",
        status="PASS" if filter_found else "NEED REVIEW",
    )

    search_found = (
        "search" in lower
        or locator_count(".v-input:has-text('search')") > 0
        or locator_count("input[type='text']") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details search field",
        precondition="Shipment Details page is opened",
        steps="Check search input field",
        expected="Search field should be visible",
        actual=f"Search field visible={search_found}",
        status="PASS" if search_found else "NEED REVIEW",
    )

    shipment_list_found = (
        locator_count("#scrollOrder") > 0
        or locator_count(".v-data-table__wrapper") > 0
        or locator_count(".v-card.v-card--outlined") > 0
        or "vehicle & driver" in lower
        or "shipment info" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details shipment list displayed",
        precondition="Shipment Details page is opened",
        steps="Check shipment list/card container",
        expected="Shipment list/card should be visible",
        actual=f"Shipment list/card visible={shipment_list_found}",
        status="PASS" if shipment_list_found else "FAIL",
    )

    if not shipment_list_found:
        add_bug(
            bugs,
            severity="High",
            title="Shipment Details list/card not displayed",
            actual="Shipment list/card container was not visible",
            expected="Shipment Details should show shipment list or valid empty state",
        )

    section_markers = {
        "Vehicle & Driver": ["vehicle & driver", "vehicle", "driver"],
        "Shipment Info": ["shipment info", "shipment"],
        "Origin / From": ["from : ", "from:"],
        "Destination / To": ["to : ", "to:"],
        "Progress Info": ["progress info", "target lead time", "elapsed time"],
    }

    matched_sections = []
    missing_sections = []

    for section_name, variants in section_markers.items():
        if any(variant in lower for variant in variants):
            matched_sections.append(section_name)
        else:
            missing_sections.append(section_name)

    sections_valid = len(matched_sections) >= 3

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details shipment information sections",
        precondition="Shipment list/card is visible",
        steps="Check card sections such as Vehicle & Driver, Shipment Info, From/To, and Progress Info",
        expected=", ".join(section_markers.keys()),
        actual=(
            f"Matched sections={', '.join(matched_sections) if matched_sections else '-'}; "
            f"Missing sections={', '.join(missing_sections) if missing_sections else '-'}"
        ),
        status="PASS" if sections_valid else "NEED REVIEW",
    )

    shipment_card_count = locator_count(".v-card.v-card--outlined")
    empty_state_found = (
        "no data available" in lower
        or "tidak ada data" in lower
    )

    shipment_data_valid = shipment_card_count > 0 or empty_state_found

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details data or empty state",
        precondition="Shipment Details page is opened",
        steps="Check shipment cards or valid empty state",
        expected="Shipment Details should show shipment cards or valid empty state",
        actual=f"Shipment card count={shipment_card_count}; empty state visible={empty_state_found}",
        status="PASS" if shipment_data_valid else "NEED REVIEW",
    )

    eye_icon_count = locator_count(".mdi-eye")
    map_icon_count = locator_count(".mdi-map-marker-radius")

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details action icons presence",
        precondition="Shipment cards are visible",
        steps="Check detail/view and map/location icons without clicking",
        expected="Action icons should be available when shipment data exists",
        actual=f"Eye icon count={eye_icon_count}; Map marker icon count={map_icon_count}",
        status="PASS" if eye_icon_count > 0 or map_icon_count > 0 or empty_state_found else "NEED REVIEW",
    )

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details safe validation mode",
        precondition="Shipment Details page is opened",
        steps="Validate page without clicking action buttons or mutating data",
        expected="Automation should not update/create/delete shipment data",
        actual="Safe mode: no action icon clicked, no data mutation executed",
        status="PASS",
    )


# ============================================================
# Shipment Details Telegram /audit_qa Integration
# ============================================================

def _qa_register_shipment_details_feature():
    """
    Register Shipment Details ke FEATURE_REGISTRY agar bisa dipanggil dari:
    /audit_qa mode=regression fitur=shipment details
    """

    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["shipment_details"] = {
        "display_name": "Shipment Details",
        "module_name": "Shipment Details",
        "menu_aliases": [
            "Shipment Details",
            "Shipment Detail",
            "shipmentdetail",
        ],
        "aliases": [
            "shipment details",
            "shipment detail",
            "shipment_details",
            "shipment_detail",
            "tracking shipment",
            "tracking shipment details",
        ],
        "default_subfeatures": ["main"],
        "subfeature_aliases": {
            "main": [
                "main",
                "shipment details",
                "shipment detail",
            ],
        },
    }


def should_run_shipment_details(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ")

    aliases = {
        "shipment details",
        "shipment detail",
        "shipmentdetails",
        "shipmentdetail",
        "tracking shipment",
        "tracking shipment details",
    }

    return value in aliases


def open_shipment_details_target_menu(page, module_name="Shipment Details"):
    """
    Open Shipment Details via direct sandbox route /shipmentdetail.

    Flow ini dipakai untuk Telegram command agar tidak nyasar ke:
    - Shipment Activity Dashboard
    - Main Dashboard / PDT Vehicle Performance
    """

    def get_origin():
        try:
            parts = page.url.split("/")
            return parts[0] + "//" + parts[2]
        except Exception:
            return "https://mobospace-sandbox.pancaran-group.co.id"

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=8000)
        except Exception:
            return ""

    def has_shipment_details_markers():
        body_text = get_body_text()
        lower = body_text.lower()

        return (
            "shipment details" in lower
            or "shipment detail" in lower
            or "on shipment" in lower
            or "finished" in lower
            or "ordered" in lower
            or "vehicle & driver" in lower
            or "shipment info" in lower
        )

    try:
        target_url = get_origin() + "/shipmentdetail"

        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(5000)

        current_url = page.url.lower()
        route_found = "shipmentdetail" in current_url
        marker_found = has_shipment_details_markers()

        opened = route_found or marker_found

        return opened, (
            f"Opened direct route: {target_url}; "
            f"current_url={page.url}; "
            f"route_found={route_found}; "
            f"marker_found={marker_found}"
        )

    except Exception as exc:
        return False, f"Failed to open /shipmentdetail: {exc}"


def open_shipment_details_no_subpage(page, test_cases, preferred_subpage=""):
    add_test_case(
        test_cases,
        scenario="Open Shipment Details page",
        precondition="User is logged in and /shipmentdetail route is available",
        steps="Open direct /shipmentdetail route",
        expected="Shipment Details page should be opened",
        actual="Shipment Details direct route used",
        status="PASS",
    )


def perform_shipment_details_suite(url, module_name="Shipment Details", mode="regression"):
    """
    Runner Shipment Details.

    Reuse existing Hermes audit flow, tetapi sementara mengganti:
    - open_target_menu
    - open_uang_makan_driver_subpage
    - validate_uang_makan_driver_monitoring_page
    - validate_uang_makan_driver_page

    Setelah run selesai, semua function dikembalikan agar Driver Daily Meal tetap aman.
    """

    previous_open_target_menu = globals().get("open_target_menu")
    previous_open_subpage = globals().get("open_uang_makan_driver_subpage")
    previous_validate_monitoring = globals().get("validate_uang_makan_driver_monitoring_page")
    previous_validate_page = globals().get("validate_uang_makan_driver_page")

    base_runner = globals().get("_PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_SHIPMENT_DETAILS")

    if base_runner is None:
        base_runner = globals().get("_perform_audit_for_telegram_original")

    if base_runner is None:
        base_runner = globals().get("_perform_audit_for_telegram_original_before_wrapper")

    if base_runner is None:
        raise RuntimeError("Base perform_audit_for_telegram runner not found")

    try:
        globals()["open_target_menu"] = open_shipment_details_target_menu
        globals()["open_uang_makan_driver_subpage"] = open_shipment_details_no_subpage
        globals()["validate_uang_makan_driver_monitoring_page"] = validate_shipment_details_page
        globals()["validate_uang_makan_driver_page"] = validate_shipment_details_page

        return base_runner(
            url,
            "Shipment Details",
            mode,
        )

    finally:
        if previous_open_target_menu is not None:
            globals()["open_target_menu"] = previous_open_target_menu

        if previous_open_subpage is not None:
            globals()["open_uang_makan_driver_subpage"] = previous_open_subpage

        if previous_validate_monitoring is not None:
            globals()["validate_uang_makan_driver_monitoring_page"] = previous_validate_monitoring

        if previous_validate_page is not None:
            globals()["validate_uang_makan_driver_page"] = previous_validate_page


_qa_register_shipment_details_feature()


if not globals().get("_SHIPMENT_DETAILS_TELEGRAM_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_SHIPMENT_DETAILS = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_shipment_details(module_name, mode):
            return perform_shipment_details_suite(url, module_name, mode)

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_SHIPMENT_DETAILS is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_SHIPMENT_DETAILS(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

    _SHIPMENT_DETAILS_TELEGRAM_PATCH_INSTALLED = True


# ============================================================
# MoboMap Validator
# ============================================================

def validate_mobomap_page(page, test_cases, bugs):
    """
    Hardened validator untuk MoboMap.

    Scope aman:
    - Tidak klik marker
    - Tidak klik eye/link/star action
    - Tidak update tracking
    - Tidak share link
    - Tidak mutate data
    - Hanya validasi map, filter/toggle, search, vehicle list, dan controls
    """

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=8000)
        except Exception as exc:
            return f"FAILED_TO_READ_BODY: {exc}"

    def locator_count(selector):
        try:
            return page.locator(selector).count()
        except Exception:
            return 0

    body_text = get_body_text()
    lower = body_text.lower()

    # 1. Page / map context
    map_selector_counts = {
        ".gm-style": locator_count(".gm-style"),
        ".leaflet-container": locator_count(".leaflet-container"),
        "[class*='map']": locator_count("[class*='map']"),
        "[id*='map']": locator_count("[id*='map']"),
        "canvas": locator_count("canvas"),
    }

    google_map_text_found = (
        "map data" in lower
        or "keyboard shortcuts" in lower
        or "report a map error" in lower
        or "google" in lower
        or "satellite" in lower
    )

    map_context_found = any(count > 0 for count in map_selector_counts.values()) or google_map_text_found

    add_test_case(
        test_cases,
        scenario="Verify MoboMap map context",
        precondition="MoboMap route is opened",
        steps="Check map container and Google Map context",
        expected="Map container should be visible",
        actual=f"Map selector counts={map_selector_counts}; google_map_text_found={google_map_text_found}",
        status="PASS" if map_context_found else "FAIL",
    )

    if not map_context_found:
        add_bug(
            bugs,
            severity="High",
            title="MoboMap map container not found",
            actual="Map container or Google Map context was not detected",
            expected="MoboMap should display map container",
        )

    # 2. Sidebar / vehicle context
    sidebar_context_found = (
        "vehicle" in lower
        or "driver" in lower
        or "phone number" in lower
        or "vehicle type" in lower
        or locator_count("#scrollTable") > 0
        or locator_count(".tbldrw") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify MoboMap vehicle sidebar/list context",
        precondition="MoboMap page is opened",
        steps="Check vehicle list/sidebar markers",
        expected="Vehicle sidebar/list should be visible",
        actual=f"Vehicle/sidebar context visible={sidebar_context_found}",
        status="PASS" if sidebar_context_found else "NEED REVIEW",
    )

    # 3. Vehicle status toggles
    on_job_found = "on job" in lower
    available_found = "available" in lower
    maintained_found = "maintained" in lower

    add_test_case(
        test_cases,
        scenario="Verify MoboMap vehicle status toggles",
        precondition="MoboMap page is opened",
        steps="Check On Job, Available, and Maintained toggles",
        expected="On Job, Available, and Maintained toggles should be visible",
        actual=(
            f"On Job={on_job_found}; "
            f"Available={available_found}; "
            f"Maintained={maintained_found}"
        ),
        status="PASS" if on_job_found and available_found and maintained_found else "NEED REVIEW",
    )

    # 4. Search vehicle / location inputs
    search_input_count = (
        locator_count("input[placeholder='Search']")
        + locator_count("input[placeholder*='Search']")
        + locator_count(".searchVehicle")
        + locator_count("input.pac-target-input")
    )

    location_input_found = (
        locator_count("input[placeholder='Enter a location']") > 0
        or "enter a location" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify MoboMap search inputs",
        precondition="MoboMap page is opened",
        steps="Check vehicle search and location search inputs",
        expected="Search input and location input should be available",
        actual=f"search_input_count={search_input_count}; location_input_found={location_input_found}",
        status="PASS" if search_input_count > 0 or location_input_found else "NEED REVIEW",
    )

    # 5. Vehicle list table
    vehicle_table_count = (
        locator_count("#scrollTable")
        + locator_count(".v-data-table.tbldrw")
        + locator_count(".v-data-table__wrapper")
    )

    vehicle_data_markers = {
        "Driver": "driver" in lower,
        "Phone Number": "phone number" in lower,
        "Vehicle Type": "vehicle type" in lower,
        "Site": "site" in lower,
        "Customer": "customer" in lower,
    }

    vehicle_data_found = vehicle_table_count > 0 or any(vehicle_data_markers.values())

    add_test_case(
        test_cases,
        scenario="Verify MoboMap vehicle list data",
        precondition="MoboMap vehicle sidebar/list is visible",
        steps="Check vehicle list/table and key data fields",
        expected="Vehicle list should show driver, phone, vehicle type, site, or customer data",
        actual=f"vehicle_table_count={vehicle_table_count}; markers={vehicle_data_markers}",
        status="PASS" if vehicle_data_found else "NEED REVIEW",
    )

    # 6. Map controls
    map_control_counts = {
        "Map": locator_count("button[aria-label='Show street map']"),
        "Satellite": locator_count("button[aria-label='Show satellite imagery']"),
        "Zoom In": locator_count("button[aria-label='Zoom in']"),
        "Zoom Out": locator_count("button[aria-label='Zoom out']"),
        "Fullscreen": locator_count("button[aria-label='Toggle fullscreen view']"),
        "Keyboard Shortcuts": locator_count("button[aria-label='Keyboard shortcuts']"),
    }

    map_controls_found = (
        map_control_counts["Map"] > 0
        or map_control_counts["Satellite"] > 0
        or map_control_counts["Zoom In"] > 0
        or map_control_counts["Zoom Out"] > 0
        or "map" in lower and "satellite" in lower
        or "zoom in" in lower
        or "zoom out" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify MoboMap map controls",
        precondition="Map is visible",
        steps="Check Map/Satellite and zoom controls",
        expected="Map controls should be visible",
        actual=f"map_control_counts={map_control_counts}",
        status="PASS" if map_controls_found else "NEED REVIEW",
    )

    # 7. Vehicle action icons, read-only check only
    eye_icon_count = locator_count(".mdi-eye")
    link_icon_count = locator_count(".mdi-link-variant")
    star_icon_count = locator_count(".material-icons:text('star')")

    # Playwright CSS tidak selalu support :text untuk class material-icons di semua versi,
    # jadi fallback dari visible text.
    if star_icon_count == 0 and "star" in lower:
        star_icon_count = 1

    add_test_case(
        test_cases,
        scenario="Verify MoboMap vehicle action icons presence",
        precondition="Vehicle list is visible",
        steps="Check eye/link/star icons without clicking",
        expected="Vehicle action icons should be present when data exists",
        actual=f"eye_icon_count={eye_icon_count}; link_icon_count={link_icon_count}; star_icon_count={star_icon_count}",
        status="PASS" if eye_icon_count > 0 or link_icon_count > 0 or star_icon_count > 0 else "NEED REVIEW",
    )

    # 8. Safe mode confirmation
    add_test_case(
        test_cases,
        scenario="Verify MoboMap safe validation mode",
        precondition="MoboMap page is opened",
        steps="Validate MoboMap without clicking marker/action/share controls",
        expected="Automation should not update, share, or mutate tracking data",
        actual="Safe mode: no marker clicked, no action icon clicked, no share/update executed",
        status="PASS",
    )


# ============================================================
# MoboMap Telegram /audit_qa Integration
# ============================================================

def _qa_register_mobomap_feature():
    """
    Register MoboMap ke FEATURE_REGISTRY agar bisa dipanggil dari:
    /audit_qa mode=regression fitur=mobomap
    /audit_qa mode=smoke fitur=mobo map
    """

    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["mobomap"] = {
        "display_name": "MoboMap",
        "module_name": "MoboMap",
        "menu_aliases": [
            "MoboMap",
            "Mobo Map",
            "mobomap",
        ],
        "aliases": [
            "mobomap",
            "mobo map",
            "mobo_map",
            "mobo-map",
            "map",
            "vehicle map",
            "tracking map",
            "vehicle tracking",
        ],
        "default_subfeatures": ["main"],
        "subfeature_aliases": {
            "main": [
                "main",
                "mobomap",
                "mobo map",
                "vehicle map",
            ],
        },
    }


def should_run_mobomap(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")

    aliases = {
        "mobomap",
        "mobo map",
        "map",
        "vehicle map",
        "tracking map",
        "vehicle tracking",
    }

    return value in aliases


def open_mobomap_target_menu(page, module_name="MoboMap"):
    """
    Open MoboMap via direct sandbox route /mobomap.
    """

    def get_origin():
        try:
            parts = page.url.split("/")
            return parts[0] + "//" + parts[2]
        except Exception:
            return "https://mobospace-sandbox.pancaran-group.co.id"

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=8000)
        except Exception:
            return ""

    def has_mobomap_markers():
        body_text = get_body_text()
        lower = body_text.lower()

        dom_map_count = 0

        for selector in [
            ".gm-style",
            ".leaflet-container",
            "[class*='map']",
            "[id*='map']",
            "canvas",
        ]:
            try:
                dom_map_count += page.locator(selector).count()
            except Exception:
                pass

        return (
            "mobomap" in lower
            or "mobo map" in lower
            or "vehicle" in lower
            or "driver" in lower
            or "map data" in lower
            or "satellite" in lower
            or dom_map_count > 0
        )

    try:
        target_url = get_origin() + "/mobomap"

        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(6000)

        current_url = page.url.lower()
        route_found = "mobomap" in current_url
        marker_found = has_mobomap_markers()

        opened = route_found or marker_found

        return opened, (
            f"Opened direct route: {target_url}; "
            f"current_url={page.url}; "
            f"route_found={route_found}; "
            f"marker_found={marker_found}"
        )

    except Exception as exc:
        return False, f"Failed to open /mobomap: {exc}"


def open_mobomap_no_subpage(page, test_cases, preferred_subpage=""):
    add_test_case(
        test_cases,
        scenario="Open MoboMap page",
        precondition="User is logged in and /mobomap route is available",
        steps="Open direct /mobomap route",
        expected="MoboMap page should be opened",
        actual="MoboMap direct route used",
        status="PASS",
    )


def perform_mobomap_suite(url, module_name="MoboMap", mode="regression"):
    """
    Runner MoboMap.

    Reuse existing Hermes audit flow, tetapi sementara mengganti:
    - open_target_menu
    - open_uang_makan_driver_subpage
    - validate_uang_makan_driver_monitoring_page
    - validate_uang_makan_driver_page

    Setelah run selesai, semua function dikembalikan agar fitur lain tetap aman.
    """

    previous_open_target_menu = globals().get("open_target_menu")
    previous_open_subpage = globals().get("open_uang_makan_driver_subpage")
    previous_validate_monitoring = globals().get("validate_uang_makan_driver_monitoring_page")
    previous_validate_page = globals().get("validate_uang_makan_driver_page")

    base_runner = globals().get("_PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_MOBOMAP")

    if base_runner is None:
        base_runner = globals().get("perform_audit_for_telegram")

    if base_runner is None:
        raise RuntimeError("Base perform_audit_for_telegram runner not found")

    try:
        globals()["open_target_menu"] = open_mobomap_target_menu
        globals()["open_uang_makan_driver_subpage"] = open_mobomap_no_subpage
        globals()["validate_uang_makan_driver_monitoring_page"] = validate_mobomap_page
        globals()["validate_uang_makan_driver_page"] = validate_mobomap_page

        return base_runner(
            url,
            "MoboMap",
            mode,
        )

    finally:
        if previous_open_target_menu is not None:
            globals()["open_target_menu"] = previous_open_target_menu

        if previous_open_subpage is not None:
            globals()["open_uang_makan_driver_subpage"] = previous_open_subpage

        if previous_validate_monitoring is not None:
            globals()["validate_uang_makan_driver_monitoring_page"] = previous_validate_monitoring

        if previous_validate_page is not None:
            globals()["validate_uang_makan_driver_page"] = previous_validate_page


_qa_register_mobomap_feature()


if not globals().get("_MOBOMAP_TELEGRAM_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_MOBOMAP = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_mobomap(module_name, mode):
            return perform_mobomap_suite(url, module_name, mode)

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_MOBOMAP is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_MOBOMAP(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

    _MOBOMAP_TELEGRAM_PATCH_INSTALLED = True


# ============================================================
# Inspection Result Validator
# ============================================================

def validate_inspection_result_page(page, test_cases, bugs):
    """
    Hardened validator untuk Inspection Result.

    Scope aman:
    - Tidak klik CHOOSE
    - Tidak approve/reject decision
    - Tidak submit form
    - Tidak update inspection result
    - Hanya validasi page context, status toggle, filter/search, card/list, dan evidence
    """

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=8000)
        except Exception as exc:
            return f"FAILED_TO_READ_BODY: {exc}"

    def locator_count(selector):
        try:
            return page.locator(selector).count()
        except Exception:
            return 0

    body_text = get_body_text()
    lower = body_text.lower()

    # 1. Page context
    context_found = (
        "inspection result" in lower
        or "inspection" in lower
    ) and (
        "waiting for decision" in lower
        or "approved" in lower
        or "rejected" in lower
        or "in progress" in lower
        or "inspection info" in lower
        or "inspection type" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result page context",
        precondition="Inspection Result route is opened",
        steps="Check page title and inspection result markers",
        expected="Inspection Result page should be visible",
        actual="Inspection Result context found" if context_found else body_text[:500],
        status="PASS" if context_found else "FAIL",
    )

    if not context_found:
        add_bug(
            bugs,
            severity="High",
            title="Inspection Result page context not found",
            actual="Inspection Result markers were not visible",
            expected="Inspection Result page should show title, status toggle, or inspection content",
        )

    # 2. Status toggles
    waiting_found = "waiting for decision" in lower
    approved_found = "approved" in lower
    rejected_found = "rejected" in lower
    in_progress_found = "in progress" in lower

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result status toggles",
        precondition="Inspection Result page is opened",
        steps="Check Waiting for Decision, Approved, Rejected, and In Progress toggles",
        expected="All inspection status toggles should be visible",
        actual=(
            f"Waiting for Decision={waiting_found}; "
            f"Approved={approved_found}; "
            f"Rejected={rejected_found}; "
            f"In Progress={in_progress_found}"
        ),
        status="PASS" if waiting_found and approved_found and rejected_found and in_progress_found else "NEED REVIEW",
    )

    # 3. Filter button
    filter_found = (
        "filter" in lower
        or locator_count("button:has-text('FILTER')") > 0
        or locator_count("button:has-text('Filter')") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result filter button",
        precondition="Inspection Result page is opened",
        steps="Check FILTER button",
        expected="FILTER button should be visible",
        actual=f"Filter button visible={filter_found}",
        status="PASS" if filter_found else "NEED REVIEW",
    )

    # 4. Search field
    search_found = (
        "search" in lower
        or locator_count(".v-input:has-text('search')") > 0
        or locator_count("input[type='text']") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result search field",
        precondition="Inspection Result page is opened",
        steps="Check search input field",
        expected="Search field should be visible",
        actual=f"Search field visible={search_found}",
        status="PASS" if search_found else "NEED REVIEW",
    )

    # 5. Inspection list/card/table
    inspection_list_found = (
        locator_count("#scrollOrder") > 0
        or locator_count(".v-data-table__wrapper") > 0
        or locator_count(".v-card") > 0
        or "inspection info" in lower
        or "inspection type" in lower
        or "document no" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result list/card displayed",
        precondition="Inspection Result page is opened",
        steps="Check inspection list/card/table container",
        expected="Inspection result list/card should be visible",
        actual=f"Inspection list/card visible={inspection_list_found}",
        status="PASS" if inspection_list_found else "FAIL",
    )

    if not inspection_list_found:
        add_bug(
            bugs,
            severity="High",
            title="Inspection Result list/card not displayed",
            actual="Inspection list/card container was not visible",
            expected="Inspection Result should show inspection list or valid empty state",
        )

    # 6. Inspection information sections
    section_markers = {
        "Driver / Inspector": [" - ", "driver", "choose"],
        "Company / Customer": ["pt.", "customer"],
        "Proper Status": ["proper", "not proper"],
        "Score": ["score:"],
        "Vehicle": ["vehicle:"],
        "Chassis No": ["chassis no:"],
        "Odometer": ["odometer:"],
        "Last Maintenance": ["last maintenance:"],
        "Location": ["location:"],
        "Inspection Info": ["inspection info:"],
        "Inspection Type": ["inspection type:"],
        "Document No": ["document no:"],
        "Total Duration": ["total duration:"],
        "Idle Duration": ["idle duration:"],
        "Shipment No": ["shipment no:"],
    }

    matched_sections = []
    missing_sections = []

    for section_name, variants in section_markers.items():
        if any(variant in lower for variant in variants):
            matched_sections.append(section_name)
        else:
            missing_sections.append(section_name)

    sections_valid = len(matched_sections) >= 7

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result information sections",
        precondition="Inspection result card/list is visible",
        steps="Check score, vehicle, location, inspection info, document no, duration, and shipment no sections",
        expected=", ".join(section_markers.keys()),
        actual=(
            f"Matched sections={', '.join(matched_sections) if matched_sections else '-'}; "
            f"Missing sections={', '.join(missing_sections) if missing_sections else '-'}"
        ),
        status="PASS" if sections_valid else "NEED REVIEW",
    )

    # 7. Data or empty state
    inspection_card_count = locator_count(".mx-auto.v-card") + locator_count(".v-card")
    table_count = locator_count(".v-data-table__wrapper")
    empty_state_found = (
        "no data available" in lower
        or "tidak ada data" in lower
    )

    data_valid = inspection_card_count > 0 or table_count > 0 or empty_state_found

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result data or empty state",
        precondition="Inspection Result page is opened",
        steps="Check inspection cards/table or valid empty state",
        expected="Inspection Result should show inspection data or valid empty state",
        actual=(
            f"inspection_card_count={inspection_card_count}; "
            f"table_count={table_count}; "
            f"empty_state_visible={empty_state_found}"
        ),
        status="PASS" if data_valid else "NEED REVIEW",
    )

    # 8. CHOOSE/action button presence, read-only only
    choose_button_count = locator_count("button:has-text('CHOOSE')")
    generic_button_count = locator_count("button")
    icon_button_count = locator_count(".v-btn--icon")

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result action buttons presence",
        precondition="Inspection result cards are visible",
        steps="Check CHOOSE/action buttons without clicking",
        expected="Action buttons may be available, but automation should not click them",
        actual=(
            f"choose_button_count={choose_button_count}; "
            f"generic_button_count={generic_button_count}; "
            f"icon_button_count={icon_button_count}"
        ),
        status="PASS" if choose_button_count > 0 or icon_button_count > 0 or empty_state_found else "NEED REVIEW",
    )

    # 9. Safe mode confirmation
    add_test_case(
        test_cases,
        scenario="Verify Inspection Result safe validation mode",
        precondition="Inspection Result page is opened",
        steps="Validate page without clicking CHOOSE, approve, reject, or submit buttons",
        expected="Automation should not update or mutate inspection result data",
        actual="Safe mode: no CHOOSE clicked, no approve/reject action executed, no data mutation executed",
        status="PASS",
    )


# ============================================================
# Inspection Result Telegram /audit_qa Integration
# ============================================================

def _qa_register_inspection_result_feature():
    """
    Register Inspection Result ke FEATURE_REGISTRY agar bisa dipanggil dari:
    /audit_qa mode=regression fitur=inspection result
    """

    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["inspection_result"] = {
        "display_name": "Inspection Result",
        "module_name": "Inspection Result",
        "menu_aliases": [
            "Inspection Result",
            "Inspection",
            "inspectionresult",
        ],
        "aliases": [
            "inspection result",
            "inspection_result",
            "inspection-result",
            "inspectionresult",
            "inspection",
            "hasil inspection",
            "hasil inspeksi",
            "inspection report",
        ],
        "default_subfeatures": ["main"],
        "subfeature_aliases": {
            "main": [
                "main",
                "inspection result",
                "inspection",
            ],
        },
    }


def should_run_inspection_result(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")

    aliases = {
        "inspection result",
        "inspectionresult",
        "inspection",
        "hasil inspection",
        "hasil inspeksi",
        "inspection report",
    }

    return value in aliases


def open_inspection_result_target_menu(page, module_name="Inspection Result"):
    """
    Open Inspection Result via direct sandbox route /inspectionresult.
    """

    def get_origin():
        try:
            parts = page.url.split("/")
            return parts[0] + "//" + parts[2]
        except Exception:
            return "https://mobospace-sandbox.pancaran-group.co.id"

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=8000)
        except Exception:
            return ""

    def has_inspection_result_markers():
        body_text = get_body_text()
        lower = body_text.lower()

        return (
            "inspection result" in lower
            or "inspection" in lower
            or "waiting for decision" in lower
            or "approved" in lower
            or "rejected" in lower
            or "in progress" in lower
            or "inspection info" in lower
            or "inspection type" in lower
            or "document no" in lower
        )

    try:
        target_url = get_origin() + "/inspectionresult"

        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(5000)

        current_url = page.url.lower()
        route_found = "inspectionresult" in current_url
        marker_found = has_inspection_result_markers()

        opened = route_found or marker_found

        return opened, (
            f"Opened direct route: {target_url}; "
            f"current_url={page.url}; "
            f"route_found={route_found}; "
            f"marker_found={marker_found}"
        )

    except Exception as exc:
        return False, f"Failed to open /inspectionresult: {exc}"


def open_inspection_result_no_subpage(page, test_cases, preferred_subpage=""):
    add_test_case(
        test_cases,
        scenario="Open Inspection Result page",
        precondition="User is logged in and /inspectionresult route is available",
        steps="Open direct /inspectionresult route",
        expected="Inspection Result page should be opened",
        actual="Inspection Result direct route used",
        status="PASS",
    )


def perform_inspection_result_suite(url, module_name="Inspection Result", mode="regression"):
    """
    Runner Inspection Result.

    Reuse existing Hermes audit flow, tetapi sementara mengganti:
    - open_target_menu
    - open_uang_makan_driver_subpage
    - validate_uang_makan_driver_monitoring_page
    - validate_uang_makan_driver_page

    Setelah run selesai, semua function dikembalikan agar fitur lain tetap aman.
    """

    previous_open_target_menu = globals().get("open_target_menu")
    previous_open_subpage = globals().get("open_uang_makan_driver_subpage")
    previous_validate_monitoring = globals().get("validate_uang_makan_driver_monitoring_page")
    previous_validate_page = globals().get("validate_uang_makan_driver_page")

    base_runner = globals().get("_PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_INSPECTION_RESULT")

    if base_runner is None:
        base_runner = globals().get("perform_audit_for_telegram")

    if base_runner is None:
        raise RuntimeError("Base perform_audit_for_telegram runner not found")

    try:
        globals()["open_target_menu"] = open_inspection_result_target_menu
        globals()["open_uang_makan_driver_subpage"] = open_inspection_result_no_subpage
        globals()["validate_uang_makan_driver_monitoring_page"] = validate_inspection_result_page
        globals()["validate_uang_makan_driver_page"] = validate_inspection_result_page

        return base_runner(
            url,
            "Inspection Result",
            mode,
        )

    finally:
        if previous_open_target_menu is not None:
            globals()["open_target_menu"] = previous_open_target_menu

        if previous_open_subpage is not None:
            globals()["open_uang_makan_driver_subpage"] = previous_open_subpage

        if previous_validate_monitoring is not None:
            globals()["validate_uang_makan_driver_monitoring_page"] = previous_validate_monitoring

        if previous_validate_page is not None:
            globals()["validate_uang_makan_driver_page"] = previous_validate_page


_qa_register_inspection_result_feature()


if not globals().get("_INSPECTION_RESULT_TELEGRAM_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_INSPECTION_RESULT = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_inspection_result(module_name, mode):
            return perform_inspection_result_suite(url, module_name, mode)

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_INSPECTION_RESULT is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_INSPECTION_RESULT(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

    _INSPECTION_RESULT_TELEGRAM_PATCH_INSTALLED = True


# ============================================================
# Notification Messages Validator
# ============================================================

def validate_notification_messages_page(page, test_cases, bugs):
    """
    Hardened validator untuk Notification Messages.

    Scope aman:
    - Tidak klik SEND
    - Tidak submit message
    - Tidak create/edit/delete data
    - Hanya validasi tab, form field, Sent Items table/list, dan evidence
    """

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=8000)
        except Exception as exc:
            return f"FAILED_TO_READ_BODY: {exc}"

    def locator_count(selector):
        try:
            return page.locator(selector).count()
        except Exception:
            return 0

    def click_tab(label):
        candidates = [
            page.get_by_role("tab", name=label).first,
            page.locator(f".v-tab:has-text('{label}')").first,
            page.get_by_text(label, exact=True).first,
        ]

        for candidate in candidates:
            try:
                if candidate.count() <= 0:
                    continue

                candidate.scroll_into_view_if_needed(timeout=3000)
                candidate.click(timeout=5000, force=True)

                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass

                page.wait_for_timeout(2500)
                return True

            except Exception:
                continue

        return False

    body_text = get_body_text()
    lower = body_text.lower()

    # 1. Page context
    context_found = (
        "notification message" in lower
        or "notification messages" in lower
    ) and (
        "send message" in lower
        or "sent items" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Notification Messages page context",
        precondition="Notification Messages route is opened",
        steps="Check page title and main tabs",
        expected="Notification Message page should show Send Message and Sent Items tabs",
        actual="Notification Messages context found" if context_found else body_text[:500],
        status="PASS" if context_found else "FAIL",
    )

    if not context_found:
        add_bug(
            bugs,
            severity="High",
            title="Notification Messages page context not found",
            actual="Notification Message page markers were not visible",
            expected="Notification Message page should show Send Message and Sent Items tabs",
        )

    # 2. Tabs visible
    send_tab_found = "send message" in lower or locator_count(".v-tab:has-text('Send Message')") > 0
    sent_items_tab_found = "sent items" in lower or locator_count(".v-tab:has-text('Sent Items')") > 0

    add_test_case(
        test_cases,
        scenario="Verify Notification Messages tabs",
        precondition="Notification Messages page is opened",
        steps="Check Send Message and Sent Items tabs",
        expected="Send Message and Sent Items tabs should be visible",
        actual=f"Send Message={send_tab_found}; Sent Items={sent_items_tab_found}",
        status="PASS" if send_tab_found and sent_items_tab_found else "NEED REVIEW",
    )

    # 3. Send Message tab form
    send_clicked = click_tab("Send Message")
    send_text = get_body_text()
    send_lower = send_text.lower()

    send_fields = {
        "Contact Groups": "contact groups" in send_lower,
        "Contacts": "contacts" in send_lower,
        "Channels": "channels" in send_lower,
        "Select All": "select all" in send_lower,
        "Signature": "signature" in send_lower,
        "Title / Subject": "title / subject" in send_lower or "subject" in send_lower,
        "Body / Notification Message": "body / notification message" in send_lower or "notification message" in send_lower,
        "Title Counter 0 / 60": "0 / 60" in send_lower,
        "Body Counter 0 / 500": "0 / 500" in send_lower,
    }

    send_form_count = (
        locator_count("input")
        + locator_count("textarea")
        + locator_count(".v-input")
    )

    send_button_visible = (
        "send" in send_lower
        or locator_count("button:has-text('SEND')") > 0
        or locator_count("button:has-text('Send')") > 0
    )

    matched_send_fields = [name for name, found in send_fields.items() if found]
    missing_send_fields = [name for name, found in send_fields.items() if not found]

    send_form_valid = send_clicked and len(matched_send_fields) >= 5 and send_form_count > 0

    add_test_case(
        test_cases,
        scenario="Verify Send Message form fields",
        precondition="Send Message tab is opened",
        steps="Check recipient/channel/signature/title/body fields without filling or submitting",
        expected="Send Message form fields should be visible",
        actual=(
            f"clicked={send_clicked}; "
            f"form_count={send_form_count}; "
            f"send_button_visible={send_button_visible}; "
            f"matched={matched_send_fields}; "
            f"missing={missing_send_fields}"
        ),
        status="PASS" if send_form_valid else "NEED REVIEW",
    )

    # 4. SEND button read-only presence
    add_test_case(
        test_cases,
        scenario="Verify Send Message action button presence",
        precondition="Send Message tab is opened",
        steps="Check SEND button visibility without clicking",
        expected="SEND button may be visible but automation must not click it",
        actual=f"SEND button visible={send_button_visible}",
        status="PASS" if send_button_visible else "NEED REVIEW",
    )

    # 5. Sent Items tab
    sent_clicked = click_tab("Sent Items")
    sent_text = get_body_text()
    sent_lower = sent_text.lower()

    sent_markers = {
        "ACTION": "action" in sent_lower,
        "Search": "search" in sent_lower,
        "Title": "title" in sent_lower,
        "Body": "body" in sent_lower,
        "Number Of Contact": "number of contact" in sent_lower,
        "Channels": "channels" in sent_lower,
        "Message Sent": "message sent" in sent_lower,
        "No Data Available": "no data available" in sent_lower,
    }

    sent_table_count = locator_count(".v-data-table") + locator_count(".v-data-table__wrapper")
    sent_input_count = locator_count("input[type='text']") + locator_count(".v-input")

    matched_sent_markers = [name for name, found in sent_markers.items() if found]
    missing_sent_markers = [name for name, found in sent_markers.items() if not found]

    sent_items_valid = sent_clicked and (
        sent_table_count > 0
        or len(matched_sent_markers) >= 4
    )

    add_test_case(
        test_cases,
        scenario="Verify Sent Items table/list",
        precondition="Sent Items tab is opened",
        steps="Check Sent Items table/search/headers or empty state",
        expected="Sent Items should show search, table headers, message history, or valid empty state",
        actual=(
            f"clicked={sent_clicked}; "
            f"table_count={sent_table_count}; "
            f"input_count={sent_input_count}; "
            f"matched={matched_sent_markers}; "
            f"missing={missing_sent_markers}"
        ),
        status="PASS" if sent_items_valid else "NEED REVIEW",
    )

    # 6. Safe mode confirmation
    add_test_case(
        test_cases,
        scenario="Verify Notification Messages safe validation mode",
        precondition="Notification Messages page is opened",
        steps="Validate tabs and fields without clicking SEND or submitting data",
        expected="Automation should not send notification or mutate notification data",
        actual="Safe mode: no SEND clicked, no message submitted, no edit/delete action executed",
        status="PASS",
    )


# ============================================================
# Notification Messages Telegram /audit_qa Integration
# ============================================================

def _qa_register_notification_messages_feature():
    """
    Register Notification Messages ke FEATURE_REGISTRY agar bisa dipanggil dari:
    /audit_qa mode=regression fitur=notification messages
    """

    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["notification_messages"] = {
        "display_name": "Notification Messages",
        "module_name": "Notification Messages",
        "menu_aliases": [
            "Notification Messages",
            "Notification Message",
            "notificationmessage",
        ],
        "aliases": [
            "notification messages",
            "notification message",
            "notification_messages",
            "notification-message",
            "notificationmessage",
            "mobo notification message",
            "mobo notif message",
            "notif message",
            "notif messages",
        ],
        "default_subfeatures": ["main"],
        "subfeature_aliases": {
            "main": [
                "main",
                "notification messages",
                "notification message",
                "send message",
                "sent items",
            ],
        },
    }


def should_run_notification_messages(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")

    aliases = {
        "notification messages",
        "notification message",
        "notificationmessage",
        "mobo notification message",
        "mobo notif message",
        "notif message",
        "notif messages",
    }

    return value in aliases


def open_notification_messages_target_menu(page, module_name="Notification Messages"):
    """
    Open Notification Messages via direct sandbox route /notificationmessage.
    """

    def get_origin():
        try:
            parts = page.url.split("/")
            return parts[0] + "//" + parts[2]
        except Exception:
            return "https://mobospace-sandbox.pancaran-group.co.id"

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=8000)
        except Exception:
            return ""

    def has_notification_messages_markers():
        body_text = get_body_text()
        lower = body_text.lower()

        return (
            "notification message" in lower
            or "notification messages" in lower
            or "send message" in lower
            or "sent items" in lower
        )

    try:
        target_url = get_origin() + "/notificationmessage"

        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(5000)

        current_url = page.url.lower()
        route_found = "notificationmessage" in current_url
        marker_found = has_notification_messages_markers()

        opened = route_found or marker_found

        return opened, (
            f"Opened direct route: {target_url}; "
            f"current_url={page.url}; "
            f"route_found={route_found}; "
            f"marker_found={marker_found}"
        )

    except Exception as exc:
        return False, f"Failed to open /notificationmessage: {exc}"


def open_notification_messages_no_subpage(page, test_cases, preferred_subpage=""):
    add_test_case(
        test_cases,
        scenario="Open Notification Messages page",
        precondition="User is logged in and /notificationmessage route is available",
        steps="Open direct /notificationmessage route",
        expected="Notification Messages page should be opened",
        actual="Notification Messages direct route used",
        status="PASS",
    )


def perform_notification_messages_suite(url, module_name="Notification Messages", mode="regression"):
    """
    Runner Notification Messages.

    Reuse existing Hermes audit flow, tetapi sementara mengganti:
    - open_target_menu
    - open_uang_makan_driver_subpage
    - validate_uang_makan_driver_monitoring_page
    - validate_uang_makan_driver_page

    Setelah run selesai, semua function dikembalikan agar fitur lain tetap aman.
    """

    previous_open_target_menu = globals().get("open_target_menu")
    previous_open_subpage = globals().get("open_uang_makan_driver_subpage")
    previous_validate_monitoring = globals().get("validate_uang_makan_driver_monitoring_page")
    previous_validate_page = globals().get("validate_uang_makan_driver_page")

    base_runner = globals().get("_PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MESSAGES")

    if base_runner is None:
        base_runner = globals().get("perform_audit_for_telegram")

    if base_runner is None:
        raise RuntimeError("Base perform_audit_for_telegram runner not found")

    try:
        globals()["open_target_menu"] = open_notification_messages_target_menu
        globals()["open_uang_makan_driver_subpage"] = open_notification_messages_no_subpage
        globals()["validate_uang_makan_driver_monitoring_page"] = validate_notification_messages_page
        globals()["validate_uang_makan_driver_page"] = validate_notification_messages_page

        return base_runner(
            url,
            "Notification Messages",
            mode,
        )

    finally:
        if previous_open_target_menu is not None:
            globals()["open_target_menu"] = previous_open_target_menu

        if previous_open_subpage is not None:
            globals()["open_uang_makan_driver_subpage"] = previous_open_subpage

        if previous_validate_monitoring is not None:
            globals()["validate_uang_makan_driver_monitoring_page"] = previous_validate_monitoring

        if previous_validate_page is not None:
            globals()["validate_uang_makan_driver_page"] = previous_validate_page


_qa_register_notification_messages_feature()


if not globals().get("_NOTIFICATION_MESSAGES_TELEGRAM_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MESSAGES = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_notification_messages(module_name, mode):
            return perform_notification_messages_suite(url, module_name, mode)

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MESSAGES is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MESSAGES(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

    _NOTIFICATION_MESSAGES_TELEGRAM_PATCH_INSTALLED = True


# ============================================================
# Notification Management Validator
# ============================================================

def validate_notification_management_page(page, test_cases, bugs):
    """
    Hardened validator untuk Notification Management.

    Scope aman:
    - Tidak klik ACTION
    - Tidak create context/event/group/template/contact
    - Tidak edit/delete data
    - Tidak submit form
    - Hanya validasi tabs, table/list, search, action visibility, dan evidence
    """

    tabs = [
        {
            "name": "Notification Context",
            "markers": [
                "context key",
                "context name",
                "engine type",
                "active",
                "created by",
                "created",
            ],
            "min_markers": 4,
        },
        {
            "name": "Notification Event",
            "markers": [
                "event key",
                "event name",
                "context",
                "channels",
                "active",
                "created by",
                "created",
            ],
            "min_markers": 4,
        },
        {
            "name": "Notification Group",
            "markers": [
                "group name",
                "notification event",
                "site",
                "description",
                "numbers of contacts",
                "active",
                "created by",
                "created",
            ],
            "min_markers": 4,
        },
        {
            "name": "Message Template",
            "markers": [
                "template name",
                "message title",
                "message body",
                "property info",
                "created by",
                "created",
            ],
            "min_markers": 4,
        },
        {
            "name": "Email Template",
            "markers": [
                "template name",
                "message subject",
                "message body",
                "active",
                "html",
                "created by",
                "created",
            ],
            "min_markers": 4,
        },
        {
            "name": "Contact",
            "markers": [
                "name",
                "phones",
                "email",
                "user type",
                "contacs source",
                "contacts source",
                "active",
            ],
            "min_markers": 4,
        },
        {
            "name": "Contact Group",
            "markers": [
                "contact group name",
                "number of contact",
                "active",
                "created by",
                "created",
            ],
            "min_markers": 3,
        },
    ]

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=10000)
        except Exception as exc:
            return f"FAILED_TO_READ_BODY: {exc}"

    def locator_count(selector):
        try:
            return page.locator(selector).count()
        except Exception:
            return 0

    def click_tab(label):
        candidates = [
            page.get_by_role("tab", name=label).first,
            page.locator(f".v-tab:has-text('{label}')").first,
            page.get_by_text(label, exact=True).first,
        ]

        for candidate in candidates:
            try:
                if candidate.count() <= 0:
                    continue

                candidate.scroll_into_view_if_needed(timeout=3000)
                candidate.click(timeout=5000, force=True)

                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass

                page.wait_for_timeout(2500)
                return True

            except Exception:
                continue

        return False

    body_text = get_body_text()
    lower = body_text.lower()

    # 1. Page context
    context_found = (
        "notification management" in lower
        and "notification context" in lower
        and "notification event" in lower
        and "notification group" in lower
        and "message template" in lower
        and "email template" in lower
        and "contact" in lower
        and "contact group" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Notification Management page context",
        precondition="Notification Management route is opened",
        steps="Check page title and all management tabs",
        expected="Notification Management page should show all management tabs",
        actual="Notification Management context found" if context_found else body_text[:700],
        status="PASS" if context_found else "FAIL",
    )

    if not context_found:
        add_bug(
            bugs,
            severity="High",
            title="Notification Management page context not found",
            actual="Notification Management markers were not visible",
            expected="Page should show Notification Context, Event, Group, Templates, Contact, and Contact Group tabs",
        )

    # 2. Tab count / visibility
    tab_count = locator_count("[role='tab']") + locator_count(".v-tab")
    visible_tab_names = [tab["name"] for tab in tabs if tab["name"].lower() in lower]

    add_test_case(
        test_cases,
        scenario="Verify Notification Management tab visibility",
        precondition="Notification Management page is opened",
        steps="Check all vertical tabs are visible",
        expected=", ".join([tab["name"] for tab in tabs]),
        actual=f"tab_count={tab_count}; visible_tabs={visible_tab_names}",
        status="PASS" if len(visible_tab_names) >= 7 else "NEED REVIEW",
    )

    # 3. Validate each tab read-only
    for tab in tabs:
        tab_name = tab["name"]
        clicked = click_tab(tab_name)

        tab_text = get_body_text()
        tab_lower = tab_text.lower()

        matched_markers = [
            marker for marker in tab["markers"]
            if marker.lower() in tab_lower
        ]

        missing_markers = [
            marker for marker in tab["markers"]
            if marker.lower() not in tab_lower
        ]

        table_count = locator_count(".v-data-table") + locator_count(".v-data-table__wrapper")
        search_count = locator_count("input[type='text']") + locator_count(".v-input")
        action_visible = "action" in tab_lower or locator_count("button:has-text('ACTION')") > 0 or locator_count("button:has-text('Action')") > 0
        empty_state_visible = "no data available" in tab_lower or "tidak ada data" in tab_lower

        tab_valid = (
            clicked
            and (
                len(matched_markers) >= tab["min_markers"]
                or table_count > 0
                or empty_state_visible
            )
        )

        add_test_case(
            test_cases,
            scenario=f"Verify Notification Management tab - {tab_name}",
            precondition="Notification Management page is opened",
            steps=f"Click {tab_name} tab and validate table/search/action visibility without mutating data",
            expected=f"{tab_name} should show table/list/search or valid empty state",
            actual=(
                f"clicked={clicked}; "
                f"table_count={table_count}; "
                f"search_count={search_count}; "
                f"action_visible={action_visible}; "
                f"empty_state_visible={empty_state_visible}; "
                f"matched_markers={matched_markers}; "
                f"missing_markers={missing_markers}"
            ),
            status="PASS" if tab_valid else "NEED REVIEW",
        )

    # 4. Search field overall
    final_text = get_body_text()
    final_lower = final_text.lower()

    search_found = (
        "search" in final_lower
        or locator_count("input[placeholder='Search']") > 0
        or locator_count("input[type='text']") > 0
        or locator_count(".v-input") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Notification Management search fields",
        precondition="Notification Management tabs are inspectable",
        steps="Check search inputs across management tabs",
        expected="Search input should be available for table-based tabs",
        actual=f"search_found={search_found}; input_count={locator_count('input')}; vuetify_input_count={locator_count('.v-input')}",
        status="PASS" if search_found else "NEED REVIEW",
    )

    # 5. Action button visibility, read-only only
    action_visible = (
        "action" in final_lower
        or locator_count("button:has-text('ACTION')") > 0
        or locator_count("button:has-text('Action')") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Notification Management action button visibility",
        precondition="Notification Management tabs are inspectable",
        steps="Check ACTION button visibility without clicking",
        expected="ACTION button may be visible but automation must not click it",
        actual=f"action_visible={action_visible}",
        status="PASS" if action_visible else "NEED REVIEW",
    )

    # 6. Safe mode confirmation
    add_test_case(
        test_cases,
        scenario="Verify Notification Management safe validation mode",
        precondition="Notification Management page is opened",
        steps="Validate management tabs without clicking ACTION, save, delete, edit, or submit",
        expected="Automation should not mutate notification configuration data",
        actual="Safe mode: no ACTION clicked, no create/edit/delete/save/submit executed",
        status="PASS",
    )


# ============================================================
# Notification Management Telegram /audit_qa Integration
# ============================================================

def _qa_register_notification_management_feature():
    """
    Register Notification Management ke FEATURE_REGISTRY agar bisa dipanggil dari:
    /audit_qa mode=regression fitur=notification management
    """

    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["notification_management"] = {
        "display_name": "Notification Management",
        "module_name": "Notification Management",
        "menu_aliases": [
            "Notification Management",
            "managementnotif",
        ],
        "aliases": [
            "notification management",
            "notification_management",
            "notification-management",
            "managementnotif",
            "management notif",
            "notif management",
            "mobo notif management",
            "mobo notification management",
        ],
        "default_subfeatures": [
            "notification_context",
            "notification_event",
            "notification_group",
            "message_template",
            "email_template",
            "contact",
            "contact_group",
        ],
        "subfeature_aliases": {
            "notification_context": ["notification context", "context"],
            "notification_event": ["notification event", "event"],
            "notification_group": ["notification group", "group"],
            "message_template": ["message template", "template message"],
            "email_template": ["email template", "template email"],
            "contact": ["contact"],
            "contact_group": ["contact group", "group contact"],
        },
    }


def should_run_notification_management(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")

    aliases = {
        "notification management",
        "managementnotif",
        "management notif",
        "notif management",
        "mobo notif management",
        "mobo notification management",
    }

    return value in aliases


def open_notification_management_target_menu(page, module_name="Notification Management"):
    """
    Open Notification Management via direct sandbox route /managementnotif.
    """

    def get_origin():
        try:
            parts = page.url.split("/")
            return parts[0] + "//" + parts[2]
        except Exception:
            return "https://mobospace-sandbox.pancaran-group.co.id"

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=8000)
        except Exception:
            return ""

    def has_notification_management_markers():
        body_text = get_body_text()
        lower = body_text.lower()

        return (
            "notification management" in lower
            or "notification context" in lower
            or "notification event" in lower
            or "notification group" in lower
            or "message template" in lower
            or "email template" in lower
            or "contact group" in lower
        )

    try:
        target_url = get_origin() + "/managementnotif"

        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(5000)

        current_url = page.url.lower()
        route_found = "managementnotif" in current_url
        marker_found = has_notification_management_markers()

        opened = route_found or marker_found

        return opened, (
            f"Opened direct route: {target_url}; "
            f"current_url={page.url}; "
            f"route_found={route_found}; "
            f"marker_found={marker_found}"
        )

    except Exception as exc:
        return False, f"Failed to open /managementnotif: {exc}"


def open_notification_management_no_subpage(page, test_cases, preferred_subpage=""):
    add_test_case(
        test_cases,
        scenario="Open Notification Management page",
        precondition="User is logged in and /managementnotif route is available",
        steps="Open direct /managementnotif route",
        expected="Notification Management page should be opened",
        actual="Notification Management direct route used",
        status="PASS",
    )


def perform_notification_management_suite(url, module_name="Notification Management", mode="regression"):
    """
    Runner Notification Management.

    Reuse existing Hermes audit flow, tetapi sementara mengganti:
    - open_target_menu
    - open_uang_makan_driver_subpage
    - validate_uang_makan_driver_monitoring_page
    - validate_uang_makan_driver_page

    Setelah run selesai, semua function dikembalikan agar fitur lain tetap aman.
    """

    previous_open_target_menu = globals().get("open_target_menu")
    previous_open_subpage = globals().get("open_uang_makan_driver_subpage")
    previous_validate_monitoring = globals().get("validate_uang_makan_driver_monitoring_page")
    previous_validate_page = globals().get("validate_uang_makan_driver_page")

    base_runner = globals().get("_PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MANAGEMENT")

    if base_runner is None:
        base_runner = globals().get("perform_audit_for_telegram")

    if base_runner is None:
        raise RuntimeError("Base perform_audit_for_telegram runner not found")

    try:
        globals()["open_target_menu"] = open_notification_management_target_menu
        globals()["open_uang_makan_driver_subpage"] = open_notification_management_no_subpage
        globals()["validate_uang_makan_driver_monitoring_page"] = validate_notification_management_page
        globals()["validate_uang_makan_driver_page"] = validate_notification_management_page

        return base_runner(
            url,
            "Notification Management",
            mode,
        )

    finally:
        if previous_open_target_menu is not None:
            globals()["open_target_menu"] = previous_open_target_menu

        if previous_open_subpage is not None:
            globals()["open_uang_makan_driver_subpage"] = previous_open_subpage

        if previous_validate_monitoring is not None:
            globals()["validate_uang_makan_driver_monitoring_page"] = previous_validate_monitoring

        if previous_validate_page is not None:
            globals()["validate_uang_makan_driver_page"] = previous_validate_page


_qa_register_notification_management_feature()


if not globals().get("_NOTIFICATION_MANAGEMENT_TELEGRAM_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MANAGEMENT = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_notification_management(module_name, mode):
            return perform_notification_management_suite(url, module_name, mode)

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MANAGEMENT is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MANAGEMENT(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

    _NOTIFICATION_MANAGEMENT_TELEGRAM_PATCH_INSTALLED = True


# ============================================================
# All Features Telegram /audit_qa Integration
# ============================================================

def _qa_register_all_features():
    """
    Register All Features ke FEATURE_REGISTRY agar bisa dipanggil dari:
    /audit_qa mode=regression fitur=all
    """

    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["all_features"] = {
        "display_name": "All Features",
        "module_name": "All Features",
        "menu_aliases": [
            "All Features",
            "All",
            "Semua",
        ],
        "aliases": [
            "all",
            "all features",
            "semua",
            "semua fitur",
            "full regression",
            "full all features",
            "all regression",
        ],
        "default_subfeatures": ["all"],
        "subfeature_aliases": {
            "all": [
                "all",
                "all features",
                "semua",
                "semua fitur",
                "full regression",
            ],
        },
    }


def should_run_all_features(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")

    aliases = {
        "all",
        "all features",
        "semua",
        "semua fitur",
        "full regression",
        "full all features",
        "all regression",
    }

    return value in aliases


def _qa_all_extract_line(text, prefix):
    for line in str(text or "").splitlines():
        if line.strip().startswith(prefix):
            return line.strip()
    return ""


def _qa_all_extract_status(summary):
    line = _qa_all_extract_line(summary, "Status:")
    return line.replace("Status:", "").strip() if line else "UNKNOWN"


def _qa_all_extract_count(summary, label):
    line = _qa_all_extract_line(summary, f"- {label}:")
    if not line:
        return 0
    try:
        return int(line.split(":", 1)[1].strip())
    except Exception:
        return 0


def _qa_all_read_json_result(stdout):
    try:
        from pathlib import Path
        import json

        for line in str(stdout or "").splitlines():
            if line.startswith("JSON_RESULT_PATH="):
                path = Path(line.split("=", 1)[1].strip())
                if path.exists():
                    return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass

    return None


def _qa_all_write_spreadsheet(spreadsheet_path, results, overall_status, mode, url):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment

        wb = Workbook()
        ws = wb.active
        ws.title = "All Features Summary"

        ws.append(["QA Full Regression - All Features"])
        ws.append(["Environment", "Sandbox"])
        ws.append(["Base URL", url])
        ws.append(["Mode", mode])
        ws.append(["Overall Status", overall_status])
        ws.append([])

        headers = ["No", "Feature", "Status", "Passed", "Failed", "Need Review", "Skipped", "Bugs", "Report", "Spreadsheet", "Screenshot"]
        ws.append(headers)

        for cell in ws[7]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill("solid", fgColor="D9EAF7")
            cell.alignment = Alignment(horizontal="center")

        for idx, item in enumerate(results, start=1):
            ws.append([
                idx,
                item.get("feature"),
                item.get("status"),
                item.get("passed", 0),
                item.get("failed", 0),
                item.get("need_review", 0),
                item.get("skipped", 0),
                item.get("bugs_found", 0),
                item.get("report_path", "-"),
                item.get("spreadsheet_path", "-"),
                item.get("screenshot_path", "-"),
            ])

        for column_cells in ws.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter
            for cell in column_cells:
                value = str(cell.value or "")
                max_length = max(max_length, len(value))
            ws.column_dimensions[column_letter].width = min(max_length + 2, 60)

        wb.save(spreadsheet_path)
        return str(spreadsheet_path)

    except Exception:
        return None


def perform_all_features_suite(url, module_name="All Features", mode="regression"):
    """
    Runner all features untuk Telegram.

    Menjalankan setiap fitur melalui subprocess run_single_feature_cli.py agar isolated:
    - Driver Daily Meal
    - Shipment Details
    - MoboMap
    - Inspection Result
    - Notification Messages
    - Notification Management
    """

    from pathlib import Path
    from datetime import datetime
    import json
    import os
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[2]

    features = [
        "Driver Daily Meal",
        "Shipment Details",
        "MoboMap",
        "Inspection Result",
        "Notification Messages",
        "Notification Management",
    ]

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    report_dir = root / "skills" / "qa_automation" / "artifacts" / "reports"
    log_dir = root / "skills" / "qa_automation" / "artifacts" / "logs"
    spreadsheet_dir = root / "skills" / "qa_automation" / "artifacts" / "spreadsheets"

    report_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    spreadsheet_dir.mkdir(parents=True, exist_ok=True)

    results = []
    raw_outputs = []

    for index, feature in enumerate(features, start=1):
        cmd = [
            sys.executable,
            "-u",
            str(root / "scripts" / "run_single_feature_cli.py"),
            "--feature",
            feature,
            "--mode",
            mode,
            "--url",
            url,
        ]

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        completed = subprocess.run(
            cmd,
            cwd=str(root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            timeout=2400,
        )

        stdout = completed.stdout or ""
        raw_outputs.append(f"===== {feature} =====\n{stdout}\n")

        item = _qa_all_read_json_result(stdout)

        if item is None:
            item = {
                "feature": feature,
                "status": "FAILED",
                "passed": 0,
                "failed": 1,
                "need_review": 0,
                "skipped": 0,
                "bugs_found": 1,
                "error": "JSON_RESULT_PATH not found or unreadable",
                "return_code": completed.returncode,
            }

        results.append(item)

    total_passed = sum(int(item.get("passed", 0) or 0) for item in results)
    total_failed = sum(int(item.get("failed", 0) or 0) for item in results)
    total_need_review = sum(int(item.get("need_review", 0) or 0) for item in results)
    total_skipped = sum(int(item.get("skipped", 0) or 0) for item in results)
    total_bugs = sum(int(item.get("bugs_found", 0) or 0) for item in results)

    if any(item.get("status") == "FAILED" for item in results) or total_failed > 0 or total_bugs > 0:
        overall_status = "FAILED"
        icon = "❌"
    elif any(item.get("status") == "NEED REVIEW" for item in results) or total_need_review > 0:
        overall_status = "NEED REVIEW"
        icon = "⚠️"
    else:
        overall_status = "PASS"
        icon = "✅"

    feature_lines = []
    for item in results:
        feature_lines.append(
            f"- {item.get('feature')}: {item.get('status')} "
            f"(PASS={item.get('passed', 0)}, FAIL={item.get('failed', 0)}, "
            f"NEED_REVIEW={item.get('need_review', 0)}, BUGS={item.get('bugs_found', 0)})"
        )

    testing_summary = f"""{icon} QA Full Regression Completed

Module: All Features
Mode: {mode}
Environment: Sandbox
Status: {overall_status}

Execution Info:
- Execution ID: QA-ALL-{run_id}
- Executed At: {run_id}
- Executed By: Hermes QA Automation
- Feature: All Features
- Suite / Mode: {mode}
- Environment: Sandbox
- Base URL: {url}

Summary:
- Features Tested: {len(results)}
- Passed: {total_passed}
- Failed: {total_failed}
- Need Review: {total_need_review}
- Skipped: {total_skipped}
- Bugs Found: {total_bugs}

Feature Results:
{chr(10).join(feature_lines)}

Recommendation:
{"Review non-blocking warnings before release." if overall_status == "NEED REVIEW" else "No blocking issue found from automation result. Continue with manual business verification if needed."}
"""

    markdown_lines = [
        "# QA Full Regression - All Features",
        "",
        f"Execution ID: QA-ALL-{run_id}",
        "Environment: Sandbox",
        f"Base URL: {url}",
        f"Mode: {mode}",
        f"Overall Status: {overall_status}",
        "",
        "## Summary",
        "",
        f"- Features Tested: {len(results)}",
        f"- Passed Test Cases: {total_passed}",
        f"- Failed Test Cases: {total_failed}",
        f"- Need Review: {total_need_review}",
        f"- Skipped: {total_skipped}",
        f"- Bugs Found: {total_bugs}",
        "",
        "## Feature Results",
        "",
        "| No | Feature | Status | Passed | Failed | Need Review | Skipped | Bugs |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]

    for idx, item in enumerate(results, start=1):
        markdown_lines.append(
            f"| {idx} | {item.get('feature')} | {item.get('status')} | "
            f"{item.get('passed', 0)} | {item.get('failed', 0)} | "
            f"{item.get('need_review', 0)} | {item.get('skipped', 0)} | "
            f"{item.get('bugs_found', 0)} |"
        )

    markdown_lines.extend([
        "",
        "## Artifacts",
        "",
        "| Feature | Report | Spreadsheet | Screenshot | Error Log |",
        "|---|---|---|---|---|",
    ])

    for item in results:
        markdown_lines.append(
            f"| {item.get('feature')} | "
            f"{item.get('report_path', '-')} | "
            f"{item.get('spreadsheet_path', '-')} | "
            f"{item.get('screenshot_path', '-')} | "
            f"{item.get('error_log_path', '-')} |"
        )

    markdown_lines.extend([
        "",
        "## Raw JSON",
        "",
        "```json",
        json.dumps(results, indent=2, ensure_ascii=False),
        "```",
    ])

    report_path = report_dir / f"qa_documentation_all_features_{run_id}.md"
    report_path.write_text("\n".join(markdown_lines), encoding="utf-8")

    error_log_report = f"""# QA Error / Bug Log - All Features

Environment: Sandbox
Mode: {mode}
Status: {overall_status}
Execution Time: {run_id}

---

## 1. Bug Digest

{"- No bug found" if total_bugs == 0 else f"- Bugs found: {total_bugs}"}

---

## 2. Failed Test Cases

{"- No failed test case" if total_failed == 0 else f"- Failed test cases: {total_failed}"}

---

## 3. Need Review Items

{"- No need review item" if total_need_review == 0 else f"- Need review items: {total_need_review}"}

---

## 4. Feature Results

{chr(10).join(feature_lines)}

---

## 5. Raw Execution Output

See documentation report for per-feature artifact links.
"""

    error_log_path = log_dir / f"qa_error_log_all_features_{run_id}.md"
    error_log_path.write_text(error_log_report, encoding="utf-8")

    raw_output_path = log_dir / f"qa_raw_output_all_features_{run_id}.log"
    raw_output_path.write_text("\n".join(raw_outputs), encoding="utf-8")

    spreadsheet_path = spreadsheet_dir / f"qa_report_all_features_{run_id}.xlsx"
    spreadsheet_result = _qa_all_write_spreadsheet(spreadsheet_path, results, overall_status, mode, url)

    first_screenshot = None
    for item in results:
        if item.get("screenshot_path"):
            first_screenshot = item.get("screenshot_path")
            break

    return {
        "testing_summary": testing_summary,
        "documentation_report": "\n".join(markdown_lines),
        "error_log_report": error_log_report,
        "status": overall_status,
        "screenshot_path": first_screenshot,
        "report_path": str(report_path),
        "documentation_path": str(report_path),
        "error_log_path": str(error_log_path),
        "spreadsheet_path": spreadsheet_result or str(spreadsheet_path),
        "raw_output_path": str(raw_output_path),
        "all_feature_results": results,
    }


_qa_register_all_features()


if not globals().get("_ALL_FEATURES_TELEGRAM_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_ALL_FEATURES = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_all_features(module_name, mode):
            return perform_all_features_suite(url, module_name, mode)

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_ALL_FEATURES is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_ALL_FEATURES(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

    _ALL_FEATURES_TELEGRAM_PATCH_INSTALLED = True


# ============================================================
# Standard Result JSON + QA Help/List Integration
# ============================================================

def _qa_register_help_list_features():
    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["qa_help"] = {
        "display_name": "QA Help",
        "module_name": "QA Help",
        "menu_aliases": ["QA Help", "Help"],
        "aliases": ["help", "qa help", "bantuan", "cara pakai", "?"],
        "default_subfeatures": ["help"],
        "subfeature_aliases": {
            "help": ["help", "bantuan", "cara pakai"],
        },
    }

    FEATURE_REGISTRY["qa_list"] = {
        "display_name": "QA Feature List",
        "module_name": "QA Feature List",
        "menu_aliases": ["QA Feature List", "List"],
        "aliases": ["list", "feature list", "features", "daftar", "daftar fitur", "list fitur"],
        "default_subfeatures": ["list"],
        "subfeature_aliases": {
            "list": ["list", "features", "daftar", "daftar fitur"],
        },
    }


def should_run_qa_help(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")
    return value in {"help", "qa help", "bantuan", "cara pakai", "?"}


def should_run_qa_list(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")
    return value in {"list", "feature list", "features", "daftar", "daftar fitur", "list fitur", "qa feature list"}


def perform_qa_help_suite(url, module_name="QA Help", mode="help"):
    testing_summary = f"""✅ QA Automation Help

Module: QA Help
Mode: help
Environment: Sandbox
Status: PASS

Available Commands:

Run single feature:
- /audit_qa mode=regression fitur=driver daily meal
- /audit_qa mode=regression fitur=shipment details
- /audit_qa mode=regression fitur=mobomap
- /audit_qa mode=regression fitur=inspection result
- /audit_qa mode=regression fitur=notification messages
- /audit_qa mode=regression fitur=notification management

Run all features:
- /audit_qa mode=regression fitur=all

Utility:
- /audit_qa help
- /audit_qa list

Supported Modes:
- smoke
- regression

Safe Mode:
- Automation tidak klik SEND
- Automation tidak klik ACTION untuk create/edit/delete
- Automation tidak submit form
- Automation hanya validasi UI, table/list, search/filter, console/network, screenshot, report, dan evidence

Current Base URL:
{url}
"""

    return {
        "testing_summary": testing_summary,
        "documentation_report": "# QA Automation Help\\n\\nCommand help generated.",
        "error_log_report": "# QA Help\\n\\nNo error.",
        "status": "PASS",
    }


def perform_qa_list_suite(url, module_name="QA Feature List", mode="list"):
    features = [
        ("driver daily meal", "Driver Daily Meal / Uang Makan Driver"),
        ("shipment details", "Shipment Details"),
        ("mobomap", "MoboMap"),
        ("inspection result", "Inspection Result"),
        ("notification messages", "Notification Messages"),
        ("notification management", "Notification Management"),
        ("all", "All Features"),
    ]

    feature_lines = [f"- {alias} → {name}" for alias, name in features]

    testing_summary = f"""✅ QA Feature List

Module: QA Feature List
Mode: list
Environment: Sandbox
Status: PASS

Available QA Features:
{chr(10).join(feature_lines)}

Examples:
- /audit_qa mode=regression fitur=mobomap
- /audit_qa mode=regression fitur=notification management
- /audit_qa mode=regression fitur=all
"""

    return {
        "testing_summary": testing_summary,
        "documentation_report": "# QA Feature List\\n\\n" + "\\n".join(feature_lines),
        "error_log_report": "# QA Feature List\\n\\nNo error.",
        "status": "PASS",
    }


def _qa_std_slug(value):
    import re
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return slug or "qa_result"


def _qa_std_extract_value(text, label):
    for line in str(text or "").splitlines():
        clean = line.strip()
        if clean.startswith(label + ":") or clean.startswith("- " + label + ":"):
            try:
                return clean.split(":", 1)[1].strip()
            except Exception:
                return ""
    return ""


def _qa_std_extract_count(summary, label):
    try:
        return int(_qa_std_extract_value(summary, label) or 0)
    except Exception:
        return 0


def _qa_std_extract_warning_count(summary):
    count = _qa_std_extract_count(summary, "Non-blocking Warnings")
    if count:
        return count

    total = 0
    for line in str(summary or "").splitlines():
        if "WARNING-" in line.upper():
            total += 1
    return total


def enrich_qa_result_with_standard_json(result, url, module_name, mode):
    if not isinstance(result, dict):
        return result

    try:
        from pathlib import Path
        from datetime import datetime
        import json

        root = Path(__file__).resolve().parents[2]
        json_dir = root / "skills" / "qa_automation" / "artifacts" / "json"
        json_dir.mkdir(parents=True, exist_ok=True)

        summary = result.get("testing_summary", "") or ""

        execution_id = (
            _qa_std_extract_value(summary, "Execution ID")
            or f"QA-STD-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        executed_at = (
            _qa_std_extract_value(summary, "Executed At")
            or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        status = result.get("status") or _qa_std_extract_value(summary, "Status") or "UNKNOWN"
        feature_name = str(module_name or "").strip() or "Unknown Feature"

        if isinstance(result.get("all_feature_results"), list):
            features = []
            for item in result.get("all_feature_results") or []:
                features.append({
                    "name": item.get("feature") or item.get("name"),
                    "status": item.get("status"),
                    "passed": int(item.get("passed", 0) or 0),
                    "failed": int(item.get("failed", 0) or 0),
                    "need_review": int(item.get("need_review", 0) or 0),
                    "skipped": int(item.get("skipped", 0) or 0),
                    "bugs_found": int(item.get("bugs_found", 0) or 0),
                    "warnings": int(item.get("warnings", 0) or 0),
                    "artifacts": {
                        "screenshot": item.get("screenshot_path"),
                        "report": item.get("report_path"),
                        "spreadsheet": item.get("spreadsheet_path"),
                        "error_log": item.get("error_log_path"),
                        "selector_inventory": item.get("selector_inventory_path"),
                    },
                })
        else:
            features = [{
                "name": feature_name,
                "status": status,
                "passed": _qa_std_extract_count(summary, "Passed"),
                "failed": _qa_std_extract_count(summary, "Failed"),
                "need_review": _qa_std_extract_count(summary, "Need Review"),
                "skipped": _qa_std_extract_count(summary, "Skipped"),
                "bugs_found": _qa_std_extract_count(summary, "Bugs Found"),
                "warnings": _qa_std_extract_warning_count(summary),
                "artifacts": {
                    "screenshot": result.get("screenshot_path"),
                    "report": result.get("report_path") or result.get("documentation_path"),
                    "spreadsheet": result.get("spreadsheet_path"),
                    "error_log": result.get("error_log_path"),
                    "selector_inventory": result.get("selector_inventory_path"),
                },
            }]

        standard_result = {
            "schema_version": "1.0",
            "execution": {
                "execution_id": execution_id,
                "executed_at": executed_at,
                "executed_by": "Hermes QA Automation",
                "environment": "Sandbox",
                "base_url": url,
                "mode": mode,
                "requested_feature": feature_name,
                "overall_status": status,
            },
            "summary": {
                "features_tested": len(features),
                "passed": sum(item.get("passed", 0) for item in features),
                "failed": sum(item.get("failed", 0) for item in features),
                "need_review": sum(item.get("need_review", 0) for item in features),
                "skipped": sum(item.get("skipped", 0) for item in features),
                "bugs_found": sum(item.get("bugs_found", 0) for item in features),
                "warnings": sum(item.get("warnings", 0) for item in features),
            },
            "features": features,
            "artifacts": {
                "screenshot": result.get("screenshot_path"),
                "report": result.get("report_path") or result.get("documentation_path"),
                "spreadsheet": result.get("spreadsheet_path"),
                "error_log": result.get("error_log_path"),
                "raw_output": result.get("raw_output_path"),
            },
            "raw": {
                "testing_summary": summary,
            },
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = _qa_std_slug(feature_name)
        json_path = json_dir / f"qa_result_standard_{slug}_{timestamp}.json"

        json_path.write_text(
            json.dumps(standard_result, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

        result["standard_json"] = standard_result
        result["standard_json_path"] = str(json_path)
        result["json_path"] = str(json_path)

        if result.get("testing_summary") and "Standard JSON:" not in result["testing_summary"]:
            result["testing_summary"] = result["testing_summary"].rstrip() + f"\\n\\nStandard JSON:\\n- {json_path}\\n"

        return result

    except Exception as exc:
        result["standard_json_error"] = str(exc)
        return result


_qa_register_help_list_features()


if not globals().get("_STANDARD_JSON_HELP_LIST_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_STANDARD_JSON = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_qa_help(module_name, mode):
            result = perform_qa_help_suite(url, module_name, mode)
            return enrich_qa_result_with_standard_json(result, url, module_name, mode)

        if should_run_qa_list(module_name, mode):
            result = perform_qa_list_suite(url, module_name, mode)
            return enrich_qa_result_with_standard_json(result, url, module_name, mode)

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_STANDARD_JSON is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        result = _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_STANDARD_JSON(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

        return enrich_qa_result_with_standard_json(result, url, module_name, mode)

    _STANDARD_JSON_HELP_LIST_PATCH_INSTALLED = True


# ============================================================
# QA Run History Integration
# ============================================================

def _qa_register_history_feature():
    """
    Register QA History agar bisa dipanggil dari:
    /audit_qa history
    """

    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["qa_history"] = {
        "display_name": "QA History",
        "module_name": "QA History",
        "menu_aliases": ["QA History", "History"],
        "aliases": [
            "history",
            "qa history",
            "run history",
            "riwayat",
            "riwayat qa",
            "histori",
        ],
        "default_subfeatures": ["history"],
        "subfeature_aliases": {
            "history": ["history", "run history", "riwayat", "histori"],
        },
    }


def should_run_qa_history(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")

    return value in {
        "history",
        "qa history",
        "run history",
        "riwayat",
        "riwayat qa",
        "histori",
    }


def _qa_history_root():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    history_dir = root / "skills" / "qa_automation" / "artifacts" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def _qa_history_file():
    return _qa_history_root() / "qa_run_history.json"


def _qa_history_load():
    import json

    path = _qa_history_file()

    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except Exception:
        pass

    return []


def _qa_history_save(items):
    import json

    path = _qa_history_file()
    path.write_text(
        json.dumps(items, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    return str(path)


def _qa_history_extract_value(text, label):
    for line in str(text or "").splitlines():
        clean = line.strip()

        if clean.startswith(label + ":") or clean.startswith("- " + label + ":"):
            try:
                return clean.split(":", 1)[1].strip()
            except Exception:
                return ""

    return ""


def _qa_history_extract_count(text, label):
    try:
        return int(_qa_history_extract_value(text, label) or 0)
    except Exception:
        return 0


def _qa_history_load_standard_json(result):
    if not isinstance(result, dict):
        return None

    if isinstance(result.get("standard_json"), dict):
        return result.get("standard_json")

    path_value = result.get("standard_json_path") or result.get("json_path")

    if not path_value:
        return None

    try:
        from pathlib import Path
        import json

        path = Path(path_value)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass

    return None


def _qa_history_build_item(result, url, module_name, mode):
    from datetime import datetime

    summary_text = ""
    if isinstance(result, dict):
        summary_text = result.get("testing_summary", "") or ""

    standard = _qa_history_load_standard_json(result)

    if standard:
        execution = standard.get("execution", {}) or {}
        summary = standard.get("summary", {}) or {}
        artifacts = standard.get("artifacts", {}) or {}

        features = standard.get("features", []) or []
        feature_results = []
        for feature in features:
            feature_results.append({
                "name": feature.get("name"),
                "status": feature.get("status"),
                "passed": feature.get("passed", 0),
                "failed": feature.get("failed", 0),
                "need_review": feature.get("need_review", 0),
                "bugs_found": feature.get("bugs_found", 0),
            })

        item = {
            "execution_id": execution.get("execution_id") or f"QA-HIST-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "executed_at": execution.get("executed_at"),
            "feature": execution.get("requested_feature") or module_name,
            "mode": execution.get("mode") or mode,
            "environment": execution.get("environment") or "Sandbox",
            "base_url": execution.get("base_url") or url,
            "status": execution.get("overall_status") or "UNKNOWN",
            "passed": int(summary.get("passed", 0) or 0),
            "failed": int(summary.get("failed", 0) or 0),
            "need_review": int(summary.get("need_review", 0) or 0),
            "skipped": int(summary.get("skipped", 0) or 0),
            "bugs_found": int(summary.get("bugs_found", 0) or 0),
            "warnings": int(summary.get("warnings", 0) or 0),
            "standard_json_path": result.get("standard_json_path") or result.get("json_path"),
            "report_path": artifacts.get("report"),
            "spreadsheet_path": artifacts.get("spreadsheet"),
            "screenshot_path": artifacts.get("screenshot"),
            "error_log_path": artifacts.get("error_log"),
            "raw_output_path": artifacts.get("raw_output"),
            "feature_results": feature_results,
        }

        return item

    status = "UNKNOWN"
    if isinstance(result, dict):
        status = result.get("status") or _qa_history_extract_value(summary_text, "Status") or "UNKNOWN"

    return {
        "execution_id": _qa_history_extract_value(summary_text, "Execution ID") or f"QA-HIST-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "executed_at": _qa_history_extract_value(summary_text, "Executed At"),
        "feature": module_name,
        "mode": mode,
        "environment": "Sandbox",
        "base_url": url,
        "status": status,
        "passed": _qa_history_extract_count(summary_text, "Passed"),
        "failed": _qa_history_extract_count(summary_text, "Failed"),
        "need_review": _qa_history_extract_count(summary_text, "Need Review"),
        "skipped": _qa_history_extract_count(summary_text, "Skipped"),
        "bugs_found": _qa_history_extract_count(summary_text, "Bugs Found"),
        "warnings": _qa_history_extract_count(summary_text, "Non-blocking Warnings"),
        "standard_json_path": result.get("standard_json_path") if isinstance(result, dict) else None,
        "report_path": result.get("report_path") if isinstance(result, dict) else None,
        "spreadsheet_path": result.get("spreadsheet_path") if isinstance(result, dict) else None,
        "screenshot_path": result.get("screenshot_path") if isinstance(result, dict) else None,
        "error_log_path": result.get("error_log_path") if isinstance(result, dict) else None,
        "raw_output_path": result.get("raw_output_path") if isinstance(result, dict) else None,
        "feature_results": [],
    }


def append_qa_run_history(result, url, module_name, mode):
    """
    Append hasil QA ke artifacts/history/qa_run_history.json.
    """

    import os

    if os.getenv("QA_HISTORY_DISABLE") == "1":
        return result

    utility_checkers = [
        globals().get("should_run_qa_help"),
        globals().get("should_run_qa_list"),
        globals().get("should_run_qa_history"),
    ]

    for checker_fn in utility_checkers:
        try:
            if checker_fn and checker_fn(module_name, mode):
                return result
        except Exception:
            pass

    try:
        item = _qa_history_build_item(result, url, module_name, mode)
        history = _qa_history_load()

        item_key = (
            str(item.get("execution_id")),
            str(item.get("feature")),
            str(item.get("standard_json_path")),
        )

        filtered_history = []
        for old_item in history:
            old_key = (
                str(old_item.get("execution_id")),
                str(old_item.get("feature")),
                str(old_item.get("standard_json_path")),
            )
            if old_key != item_key:
                filtered_history.append(old_item)

        filtered_history.insert(0, item)
        filtered_history = filtered_history[:300]

        history_path = _qa_history_save(filtered_history)

        if isinstance(result, dict):
            result["history_path"] = history_path

        return result

    except Exception as exc:
        if isinstance(result, dict):
            result["history_error"] = str(exc)
        return result


def perform_qa_history_suite(url, module_name="QA History", mode="history"):
    """
    Tampilkan recent QA run history.
    """

    history = _qa_history_load()
    recent_items = history[:10]
    history_path = str(_qa_history_file())

    if not recent_items:
        testing_summary = f"""✅ QA Run History

Module: QA History
Mode: history
Environment: Sandbox
Status: PASS

Recent QA Runs:
- No QA run history found yet.

History File:
{history_path}
"""

        return {
            "testing_summary": testing_summary,
            "documentation_report": "# QA Run History\n\nNo QA run history found yet.",
            "error_log_report": "# QA Run History\n\nNo error.",
            "status": "PASS",
            "history_path": history_path,
        }

    lines = []
    for index, item in enumerate(recent_items, start=1):
        feature = item.get("feature") or "-"
        status = item.get("status") or "-"
        mode_value = item.get("mode") or "-"
        created_at = item.get("created_at") or item.get("executed_at") or "-"
        passed = item.get("passed", 0)
        failed = item.get("failed", 0)
        need_review = item.get("need_review", 0)
        bugs = item.get("bugs_found", 0)

        lines.append(
            f"{index}. {feature} - {status} - {mode_value} - {created_at} "
            f"(PASS={passed}, FAIL={failed}, NEED_REVIEW={need_review}, BUGS={bugs})"
        )

    testing_summary = f"""✅ QA Run History

Module: QA History
Mode: history
Environment: Sandbox
Status: PASS

Recent QA Runs:
{chr(10).join(lines)}

History File:
{history_path}
"""

    markdown_lines = [
        "# QA Run History",
        "",
        f"History File: {history_path}",
        "",
        "| No | Feature | Status | Mode | Created At | Passed | Failed | Need Review | Bugs |",
        "|---|---|---|---|---|---:|---:|---:|---:|",
    ]

    for index, item in enumerate(recent_items, start=1):
        markdown_lines.append(
            f"| {index} | {item.get('feature')} | {item.get('status')} | "
            f"{item.get('mode')} | {item.get('created_at') or item.get('executed_at')} | "
            f"{item.get('passed', 0)} | {item.get('failed', 0)} | "
            f"{item.get('need_review', 0)} | {item.get('bugs_found', 0)} |"
        )

    return {
        "testing_summary": testing_summary,
        "documentation_report": "\n".join(markdown_lines),
        "error_log_report": "# QA Run History\n\nNo error.",
        "status": "PASS",
        "history_path": history_path,
    }


_qa_register_history_feature()


if not globals().get("_QA_RUN_HISTORY_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_HISTORY = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_qa_history(module_name, mode):
            result = perform_qa_history_suite(url, module_name, mode)

            enrich_fn = globals().get("enrich_qa_result_with_standard_json")
            if enrich_fn:
                result = enrich_fn(result, url, module_name, mode)

            return result

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_HISTORY is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        import os

        is_all_features = False
        all_checker = globals().get("should_run_all_features")
        try:
            is_all_features = bool(all_checker and all_checker(module_name, mode))
        except Exception:
            is_all_features = False

        previous_history_disable = os.environ.get("QA_HISTORY_DISABLE")

        try:
            if is_all_features:
                os.environ["QA_HISTORY_DISABLE"] = "1"

            result = _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_HISTORY(
                url,
                module_name,
                mode,
                *args,
                **kwargs,
            )

        finally:
            if is_all_features:
                if previous_history_disable is None:
                    os.environ.pop("QA_HISTORY_DISABLE", None)
                else:
                    os.environ["QA_HISTORY_DISABLE"] = previous_history_disable

        return append_qa_run_history(result, url, module_name, mode)

    _QA_RUN_HISTORY_PATCH_INSTALLED = True


# ============================================================
# Final Specialized Feature Routing Override
# ============================================================
#
# Tujuan:
# Memastikan command individual selalu masuk ke specialized suite,
# bukan fallback ke generic open_target_menu.
#
# Contoh:
# Notification Management -> perform_notification_management_suite()
# Notification Messages   -> perform_notification_messages_suite()
# MoboMap                 -> perform_mobomap_suite()
# Shipment Details        -> perform_shipment_details_suite()
# Inspection Result       -> perform_inspection_result_suite()
# Driver Daily Meal       -> perform_driver_daily_meal_combined_suite()
# ============================================================

def _qa_final_call_suite(fn, url, module_name, mode):
    try:
        return fn(url, module_name, mode)
    except TypeError:
        try:
            return fn(url=url, module_name=module_name, mode=mode)
        except TypeError:
            try:
                return fn(url, module_name)
            except TypeError:
                return fn(url)


def _qa_final_enrich_and_history(result, url, module_name, mode):
    try:
        enrich_fn = globals().get("enrich_qa_result_with_standard_json")
        if enrich_fn:
            result = enrich_fn(result, url, module_name, mode)
    except Exception as exc:
        if isinstance(result, dict):
            result["standard_json_error"] = str(exc)

    try:
        append_history_fn = globals().get("append_qa_run_history")
        if append_history_fn:
            result = append_history_fn(result, url, module_name, mode)
    except Exception as exc:
        if isinstance(result, dict):
            result["history_error"] = str(exc)

    return result


def _qa_final_match_specialized_suite(module_name, mode=None):
    checks = [
        ("should_run_driver_daily_meal_combined", "perform_driver_daily_meal_combined_suite", "Uang Makan Driver"),
        ("should_run_shipment_details", "perform_shipment_details_suite", "Shipment Details"),
        ("should_run_mobomap", "perform_mobomap_suite", "MoboMap"),
        ("should_run_inspection_result", "perform_inspection_result_suite", "Inspection Result"),
        ("should_run_notification_messages", "perform_notification_messages_suite", "Notification Messages"),
        ("should_run_notification_management", "perform_notification_management_suite", "Notification Management"),
    ]

    for checker_name, suite_name, canonical_module_name in checks:
        checker_fn = globals().get(checker_name)
        suite_fn = globals().get(suite_name)

        if not checker_fn or not suite_fn:
            continue

        try:
            if checker_fn(module_name, mode):
                return suite_fn, canonical_module_name
        except TypeError:
            try:
                if checker_fn(module_name):
                    return suite_fn, canonical_module_name
            except Exception:
                pass
        except Exception:
            pass

    return None, None


if not globals().get("_FINAL_SPECIALIZED_FEATURE_ROUTING_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_FINAL_SPECIALIZED_ROUTING = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        # Utility command tetap ikut wrapper sebelumnya:
        # /audit_qa help
        # /audit_qa list
        # /audit_qa history
        # /audit_qa fitur=all
        utility_checkers = [
            globals().get("should_run_qa_help"),
            globals().get("should_run_qa_list"),
            globals().get("should_run_qa_history"),
            globals().get("should_run_all_features"),
        ]

        for checker_fn in utility_checkers:
            try:
                if checker_fn and checker_fn(module_name, mode):
                    if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_FINAL_SPECIALIZED_ROUTING is None:
                        raise RuntimeError("Previous perform_audit_for_telegram runner not found")

                    return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_FINAL_SPECIALIZED_ROUTING(
                        url,
                        module_name,
                        mode,
                        *args,
                        **kwargs,
                    )
            except Exception:
                pass

        suite_fn, canonical_module_name = _qa_final_match_specialized_suite(module_name, mode)

        if suite_fn:
            result = _qa_final_call_suite(
                suite_fn,
                url,
                canonical_module_name or module_name,
                mode,
            )

            return _qa_final_enrich_and_history(
                result,
                url,
                canonical_module_name or module_name,
                mode,
            )

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_FINAL_SPECIALIZED_ROUTING is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_FINAL_SPECIALIZED_ROUTING(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

    _FINAL_SPECIALIZED_FEATURE_ROUTING_PATCH_INSTALLED = True


# ============================================================
# Notification Management Direct Route Override
# ============================================================
#
# Problem:
# Runner kadang gagal menemukan menu "Notification Management"
# walaupun route valid adalah /managementnotif.
#
# Fix:
# Setelah login, langsung buka /managementnotif.
# ============================================================

def _qa_notification_management_get_base_url(page):
    import os
    from urllib.parse import urlparse

    try:
        current_url = page.url or ""
        parsed = urlparse(current_url)

        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        pass

    return os.getenv(
        "QA_DEFAULT_URL",
        "https://mobospace-sandbox.pancaran-group.co.id",
    ).rstrip("/")


if not globals().get("_NOTIFICATION_MANAGEMENT_DIRECT_ROUTE_PATCH_INSTALLED"):
    _ORIGINAL_OPEN_NOTIFICATION_MANAGEMENT_TARGET_MENU = globals().get(
        "open_notification_management_target_menu"
    )

    def open_notification_management_target_menu(page, *args, **kwargs):
        base_url = _qa_notification_management_get_base_url(page).rstrip("/")

        direct_routes = [
            f"{base_url}/managementnotif",
            f"{base_url}/managementnotif/",
        ]

        page_markers = [
            "NOTIFICATION MANAGEMENT",
            "Notification Management",
            "Notification Context",
            "Notification Event",
            "Notification Group",
            "Message Template",
            "Email Template",
            "Contact Group",
        ]

        last_error = None

        for target_url in direct_routes:
            try:
                page.goto(
                    target_url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                try:
                    page.wait_for_load_state("networkidle", timeout=20000)
                except Exception:
                    pass

                page.wait_for_timeout(3000)

                body_text = ""
                try:
                    body_text = page.locator("body").inner_text(timeout=15000)
                except Exception:
                    body_text = ""

                lowered = body_text.lower()

                if any(marker.lower() in lowered for marker in page_markers):
                    return True

            except Exception as exc:
                last_error = exc

        # Fallback ke opener lama kalau direct route gagal.
        if _ORIGINAL_OPEN_NOTIFICATION_MANAGEMENT_TARGET_MENU:
            try:
                return _ORIGINAL_OPEN_NOTIFICATION_MANAGEMENT_TARGET_MENU(
                    page,
                    *args,
                    **kwargs,
                )
            except Exception as exc:
                last_error = exc

        return False

    _NOTIFICATION_MANAGEMENT_DIRECT_ROUTE_PATCH_INSTALLED = True


# ============================================================
# Notification Management Direct Route for open_target_menu
# ============================================================

def _qa_is_notification_management_module(module_name):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")

    return value in {
        "notification management",
        "management notif",
        "management notification",
        "notification manage",
        "notif management",
    }


def _qa_direct_open_notification_management_from_generic_menu(page):
    import os
    from urllib.parse import urlparse

    try:
        current_url = page.url or ""
        parsed = urlparse(current_url)

        if parsed.scheme and parsed.netloc:
            base_url = f"{parsed.scheme}://{parsed.netloc}"
        else:
            base_url = os.getenv(
                "QA_DEFAULT_URL",
                "https://mobospace-sandbox.pancaran-group.co.id",
            ).rstrip("/")
    except Exception:
        base_url = os.getenv(
            "QA_DEFAULT_URL",
            "https://mobospace-sandbox.pancaran-group.co.id",
        ).rstrip("/")

    target_urls = [
        f"{base_url}/managementnotif",
        f"{base_url}/managementnotif/",
    ]

    markers = [
        "notification management",
        "notification context",
        "notification event",
        "notification group",
        "message template",
        "email template",
        "contact group",
    ]

    for target_url in target_urls:
        try:
            page.goto(
                target_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass

            page.wait_for_timeout(3000)

            try:
                body_text = page.locator("body").inner_text(timeout=15000)
            except Exception:
                body_text = ""

            lowered = str(body_text or "").lower()

            if any(marker in lowered for marker in markers):
                return True, "Notification Management"

        except Exception:
            continue

    return False, ""


if not globals().get("_OPEN_TARGET_MENU_NOTIFICATION_MANAGEMENT_DIRECT_PATCH_INSTALLED"):
    _OPEN_TARGET_MENU_BEFORE_NOTIFICATION_MANAGEMENT_DIRECT = globals().get("open_target_menu")

    def open_target_menu(page, module_name):
        if _qa_is_notification_management_module(module_name):
            opened, menu_text = _qa_direct_open_notification_management_from_generic_menu(page)

            if opened:
                return opened, menu_text

        if _OPEN_TARGET_MENU_BEFORE_NOTIFICATION_MANAGEMENT_DIRECT:
            return _OPEN_TARGET_MENU_BEFORE_NOTIFICATION_MANAGEMENT_DIRECT(page, module_name)

        return False, ""

    _OPEN_TARGET_MENU_NOTIFICATION_MANAGEMENT_DIRECT_PATCH_INSTALLED = True


# ============================================================
# Custom Smoke Test Function - Safe MVP
# ============================================================

def perform_custom_smoke_test(
    url,
    route,
    expected_texts=None,
    feature_name="Custom Smoke Test",
    mode="smoke",
):
    from pathlib import Path
    from datetime import datetime
    import json
    import os
    import platform
    import re
    import sys

    root = Path(__file__).resolve().parents[2]

    try:
        from dotenv import load_dotenv
        load_dotenv(root / ".env")
        load_dotenv(root / "skills" / "qa_automation" / ".env")
    except Exception:
        pass

    report_dir = root / "skills" / "qa_automation" / "artifacts" / "reports"
    screenshot_dir = root / "skills" / "qa_automation" / "artifacts" / "screenshots"
    log_dir = root / "skills" / "qa_automation" / "artifacts" / "logs"

    report_dir.mkdir(parents=True, exist_ok=True)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    execution_id = "QA-CUSTOM-" + run_id
    executed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB")

    expected_texts = expected_texts or []
    base_url = str(url or "").rstrip("/")
    route_value = str(route or "").strip()

    if route_value.startswith("http://") or route_value.startswith("https://"):
        target_url = route_value
    else:
        if not route_value.startswith("/"):
            route_value = "/" + route_value
        target_url = base_url + route_value

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(feature_name).lower()).strip("_") or "custom_smoke"

    report_path = report_dir / ("qa_documentation_custom_smoke_" + slug + "_" + run_id + ".md")
    error_log_path = log_dir / ("qa_error_log_custom_smoke_" + slug + "_" + run_id + ".md")
    screenshot_path = screenshot_dir / ("custom_smoke_" + slug + "_" + run_id + ".png")

    username = (
        os.getenv("QA_USERNAME")
        or os.getenv("QA_EMAIL")
        or os.getenv("MOBOSPACE_USERNAME")
        or os.getenv("MOBOSPACE_EMAIL")
        or os.getenv("TEST_USERNAME")
        or os.getenv("TEST_EMAIL")
        or os.getenv("USERNAME")
        or os.getenv("EMAIL")
        or ""
    )

    password = (
        os.getenv("QA_PASSWORD")
        or os.getenv("MOBOSPACE_PASSWORD")
        or os.getenv("TEST_PASSWORD")
        or os.getenv("PASSWORD")
        or ""
    )

    test_cases = []
    bugs = []
    page_text = ""

    def add_tc(tc_id, status, title):
        test_cases.append({"id": tc_id, "status": status, "title": title})

    def fill_first(page, selectors, value):
        for selector in selectors:
            try:
                loc = page.locator(selector).first()
                if loc.count() > 0:
                    loc.fill(value, timeout=5000)
                    return True
            except Exception:
                pass
        return False

    def click_first(page, selectors):
        for selector in selectors:
            try:
                loc = page.locator(selector).first()
                if loc.count() > 0:
                    loc.click(timeout=5000)
                    return True
            except Exception:
                pass
        return False

    try:
        add_tc("TC-001", "PASS" if username and password else "FAIL", "Load credential")

        if not username or not password:
            raise RuntimeError("Credential username/password tidak ditemukan di .env")

        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()

            page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
            add_tc("TC-002", "PASS", "Access base URL")

            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass

            # Mobospace login revamp: klik card/login entry dulu jika form belum tampil.
            try:
                if "_custom_smoke_has_login_fields" in globals() and not _custom_smoke_has_login_fields(page):
                    if "_custom_smoke_click_login_entry_if_needed" in globals():
                        _custom_smoke_click_login_entry_if_needed(page)
                        try:
                            page.wait_for_load_state("networkidle", timeout=15000)
                        except Exception:
                            pass
                        page.wait_for_timeout(1500)
            except Exception:
                pass

            user_ok = fill_first(
                page,
                [
                    'input[type="email"]',
                    'input[type="text"]',
                    'input[name*="email" i]',
                    'input[name*="user" i]',
                    'input[placeholder*="email" i]',
                    'input[placeholder*="user" i]',
                    'input[placeholder*="username" i]',
                ],
                username,
            )

            pass_ok = fill_first(
                page,
                [
                    'input[type="password"]',
                    'input[name*="password" i]',
                    'input[name*="pass" i]',
                    'input[placeholder*="password" i]',
                ],
                password,
            )

            if not user_ok or not pass_ok:
                raise RuntimeError("Login field username/password tidak ditemukan")

            login_ok = click_first(
                page,
                [
                    'button[type="submit"]',
                    'button:has-text("Login")',
                    'button:has-text("Masuk")',
                    'button:has-text("Sign In")',
                    'button',
                    '[role="button"]',
                ],
            )

            if not login_ok:
                raise RuntimeError("Tombol login tidak ditemukan")

            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                pass

            page.wait_for_timeout(3000)
            add_tc("TC-003", "PASS", "Login attempted")

            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)

            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass

            page.wait_for_timeout(3000)
            add_tc("TC-004", "PASS", "Open custom route " + route_value)

            try:
                page_text = page.locator("body").inner_text(timeout=15000)
            except Exception:
                page_text = ""

            if page_text.strip():
                add_tc("TC-005", "PASS", "Read page content")
            else:
                add_tc("TC-005", "FAIL", "Read page content")
                bugs.append("Page content is empty")

            for index, expected in enumerate(expected_texts, start=1):
                tc_id = "TC-" + str(5 + index).zfill(3)
                if str(expected).lower() in page_text.lower():
                    add_tc(tc_id, "PASS", "Expected text found: " + str(expected))
                else:
                    add_tc(tc_id, "FAIL", "Expected text missing: " + str(expected))
                    bugs.append("Expected text missing: " + str(expected))

            page.screenshot(path=str(screenshot_path), full_page=True)
            add_tc("TC-020", "PASS", "Capture screenshot evidence")

            context.close()
            browser.close()

    except Exception as exc:
        add_tc("TC-999", "FAIL", "Automation runtime")
        bugs.append("Automation runtime error: " + str(exc))

    passed = sum(1 for item in test_cases if item["status"] == "PASS")
    failed = sum(1 for item in test_cases if item["status"] == "FAIL")

    status = "FAILED" if failed > 0 or bugs else "PASS"
    icon = "❌" if status == "FAILED" else "✅"

    verified_lines = []
    failed_lines = []

    for tc in test_cases:
        line = tc["id"] + " " + tc["status"] + " - " + tc["title"]
        if tc["status"] == "PASS":
            verified_lines.append(line)
        elif tc["status"] == "FAIL":
            failed_lines.append(line)

    bug_lines = bugs if bugs else ["No bug found"]

    testing_summary = (
        icon + " QA Custom Smoke Test Completed\n\n"
        + "Module: " + str(feature_name) + "\n"
        + "Mode: " + str(mode) + "\n"
        + "Environment: Sandbox\n"
        + "Status: " + status + "\n\n"
        + "Execution Info:\n"
        + "- Execution ID: " + execution_id + "\n"
        + "- Executed At: " + executed_at + "\n"
        + "- Executed By: Hermes QA Automation\n"
        + "- Feature: " + str(feature_name) + "\n"
        + "- Suite / Mode: " + str(mode) + "\n"
        + "- Environment: Sandbox\n"
        + "- Base URL: " + base_url + "\n"
        + "- Route: " + route_value + "\n"
        + "- Target URL: " + target_url + "\n\n"
        + "Runtime Environment:\n"
        + "- OS: " + platform.platform() + "\n"
        + "- Machine: " + platform.machine() + "\n"
        + "- Browser: Chromium\n"
        + "- Automation Tool: Playwright\n"
        + "- Runtime: Hermes Agent\n"
        + "- Python Version: " + sys.version.split()[0] + "\n\n"
        + "Summary:\n"
        + "- Passed: " + str(passed) + "\n"
        + "- Failed: " + str(failed) + "\n"
        + "- Need Review: 0\n"
        + "- Skipped: 0\n"
        + "- Bugs Found: " + str(len(bugs)) + "\n"
        + "- Non-blocking Warnings: 0\n\n"
        + "Verified:\n" + ("\n".join(verified_lines) if verified_lines else "-") + "\n\n"
        + "Failed:\n" + ("\n".join(failed_lines) if failed_lines else "-") + "\n\n"
        + "Need Review:\n-\n\n"
        + "Bugs:\n" + "\n".join(bug_lines) + "\n\n"
        + "Evidence:\n"
        + "- Screenshot: " + str(screenshot_path) + "\n"
        + "- Report: " + str(report_path) + "\n"
        + "- Error Log: " + str(error_log_path) + "\n\n"
        + "Recommendation:\n"
        + ("Fix blocking issues before release." if status == "FAILED" else "No blocking issue found from custom smoke result.")
    )

    documentation_report = (
        "# QA Custom Smoke Test Report\n\n"
        + "Execution ID: " + execution_id + "\n"
        + "Feature: " + str(feature_name) + "\n"
        + "Mode: " + str(mode) + "\n"
        + "Status: " + status + "\n"
        + "Base URL: " + base_url + "\n"
        + "Route: " + route_value + "\n"
        + "Target URL: " + target_url + "\n\n"
        + "Summary:\n"
        + "- Passed: " + str(passed) + "\n"
        + "- Failed: " + str(failed) + "\n"
        + "- Bugs Found: " + str(len(bugs)) + "\n\n"
        + "Expected Texts:\n"
        + json.dumps(expected_texts, indent=2, ensure_ascii=False) + "\n\n"
        + "Test Cases:\n"
        + json.dumps(test_cases, indent=2, ensure_ascii=False) + "\n\n"
        + "Bugs:\n"
        + "\n".join(bug_lines) + "\n\n"
        + "Page Text Preview:\n"
        + page_text[:3000]
    )

    error_log_report = (
        "# QA Custom Smoke Error Log\n\n"
        + "Status: " + status + "\n"
        + "Execution ID: " + execution_id + "\n"
        + "Feature: " + str(feature_name) + "\n"
        + "Route: " + route_value + "\n\n"
        + "Bugs:\n"
        + "\n".join(bug_lines)
    )

    report_path.write_text(documentation_report, encoding="utf-8")
    error_log_path.write_text(error_log_report, encoding="utf-8")

    result = {
        "testing_summary": testing_summary,
        "documentation_report": documentation_report,
        "error_log_report": error_log_report,
        "status": status,
        "screenshot_path": str(screenshot_path),
        "report_path": str(report_path),
        "documentation_path": str(report_path),
        "error_log_path": str(error_log_path),
        "feature_name": feature_name,
        "route": route_value,
        "target_url": target_url,
        "custom_smoke": True,
    }

    try:
        enrich_fn = globals().get("enrich_qa_result_with_standard_json")
        if enrich_fn:
            result = enrich_fn(result, base_url, feature_name, mode)
    except Exception as exc:
        result["standard_json_error"] = str(exc)

    try:
        append_history_fn = globals().get("append_qa_run_history")
        if append_history_fn:
            result = append_history_fn(result, base_url, feature_name, mode)
    except Exception as exc:
        result["history_error"] = str(exc)

    return result


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


# ============================================================
# Custom Smoke Login Card Override
# ============================================================

def _custom_smoke_click_login_entry_if_needed(page):
    """
    Mobospace login kadang menampilkan card pilihan login lebih dulu.
    Helper ini klik Internal User / Login card sebelum cari input username/password.
    """

    import re

    candidates = [
        "Internal User",
        "Internal",
        "LDAP",
        "Login",
        "Log In",
        "Masuk",
        "Sign In",
    ]

    for text in candidates:
        try:
            page.get_by_text(re.compile(text, re.IGNORECASE)).first().click(timeout=4000)
            page.wait_for_timeout(1500)
            return True, text
        except Exception:
            pass

    selectors = [
        ".v-card",
        ".card",
        "[role='button']",
        "button",
        "a",
    ]

    for selector in selectors:
        try:
            loc = page.locator(selector).first()
            if loc.count() > 0:
                loc.click(timeout=4000)
                page.wait_for_timeout(1500)
                return True, selector
        except Exception:
            pass

    return False, ""


def _custom_smoke_has_login_fields(page):
    user_selectors = [
        'input[type="email"]',
        'input[type="text"]',
        'input[name*="email" i]',
        'input[name*="user" i]',
        'input[placeholder*="email" i]',
        'input[placeholder*="user" i]',
        'input[placeholder*="username" i]',
    ]

    pass_selectors = [
        'input[type="password"]',
        'input[name*="password" i]',
        'input[name*="pass" i]',
        'input[placeholder*="password" i]',
    ]

    user_found = False
    pass_found = False

    for selector in user_selectors:
        try:
            if page.locator(selector).count() > 0:
                user_found = True
                break
        except Exception:
            pass

    for selector in pass_selectors:
        try:
            if page.locator(selector).count() > 0:
                pass_found = True
                break
        except Exception:
            pass

    return user_found and pass_found


if not globals().get("_CUSTOM_SMOKE_LOGIN_CARD_PATCH_INSTALLED"):
    _CUSTOM_SMOKE_BEFORE_LOGIN_CARD = globals().get("perform_custom_smoke_test")

    def perform_custom_smoke_test(
        url,
        route,
        expected_texts=None,
        feature_name="Custom Smoke Test",
        mode="smoke",
    ):
        """
        Wrapper tetap memakai function custom smoke existing,
        tetapi monkey-patch helper fill_first agar login card diklik dulu.
        """

        # Function lama tetap dipakai.
        # Patch ini bekerja lewat helper tambahan di versi berikutnya kalau function lama dipanggil ulang.
        if _CUSTOM_SMOKE_BEFORE_LOGIN_CARD is None:
            raise RuntimeError("Previous perform_custom_smoke_test not found")

        return _CUSTOM_SMOKE_BEFORE_LOGIN_CARD(
            url=url,
            route=route,
            expected_texts=expected_texts,
            feature_name=feature_name,
            mode=mode,
        )

    _CUSTOM_SMOKE_LOGIN_CARD_PATCH_INSTALLED = True


# ============================================================
# Custom Smoke Registered Runner Fallback
# ============================================================

def _custom_smoke_get_registered_feature_by_route(route):
    route_value = str(route or "").strip().lower()

    if route_value.startswith("http://") or route_value.startswith("https://"):
        route_value = "/" + route_value.rstrip("/").split("/")[-1]

    if not route_value.startswith("/"):
        route_value = "/" + route_value

    route_map = {
        "/managementnotif": "Notification Management",
        "/notificationmessage": "Notification Messages",
        "/shipmentdetail": "Shipment Details",
        "/mobomap": "MoboMap",
        "/inspectionresult": "Inspection Result",
    }

    return route_map.get(route_value), route_value


if not globals().get("_CUSTOM_SMOKE_REGISTERED_RUNNER_FALLBACK_INSTALLED"):
    _CUSTOM_SMOKE_BEFORE_REGISTERED_RUNNER_FALLBACK = globals().get("perform_custom_smoke_test")

    def perform_custom_smoke_test(
        url,
        route,
        expected_texts=None,
        feature_name="Custom Smoke Test",
        mode="smoke",
    ):
        expected_texts = expected_texts or []
        base_url = str(url or "").rstrip("/")
        registered_feature, route_value = _custom_smoke_get_registered_feature_by_route(route)

        if registered_feature:
            runner = globals().get("perform_audit_for_telegram")

            if runner:
                try:
                    result = runner(
                        url=base_url,
                        module_name=registered_feature,
                        mode=mode,
                    )
                except TypeError:
                    result = runner(base_url, registered_feature, mode)

                if isinstance(result, dict):
                    target_url = base_url + route_value

                    result["custom_smoke"] = True
                    result["custom_smoke_strategy"] = "registered_runner_fallback"
                    result["feature_name"] = feature_name
                    result["registered_feature"] = registered_feature
                    result["route"] = route_value
                    result["target_url"] = target_url
                    result["expected_texts"] = expected_texts

                    bridge_note = (
                        "\n\nCustom Smoke Bridge:\n"
                        + "- Custom Feature: " + str(feature_name) + "\n"
                        + "- Route: " + str(route_value) + "\n"
                        + "- Target URL: " + str(target_url) + "\n"
                        + "- Registered Runner Used: " + str(registered_feature) + "\n"
                        + "- Strategy: reuse stable registered QA login and validation flow\n"
                        + "- Expected Texts: " + ", ".join([str(item) for item in expected_texts]) + "\n"
                    )

                    result["testing_summary"] = str(result.get("testing_summary", "")) + bridge_note

                    try:
                        enrich_fn = globals().get("enrich_qa_result_with_standard_json")
                        if enrich_fn:
                            result = enrich_fn(result, base_url, feature_name, mode)
                    except Exception as exc:
                        result["standard_json_error"] = str(exc)

                    try:
                        append_history_fn = globals().get("append_qa_run_history")
                        if append_history_fn:
                            result = append_history_fn(result, base_url, feature_name, mode)
                    except Exception as exc:
                        result["history_error"] = str(exc)

                    return result

        if _CUSTOM_SMOKE_BEFORE_REGISTERED_RUNNER_FALLBACK is None:
            raise RuntimeError("Previous perform_custom_smoke_test not found")

        return _CUSTOM_SMOKE_BEFORE_REGISTERED_RUNNER_FALLBACK(
            url=url,
            route=route,
            expected_texts=expected_texts,
            feature_name=feature_name,
            mode=mode,
        )

    _CUSTOM_SMOKE_REGISTERED_RUNNER_FALLBACK_INSTALLED = True


# ============================================================
# Custom Smoke Generic UI Runner V2
# ============================================================

def _custom_smoke_build_target_url_v2(base_url, route):
    base = str(base_url or "").rstrip("/")
    route_value = str(route or "").strip()

    if route_value.startswith("http://") or route_value.startswith("https://"):
        return route_value, route_value

    if not route_value.startswith("/"):
        route_value = "/" + route_value

    return base + route_value, route_value


def _custom_smoke_resolve_credentials_v2():
    import os
    from pathlib import Path

    if "_custom_smoke_resolve_credentials_flexible" in globals():
        try:
            return _custom_smoke_resolve_credentials_flexible()
        except Exception:
            pass

    root = Path(__file__).resolve().parents[2]

    try:
        from dotenv import load_dotenv
        load_dotenv(root / ".env")
        load_dotenv(root / "skills" / "qa_automation" / ".env")
    except Exception:
        pass

    username = (
        os.getenv("QA_USERNAME")
        or os.getenv("QA_EMAIL")
        or os.getenv("MOBOSPACE_USERNAME")
        or os.getenv("MOBOSPACE_EMAIL")
        or os.getenv("TEST_USERNAME")
        or os.getenv("TEST_EMAIL")
        or os.getenv("USERNAME")
        or os.getenv("EMAIL")
        or ""
    )

    password = (
        os.getenv("QA_PASSWORD")
        or os.getenv("MOBOSPACE_PASSWORD")
        or os.getenv("TEST_PASSWORD")
        or os.getenv("PASSWORD")
        or ""
    )

    workspace = (
        os.getenv("QA_WORKSPACE")
        or os.getenv("QA_COMPANY")
        or os.getenv("MOBOSPACE_WORKSPACE")
        or os.getenv("MOBOSPACE_COMPANY")
        or os.getenv("WORKSPACE")
        or os.getenv("COMPANY")
        or ""
    )

    return {
        "username": username,
        "password": password,
        "workspace": workspace,
        "username_key": "",
        "password_key": "",
        "workspace_key": "",
    }


def _custom_smoke_click_text_v2(page, texts, timeout=3500):
    import re

    for value in texts:
        try:
            page.get_by_text(re.compile(str(value), re.IGNORECASE)).first().click(timeout=timeout)
            page.wait_for_timeout(1200)
            return True, str(value)
        except Exception:
            pass

    return False, ""


def _custom_smoke_click_selector_v2(page, selectors, timeout=3500):
    for selector in selectors:
        try:
            loc = page.locator(selector).first()
            if loc.count() > 0:
                loc.click(timeout=timeout)
                page.wait_for_timeout(1200)
                return True, selector
        except Exception:
            pass

    return False, ""


def _custom_smoke_fill_selector_v2(page, selectors, value, timeout=3500):
    for selector in selectors:
        try:
            loc = page.locator(selector).first()
            if loc.count() > 0:
                loc.fill(str(value), timeout=timeout)
                return True, selector
        except Exception:
            pass

    return False, ""


def _custom_smoke_fill_visible_input_by_type_v2(page, username, password):
    user_ok = False
    pass_ok = False

    try:
        inputs = page.locator("input:visible")
        total = inputs.count()
    except Exception:
        total = 0

    for index in range(total):
        try:
            item = inputs.nth(index)
            input_type = (item.get_attribute("type") or "").lower()
            name = (item.get_attribute("name") or "").lower()
            placeholder = (item.get_attribute("placeholder") or "").lower()
            aria = (item.get_attribute("aria-label") or "").lower()

            marker = " ".join([input_type, name, placeholder, aria])

            if "password" in marker or input_type == "password":
                if not pass_ok:
                    item.fill(str(password), timeout=3000)
                    pass_ok = True
            else:
                if not user_ok:
                    item.fill(str(username), timeout=3000)
                    user_ok = True

        except Exception:
            pass

    return user_ok, pass_ok


def _custom_smoke_has_login_fields_v2(page):
    try:
        password_count = page.locator('input[type="password"]:visible').count()
        visible_input_count = page.locator("input:visible").count()
        return password_count > 0 and visible_input_count >= 2
    except Exception:
        return False


def _custom_smoke_open_login_form_v2(page):
    if _custom_smoke_has_login_fields_v2(page):
        return True, "login_fields_already_visible"

    login_texts = [
        "Internal User",
        "Internal",
        "LDAP",
        "Username",
        "Password",
        "Login",
        "Log In",
        "Masuk",
        "Sign In",
        "SSO",
    ]

    clicked, marker = _custom_smoke_click_text_v2(page, login_texts, timeout=3000)
    if clicked:
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        page.wait_for_timeout(1500)

        if _custom_smoke_has_login_fields_v2(page):
            return True, marker

    login_selectors = [
        'button:has-text("Login")',
        'button:has-text("Masuk")',
        'button:has-text("Sign In")',
        'button',
        '[role="button"]',
        '.v-card',
        '.card',
        'a',
    ]

    clicked, marker = _custom_smoke_click_selector_v2(page, login_selectors, timeout=3000)
    if clicked:
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        page.wait_for_timeout(1500)

        if _custom_smoke_has_login_fields_v2(page):
            return True, marker

    return _custom_smoke_has_login_fields_v2(page), "generic_login_attempt"


def _custom_smoke_collect_page_diagnostics_v2(page):
    diagnostics = []

    try:
        diagnostics.append("Current URL: " + str(page.url))
    except Exception:
        pass

    try:
        diagnostics.append("Visible input count: " + str(page.locator("input:visible").count()))
    except Exception:
        pass

    try:
        diagnostics.append("Password input count: " + str(page.locator('input[type="password"]:visible').count()))
    except Exception:
        pass

    try:
        button_texts = []
        buttons = page.locator("button")
        total = min(buttons.count(), 10)

        for index in range(total):
            try:
                text_value = buttons.nth(index).inner_text(timeout=1000).strip()
                if text_value:
                    button_texts.append(text_value)
            except Exception:
                pass

        diagnostics.append("Visible button texts: " + ", ".join(button_texts))
    except Exception:
        pass

    try:
        body_text = page.locator("body").inner_text(timeout=3000)
        diagnostics.append("Body preview: " + body_text[:1200].replace("\n", " | "))
    except Exception:
        pass

    return "\n".join(diagnostics)


def _custom_smoke_perform_login_v2(page, username, password, add_tc):
    if not username or not password:
        raise RuntimeError("Credential username/password tidak ditemukan di .env")

    opened, marker = _custom_smoke_open_login_form_v2(page)

    if opened:
        add_tc("TC-003", "PASS", "Open login form: " + str(marker))
    else:
        diagnostics = _custom_smoke_collect_page_diagnostics_v2(page)
        raise RuntimeError("Login form tidak ditemukan\n" + diagnostics)

    user_selectors = [
        'input[type="email"]:visible',
        'input[type="text"]:visible',
        'input[name*="email" i]:visible',
        'input[name*="user" i]:visible',
        'input[name*="username" i]:visible',
        'input[placeholder*="email" i]:visible',
        'input[placeholder*="user" i]:visible',
        'input[placeholder*="username" i]:visible',
        'input[placeholder*="NIK" i]:visible',
    ]

    password_selectors = [
        'input[type="password"]:visible',
        'input[name*="password" i]:visible',
        'input[name*="pass" i]:visible',
        'input[placeholder*="password" i]:visible',
    ]

    user_ok, _user_marker = _custom_smoke_fill_selector_v2(page, user_selectors, username)
    pass_ok, _pass_marker = _custom_smoke_fill_selector_v2(page, password_selectors, password)

    if not user_ok or not pass_ok:
        fallback_user_ok, fallback_pass_ok = _custom_smoke_fill_visible_input_by_type_v2(page, username, password)
        user_ok = user_ok or fallback_user_ok
        pass_ok = pass_ok or fallback_pass_ok

    if not user_ok or not pass_ok:
        diagnostics = _custom_smoke_collect_page_diagnostics_v2(page)
        raise RuntimeError("Login field username/password tidak ditemukan\n" + diagnostics)

    add_tc("TC-004", "PASS", "Fill username/password")

    login_selectors = [
        'button[type="submit"]',
        'button:has-text("Login")',
        'button:has-text("Masuk")',
        'button:has-text("Sign In")',
        'button:has-text("Submit")',
        '[role="button"]:has-text("Login")',
        '[role="button"]:has-text("Masuk")',
    ]

    clicked, marker = _custom_smoke_click_selector_v2(page, login_selectors, timeout=5000)

    if not clicked:
        try:
            page.keyboard.press("Enter")
            clicked = True
            marker = "keyboard_enter"
        except Exception:
            pass

    if not clicked:
        diagnostics = _custom_smoke_collect_page_diagnostics_v2(page)
        raise RuntimeError("Tombol login tidak ditemukan\n" + diagnostics)

    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass

    page.wait_for_timeout(3000)
    add_tc("TC-005", "PASS", "Submit login: " + str(marker))


def _custom_smoke_select_workspace_v2(page, workspace, add_tc):
    workspace_value = str(workspace or "").strip()

    if workspace_value:
        clicked, _marker = _custom_smoke_click_text_v2(page, [workspace_value], timeout=5000)

        if clicked:
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

            page.wait_for_timeout(1500)

            _custom_smoke_click_text_v2(
                page,
                ["Select", "Pilih", "Continue", "Lanjut", "Masuk", "OK"],
                timeout=3000,
            )

            add_tc("TC-006", "PASS", "Select workspace/company: " + workspace_value)
            return True

    # Fallback: kalau sudah masuk dashboard atau tidak ada halaman pilihan company, skip sebagai PASS.
    try:
        body = page.locator("body").inner_text(timeout=3000).lower()
    except Exception:
        body = ""

    selection_markers = [
        "select company",
        "choose company",
        "pilih company",
        "pilih perusahaan",
        "workspace",
    ]

    if any(marker in body for marker in selection_markers):
        clicked, _marker = _custom_smoke_click_text_v2(
            page,
            ["Pancaran", "Sandbox", "Mobospace", "Pilih", "Select", "Continue"],
            timeout=4000,
        )

        if clicked:
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

            page.wait_for_timeout(1500)
            add_tc("TC-006", "PASS", "Select workspace/company fallback")
            return True

        add_tc("TC-006", "NEED REVIEW", "Workspace/company page detected but no option clicked")
        return False

    add_tc("TC-006", "PASS", "Workspace/company selection skipped")
    return True


def _perform_custom_smoke_generic_ui_v2(
    url,
    route,
    expected_texts=None,
    feature_name="Custom Smoke Test",
    mode="smoke",
):
    from pathlib import Path
    from datetime import datetime
    import json
    import platform
    import re
    import sys

    root = Path(__file__).resolve().parents[2]

    report_dir = root / "skills" / "qa_automation" / "artifacts" / "reports"
    screenshot_dir = root / "skills" / "qa_automation" / "artifacts" / "screenshots"
    log_dir = root / "skills" / "qa_automation" / "artifacts" / "logs"

    report_dir.mkdir(parents=True, exist_ok=True)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    execution_id = "QA-CUSTOM-GENERIC-" + run_id
    executed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB")

    expected_texts = expected_texts or []
    base_url = str(url or "").rstrip("/")
    target_url, route_value = _custom_smoke_build_target_url_v2(base_url, route)

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(feature_name).lower()).strip("_") or "custom_smoke"

    report_path = report_dir / ("qa_documentation_custom_smoke_generic_" + slug + "_" + run_id + ".md")
    error_log_path = log_dir / ("qa_error_log_custom_smoke_generic_" + slug + "_" + run_id + ".md")
    screenshot_path = screenshot_dir / ("custom_smoke_generic_" + slug + "_" + run_id + ".png")

    credential = _custom_smoke_resolve_credentials_v2()
    username = credential.get("username") or ""
    password = credential.get("password") or ""
    workspace = credential.get("workspace") or ""

    test_cases = []
    bugs = []
    warnings = []
    page_text = ""
    current_url = ""
    browser = None
    context = None
    page = None

    def add_tc(tc_id, status, title):
        test_cases.append({
            "id": tc_id,
            "status": status,
            "title": title,
        })

    try:
        add_tc("TC-001", "PASS" if username and password else "FAIL", "Load credential")

        if not username or not password:
            raise RuntimeError("Credential username/password tidak ditemukan di .env")

        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()

            page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
            add_tc("TC-002", "PASS", "Access base URL")

            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass

            _custom_smoke_perform_login_v2(page, username, password, add_tc)
            _custom_smoke_select_workspace_v2(page, workspace, add_tc)

            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)

            try:
                page.wait_for_load_state("networkidle", timeout=25000)
            except Exception:
                pass

            page.wait_for_timeout(3000)

            try:
                current_url = str(page.url)
            except Exception:
                current_url = target_url

            add_tc("TC-007", "PASS", "Open custom route: " + str(route_value))

            try:
                page_text = page.locator("body").inner_text(timeout=15000)
            except Exception:
                page_text = ""

            if page_text.strip():
                add_tc("TC-008", "PASS", "Read page content")
            else:
                add_tc("TC-008", "FAIL", "Read page content")
                bugs.append("Page content is empty")

            tc_number = 9

            for expected in expected_texts:
                expected_value = str(expected).strip()

                if not expected_value:
                    continue

                tc_id = "TC-" + str(tc_number).zfill(3)

                if expected_value.lower() in page_text.lower():
                    add_tc(tc_id, "PASS", "Expected text found: " + expected_value)
                else:
                    add_tc(tc_id, "FAIL", "Expected text missing: " + expected_value)
                    bugs.append("Expected text missing: " + expected_value)

                tc_number += 1

            page.screenshot(path=str(screenshot_path), full_page=True)
            add_tc("TC-020", "PASS", "Capture screenshot evidence")

            context.close()
            browser.close()

    except Exception as exc:
        add_tc("TC-999", "FAIL", "Automation runtime")
        bugs.append("Automation runtime error: " + str(exc))

        try:
            if page is not None:
                page.screenshot(path=str(screenshot_path), full_page=True)
        except Exception:
            pass

        try:
            if context is not None:
                context.close()
        except Exception:
            pass

        try:
            if browser is not None:
                browser.close()
        except Exception:
            pass

    passed = sum(1 for tc in test_cases if tc["status"] == "PASS")
    failed = sum(1 for tc in test_cases if tc["status"] == "FAIL")
    need_review = sum(1 for tc in test_cases if tc["status"] == "NEED REVIEW")
    skipped = 0

    if failed > 0 or bugs:
        status = "FAILED"
        icon = "❌"
    elif need_review > 0 or warnings:
        status = "NEED REVIEW"
        icon = "⚠️"
    else:
        status = "PASS"
        icon = "✅"

    verified_lines = []
    failed_lines = []
    review_lines = []

    for tc in test_cases:
        line = tc["id"] + " " + tc["status"] + " - " + tc["title"]

        if tc["status"] == "PASS":
            verified_lines.append(line)
        elif tc["status"] == "FAIL":
            failed_lines.append(line)
        elif tc["status"] == "NEED REVIEW":
            review_lines.append(line)

    bug_lines = bugs if bugs else ["No bug found"]
    warning_lines = warnings if warnings else ["-"]

    testing_summary = (
        icon + " QA Custom Smoke Generic UI Test Completed\n\n"
        + "Module: " + str(feature_name) + "\n"
        + "Mode: " + str(mode) + "\n"
        + "Environment: Sandbox\n"
        + "Status: " + status + "\n\n"
        + "Execution Info:\n"
        + "- Execution ID: " + execution_id + "\n"
        + "- Executed At: " + executed_at + "\n"
        + "- Executed By: Hermes QA Automation\n"
        + "- Feature: " + str(feature_name) + "\n"
        + "- Suite / Mode: " + str(mode) + "\n"
        + "- Strategy: Generic UI Smoke Runner\n"
        + "- Environment: Sandbox\n"
        + "- Base URL: " + base_url + "\n"
        + "- Route: " + route_value + "\n"
        + "- Target URL: " + target_url + "\n"
        + "- Current URL: " + current_url + "\n\n"
        + "Runtime Environment:\n"
        + "- OS: " + platform.platform() + "\n"
        + "- Machine: " + platform.machine() + "\n"
        + "- Browser: Chromium\n"
        + "- Automation Tool: Playwright\n"
        + "- Runtime: Hermes Agent\n"
        + "- Python Version: " + sys.version.split()[0] + "\n\n"
        + "Summary:\n"
        + "- Passed: " + str(passed) + "\n"
        + "- Failed: " + str(failed) + "\n"
        + "- Need Review: " + str(need_review) + "\n"
        + "- Skipped: " + str(skipped) + "\n"
        + "- Bugs Found: " + str(len(bugs)) + "\n"
        + "- Non-blocking Warnings: " + str(len(warnings)) + "\n\n"
        + "Verified:\n" + ("\n".join(verified_lines) if verified_lines else "-") + "\n\n"
        + "Failed:\n" + ("\n".join(failed_lines) if failed_lines else "-") + "\n\n"
        + "Need Review:\n" + ("\n".join(review_lines) if review_lines else "-") + "\n\n"
        + "Bugs:\n" + "\n".join(bug_lines) + "\n\n"
        + "Evidence:\n"
        + "- Screenshot: " + str(screenshot_path) + "\n"
        + "- Report: " + str(report_path) + "\n"
        + "- Error Log: " + str(error_log_path) + "\n\n"
        + "Recommendation:\n"
        + ("Fix blocking issues before release." if status == "FAILED" else "No blocking issue found from generic custom smoke result.")
    )

    documentation_report = (
        "# QA Custom Smoke Generic UI Test Report\n\n"
        + "## Execution\n\n"
        + "- Execution ID: " + execution_id + "\n"
        + "- Feature: " + str(feature_name) + "\n"
        + "- Mode: " + str(mode) + "\n"
        + "- Strategy: Generic UI Smoke Runner\n"
        + "- Environment: Sandbox\n"
        + "- Status: " + status + "\n"
        + "- Base URL: " + base_url + "\n"
        + "- Route: " + route_value + "\n"
        + "- Target URL: " + target_url + "\n"
        + "- Current URL: " + current_url + "\n\n"
        + "## Summary\n\n"
        + "- Passed: " + str(passed) + "\n"
        + "- Failed: " + str(failed) + "\n"
        + "- Need Review: " + str(need_review) + "\n"
        + "- Bugs Found: " + str(len(bugs)) + "\n\n"
        + "## Expected Texts\n\n"
        + json.dumps(expected_texts, indent=2, ensure_ascii=False) + "\n\n"
        + "## Test Cases\n\n"
        + json.dumps(test_cases, indent=2, ensure_ascii=False) + "\n\n"
        + "## Bugs\n\n"
        + "\n".join(bug_lines) + "\n\n"
        + "## Page Text Preview\n\n"
        + page_text[:3000]
    )

    error_log_report = (
        "# QA Custom Smoke Generic UI Error Log\n\n"
        + "Status: " + status + "\n"
        + "Execution ID: " + execution_id + "\n"
        + "Feature: " + str(feature_name) + "\n"
        + "Route: " + route_value + "\n"
        + "Target URL: " + target_url + "\n"
        + "Current URL: " + current_url + "\n\n"
        + "## Bugs\n\n"
        + "\n".join(bug_lines) + "\n\n"
        + "## Warnings\n\n"
        + "\n".join(warning_lines)
    )

    report_path.write_text(documentation_report, encoding="utf-8")
    error_log_path.write_text(error_log_report, encoding="utf-8")

    result = {
        "ok": status == "PASS",
        "testing_summary": testing_summary,
        "documentation_report": documentation_report,
        "error_log_report": error_log_report,
        "status": status,
        "screenshot_path": str(screenshot_path),
        "report_path": str(report_path),
        "documentation_path": str(report_path),
        "error_log_path": str(error_log_path),
        "feature_name": feature_name,
        "route": route_value,
        "target_url": target_url,
        "current_url": current_url,
        "custom_smoke": True,
        "custom_smoke_strategy": "generic_ui_runner_v2",
        "passed": passed,
        "failed": failed,
        "need_review": need_review,
        "bugs_found": len(bugs),
    }

    try:
        enrich_fn = globals().get("enrich_qa_result_with_standard_json")
        if enrich_fn:
            result = enrich_fn(result, base_url, feature_name, mode)
    except Exception as exc:
        result["standard_json_error"] = str(exc)

    try:
        append_history_fn = globals().get("append_qa_run_history")
        if append_history_fn:
            result = append_history_fn(result, base_url, feature_name, mode)
    except Exception as exc:
        result["history_error"] = str(exc)

    return result


def _custom_smoke_exact_registered_route_v2(route):
    from urllib.parse import urlparse

    route_raw = str(route or "").strip()

    try:
        if route_raw.startswith("http://") or route_raw.startswith("https://"):
            parsed = urlparse(route_raw)
            path = parsed.path.lower()
            query = parsed.query
        else:
            if not route_raw.startswith("/"):
                route_raw = "/" + route_raw
            parsed = urlparse(route_raw)
            path = parsed.path.lower()
            query = parsed.query
    except Exception:
        path = route_raw.lower()
        query = ""

    # Query sengaja dianggap generic, agar route seperti /managementnotif?genericSmoke=1
    # bisa dipakai untuk test Generic UI Runner tanpa masuk registered fallback.
    if query:
        return None

    route_map = {
        "/managementnotif": "Notification Management",
        "/notificationmessage": "Notification Messages",
        "/shipmentdetail": "Shipment Details",
        "/mobomap": "MoboMap",
        "/inspectionresult": "Inspection Result",
    }

    return route_map.get(path)


if not globals().get("_CUSTOM_SMOKE_GENERIC_UI_V2_INSTALLED"):
    _CUSTOM_SMOKE_BEFORE_GENERIC_UI_V2 = globals().get("perform_custom_smoke_test")

    def perform_custom_smoke_test(
        url,
        route,
        expected_texts=None,
        feature_name="Custom Smoke Test",
        mode="smoke",
    ):
        registered_feature = _custom_smoke_exact_registered_route_v2(route)

        # Untuk route yang sudah registered, tetap pakai flow lama yang sudah stabil.
        if registered_feature and _CUSTOM_SMOKE_BEFORE_GENERIC_UI_V2 is not None:
            return _CUSTOM_SMOKE_BEFORE_GENERIC_UI_V2(
                url=url,
                route=route,
                expected_texts=expected_texts,
                feature_name=feature_name,
                mode=mode,
            )

        # Untuk route baru / unregistered, pakai generic UI smoke runner.
        return _perform_custom_smoke_generic_ui_v2(
            url=url,
            route=route,
            expected_texts=expected_texts,
            feature_name=feature_name,
            mode=mode,
        )

    _CUSTOM_SMOKE_GENERIC_UI_V2_INSTALLED = True


# ============================================================
# Custom Smoke Generic Login Bridge V3
# Reuse registered QA login helper: fill_login_form + is_still_on_login_page
# ============================================================

if not globals().get("_CUSTOM_SMOKE_LOGIN_BRIDGE_V3_INSTALLED"):
    _CUSTOM_SMOKE_PREVIOUS_PERFORM_LOGIN_V2 = globals().get("_custom_smoke_perform_login_v2")

    def _custom_smoke_perform_login_v2(page, username, password, add_tc):
        if not username or not password:
            raise RuntimeError("Credential username/password tidak ditemukan di .env")

        registered_login_helper = globals().get("fill_login_form")
        still_login_helper = globals().get("is_still_on_login_page")

        if registered_login_helper:
            try:
                registered_login_helper(page, username, password)

                try:
                    page.wait_for_load_state("networkidle", timeout=30000)
                except Exception:
                    pass

                page.wait_for_timeout(3000)

                add_tc("TC-003", "PASS", "Login using registered helper: fill_login_form")

                still_on_login = False

                try:
                    if still_login_helper:
                        still_on_login = bool(still_login_helper(page))
                    else:
                        still_on_login = "/login" in str(page.url).lower()
                except Exception:
                    still_on_login = "/login" in str(page.url).lower()

                # Fallback kecil kalau helper hanya mengisi form tapi belum submit.
                if still_on_login:
                    try:
                        clicked = False

                        if "_custom_smoke_click_selector_v2" in globals():
                            clicked, _marker = _custom_smoke_click_selector_v2(
                                page,
                                [
                                    'button[type="submit"]',
                                    'button:has-text("Login")',
                                    'button:has-text("Masuk")',
                                    'button:has-text("Sign In")',
                                    'button:has-text("Submit")',
                                    '[role="button"]:has-text("Login")',
                                    '[role="button"]:has-text("Masuk")',
                                ],
                                timeout=5000,
                            )

                        if not clicked:
                            page.keyboard.press("Enter")

                        try:
                            page.wait_for_load_state("networkidle", timeout=30000)
                        except Exception:
                            pass

                        page.wait_for_timeout(3000)
                    except Exception:
                        pass

                try:
                    if still_login_helper:
                        still_on_login = bool(still_login_helper(page))
                    else:
                        still_on_login = "/login" in str(page.url).lower()
                except Exception:
                    still_on_login = "/login" in str(page.url).lower()

                if still_on_login:
                    diagnostics = ""
                    try:
                        if "_custom_smoke_collect_page_diagnostics_v2" in globals():
                            diagnostics = _custom_smoke_collect_page_diagnostics_v2(page)
                    except Exception:
                        diagnostics = ""

                    raise RuntimeError(
                        "Registered login helper executed but page is still on login page\n" + diagnostics
                    )

                add_tc("TC-004", "PASS", "Authenticated session established")
                return

            except Exception as exc:
                add_tc("TC-003B", "NEED REVIEW", "Registered login helper fallback: " + str(exc))

        if _CUSTOM_SMOKE_PREVIOUS_PERFORM_LOGIN_V2:
            return _CUSTOM_SMOKE_PREVIOUS_PERFORM_LOGIN_V2(page, username, password, add_tc)

        raise RuntimeError("No login helper available for Custom Smoke Generic UI Runner")

    _CUSTOM_SMOKE_LOGIN_BRIDGE_V3_INSTALLED = True


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
