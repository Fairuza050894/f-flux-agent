from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path('/Users/user/.hermes/hermes-agent')
HTML_PATH = ROOT / 'qa_dashboard' / 'frontend' / 'dashboard.html'
CSS_MARKER = '/* QA SIDEBAR MOUNT FIX V1.3 CSS */'
JS_MARKER = '/* QA SIDEBAR MOUNT FIX V1.3 JS */'


def fail(message: str) -> None:
    print(f'[ERROR] {message}')
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f'Dashboard file not found: {HTML_PATH}')

stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup = HTML_PATH.with_name(
    f'dashboard.html.backup_before_sidebar_mount_fix_v1_3_{stamp}'
)
shutil.copy2(HTML_PATH, backup)
text = HTML_PATH.read_text(encoding='utf-8')

css = r'''
/* QA SIDEBAR MOUNT FIX V1.3 CSS */

/* V1.2 hid this host. V1.3 uses it as the actual navigation container. */
#qaSidebarNavigation.qa-sidebar-nav-host {
  display: flex !important;
  min-height: 0 !important;
  flex: 1 1 auto !important;
  flex-direction: column !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow-y: auto !important;
  overflow-x: visible !important;
  visibility: visible !important;
  opacity: 1 !important;
}

#qaSidebarNavigation > #qaSidebarNavV1.qa-sidebar-nav-v1 {
  position: relative !important;
  inset: auto !important;
  display: flex !important;
  width: 100% !important;
  min-height: 0 !important;
  flex: 1 1 auto !important;
  flex-direction: column !important;
  gap: 20px !important;
  margin: 0 !important;
  padding: 18px 12px !important;
  overflow: visible !important;
  visibility: visible !important;
  opacity: 1 !important;
}

#qaSidebar.qa-sidebar-v1 {
  display: flex !important;
  width: 264px !important;
  min-width: 264px !important;
  min-height: 100vh !important;
  flex-direction: column !important;
  overflow: visible !important;
}

#qaSidebarNavV1 .qa-sidebar-group-v1,
#qaSidebarNavV1 .qa-sidebar-group-items-v1 {
  display: flex !important;
  flex-direction: column !important;
  visibility: visible !important;
  opacity: 1 !important;
}

#qaSidebarNavV1 .qa-sidebar-group-v1 {
  gap: 6px !important;
}

#qaSidebarNavV1 .qa-sidebar-group-items-v1 {
  gap: 5px !important;
}

#qaSidebarNavV1 .qa-sidebar-group-title-v1 {
  display: block !important;
  margin: 0 !important;
  padding: 0 11px 6px !important;
  color: #94a3b8 !important;
  font-size: 10px !important;
  font-weight: 800 !important;
  letter-spacing: .12em !important;
  line-height: 1 !important;
  text-transform: uppercase !important;
}

#qaSidebarNavV1 .qa-nav-item-v1 {
  position: relative !important;
  display: flex !important;
  width: 100% !important;
  min-height: 44px !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 11px !important;
  margin: 0 !important;
  padding: 10px 11px !important;
  border: 1px solid transparent !important;
  border-radius: 10px !important;
  background: transparent !important;
  color: #cbd5e1 !important;
  box-shadow: none !important;
  visibility: visible !important;
  opacity: 1 !important;
}

#qaSidebarNavV1 .qa-nav-item-v1:hover {
  border-color: rgba(148, 163, 184, .25) !important;
  background: rgba(255, 255, 255, .07) !important;
  color: #fff !important;
}

#qaSidebarNavV1 .qa-nav-item-v1.active,
#qaSidebarNavV1 .qa-nav-item-v1[aria-current='page'] {
  border-color: rgba(96, 165, 250, .38) !important;
  background: rgba(37, 99, 235, .22) !important;
  color: #fff !important;
  box-shadow: inset 3px 0 0 #60a5fa !important;
}

#qaSidebarNavV1 .qa-nav-icon-v1 {
  display: inline-flex !important;
  width: 20px !important;
  min-width: 20px !important;
  height: 20px !important;
  align-items: center !important;
  justify-content: center !important;
  color: inherit !important;
}

#qaSidebarNavV1 .qa-nav-icon-v1 svg {
  display: block !important;
  width: 19px !important;
  height: 19px !important;
  fill: none !important;
  stroke: currentColor !important;
}

#qaSidebarNavV1 .qa-nav-label-v1 {
  display: inline-block !important;
  min-width: 0 !important;
  overflow: hidden !important;
  color: inherit !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

#qaSidebarFooterV1.qa-sidebar-footer-v1 {
  display: block !important;
  flex: 0 0 auto !important;
  margin-top: auto !important;
}

#qaSidebarCollapseV1.qa-sidebar-collapse-v1 {
  border-color: rgba(148, 163, 184, .25) !important;
  background: rgba(255, 255, 255, .05) !important;
  color: #cbd5e1 !important;
}

#qaSidebarCollapseV1.qa-sidebar-collapse-v1:hover {
  background: rgba(255, 255, 255, .09) !important;
  color: #fff !important;
}

body.qa-sidebar-collapsed #qaSidebar.qa-sidebar-v1 {
  width: 76px !important;
  min-width: 76px !important;
}

body.qa-sidebar-collapsed #qaSidebarNavigation > #qaSidebarNavV1 {
  padding-right: 9px !important;
  padding-left: 9px !important;
}

body.qa-sidebar-collapsed #qaSidebarNavV1 .qa-sidebar-group-title-v1,
body.qa-sidebar-collapsed #qaSidebarNavV1 .qa-nav-label-v1,
body.qa-sidebar-collapsed #qaSidebarCollapseV1 .qa-sidebar-collapse-label-v1 {
  display: none !important;
}

body.qa-sidebar-collapsed #qaSidebarNavV1 .qa-nav-item-v1 {
  justify-content: center !important;
  padding: 10px !important;
}

@media (min-width: 901px) {
  body:not(.qa-sidebar-collapsed) .qa-app-shell {
    grid-template-columns: 264px minmax(0, 1fr) !important;
  }

  body.qa-sidebar-collapsed .qa-app-shell {
    grid-template-columns: 76px minmax(0, 1fr) !important;
  }
}

@media (max-width: 900px) {
  #qaSidebar.qa-sidebar-v1,
  body.qa-sidebar-collapsed #qaSidebar.qa-sidebar-v1 {
    width: 284px !important;
    min-width: 284px !important;
  }

  body.qa-sidebar-collapsed #qaSidebarNavV1 .qa-sidebar-group-title-v1,
  body.qa-sidebar-collapsed #qaSidebarNavV1 .qa-nav-label-v1 {
    display: block !important;
  }

  body.qa-sidebar-collapsed #qaSidebarNavV1 .qa-nav-item-v1 {
    justify-content: flex-start !important;
    padding: 10px 11px !important;
  }
}
'''

