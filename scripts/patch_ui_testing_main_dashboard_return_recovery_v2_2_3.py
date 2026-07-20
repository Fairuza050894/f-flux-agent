from pathlib import Path
from datetime import datetime
import ast
import shutil
import sys


ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

JS_MARKER = (
    "/* QA UI TESTING MAIN DASHBOARD RETURN "
    "RECOVERY V2.2.3 JS */"
)


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


if not HTML_PATH.exists():
    fail(
        f"Dashboard file not found: {HTML_PATH}"
    )


text = HTML_PATH.read_text(
    encoding="utf-8"
)

required_markers = [
    "/* QA UI TESTING PANEL SCOPE V2.1.2 PATCHED */",
    "/* QA UI TESTING DRAFT PERSISTENCE V2.1.3 JS */",
    "/* QA UI TESTING EXECUTION BRIDGE V2.2.2 JS */",
]

missing = [
    marker
    for marker in required_markers
    if marker not in text
]

if missing:
    fail(
        "Required UI Testing patches were not found: "
        + ", ".join(missing)
    )


stamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

backup_path = HTML_PATH.with_name(
    "dashboard.html.backup_before_"
    "ui_testing_main_dashboard_return_"
    f"recovery_v2_2_3_{stamp}"
)

shutil.copy2(
    HTML_PATH,
    backup_path,
)


