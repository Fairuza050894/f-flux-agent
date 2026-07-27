import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

LAYOUT = (
    ROOT
    / "qa_dashboard"
    / "frontend_v3"
    / "src"
    / "layouts"
    / "DashboardLayout.jsx"
)

ACCOUNT_MENU = (
    ROOT
    / "qa_dashboard"
    / "frontend_v3"
    / "src"
    / "components"
    / "account"
    / "AccountMenu.jsx"
)

ACCOUNT_STYLE = (
    ROOT
    / "qa_dashboard"
    / "frontend_v3"
    / "src"
    / "styles"
    / "account.css"
)


def test_account_menu_uses_two_level_settings():
    layout = LAYOUT.read_text(
        encoding="utf-8",
    )
    component = ACCOUNT_MENU.read_text(
        encoding="utf-8",
    )
    style = ACCOUNT_STYLE.read_text(
        encoding="utf-8",
    )

    account_menu_match = re.search(
        r"<AccountMenu\b[\s\S]*?/>",
        layout,
    )

    assert account_menu_match

    account_menu_jsx = account_menu_match.group(0)

    assert re.search(
        r"theme\s*=\s*\{\s*"
        r"themePreference\s*\}",
        account_menu_jsx,
    )
    assert re.search(
        r"onThemeChange\s*=\s*\{\s*"
        r"handleThemeChange\s*\}",
        account_menu_jsx,
    )

    assert "P8D2C_ACCOUNT_TWO_LEVEL_SETTINGS_V1" in style
    assert "activeView" in component
    assert "setActiveView('settings')" in component
    assert "setActiveView('menu')" in component
    assert 'data-view="main"' in component
    assert 'data-view="settings"' in component

    assert "Manage account" in component
    assert "Settings" in component
    assert "Theme and dashboard settings" in component
    assert "Back to account menu" in component

    assert "System" in component
    assert "Light" in component
    assert "Dark" in component
    assert "onThemeChange(" in component

    assert "<details className=\"account-settings\">" not in component
    assert ".account-settings-choice" in style
    assert ".account-primary-action" in style


def test_account_menu_preserves_logout_contract():
    component = ACCOUNT_MENU.read_text(
        encoding="utf-8",
    )

    assert "<form onSubmit={handleSignOut}>" in component
    assert "'/auth/logout'" in component
    assert "method: 'POST'" in component
    assert "credentials: 'include'" in component
    assert "window.location.assign" in component
    assert "Signing out…" in component
