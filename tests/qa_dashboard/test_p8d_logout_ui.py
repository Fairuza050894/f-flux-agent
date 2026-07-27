import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

ACCOUNT_MENU = (
    ROOT
    / "qa_dashboard"
    / "frontend_v3"
    / "src"
    / "components"
    / "account"
    / "AccountMenu.jsx"
)

LAYOUT = (
    ROOT
    / "qa_dashboard"
    / "frontend_v3"
    / "src"
    / "layouts"
    / "DashboardLayout.jsx"
)


def test_account_menu_is_mounted_in_topbar():
    layout = LAYOUT.read_text(
        encoding="utf-8",
    )

    assert (
        "import AccountMenu"
        in layout
    )
    assert re.search(
        r"<AccountMenu\b[\s\S]*?/>",
        layout,
    )


def test_account_menu_uses_secure_logout_contract():
    component = ACCOUNT_MENU.read_text(
        encoding="utf-8",
    )

    assert "'/auth/logout'" in component
    assert "method: 'POST'" in component
    assert "credentials: 'include'" in component
    assert "window.location.assign" in component
    assert "Signing out…" in component


def test_account_menu_exposes_professional_identity_details():
    component = ACCOUNT_MENU.read_text(
        encoding="utf-8",
    )

    assert "Signed in as" in component
    assert "Role" in component
    assert "Provider" in component
    assert "Manage account" in component
    assert "account-avatar" in component
