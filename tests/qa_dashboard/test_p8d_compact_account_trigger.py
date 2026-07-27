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

ACCOUNT_STYLE = (
    ROOT
    / "qa_dashboard"
    / "frontend_v3"
    / "src"
    / "styles"
    / "account.css"
)


def test_account_trigger_is_compact_and_accessible():
    component = ACCOUNT_MENU.read_text(
        encoding="utf-8",
    )
    style = ACCOUNT_STYLE.read_text(
        encoding="utf-8",
    )

    assert (
        "Open account menu for "
        "${displayName}"
        in component
    )
    assert (
        "P8D2C_COMPACT_AVATAR_"
        "ACCOUNT_TRIGGER_V1"
        in style
    )
    assert (
        "--account-trigger-size: 48px"
        in style
    )
    assert (
        ".account-trigger-copy"
        in style
    )
    assert (
        ".account-menu-popover"
        in style
    )
