from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path('/Users/user/.hermes/hermes-agent')
HTML_PATH = ROOT / 'qa_dashboard' / 'frontend' / 'dashboard.html'
CSS_MARKER = '/* QA REGRESSION TESTING UX V2 CSS */'
JS_MARKER = '/* QA REGRESSION TESTING UX V2 JS */'


def fail(message: str) -> None:
    print(f'[ERROR] {message}')
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f'Dashboard file not found: {HTML_PATH}')

stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup = HTML_PATH.with_name(
    f'dashboard.html.backup_before_regression_testing_ux_v2_{stamp}'
)
shutil.copy2(HTML_PATH, backup)
text = HTML_PATH.read_text(encoding='utf-8')

css = r'''
/* QA REGRESSION TESTING UX V2 CSS */

#tab-registered.qa-regression-v2-ready > .form-row,
#tab-registered.qa-regression-v2-ready > #qaRegressionEmptyState {
  display: none !important;
}

.qa-regression-workspace-v2 {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 16px;
}

.qa-regression-context-v2 {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) repeat(3, minmax(110px, .7fr));
  gap: 10px;
  padding: 14px;
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: #f8fbff;
}

.qa-regression-context-label-v2,
.qa-regression-meta-label-v2 {
  margin-bottom: 4px;
  color: #64748b;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: .08em;
  text-transform: uppercase;
}

.qa-regression-context-value-v2,
.qa-regression-meta-value-v2 {
  overflow: hidden;
  color: #0f172a;
  font-size: 12px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.qa-regression-context-help-v2 {
  margin-top: 4px;
  color: #64748b;
  font-size: 10px;
  line-height: 1.45;
}

.qa-regression-card-v2 {
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
}

.qa-regression-card-title-v2 {
  margin: 0;
  color: #0f172a;
  font-size: 13px;
  font-weight: 800;
}

.qa-regression-card-help-v2 {
  margin: 4px 0 14px;
  color: #64748b;
  font-size: 11px;
  line-height: 1.45;
}

.qa-regression-grid-v2 {
  display: grid;
  grid-template-columns: minmax(260px, 1.25fr) minmax(250px, 1fr);
  gap: 14px;
}

.qa-regression-field-v2 {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.qa-regression-field-v2 label {
  margin: 0;
  color: #334155;
  font-size: 11px;
  font-weight: 800;
}

.qa-regression-field-v2 select,
.qa-regression-field-v2 input {
  width: 100%;
  min-height: 42px;
  margin: 0;
}

.qa-regression-helper-v2 {
  color: #64748b;
  font-size: 10px;
  line-height: 1.45;
}

.qa-regression-feature-info-v2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 13px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
}

.qa-regression-badge-v2 {
  display: inline-flex;
  min-height: 23px;
  align-items: center;
  padding: 3px 8px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #475569;
  font-size: 9px;
  font-weight: 800;
  text-transform: uppercase;
}

.qa-regression-badge-v2.pass { background: #dcfce7; color: #166534; }
.qa-regression-badge-v2.fail { background: #fee2e2; color: #991b1b; }
.qa-regression-badge-v2.review { background: #fef3c7; color: #92400e; }
.qa-regression-badge-v2.active { background: #dbeafe; color: #1d4ed8; }

.qa-regression-advanced-v2 {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
}

.qa-regression-advanced-v2 summary {
  display: flex;
  min-height: 46px;
  align-items: center;
  justify-content: space-between;
  padding: 0 15px;
  color: #334155;
  cursor: pointer;
  font-size: 11px;
  font-weight: 800;
  list-style: none;
}

.qa-regression-advanced-v2 summary::-webkit-details-marker { display: none; }
.qa-regression-advanced-v2 summary::after { content: '⌄'; color: #64748b; font-size: 16px; }
.qa-regression-advanced-v2[open] summary::after { transform: rotate(180deg); }

.qa-regression-advanced-content-v2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  padding: 0 15px 15px;
}

.qa-regression-action-v2 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: #f8fbff;
}

.qa-regression-action-title-v2 {
  color: #0f172a;
  font-size: 11px;
  font-weight: 800;
}

.qa-regression-action-help-v2 {
  margin-top: 3px;
  color: #64748b;
  font-size: 10px;
}

.qa-regression-action-v2 #runRegisteredBtn {
  width: auto;
  min-width: 190px;
  margin: 0;
  white-space: nowrap;
}

.qa-regression-empty-v2 {
  padding: 30px 22px;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  background: #f8fafc;
  text-align: center;
}

.qa-regression-empty-title-v2 {
  color: #0f172a;
  font-size: 13px;
  font-weight: 800;
}

.qa-regression-empty-help-v2 {
  max-width: 520px;
  margin: 7px auto 0;
  color: #64748b;
  font-size: 11px;
  line-height: 1.55;
}

.qa-regression-hidden-v2 { display: none !important; }

@media (max-width: 980px) {
  .qa-regression-context-v2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .qa-regression-grid-v2 { grid-template-columns: 1fr; }
}

@media (max-width: 650px) {
  .qa-regression-context-v2,
  .qa-regression-advanced-content-v2,
  .qa-regression-feature-info-v2 { grid-template-columns: 1fr; }
  .qa-regression-action-v2 { align-items: stretch; flex-direction: column; }
  .qa-regression-action-v2 #runRegisteredBtn { width: 100%; }
}
'''

