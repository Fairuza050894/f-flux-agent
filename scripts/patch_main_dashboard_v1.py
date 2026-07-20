from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path('/Users/user/.hermes/hermes-agent')
HTML_PATH = ROOT / 'qa_dashboard' / 'frontend' / 'dashboard.html'
CSS_MARKER = '/* QA MAIN DASHBOARD V1 CSS */'
JS_MARKER = '/* QA MAIN DASHBOARD V1 JS */'


def fail(message: str) -> None:
    print(f'[ERROR] {message}')
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f'Dashboard file not found: {HTML_PATH}')

stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = HTML_PATH.with_name(
    f'dashboard.html.backup_before_main_dashboard_v1_{stamp}'
)
shutil.copy2(HTML_PATH, backup_path)
text = HTML_PATH.read_text(encoding='utf-8')

css = r'''
/* QA MAIN DASHBOARD V1 CSS */
#tab-dashboard.qa-main-dashboard-panel-v1{padding-bottom:28px}
.qa-main-dashboard-v1{display:flex;flex-direction:column;gap:16px}
.qa-main-dashboard-heading-v1{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}
.qa-main-dashboard-title-v1{margin:0;color:#0f172a;font-size:20px;font-weight:850}
.qa-main-dashboard-subtitle-v1{max-width:720px;margin:5px 0 0;color:#64748b;font-size:12px;line-height:1.55}
.qa-main-dashboard-actions-v1{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:8px}
.qa-main-dashboard-button-v1{min-height:38px;padding:8px 12px;border:1px solid #cbd5e1;border-radius:9px;background:#fff;color:#334155;cursor:pointer;font-size:11px;font-weight:800}
.qa-main-dashboard-button-v1:hover{border-color:#93c5fd;background:#eff6ff;color:#1d4ed8}
.qa-main-dashboard-button-v1.primary{border-color:#2563eb;background:#2563eb;color:#fff}
.qa-main-dashboard-context-v1{display:grid;grid-template-columns:minmax(220px,1.4fr) repeat(3,minmax(120px,.7fr));gap:10px}
.qa-main-dashboard-context-card-v1{min-width:0;padding:13px 14px;border:1px solid #dbeafe;border-radius:11px;background:#f8fbff}
.qa-main-dashboard-label-v1{margin-bottom:4px;color:#64748b;font-size:9px;font-weight:850;letter-spacing:.08em;text-transform:uppercase}
.qa-main-dashboard-value-v1{overflow:hidden;color:#0f172a;font-size:13px;font-weight:850;text-overflow:ellipsis;white-space:nowrap}
.qa-main-dashboard-value-v1.large{font-size:18px}
.qa-main-dashboard-help-v1{margin-top:4px;color:#64748b;font-size:10px;line-height:1.45}
.qa-main-dashboard-metrics-v1{display:grid;grid-template-columns:repeat(4,minmax(150px,1fr));gap:10px}
.qa-main-dashboard-metric-v1{min-height:112px;padding:15px;border:1px solid #e2e8f0;border-radius:12px;background:#fff}
.qa-main-dashboard-metric-value-v1{margin-top:9px;color:#0f172a;font-size:27px;font-weight:900;letter-spacing:-.035em}
.qa-main-dashboard-metric-meta-v1{margin-top:7px;color:#64748b;font-size:10px;line-height:1.4}
.qa-main-dashboard-grid-v1{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:12px}
.qa-main-dashboard-card-v1{min-width:0;padding:16px;border:1px solid #e2e8f0;border-radius:12px;background:#fff}
.qa-main-dashboard-card-header-v1{display:flex;justify-content:space-between;gap:10px;margin-bottom:13px}
.qa-main-dashboard-card-title-v1{margin:0;color:#0f172a;font-size:13px;font-weight:850}
.qa-main-dashboard-card-help-v1{margin-top:4px;color:#64748b;font-size:10px;line-height:1.45}
.qa-main-dashboard-status-v1{display:inline-flex;min-height:24px;align-items:center;padding:3px 8px;border-radius:999px;background:#f1f5f9;color:#475569;font-size:9px;font-weight:850;text-transform:uppercase}
.qa-main-dashboard-status-v1.pass{background:#dcfce7;color:#166534}
.qa-main-dashboard-status-v1.failed{background:#fee2e2;color:#991b1b}
.qa-main-dashboard-status-v1.review{background:#fef3c7;color:#92400e}
.qa-main-dashboard-status-v1.running{background:#dbeafe;color:#1d4ed8}
.qa-main-dashboard-empty-v1{padding:22px 12px;border:1px dashed #cbd5e1;border-radius:10px;background:#f8fafc;color:#64748b;font-size:11px;line-height:1.55;text-align:center}
.qa-main-dashboard-live-v1,.qa-main-dashboard-findings-v1{display:flex;flex-direction:column;gap:9px}
.qa-main-dashboard-live-row-v1{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:center;padding:11px 12px;border:1px solid #e2e8f0;border-radius:10px;background:#f8fafc}
.qa-main-dashboard-live-title-v1{overflow:hidden;color:#0f172a;font-size:11px;font-weight:800;text-overflow:ellipsis;white-space:nowrap}
.qa-main-dashboard-live-meta-v1{margin-top:3px;color:#64748b;font-size:9px}
.qa-main-dashboard-finding-v1{padding:11px 12px;border-left:3px solid #f59e0b;border-radius:0 9px 9px 0;background:#fffbeb}
.qa-main-dashboard-finding-title-v1{color:#78350f;font-size:10px;font-weight:850;line-height:1.45}
.qa-main-dashboard-finding-meta-v1{margin-top:4px;color:#92400e;font-size:9px}
.qa-main-dashboard-table-wrap-v1{overflow-x:auto;border:1px solid #e2e8f0;border-radius:10px}
.qa-main-dashboard-table-v1{width:100%;min-width:720px;border-collapse:collapse}
.qa-main-dashboard-table-v1 th{padding:10px 12px;border-bottom:1px solid #e2e8f0;background:#f8fafc;color:#64748b;font-size:9px;font-weight:850;text-align:left;text-transform:uppercase}
.qa-main-dashboard-table-v1 td{padding:11px 12px;border-bottom:1px solid #f1f5f9;color:#334155;font-size:10px}
.qa-main-dashboard-table-primary-v1{color:#0f172a;font-weight:800}
.qa-main-dashboard-table-secondary-v1{margin-top:3px;color:#64748b;font-size:9px}
.qa-main-dashboard-loading-v1{min-height:180px;display:flex;align-items:center;justify-content:center;color:#64748b;font-size:11px}
@media(max-width:1050px){.qa-main-dashboard-context-v1,.qa-main-dashboard-metrics-v1{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:820px){.qa-main-dashboard-heading-v1{flex-direction:column}.qa-main-dashboard-actions-v1{justify-content:flex-start}.qa-main-dashboard-grid-v1{grid-template-columns:1fr}}
@media(max-width:560px){.qa-main-dashboard-context-v1,.qa-main-dashboard-metrics-v1{grid-template-columns:1fr}}
'''