js = r'''
/* QA UI TESTING MAIN DASHBOARD RETURN RECOVERY V2.2.3 JS */
(function () {
  "use strict";

  const STATE_KEY_V223 =
    "qa.ui-testing.return-recovery.v223";

  const DASHBOARD_BODY_CLASS_V223 =
    "qa-main-dashboard-active-v11";

  let dashboardWasActiveV223 =
    document.body.classList.contains(
      DASHBOARD_BODY_CLASS_V223
    );

  let recoveryTimersV223 = [];
  let recoveryInProgressV223 = false;
  let lastRecoveryAtV223 = 0;
  let observerV223 = null;

  function normalizeTextV223(value) {
    return String(value ?? "")
      .trim()
      .replace(/\s+/g, " ");
  }

  function visibleV223(element) {
    if (
      !element
      || !element.isConnected
    ) {
      return false;
    }

    const style =
      window.getComputedStyle(
        element
      );

    return (
      !element.hidden
      && style.display !== "none"
      && style.visibility !== "hidden"
      && element.getClientRects().length > 0
    );
  }

  function uiTestingShellV223() {
    const fromTemplateButtons =
      Array.from(
        document.querySelectorAll(
          "button"
        )
      ).filter(function (button) {
        return (
          normalizeTextV223(
            button.textContent
          ) === "From Template"
          && !button.closest(
            "nav,aside,[role='navigation'],"
            + "#sidebar,.sidebar,"
            + "[class*='sidebar']"
          )
        );
      });

    for (
      const button
      of fromTemplateButtons
    ) {
      const modeContainer =
        button.parentElement;

      const hasAddCustom =
        modeContainer
        && Array.from(
          modeContainer.querySelectorAll(
            "button"
          )
        ).some(function (candidate) {
          return (
            normalizeTextV223(
              candidate.textContent
            ) === "Add Custom"
          );
        });

      if (!hasAddCustom) {
        continue;
      }

      let current =
        modeContainer;

      for (
        let depth = 0;
        current && depth < 9;
        depth += 1
      ) {
        const content =
          normalizeTextV223(
            current.textContent
          );

        const valid =
          content.includes(
            "From Template"
          )
          && content.includes(
            "Add Custom"
          )
          && content.includes(
            "Execution Result"
          );

        const tooBroad =
          content.includes(
            "API Status"
          )
          || content.includes(
            "Autonomous QA Flow"
          )
          || content.includes(
            "Collapse sidebar"
          );

        if (
          valid
          && !tooBroad
        ) {
          return current;
        }

        current =
          current.parentElement;
      }
    }

    return null;
  }

  function uiTestingVisibleV223() {
    const shell =
      uiTestingShellV223();

    return Boolean(
      shell
      && visibleV223(shell)
    );
  }

  function fieldCountV223(shell) {
    return shell
      ? shell.querySelectorAll(
          "input,select,textarea"
        ).length
      : 0;
  }

  function currentModeV223(shell) {
    if (!shell) {
      return "From Template";
    }

    const buttons =
      Array.from(
        shell.querySelectorAll(
          "button"
        )
      ).filter(function (button) {
        const label =
          normalizeTextV223(
            button.textContent
          );

        return (
          label === "From Template"
          || label === "Add Custom"
        );
      });

    const active =
      buttons.find(function (button) {
        return (
          button.getAttribute(
            "aria-pressed"
          ) === "true"
          || button.classList.contains(
            "active"
          )
          || button.classList.contains(
            "selected"
          )
          || button.classList.contains(
            "primary"
          )
          || button.getAttribute(
            "data-active"
          ) === "true"
        );
      });

    return (
      normalizeTextV223(
        active
        && active.textContent
      )
      || normalizeTextV223(
        buttons[0]
        && buttons[0].textContent
      )
      || "From Template"
    );
  }

  function saveRecoveryStateV223() {
    const shell =
      uiTestingShellV223();

    const state = {
      mode:
        currentModeV223(shell),
      field_count:
        fieldCountV223(shell),
      saved_at:
        new Date().toISOString(),
      had_active_run:
        Boolean(
          typeof window
            .qaCurrentUiRunV222
            === "function"
          && window
            .qaCurrentUiRunV222()
        )
    };

    try {
      sessionStorage.setItem(
        STATE_KEY_V223,
        JSON.stringify(state)
      );
    } catch (_) {}

    if (
      typeof window
        .qaSaveUiTestingDraftV213
        === "function"
    ) {
      try {
        window
          .qaSaveUiTestingDraftV213();
      } catch (error) {
        console.warn(
          "UI Testing pre-dashboard "
          + "draft save failed:",
          error
        );
      }
    }
  }

  function readRecoveryStateV223() {
    try {
      const raw =
        sessionStorage.getItem(
          STATE_KEY_V223
        );

      return raw
        ? JSON.parse(raw)
        : {};
    } catch (_) {
      return {};
    }
  }

  function findModeButtonV223(
    shell,
    mode
  ) {
    if (!shell) {
      return null;
    }

    return Array.from(
      shell.querySelectorAll(
        "button"
      )
    ).find(function (button) {
      return (
        normalizeTextV223(
          button.textContent
        ) === mode
      );
    }) || null;
  }

  function ensureFormRenderedV223(
    shell
  ) {
    if (!shell) {
      return false;
    }

    const fields =
      fieldCountV223(shell);

    const hasTestInformation =
      normalizeTextV223(
        shell.textContent
      ).includes(
        "Test Information"
      );

    if (
      fields >= 2
      && hasTestInformation
    ) {
      return true;
    }

    const state =
      readRecoveryStateV223();

    const preferredMode =
      state.mode
      || "From Template";

    const modeButton =
      findModeButtonV223(
        shell,
        preferredMode
      )
      || findModeButtonV223(
        shell,
        "From Template"
      );

    if (!modeButton) {
      return false;
    }

    /*
      Re-run the existing mode renderer only when the form is
      actually missing. This does not create a new QA execution.
    */
    modeButton.click();

    return false;
  }

  function restoreDraftV223() {
    if (
      typeof window
        .qaRestoreUiTestingDraftV213
        !== "function"
    ) {
      return;
    }

    try {
      window
        .qaRestoreUiTestingDraftV213();
    } catch (error) {
      console.warn(
        "UI Testing return draft "
        + "restore failed:",
        error
      );
    }
  }

  function restoreExecutionV223() {
    if (
      typeof window
        .qaRehydrateUiRunV222
        !== "function"
    ) {
      return;
    }

    try {
      const result =
        window
          .qaRehydrateUiRunV222();

      if (
        result
        && typeof result.catch
          === "function"
      ) {
        result.catch(
          function (error) {
            console.warn(
              "UI Testing return run "
              + "rehydration failed:",
              error
            );
          }
        );
      }
    } catch (error) {
      console.warn(
        "UI Testing return run "
        + "rehydration failed:",
        error
      );
    }
  }

  function enhanceWorkspaceV223() {
    if (
      typeof window
        .qaEnhanceUiTestingV21
        !== "function"
    ) {
      return;
    }

    try {
      window
        .qaEnhanceUiTestingV21();
    } catch (error) {
      console.warn(
        "UI Testing workspace "
        + "enhancement failed:",
        error
      );
    }
  }

  function performRecoveryV223() {
    if (
      document.body.classList.contains(
        DASHBOARD_BODY_CLASS_V223
      )
    ) {
      return;
    }

    const shell =
      uiTestingShellV223();

    if (
      !shell
      || !visibleV223(shell)
    ) {
      return;
    }

    enhanceWorkspaceV223();

    const ready =
      ensureFormRenderedV223(
        shell
      );

    if (!ready) {
      return;
    }

    restoreDraftV223();
    restoreExecutionV223();

    lastRecoveryAtV223 =
      Date.now();
  }

  function clearRecoveryTimersV223() {
    recoveryTimersV223.forEach(
      window.clearTimeout
    );

    recoveryTimersV223 = [];
  }

  function scheduleRecoveryV223() {
    clearRecoveryTimersV223();

    if (recoveryInProgressV223) {
      return;
    }

    recoveryInProgressV223 =
      true;

    [
      0,
      60,
      150,
      320,
      650,
      1100,
      1800,
      2600
    ].forEach(function (delay) {
      recoveryTimersV223.push(
        window.setTimeout(
          function () {
            performRecoveryV223();

            if (
              delay === 2600
            ) {
              recoveryInProgressV223 =
                false;
            }
          },
          delay
        )
      );
    });
  }

  function dashboardStateChangedV223() {
    const dashboardActive =
      document.body.classList.contains(
        DASHBOARD_BODY_CLASS_V223
      );

    if (
      dashboardActive
      && !dashboardWasActiveV223
    ) {
      saveRecoveryStateV223();
    }

    if (
      !dashboardActive
      && dashboardWasActiveV223
    ) {
      scheduleRecoveryV223();
    }

    dashboardWasActiveV223 =
      dashboardActive;
  }

  document.addEventListener(
    "pointerdown",
    function (event) {
      const target =
        event.target.closest(
          "button,a,[role='button']"
        );

      if (!target) {
        return;
      }

      const label =
        normalizeTextV223(
          target.textContent
        );

      if (
        label === "Dashboard"
        && uiTestingVisibleV223()
      ) {
        saveRecoveryStateV223();
      }

      if (
        label === "UI Testing"
      ) {
        window.setTimeout(
          scheduleRecoveryV223,
          30
        );
      }
    },
    true
  );

  document.addEventListener(
    "click",
    function (event) {
      const target =
        event.target.closest(
          "button,a,[role='button']"
        );

      const label =
        normalizeTextV223(
          target
          && target.textContent
        );

      if (
        label === "UI Testing"
      ) {
        scheduleRecoveryV223();
      }
    },
    true
  );

  window.addEventListener(
    "qa-project-changed",
    function () {
      window.setTimeout(
        scheduleRecoveryV223,
        80
      );
    }
  );

  document.addEventListener(
    "visibilitychange",
    function () {
      if (!document.hidden) {
        scheduleRecoveryV223();
      }
    }
  );

  if (!observerV223) {
    observerV223 =
      new MutationObserver(
        function (mutations) {
          dashboardStateChangedV223();

          const meaningful =
            mutations.some(
              function (mutation) {
                if (
                  mutation.type
                  === "attributes"
                ) {
                  return (
                    mutation.target
                    === document.body
                  );
                }

                return (
                  mutation.addedNodes.length
                  || mutation.removedNodes.length
                );
              }
            );

          if (
            meaningful
            && !document.body
              .classList.contains(
                DASHBOARD_BODY_CLASS_V223
              )
            && uiTestingVisibleV223()
            && (
              Date.now()
              - lastRecoveryAtV223
            ) > 300
          ) {
            scheduleRecoveryV223();
          }
        }
      );

    observerV223.observe(
      document.body,
      {
        attributes: true,
        attributeFilter: [
          "class"
        ],
        childList: true,
        subtree: true
      }
    );
  }

  window.qaRecoverUiTestingAfterDashboardV223 =
    function () {
      scheduleRecoveryV223();
    };

  if (
    document.readyState
    === "loading"
  ) {
    document.addEventListener(
      "DOMContentLoaded",
      dashboardStateChangedV223
    );
  } else {
    dashboardStateChangedV223();
  }

  window.addEventListener(
    "load",
    function () {
      dashboardStateChangedV223();

      window.setTimeout(
        function () {
          if (
            uiTestingVisibleV223()
          ) {
            scheduleRecoveryV223();
          }
        },
        400
      );
    }
  );
})();
'''