js = r'''
/* QA REGRESSION TESTING UX V2 JS */
(function () {
  'use strict';

  let historyCache = [];
  let refreshTimer = null;

  function projectId() {
    try {
      if (typeof qaSelectedProjectId !== 'undefined' && qaSelectedProjectId) {
        return String(qaSelectedProjectId);
      }
    } catch (_) {}
    return String(window.qaSelectedProject?.project_id || '');
  }

  function projectData() {
    try {
      if (typeof qaSelectedProject !== 'undefined' && qaSelectedProject) {
        return qaSelectedProject;
      }
    } catch (_) {}
    return window.qaSelectedProject || {};
  }

  function projectDetail(id) {
    try {
      if (typeof qaProjectDetailCache !== 'undefined' && qaProjectDetailCache?.[id]) {
        return qaProjectDetailCache[id];
      }
    } catch (_) {}
    return null;
  }

  function normalizeHistory(payload) {
    if (Array.isArray(payload)) return payload;
    if (Array.isArray(payload?.history)) return payload.history;
    if (Array.isArray(payload?.runs)) return payload.runs;
    if (Array.isArray(payload?.items)) return payload.items;
    return [];
  }

  async function loadHistory() {
    try {
      const response = await fetch('/history?limit=200&_=' + Date.now(), {
        cache: 'no-store'
      });
      if (!response.ok) throw new Error('History request failed');
      historyCache = normalizeHistory(await response.json());
    } catch (error) {
      console.warn('Regression last-run metadata unavailable:', error);
      try {
        if (typeof paginatedHistoryRuns !== 'undefined' && Array.isArray(paginatedHistoryRuns)) {
          historyCache = paginatedHistoryRuns;
        }
      } catch (_) {}
    }
    return historyCache;
  }

  function statusClass(value) {
    const status = String(value || '').toUpperCase();
    if (status === 'PASS') return 'pass';
    if (status === 'FAIL' || status === 'FAILED') return 'fail';
    if (status.includes('REVIEW') || status.includes('WARNING')) return 'review';
    return 'active';
  }

  function formatDate(value) {
    if (!value) return 'No run yet';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short'
    }).format(date);
  }

  function latestRun(items, activeProjectId, featureName) {
    return items
      .filter((run) =>
        String(run?.project_id || '') === String(activeProjectId || '')
        && String(run?.feature || '') === String(featureName || '')
      )
      .sort((a, b) =>
        Date.parse(b.executed_at || b.created_at || 0)
        - Date.parse(a.executed_at || a.created_at || 0)
      )[0] || null;
  }

  function ensureWorkspace() {
    const tab = document.getElementById('tab-registered');
    const url = document.getElementById('registeredUrl');
    const feature = document.getElementById('registeredFeature');
    const mode = document.getElementById('registeredMode');
    const run = document.getElementById('runRegisteredBtn');
    const result = document.getElementById('registeredResult');

    if (!tab || !url || !feature || !mode || !run || !result) return null;

    let workspace = document.getElementById('qaRegressionWorkspaceV2');
    if (workspace) return {tab, workspace, url, feature, mode, run, result};

    workspace = document.createElement('div');
    workspace.id = 'qaRegressionWorkspaceV2';
    workspace.className = 'qa-regression-workspace-v2';
    workspace.innerHTML = `
      <div class="qa-regression-context-v2" id="qaRegressionContextV2"></div>

      <div class="qa-regression-empty-v2 qa-regression-hidden-v2" id="qaRegressionEmptyV2">
        <div class="qa-regression-empty-title-v2">No registered regression features</div>
        <div class="qa-regression-empty-help-v2">
          Ad-hoc Testing is intended for direct UI and API execution.
          Select a reusable project with a feature registry before running regression testing.
        </div>
      </div>

      <div id="qaRegressionConfiguredV2">
        <div class="qa-regression-card-v2">
          <h3 class="qa-regression-card-title-v2">Test Selection</h3>
          <div class="qa-regression-card-help-v2">
            Select one registered feature from the active project.
          </div>

          <div class="qa-regression-grid-v2">
            <div class="qa-regression-field-v2" id="qaRegressionFeatureSlotV2">
              <label for="registeredFeature">Feature <span style="color:#dc2626">*</span></label>
              <div class="qa-regression-helper-v2">
                Available features are loaded from the active project registry.
              </div>
            </div>
            <div class="qa-regression-feature-info-v2" id="qaRegressionFeatureInfoV2"></div>
          </div>
        </div>

        <details class="qa-regression-advanced-v2">
          <summary>Advanced Options</summary>
          <div class="qa-regression-advanced-content-v2">
            <div class="qa-regression-field-v2" id="qaRegressionModeSlotV2">
              <label for="registeredMode">Execution Mode</label>
              <div class="qa-regression-helper-v2">
                Regression is recommended for registered project features.
              </div>
            </div>
            <div class="qa-regression-field-v2" id="qaRegressionUrlSlotV2">
              <label for="registeredUrl">Base URL Override</label>
              <div class="qa-regression-helper-v2">
                Leave empty to use the active project environment configuration.
              </div>
            </div>
          </div>
        </details>

        <div class="qa-regression-action-v2">
          <div>
            <div class="qa-regression-action-title-v2" id="qaRegressionActionTitleV2">
              Ready to run regression testing
            </div>
            <div class="qa-regression-action-help-v2" id="qaRegressionActionHelpV2">
              Existing telemetry, analysis, and artifact flow will be used.
            </div>
          </div>
          <div id="qaRegressionRunSlotV2"></div>
        </div>
      </div>
    `;

    const banner = tab.querySelector('[id^="qaProjectContextBanner-"]');
    const heading = tab.querySelector('h2');
    (banner || heading)?.insertAdjacentElement('afterend', workspace);

    document.getElementById('qaRegressionFeatureSlotV2').appendChild(feature);
    document.getElementById('qaRegressionModeSlotV2').appendChild(mode);
    document.getElementById('qaRegressionUrlSlotV2').appendChild(url);
    document.getElementById('qaRegressionRunSlotV2').appendChild(run);

    run.textContent = 'Run Regression Test';
    url.placeholder = 'Uses project environment when empty';
    feature.setAttribute('aria-required', 'true');
    tab.classList.add('qa-regression-v2-ready');

    feature.addEventListener('change', () => scheduleRefresh(false));
    mode.addEventListener('change', () => scheduleRefresh(false));

    return {tab, workspace, url, feature, mode, run, result};
  }

  async function refresh(forceHistory) {
    const elements = ensureWorkspace();
    if (!elements) return;

    const activeProjectId = projectId();
    const project = projectData();
    const detail = projectDetail(activeProjectId);
    const features = Array.isArray(detail?.features) ? detail.features : [];
    const suites = Array.isArray(detail?.regression_suites) ? detail.regression_suites : [];
    const available = activeProjectId !== 'adhoc' && features.length > 0;
    const environment = project.default_environment_name || project.default_environment || 'Custom';
    const projectName = project.name || 'No project selected';

    document.getElementById('qaRegressionConfiguredV2').classList.toggle('qa-regression-hidden-v2', !available);
    document.getElementById('qaRegressionEmptyV2').classList.toggle('qa-regression-hidden-v2', available);

    document.getElementById('qaRegressionContextV2').innerHTML = `
      <div>
        <div class="qa-regression-context-label-v2">Active Project</div>
        <div class="qa-regression-context-value-v2">${projectName}</div>
        <div class="qa-regression-context-help-v2">Content is loaded from the selected project registry.</div>
      </div>
      <div><div class="qa-regression-context-label-v2">Environment</div><div class="qa-regression-context-value-v2">${environment}</div></div>
      <div><div class="qa-regression-context-label-v2">Features</div><div class="qa-regression-context-value-v2">${features.length}</div></div>
      <div><div class="qa-regression-context-label-v2">Suites</div><div class="qa-regression-context-value-v2">${suites.length}</div></div>
    `;

    elements.feature.disabled = !available;
    elements.run.disabled = !available || !elements.feature.value;
    if (!available) return;

    const selectedName = elements.feature.value;
    const selectedFeature = features.find((item) =>
      String(item.runner_feature_name || item.name || item.feature_id || '') === selectedName
    ) || {};

    const history = forceHistory || !historyCache.length ? await loadHistory() : historyCache;
    const run = latestRun(history, activeProjectId, selectedName);
    const lastStatus = run?.status || 'No run';
    const type = String(selectedFeature.test_type || 'ui_regression').replace(/_/g, ' ');
    const registryStatus = selectedFeature.status || 'active';

    document.getElementById('qaRegressionFeatureInfoV2').innerHTML = `
      <div><div class="qa-regression-meta-label-v2">Type</div><div class="qa-regression-meta-value-v2">${type}</div></div>
      <div><div class="qa-regression-meta-label-v2">Registry Status</div><div class="qa-regression-meta-value-v2"><span class="qa-regression-badge-v2 active">${registryStatus}</span></div></div>
      <div><div class="qa-regression-meta-label-v2">Last Run</div><div class="qa-regression-meta-value-v2"><span class="qa-regression-badge-v2 ${statusClass(lastStatus)}">${lastStatus}</span></div></div>
      <div><div class="qa-regression-meta-label-v2">Last Executed</div><div class="qa-regression-meta-value-v2">${formatDate(run?.executed_at || run?.created_at)}</div></div>
    `;

    document.getElementById('qaRegressionActionTitleV2').textContent =
      selectedName ? 'Ready to run: ' + selectedName : 'Select a feature';
    document.getElementById('qaRegressionActionHelpV2').textContent =
      `Project: ${projectName} · Environment: ${environment} · Mode: ${elements.mode.value || 'regression'}`;
  }

  function scheduleRefresh(forceHistory) {
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(() => refresh(forceHistory), 120);
  }

  window.qaRegressionRefreshV2 = refresh;
  window.addEventListener('qa-project-changed', () => setTimeout(() => refresh(true), 250));
  window.addEventListener('load', () => {
    ensureWorkspace();
    setTimeout(() => refresh(true), 350);
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ensureWorkspace);
  } else {
    ensureWorkspace();
  }
})();
'''