js = r'''
/* QA SIDEBAR MOUNT FIX V1.3 JS */
(function () {
  'use strict';

  let repairing = false;
  let scheduled = false;

  function ensureSidebarMountV13() {
    if (repairing) return;
    repairing = true;

    try {
      const sidebar =
        document.getElementById('qaSidebar')
        || document.querySelector(
          '.qa-sidebar, aside.qa-sidebar, [data-qa-sidebar]'
        );

      if (!sidebar) return;
      sidebar.classList.add('qa-sidebar-v1');

      let host = document.getElementById('qaSidebarNavigation');

      if (!host) {
        host = document.createElement('div');
        host.id = 'qaSidebarNavigation';
        host.className = 'qa-sidebar-nav-host';

        const footer = document.getElementById('qaSidebarFooterV1');

        if (footer && footer.parentElement === sidebar) {
          sidebar.insertBefore(host, footer);
        } else {
          sidebar.appendChild(host);
        }
      }

      host.hidden = false;
      host.removeAttribute('aria-hidden');

      if (
        typeof window.qaEnhanceSidebarV1 === 'function'
        && !document.getElementById('qaSidebarNavV1')
      ) {
        window.qaEnhanceSidebarV1();
      }

      const nav = document.getElementById('qaSidebarNavV1');
      if (!nav) return;

      nav.hidden = false;
      nav.removeAttribute('aria-hidden');

      if (nav.parentElement !== host) {
        host.appendChild(nav);
      }

      const footer = document.getElementById('qaSidebarFooterV1');
      if (
        footer
        && footer.parentElement === sidebar
        && host.nextElementSibling !== footer
      ) {
        sidebar.insertBefore(footer, host.nextSibling);
      }

      if (typeof window.qaSidebarSyncActiveState === 'function') {
        window.qaSidebarSyncActiveState();
      }
    } finally {
      repairing = false;
    }
  }

  function scheduleSidebarMountV13() {
    if (scheduled) return;
    scheduled = true;

    window.setTimeout(function () {
      scheduled = false;
      ensureSidebarMountV13();
    }, 0);
  }

  window.qaEnsureSidebarMountV13 = ensureSidebarMountV13;

  window.addEventListener('qa-project-changed', scheduleSidebarMountV13);
  window.addEventListener('load', function () {
    ensureSidebarMountV13();
    window.setTimeout(ensureSidebarMountV13, 250);
    window.setTimeout(ensureSidebarMountV13, 1000);
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ensureSidebarMountV13);
  } else {
    ensureSidebarMountV13();
  }

  const observer = new MutationObserver(scheduleSidebarMountV13);
  observer.observe(document.body, {childList: true, subtree: true});
})();
'''

if CSS_MARKER not in text:
    pos = text.rfind('</style>')
    if pos == -1:
        shutil.copy2(backup, HTML_PATH)
        fail('Closing </style> tag was not found')
    text = text[:pos] + '\n' + css + '\n' + text[pos:]
    print('[OK] Sidebar Mount Fix V1.3 CSS inserted')
else:
    print('[SKIP] Sidebar Mount Fix V1.3 CSS already exists')

if JS_MARKER not in text:
    pos = text.rfind('</script>')
    if pos == -1:
        shutil.copy2(backup, HTML_PATH)
        fail('Closing </script> tag was not found')
    text = text[:pos] + '\n' + js + '\n' + text[pos:]
    print('[OK] Sidebar Mount Fix V1.3 JavaScript inserted')
else:
    print('[SKIP] Sidebar Mount Fix V1.3 JavaScript already exists')

required = [
    CSS_MARKER,
    JS_MARKER,
    'function ensureSidebarMountV13()',
    "host.appendChild(nav)",
]
missing = [item for item in required if item not in text]

if missing:
    shutil.copy2(backup, HTML_PATH)
    fail('Verification failed. Dashboard restored. Missing: ' + ', '.join(missing))

HTML_PATH.write_text(text, encoding='utf-8')
print(f'[OK] Backup created: {backup}')
print(f'[OK] Updated: {HTML_PATH}')
print('\n[SUCCESS] Sidebar Mount Fix V1.3 installed')
