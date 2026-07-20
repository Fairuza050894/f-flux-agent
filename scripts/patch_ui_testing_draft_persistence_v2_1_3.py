from pathlib import Path
from datetime import datetime
import shutil
import sys


ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

JS_MARKER = "/* QA UI TESTING DRAFT PERSISTENCE V2.1.3 JS */"


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")


text = HTML_PATH.read_text(encoding="utf-8")

required_markers = [
    "/* QA UI TESTING WORKSPACE V2.1 JS */",
    "/* QA UI TESTING PANEL SCOPE V2.1.2 PATCHED */",
    "qa-ui-testing-titlebar-v212",
]

missing = [
    marker
    for marker in required_markers
    if marker not in text
]

if missing:
    fail(
        "Required UI Testing V2.1.2 markers were not found: "
        + ", ".join(missing)
    )


timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_ui_testing_draft_persistence_v2_1_3_{timestamp}"
)

shutil.copy2(
    HTML_PATH,
    backup_path,
)


js = r'''
/* QA UI TESTING DRAFT PERSISTENCE V2.1.3 JS */
(function () {
  "use strict";

  const STORAGE_PREFIX_V213 =
    "qa.ui-testing.draft.v213";

  const SENSITIVE_PATTERN_V213 =
    /(password|passwd|secret|token|cookie|authorization|credential|api.?key|session)/i;

  let currentPanelV213 = null;
  let currentStorageKeyV213 = "";
  let mutationObserverV213 = null;
  let restoreTimersV213 = [];
  let statusTimerV213 = null;
  let restoringV213 = false;

  function normalizeTextV213(value) {
    return String(value ?? "")
      .trim()
      .replace(/\s+/g, " ");
  }

  function findPanelV213() {
    const buttons = Array.from(
      document.querySelectorAll("button")
    ).filter(function (button) {
      return (
        normalizeTextV213(button.textContent)
        === "From Template"
        && !button.closest(
          "nav,aside,[role='navigation'],"
          + "#sidebar,.sidebar,[class*='sidebar']"
        )
      );
    });

    for (const button of buttons) {
      let current =
        button.parentElement;

      for (
        let depth = 0;
        current && depth < 9;
        depth += 1
      ) {
        const text =
          normalizeTextV213(
            current.textContent
          );

        const fieldCount =
          current.querySelectorAll(
            "input,select,textarea"
          ).length;

        const valid =
          text.includes("From Template")
          && text.includes("Add Custom")
          && text.includes("Test Information")
          && text.includes("Target")
          && text.includes("Validation")
          && text.includes("Execution Result")
          && fieldCount >= 2;

        const tooBroad =
          text.includes("API Status")
          || text.includes("Autonomous QA Flow")
          || text.includes("Collapse sidebar")
          || text.includes("Test Planning");

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

  function isPanelVisibleV213(panel) {
    if (!panel || !panel.isConnected) {
      return false;
    }

    const style =
      window.getComputedStyle(panel);

    return (
      !panel.hidden
      && style.display !== "none"
      && style.visibility !== "hidden"
      && panel.getClientRects().length > 0
    );
  }

  function projectIdV213() {
    const selectors = [
      "#qaDashboardProjectSelectV12",
      "[data-qa-project-selector]",
      "#qaProjectSelector",
      "select[id*='Project']",
      "select[name*='project' i]"
    ];

    for (const selector of selectors) {
      const element =
        document.querySelector(selector);

      if (
        element
        && element.tagName === "SELECT"
        && element.value
      ) {
        return normalizeTextV213(
          element.value
        );
      }
    }

    return "default";
  }

  function selectedModeV213(panel) {
    const buttons = Array.from(
      panel.querySelectorAll("button")
    ).filter(function (button) {
      const label =
        normalizeTextV213(
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
          || button.matches(
            "[data-active='true']"
          )
        );
      });

    const remembered =
      sessionStorage.getItem(
        STORAGE_PREFIX_V213
        + "."
        + projectIdV213()
        + ".mode"
      );

    return (
      normalizeTextV213(
        active && active.textContent
      )
      || remembered
      || normalizeTextV213(
        buttons[0] && buttons[0].textContent
      )
      || "From Template"
    );
  }

  function storageKeyV213(panel) {
    return [
      STORAGE_PREFIX_V213,
      projectIdV213(),
      selectedModeV213(panel)
        .toLowerCase()
        .replace(/\s+/g, "-")
    ].join(".");
  }

  function labelForControlV213(
    control,
    panel
  ) {
    if (control.id) {
      try {
        const explicit =
          panel.querySelector(
            `label[for="${CSS.escape(control.id)}"]`
          );

        if (explicit) {
          return normalizeTextV213(
            explicit.textContent
          );
        }
      } catch (_) {}
    }

    const wrappingLabel =
      control.closest("label");

    if (wrappingLabel) {
      return normalizeTextV213(
        wrappingLabel.textContent
      );
    }

    let current =
      control.parentElement;

    for (
      let depth = 0;
      current
      && current !== panel
      && depth < 4;
      depth += 1
    ) {
      const labels =
        Array.from(
          current.querySelectorAll(
            ":scope > label"
          )
        );

      if (labels.length) {
        return normalizeTextV213(
          labels[0].textContent
        );
      }

      current =
        current.parentElement;
    }

    return "";
  }

  function baseFieldKeyV213(
    control,
    panel
  ) {
    const semanticParts = [
      control.getAttribute(
        "data-qa-draft-key"
      ),
      control.name,
      control.id,
      control.getAttribute(
        "aria-label"
      ),
      labelForControlV213(
        control,
        panel
      ),
      control.placeholder
    ]
      .map(normalizeTextV213)
      .filter(Boolean);

    const semantic =
      semanticParts[0]
      || "unnamed";

    return [
      control.tagName.toLowerCase(),
      normalizeTextV213(
        control.type || ""
      ).toLowerCase(),
      semantic.toLowerCase()
    ].join(":");
  }

  function persistableControlsV213(panel) {
    const controls =
      Array.from(
        panel.querySelectorAll(
          "input,select,textarea"
        )
      );

    const counts = {};

    return controls
      .map(function (control) {
        const base =
          baseFieldKeyV213(
            control,
            panel
          );

        const occurrence =
          counts[base] || 0;

        counts[base] =
          occurrence + 1;

        return {
          control,
          key:
            base
            + "#"
            + occurrence
        };
      })
      .filter(function (entry) {
        const control =
          entry.control;

        if (
          !control
          || control.disabled
          || control.type === "password"
          || control.type === "hidden"
          || control.type === "file"
          || control.type === "submit"
          || control.type === "button"
          || control.type === "reset"
        ) {
          return false;
        }

        return !SENSITIVE_PATTERN_V213.test(
          entry.key
        );
      });
  }

  function readControlV213(control) {
    if (
      control.type === "checkbox"
      || control.type === "radio"
    ) {
      return {
        kind: control.type,
        checked:
          Boolean(control.checked),
        value:
          String(control.value || "")
      };
    }

    if (
      control.tagName === "SELECT"
      && control.multiple
    ) {
      return {
        kind: "select-multiple",
        values:
          Array.from(
            control.selectedOptions
          ).map(function (option) {
            return String(option.value);
          })
      };
    }

    return {
      kind:
        control.tagName.toLowerCase(),
      value:
        String(control.value || "")
    };
  }

  function writeControlV213(
    control,
    saved
  ) {
    if (
      !saved
      || document.activeElement === control
    ) {
      return false;
    }

    let changed = false;

    if (
      control.type === "checkbox"
      || control.type === "radio"
    ) {
      const nextChecked =
        Boolean(saved.checked);

      if (
        control.checked
        !== nextChecked
      ) {
        control.checked =
          nextChecked;

        changed = true;
      }
    } else if (
      control.tagName === "SELECT"
      && control.multiple
      && Array.isArray(
        saved.values
      )
    ) {
      const selected =
        new Set(
          saved.values.map(String)
        );

      Array.from(
        control.options
      ).forEach(function (option) {
        const nextSelected =
          selected.has(
            String(option.value)
          );

        if (
          option.selected
          !== nextSelected
        ) {
          option.selected =
            nextSelected;

          changed = true;
        }
      });
    } else {
      const nextValue =
        String(
          saved.value ?? ""
        );

      if (
        control.value
        !== nextValue
      ) {
        control.value =
          nextValue;

        changed = true;
      }
    }

    if (changed) {
      control.dispatchEvent(
        new Event(
          "input",
          { bubbles: true }
        )
      );

      control.dispatchEvent(
        new Event(
          "change",
          { bubbles: true }
        )
      );
    }

    return changed;
  }

  function setStatusV213(
    message,
    temporary
  ) {
    const badge =
      document.querySelector(
        ".qa-ui-testing-titlebar-v212 "
        + ".qa-ui-testing-draft-status-v21"
      );

    if (!badge) {
      return;
    }

    badge.textContent =
      message;

    window.clearTimeout(
      statusTimerV213
    );

    if (temporary) {
      statusTimerV213 =
        window.setTimeout(
          function () {
            badge.textContent =
              "Draft saved";
          },
          1200
        );
    }
  }

  function savePanelV213(
    panel,
    explicitKey
  ) {
    if (
      !panel
      || restoringV213
    ) {
      return;
    }

    const fields = {};

    persistableControlsV213(
      panel
    ).forEach(function (entry) {
      fields[entry.key] =
        readControlV213(
          entry.control
        );
    });

    const key =
      explicitKey
      || storageKeyV213(panel);

    const payload = {
      version: "2.1.3",
      project_id:
        projectIdV213(),
      mode:
        selectedModeV213(panel),
      saved_at:
        new Date().toISOString(),
      fields
    };

    try {
      sessionStorage.setItem(
        key,
        JSON.stringify(payload)
      );

      currentStorageKeyV213 =
        key;

      setStatusV213(
        "Draft saved",
        false
      );
    } catch (error) {
      console.warn(
        "UI Testing V2.1.3 draft save failed:",
        error
      );

      setStatusV213(
        "Draft not saved",
        false
      );
    }
  }

  function restorePanelV213(
    panel,
    explicitKey
  ) {
    if (!panel) {
      return 0;
    }

    const key =
      explicitKey
      || storageKeyV213(panel);

    let payload = null;

    try {
      const raw =
        sessionStorage.getItem(key);

      payload =
        raw
          ? JSON.parse(raw)
          : null;
    } catch (error) {
      console.warn(
        "UI Testing V2.1.3 draft restore failed:",
        error
      );
    }

    if (
      !payload
      || !payload.fields
    ) {
      setStatusV213(
        "Draft ready",
        false
      );

      return 0;
    }

    let restored = 0;

    restoringV213 = true;

    try {
      persistableControlsV213(
        panel
      ).forEach(function (entry) {
        const saved =
          payload.fields[
            entry.key
          ];

        if (
          saved
          && writeControlV213(
            entry.control,
            saved
          )
        ) {
          restored += 1;
        }
      });
    } finally {
      restoringV213 = false;
    }

    currentStorageKeyV213 =
      key;

    setStatusV213(
      restored
        ? "Draft restored"
        : "Draft saved",
      Boolean(restored)
    );

    return restored;
  }

  function clearRestoreTimersV213() {
    restoreTimersV213.forEach(
      window.clearTimeout
    );

    restoreTimersV213 = [];
  }

  function scheduleRestoreV213(
    panel
  ) {
    clearRestoreTimersV213();

    const delays = [
      0,
      80,
      220,
      500,
      900,
      1500
    ];

    delays.forEach(function (delay) {
      restoreTimersV213.push(
        window.setTimeout(
          function () {
            const current =
              findPanelV213()
              || panel;

            if (
              current
              && isPanelVisibleV213(
                current
              )
            ) {
              currentPanelV213 =
                current;

              restorePanelV213(
                current
              );
            }
          },
          delay
        )
      );
    });
  }

  function syncPanelV213() {
    const nextPanel =
      findPanelV213();

    if (
      currentPanelV213
      && currentPanelV213 !== nextPanel
    ) {
      savePanelV213(
        currentPanelV213,
        currentStorageKeyV213
          || undefined
      );
    }

    if (!nextPanel) {
      currentPanelV213 =
        null;

      return;
    }

    const nextKey =
      storageKeyV213(
        nextPanel
      );

    const panelChanged =
      currentPanelV213
      !== nextPanel;

    const keyChanged =
      currentStorageKeyV213
      !== nextKey;

    currentPanelV213 =
      nextPanel;

    if (
      isPanelVisibleV213(
        nextPanel
      )
      && (
        panelChanged
        || keyChanged
      )
    ) {
      currentStorageKeyV213 =
        nextKey;

      scheduleRestoreV213(
        nextPanel
      );
    }
  }

  document.addEventListener(
    "input",
    function (event) {
      const panel =
        currentPanelV213
        || findPanelV213();

      if (
        panel
        && panel.contains(
          event.target
        )
      ) {
        savePanelV213(panel);
      }
    },
    true
  );

  document.addEventListener(
    "change",
    function (event) {
      const panel =
        currentPanelV213
        || findPanelV213();

      if (
        panel
        && panel.contains(
          event.target
        )
      ) {
        savePanelV213(panel);
      }

      window.setTimeout(
        syncPanelV213,
        40
      );

      window.setTimeout(
        syncPanelV213,
        180
      );
    },
    true
  );

  /*
    Save before a sidebar navigation click can destroy or replace
    the UI Testing form.
  */
  document.addEventListener(
    "pointerdown",
    function () {
      if (
        currentPanelV213
        && isPanelVisibleV213(
          currentPanelV213
        )
      ) {
        savePanelV213(
          currentPanelV213
        );
      }
    },
    true
  );

  document.addEventListener(
    "click",
    function (event) {
      const modeButton =
        event.target.closest(
          "button"
        );

      const modeLabel =
        normalizeTextV213(
          modeButton
          && modeButton.textContent
        );

      if (
        currentPanelV213
        && (
          modeLabel === "From Template"
          || modeLabel === "Add Custom"
        )
      ) {
        sessionStorage.setItem(
          STORAGE_PREFIX_V213
          + "."
          + projectIdV213()
          + ".mode",
          modeLabel
        );
      }

      window.setTimeout(
        syncPanelV213,
        50
      );

      window.setTimeout(
        syncPanelV213,
        220
      );

      window.setTimeout(
        syncPanelV213,
        700
      );
    },
    true
  );

  window.addEventListener(
    "qa-project-changed",
    function () {
      if (currentPanelV213) {
        savePanelV213(
          currentPanelV213,
          currentStorageKeyV213
            || undefined
        );
      }

      currentStorageKeyV213 =
        "";

      window.setTimeout(
        syncPanelV213,
        80
      );

      window.setTimeout(
        syncPanelV213,
        350
      );
    }
  );

  window.addEventListener(
    "beforeunload",
    function () {
      if (currentPanelV213) {
        savePanelV213(
          currentPanelV213
        );
      }
    }
  );

  window.addEventListener(
    "pagehide",
    function () {
      if (currentPanelV213) {
        savePanelV213(
          currentPanelV213
        );
      }
    }
  );

  document.addEventListener(
    "visibilitychange",
    function () {
      if (document.hidden) {
        if (currentPanelV213) {
          savePanelV213(
            currentPanelV213
          );
        }
      } else {
        syncPanelV213();
      }
    }
  );

  if (!mutationObserverV213) {
    mutationObserverV213 =
      new MutationObserver(
        function (mutations) {
          const relevant =
            mutations.some(
              function (mutation) {
                const target =
                  mutation.target
                  && mutation.target.nodeType === 1
                    ? mutation.target
                    : mutation.target
                      && mutation.target.parentElement;

                if (
                  target
                  && target.closest(
                    ".qa-ui-testing-draft-status-v21"
                  )
                ) {
                  return false;
                }

                return (
                  mutation.addedNodes.length
                  || mutation.removedNodes.length
                );
              }
            );

          if (relevant) {
            window.setTimeout(
              syncPanelV213,
              30
            );
          }
        }
      );

    mutationObserverV213.observe(
      document.body,
      {
        childList: true,
        subtree: true
      }
    );
  }

  window.qaSaveUiTestingDraftV213 =
    function () {
      const panel =
        currentPanelV213
        || findPanelV213();

      savePanelV213(panel);
    };

  window.qaRestoreUiTestingDraftV213 =
    function () {
      const panel =
        currentPanelV213
        || findPanelV213();

      scheduleRestoreV213(panel);
    };

  if (
    document.readyState === "loading"
  ) {
    document.addEventListener(
      "DOMContentLoaded",
      syncPanelV213
    );
  } else {
    syncPanelV213();
  }

  window.addEventListener(
    "load",
    function () {
      syncPanelV213();

      window.setTimeout(
        syncPanelV213,
        300
      );

      window.setTimeout(
        syncPanelV213,
        900
      );
    }
  );
})();
'''


if JS_MARKER not in text:
    script_close = text.rfind("</script>")

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
        "[OK] UI Testing Draft Persistence V2.1.3 JavaScript inserted"
    )
else:
    print(
        "[SKIP] UI Testing Draft Persistence V2.1.3 already exists"
    )


verification_markers = [
    JS_MARKER,
    "function savePanelV213(",
    "function restorePanelV213(",
    "function scheduleRestoreV213(",
    "qaSaveUiTestingDraftV213",
    "qaRestoreUiTestingDraftV213",
]

missing_verification = [
    marker
    for marker in verification_markers
    if marker not in text
]

if missing_verification:
    shutil.copy2(
        backup_path,
        HTML_PATH
    )

    fail(
        "Verification failed. Dashboard restored. Missing markers: "
        + ", ".join(missing_verification)
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
    "[SUCCESS] UI Testing Draft Persistence V2.1.3 installed"
)
