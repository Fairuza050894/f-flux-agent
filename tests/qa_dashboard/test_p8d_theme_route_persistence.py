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


def test_operations_uses_spa_navigation():
    layout = LAYOUT.read_text(
        encoding="utf-8",
    )

    assert 'href="/operations"' not in layout
    assert 'to="/operations"' in layout
    assert "p8c-operations-nav-link" in layout
    assert "<NavLink" in layout


def test_theme_selection_persists_to_account():
    component = ACCOUNT_MENU.read_text(
        encoding="utf-8",
    )

    assert (
        "P8D2C_THEME_ROUTE_PERSISTENCE_V1"
        in component
    )
    assert "handleThemeSelection" in component
    assert "auth.updateAccount" in component
    assert "account.revision ?? 0" in component
    assert "account.preferences ?? {}" in component
    assert "theme: nextTheme" in component
    assert "onThemeChange(previousTheme)" in component
    assert "disabled={themeSaving}" in component


def test_theme_persistence_feedback_is_styled():
    style = ACCOUNT_STYLE.read_text(
        encoding="utf-8",
    )

    assert (
        "P8D2C_THEME_ROUTE_PERSISTENCE_V1"
        in style
    )
    assert ".account-settings-theme-error" in style
    assert ".p8c-operations-nav-link.is-active" in style