js = r'''
/* QA MAIN DASHBOARD V1 JS */
(function(){
  'use strict';
  let refreshTimer=null;

  function esc(v){const e=document.createElement('div');e.textContent=String(v??'');return e.innerHTML}
  function projectId(){
    try{if(typeof qaSelectedProjectId!=='undefined'&&qaSelectedProjectId)return String(qaSelectedProjectId)}catch(_){ }
    return String(window.qaSelectedProjectId||document.querySelector('[data-qa-project-selector],#qaProjectSelector,select[id*="Project"]')?.value||'')
  }
  function project(){
    try{if(typeof qaSelectedProject!=='undefined'&&qaSelectedProject)return qaSelectedProject}catch(_){ }
    return window.qaSelectedProject||{}
  }
  function normalizeHistory(p){return Array.isArray(p)?p:(p?.history||p?.runs||p?.items||p?.data||[])}
  function dateValue(r){return r?.executed_at||r?.created_at||r?.started_at||r?.timestamp||r?.updated_at||''}
  function ts(r){const n=Date.parse(String(dateValue(r)||''));return Number.isFinite(n)?n:0}
  function fmtDate(v){if(!v)return'Not available';const d=new Date(v);return Number.isNaN(d.getTime())?String(v):new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'short'}).format(d)}
  function status(v){return String(v||'UNKNOWN').trim().replace(/[_-]+/g,' ').toUpperCase()}
  function statusClass(v){const s=status(v);if(['PASS','PASSED','SUCCESS'].includes(s))return'pass';if(['FAIL','FAILED','ERROR'].includes(s))return'failed';if(s.includes('REVIEW')||s.includes('WARNING'))return'review';if(s.includes('RUNNING')||s.includes('PROGRESS')||s.includes('QUEUED')||s.includes('STARTED'))return'running';return''}
  function num(o,keys){if(!o||typeof o!=='object')return null;for(const k of keys){const v=o[k];if(typeof v==='number'&&Number.isFinite(v))return v;if(typeof v==='string'&&v.trim()!==''&&Number.isFinite(Number(v)))return Number(v)}return null}
  function summary(run){
    if(!run)return null;
    const list=[run.summary,run.counts,run.metrics,run.result?.summary,run.standard_json?.summary,run.output?.summary,run];
    for(const o of list.filter(Boolean)){
      const passed=num(o,['passed','pass','passed_count','total_passed']);
      const failed=num(o,['failed','fail','failed_count','total_failed']);
      const review=num(o,['need_review','needReview','review','review_count','total_need_review']);
      const total=num(o,['total','total_tests','test_count','total_cases']);
      if(passed!==null||failed!==null||review!==null||total!==null){return{passed,failed,review,total:total!==null?total:[passed,failed,review].filter(v=>v!==null).reduce((a,b)=>a+b,0)}}
    }
    return null;
  }
  function feature(r){return r?.feature||r?.feature_name||r?.module||r?.suite_name||r?.name||'Unnamed execution'}
  function type(r){return r?.test_type||r?.type||r?.mode||r?.execution_mode||'Test'}
  function id(r){return r?.run_id||r?.id||r?.execution_id||'—'}
  function duration(r){const d=r?.duration||r?.duration_text||r?.elapsed||r?.elapsed_time;if(typeof d==='string'&&d.trim())return d;const ms=num(r,['duration_ms','elapsed_ms','response_time_ms']);return ms===null?'—':ms<1000?`${Math.round(ms)} ms`:`${(ms/1000).toFixed(1)} s`}
  function findingText(x){return typeof x==='string'?x.trim():String(x?.title||x?.message||x?.description||x?.finding||x?.recommendation||x?.summary||'').trim()}
  function findings(run){
    const out=[];const list=[run?.ai_findings,run?.findings,run?.recommendations,run?.anomalies,run?.analysis?.findings,run?.analysis?.recommendations,run?.result?.analysis?.findings,run?.standard_json?.analysis?.findings];
    list.forEach(v=>{(Array.isArray(v)?v:[v]).forEach(x=>{const t=findingText(x);if(t&&!out.includes(t))out.push(t)})});return out.slice(0,5)
  }
  async function loadProject(pid){try{const r=await fetch(`/projects/${encodeURIComponent(pid)}?_=${Date.now()}`,{cache:'no-store'});return r.ok?await r.json():null}catch(e){console.warn('Dashboard project detail unavailable',e);return null}}
  async function loadHistory(){try{const r=await fetch(`/history?limit=200&_=${Date.now()}`,{cache:'no-store'});return r.ok?normalizeHistory(await r.json()):[]}catch(e){console.warn('Dashboard history unavailable',e);try{return Array.isArray(paginatedHistoryRuns)?paginatedHistoryRuns:[]}catch(_){return[]}}}

  function addNav(){
    const nav=document.getElementById('qaSidebarNavV1');if(!nav||document.getElementById('qaMainDashboardNavV1'))return;
    const group=document.createElement('section');group.id='qaMainDashboardNavV1';group.className='qa-sidebar-group-v1';group.innerHTML=`<h2 class="qa-sidebar-group-title-v1">Overview</h2><div class="qa-sidebar-group-items-v1"><button class="tab-btn qa-nav-item-v1" type="button" onclick="showTab('dashboard')" data-qa-nav-key="dashboard" data-qa-panel-id="tab-dashboard" title="Dashboard"><span class="qa-nav-icon-v1"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1"></rect><rect x="14" y="3" width="7" height="7" rx="1"></rect><rect x="3" y="14" width="7" height="7" rx="1"></rect><rect x="14" y="14" width="7" height="7" rx="1"></rect></svg></span><span class="qa-nav-label-v1">Dashboard</span></button></div>`;
    nav.insertBefore(group,nav.firstElementChild);group.querySelector('button').addEventListener('click',()=>setTimeout(()=>refresh(true),30));
  }

  function addPanel(){
    let panel=document.getElementById('tab-dashboard');if(panel)return panel;
    const ref=document.getElementById('tab-registered');if(!ref||!ref.parentElement)return null;
    panel=document.createElement(ref.tagName||'section');panel.id='tab-dashboard';panel.className=ref.className;panel.classList.remove('active');panel.classList.add('qa-main-dashboard-panel-v1');panel.style.display='none';panel.innerHTML='<div class="qa-main-dashboard-v1" id="qaMainDashboardRootV1"><div class="qa-main-dashboard-loading-v1">Loading dashboard data…</div></div>';ref.parentElement.insertBefore(panel,ref);return panel;
  }

  function render(proj,detail,history){
    const root=document.getElementById('qaMainDashboardRootV1');if(!root)return;
    const pid=projectId();const name=proj.name||detail?.name||'No project selected';const env=proj.default_environment_name||proj.default_environment||detail?.default_environment_name||detail?.default_environment||'Not configured';const features=Array.isArray(detail?.features)?detail.features:[];const suites=Array.isArray(detail?.regression_suites)?detail.regression_suites:[];
    const runs=history.filter(r=>String(r?.project_id||'')===String(pid||'')).sort((a,b)=>ts(b)-ts(a));const latest=runs[0]||null;const s=summary(latest);const passRate=s&&s.total>0&&s.passed!==null?`${((s.passed/s.total)*100).toFixed(1)}%`:'—';const active=runs.filter(r=>statusClass(r.status)==='running');const f=findings(latest);
    const activeHtml=active.length?active.slice(0,4).map(r=>`<div class="qa-main-dashboard-live-row-v1"><div><div class="qa-main-dashboard-live-title-v1">${esc(feature(r))}</div><div class="qa-main-dashboard-live-meta-v1">${esc(type(r))} · ${esc(fmtDate(dateValue(r)))}</div></div><span class="qa-main-dashboard-status-v1 running">${esc(status(r.status))}</span></div>`).join(''):'<div class="qa-main-dashboard-empty-v1">No active execution was detected for the selected project.</div>';
    const findingHtml=f.length?f.map(x=>`<div class="qa-main-dashboard-finding-v1"><div class="qa-main-dashboard-finding-title-v1">${esc(x)}</div><div class="qa-main-dashboard-finding-meta-v1">Evidence: ${esc(latest?id(latest):'Not available')}</div></div>`).join(''):'<div class="qa-main-dashboard-empty-v1">No AI findings were available in the latest run data.</div>';
    const rows=runs.slice(0,7).map(r=>`<tr><td><div class="qa-main-dashboard-table-primary-v1">${esc(feature(r))}</div><div class="qa-main-dashboard-table-secondary-v1">${esc(id(r))}</div></td><td>${esc(type(r))}</td><td><span class="qa-main-dashboard-status-v1 ${statusClass(r.status)}">${esc(status(r.status))}</span></td><td>${esc(duration(r))}</td><td>${esc(fmtDate(dateValue(r)))}</td></tr>`).join('');
    root.innerHTML=`<div class="qa-main-dashboard-heading-v1"><div><h2 class="qa-main-dashboard-title-v1">Dashboard Overview</h2><p class="qa-main-dashboard-subtitle-v1">Real project data from the registry and execution history. No simulated metrics are displayed.</p></div><div class="qa-main-dashboard-actions-v1"><button class="qa-main-dashboard-button-v1" data-open-tab="history">View History</button><button class="qa-main-dashboard-button-v1" data-open-tab="custom">Open UI Testing</button><button class="qa-main-dashboard-button-v1 primary" data-open-tab="registered">Open Regression</button></div></div>
    <div class="qa-main-dashboard-context-v1"><div class="qa-main-dashboard-context-card-v1"><div class="qa-main-dashboard-label-v1">Active Project</div><div class="qa-main-dashboard-value-v1 large">${esc(name)}</div><div class="qa-main-dashboard-help-v1">Filtered by project ID: ${esc(pid||'not available')}</div></div><div class="qa-main-dashboard-context-card-v1"><div class="qa-main-dashboard-label-v1">Environment</div><div class="qa-main-dashboard-value-v1">${esc(env)}</div></div><div class="qa-main-dashboard-context-card-v1"><div class="qa-main-dashboard-label-v1">Registered Features</div><div class="qa-main-dashboard-value-v1">${features.length}</div></div><div class="qa-main-dashboard-context-card-v1"><div class="qa-main-dashboard-label-v1">Regression Suites</div><div class="qa-main-dashboard-value-v1">${suites.length}</div></div></div>
    <div class="qa-main-dashboard-metrics-v1"><div class="qa-main-dashboard-metric-v1"><div class="qa-main-dashboard-label-v1">Pass Rate</div><div class="qa-main-dashboard-metric-value-v1">${esc(passRate)}</div><div class="qa-main-dashboard-metric-meta-v1">${esc(latest?`Latest run: ${fmtDate(dateValue(latest))}`:'No project run found')}</div></div><div class="qa-main-dashboard-metric-v1"><div class="qa-main-dashboard-label-v1">Passed</div><div class="qa-main-dashboard-metric-value-v1">${esc(s?.passed??'—')}</div><div class="qa-main-dashboard-metric-meta-v1">Latest run summary.</div></div><div class="qa-main-dashboard-metric-v1"><div class="qa-main-dashboard-label-v1">Failed</div><div class="qa-main-dashboard-metric-value-v1">${esc(s?.failed??'—')}</div><div class="qa-main-dashboard-metric-meta-v1">Latest run summary.</div></div><div class="qa-main-dashboard-metric-v1"><div class="qa-main-dashboard-label-v1">Need Review</div><div class="qa-main-dashboard-metric-value-v1">${esc(s?.review??'—')}</div><div class="qa-main-dashboard-metric-meta-v1">Checks requiring review.</div></div></div>
    <div class="qa-main-dashboard-grid-v1"><section class="qa-main-dashboard-card-v1"><div class="qa-main-dashboard-card-header-v1"><div><h3 class="qa-main-dashboard-card-title-v1">Active Executions</h3><div class="qa-main-dashboard-card-help-v1">Queued, started, running, or in-progress runs.</div></div></div><div class="qa-main-dashboard-live-v1">${activeHtml}</div></section><section class="qa-main-dashboard-card-v1"><div class="qa-main-dashboard-card-header-v1"><div><h3 class="qa-main-dashboard-card-title-v1">AI Findings</h3><div class="qa-main-dashboard-card-help-v1">Findings stored with the latest execution.</div></div></div><div class="qa-main-dashboard-findings-v1">${findingHtml}</div></section></div>
    <section class="qa-main-dashboard-card-v1"><div class="qa-main-dashboard-card-header-v1"><div><h3 class="qa-main-dashboard-card-title-v1">Recent Results</h3><div class="qa-main-dashboard-card-help-v1">Seven most recent runs for the active project.</div></div></div>${rows?`<div class="qa-main-dashboard-table-wrap-v1"><table class="qa-main-dashboard-table-v1"><thead><tr><th>Feature / Run</th><th>Type</th><th>Status</th><th>Duration</th><th>Executed</th></tr></thead><tbody>${rows}</tbody></table></div>`:`<div class="qa-main-dashboard-empty-v1">No execution history with project ID ${esc(pid||'not available')} was found.</div>`}</section>`;
    root.querySelectorAll('[data-open-tab]').forEach(b=>b.addEventListener('click',()=>window.showTab?.(b.getAttribute('data-open-tab'))));
  }

  async function refresh(force){
    addNav();const panel=addPanel();if(!panel)return;const root=document.getElementById('qaMainDashboardRootV1');if(force&&root)root.innerHTML='<div class="qa-main-dashboard-loading-v1">Loading dashboard data…</div>';
    const pid=projectId();const [detail,history]=await Promise.all([loadProject(pid),loadHistory()]);render(project(),detail,history);
  }
  function schedule(force){clearTimeout(refreshTimer);refreshTimer=setTimeout(()=>refresh(force),120)}
  function init(){addPanel();addNav();schedule(true)}
  window.qaMainDashboardRefreshV1=refresh;
  window.addEventListener('qa-project-changed',()=>schedule(true));
  window.addEventListener('load',()=>{init();setTimeout(init,350)});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
'''