if JS_MARKER not in text:
    script_close = text.rfind(
        "</script>"
    )

    if script_close == -1:
        shutil.copy2(
            backup_path,
            HTML_PATH
        )

        fail(
            "Closing </script> tag was not found"
        )

    text = (
        text[:script_close]
        + "\n"
        + js
        + "\n"
        + text[script_close:]
    )

    print(
        "[OK] UI Testing Main Dashboard "
        "Return Recovery V2.2.3 inserted"
    )
else:
    print(
        "[SKIP] UI Testing Main Dashboard "
        "Return Recovery V2.2.3 already exists"
    )


verification = [
    JS_MARKER,
    "function performRecoveryV223()",
    "function scheduleRecoveryV223()",
    "qaRecoverUiTestingAfterDashboardV223",
]

missing_verification = [
    marker
    for marker in verification
    if marker not in text
]

if missing_verification:
    shutil.copy2(
        backup_path,
        HTML_PATH
    )

    fail(
        "Verification failed. Dashboard restored. "
        "Missing markers: "
        + ", ".join(
            missing_verification
        )
    )


HTML_PATH.write_text(
    text,
    encoding="utf-8"
)

print(
    f"[OK] Backup created: {backup_path}"
)

print(
    f"[OK] Updated: {HTML_PATH}"
)

print()

print(
    "[SUCCESS] UI Testing Main Dashboard "
    "Return Recovery V2.2.3 installed"
)
