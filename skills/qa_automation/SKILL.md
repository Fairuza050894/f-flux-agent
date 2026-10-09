---
name: qa-automation
description: "Playwright E2E/regression audits and QA documentation for the fork's BOSpace features."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qa, testing, playwright, e2e, regression, documentation, bospace]
    category: qa-automation
    related_skills: [veriflow-trigger, agency-agents, autodev-launcher]
    config:
      default_url: "https://mobospace-sandbox.pancaran-group.co.id"
      default_module: "Uang Makan Driver"
      default_mode: "regression"
---

# QA Automation

Drives headless Chrome through Playwright to run E2E/regression audits, diff screenshots against
baselines, and generate QA documentation. Implementation: `skills/qa_automation/checker.py`
(`__init__.py` exports `perform_audit` and `perform_audit_for_telegram`).

## When to Use

- "audit QA", "regression test", "smoke test", "QA documentation" for a BOSpace page or module
- Telegram `/audit_qa mode=<smoke|regression|documentation|full> fitur=<...> [url=...]` (fork gateway)
- Turning a manual test checklist into PASS/FAIL evidence with screenshots

## Prerequisites

- `playwright` (Python) — installed by `hermes pm install --extra google-meet`
- A Chrome build. The skill drives the pm-managed Chrome for Testing automatically
  (`AGENT_BROWSER_EXECUTABLE_PATH`, else the newest `~/.hermes/tools/chromium-*`); override with
  `QA_CHROMIUM_EXECUTABLE`. `hermes pm gc` prunes browser dirs it does not track, so never vendor a
  second copy next to pm's.
- Credentials: `BOSPACE_USER` / `BOSPACE_PASS` in `skills/qa_automation/.env`, with the per-host
  mapping (`user_env` / `pass_env`) in `skills/qa_automation/config.json`.

## Usage

```python
from skills.qa_automation import perform_audit

summary = perform_audit(                       # returns the testing-summary text
    url="https://mobospace-sandbox.pancaran-group.co.id",
    module_name="Uang Makan Driver",
    mode="regression",                         # smoke | regression | documentation | full
)
print(summary)
```

For chat/Telegram delivery (adds metadata and the report files):

```python
from skills.qa_automation import perform_audit_for_telegram

result = perform_audit_for_telegram(
    url="https://mobospace-sandbox.pancaran-group.co.id",
    module_name="Uang Makan Driver",
    mode="regression",
    environment="Sandbox",
)
```

Feature suites: `perform_driver_daily_meal_combined_suite`, `perform_shipment_details_suite`,
`perform_mobomap_suite`, `perform_inspection_result_suite`, `perform_notification_messages_suite`,
`perform_notification_management_suite`, `perform_all_features_suite`, `perform_custom_smoke_test`,
`perform_qa_list_suite`, `perform_qa_help_suite`, `perform_qa_history_suite`.

## Outputs

Everything lands under `skills/qa_automation/artifacts/` — `screenshots/`, `diffs/` (against
`baselines/`), `reports/`, `logs/`, `spreadsheets/`, `debug/`. `telegram_router.py` chunks long
reports to Telegram's 3900-character limit.