if CSS_MARKER not in text:
    pos = text.rfind('</style>')
    if pos == -1:
        shutil.copy2(backup_path, HTML_PATH)
        fail('Closing </style> tag was not found')
    text = text[:pos] + '\n' + css + '\n' + text[pos:]
    print('[OK] Main Dashboard V1 CSS inserted')
else:
    print('[SKIP] Main Dashboard V1 CSS already exists')

if JS_MARKER not in text:
    pos = text.rfind('</script>')
    if pos == -1:
        shutil.copy2(backup_path, HTML_PATH)
        fail('Closing </script> tag was not found')
    text = text[:pos] + '\n' + js + '\n' + text[pos:]
    print('[OK] Main Dashboard V1 JavaScript inserted')
else:
    print('[SKIP] Main Dashboard V1 JavaScript already exists')

required = [
    CSS_MARKER,
    JS_MARKER,
    'function addNav()',
    'function addPanel()',
    'async function refresh(force)',
    'qaMainDashboardRootV1',
]
missing = [item for item in required if item not in text]
if missing:
    shutil.copy2(backup_path, HTML_PATH)
    fail('Verification failed. Dashboard restored. Missing markers: ' + ', '.join(missing))

HTML_PATH.write_text(text, encoding='utf-8')
print(f'[OK] Backup created: {backup_path}')
print(f'[OK] Updated: {HTML_PATH}')
print()
print('[SUCCESS] Main Dashboard V1 installed')
