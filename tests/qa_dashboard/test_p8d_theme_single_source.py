from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

AUTH = (
    ROOT
    / "qa_dashboard"
    / "frontend_v3"
    / "src"
    / "features"
    / "auth"
    / "AuthenticatedApp.jsx"
)

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


def test_authenticated_app_does_not_mutate_dom_theme():
    source = AUTH.read_text(
        encoding="utf-8",
    )

    assert (
        "P8D2C_THEME_SINGLE_SOURCE_V1"
        in source
    )
    assert "applyThemePreference" not in source
    assert "persistThemePreference" not in source


def test_dashboard_layout_owns_theme_state():
    source = LAYOUT.read_text(
        encoding="utf-8",
    )

    assert (
        "P8D2C_THEME_SINGLE_SOURCE_V1"
        in source
    )
    assert "useDashboardAuth" in source
    assert "accountThemePreference" in source
    assert (
        "auth.account?.preferences?.theme"
        in source
    )
    assert "persistThemePreference(" in source
    assert "applyThemePreference(" in source


def test_saved_account_theme_reconciles_ui_state():
    source = ACCOUNT_MENU.read_text(
        encoding="utf-8",
    )

    assert "const savedAccount" in source
    assert (
        "savedAccount?.preferences?.theme"
        in source
    )
    assert "onThemeChange(savedTheme)" in source

def test_theme_is_not_synchronously_synced_in_effect():
    source = LAYOUT.read_text(
        encoding="utf-8",
    )

    assert (
        "P8D2C_THEME_INITIALIZER_ONLY_V1"
        in source
    )
    assert (
        "}, [accountThemePreference])"
        not in source
    )