if CSS_MARKER not in text:
    pos = text.rfind('</style>')
    if pos == -1:
        shutil.copy2(backup, HTML_PATH)
        fail('Closing </style> tag was not found')
    text = text[:pos] + '\n' + css + '\n' + text[pos:]
    print('[OK] Regression Testing UX V2 CSS inserted')
else:
    print('[SKIP] Regression Testing UX V2 CSS already exists')

if JS_MARKER not in text:
    pos = text.rfind('</script>')
    if pos == -1:
        shutil.copy2(backup, HTML_PATH)
        fail('Closing </script> tag was not found')
    text = text[:pos] + '\n' + js + '\n' + text[pos:]
    print('[OK] Regression Testing UX V2 JavaScript inserted')
else:
    print('[SKIP] Regression Testing UX V2 JavaScript already exists')

required = [
    CSS_MARKER,
    JS_MARKER,
    'function ensureWorkspace()',
    'function refresh(forceHistory)',
    'qaRegressionWorkspaceV2',
]
missing = [item for item in required if item not in text]

if missing:
    shutil.copy2(backup, HTML_PATH)
    fail('Verification failed. Dashboard restored. Missing markers: ' + ', '.join(missing))

HTML_PATH.write_text(text, encoding='utf-8')
print(f'[OK] Backup created: {backup}')
print(f'[OK] Updated: {HTML_PATH}')
print('\n[SUCCESS] Regression Testing UX V2 installed')
