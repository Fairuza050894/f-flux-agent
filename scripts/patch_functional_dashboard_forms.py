from pathlib import Path
from datetime import datetime
import re
import shutil

ROOT = Path.cwd()
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

if not HTML_PATH.exists():
    raise SystemExit(
        "dashboard.html tidak ditemukan. Jalankan script dari root repository: "
        "/Users/user/.hermes/hermes-agent"
    )

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_functional_forms_{stamp}"
)
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text(encoding="utf-8")


def find_balanced_element(source: str, element_id: str):
    id_match = re.search(
        rf'\bid=["\']{re.escape(element_id)}["\']',
        source,
    )
    if not id_match:
        return None

    opening_start = source.rfind("<", 0, id_match.start())
    opening_end = source.find(">", id_match.end())
    if opening_start == -1 or opening_end == -1:
        return None

    opening_tag = source[opening_start : opening_end + 1]
    tag_match = re.match(r"<([a-zA-Z0-9_-]+)\b", opening_tag)
    if not tag_match:
        return None

    tag_name = tag_match.group(1)
    token_pattern = re.compile(
        rf"</?{re.escape(tag_name)}\b[^>]*>",
        flags=re.IGNORECASE,
    )

    depth = 0
    for token in token_pattern.finditer(source, opening_start):
        token_text = token.group(0)
        is_closing = token_text.startswith("</")
        is_self_closing = token_text.rstrip().endswith("/>")

        if is_closing:
            depth -= 1
            if depth == 0:
                return opening_start, token.end(), source[opening_start : token.end()]
        elif not is_self_closing:
            depth += 1

    return None


def replace_element_by_id(source: str, element_id: str, replacement: str):
    found = find_balanced_element(source, element_id)
    if not found:
        raise RuntimeError(f"Elemen tidak ditemukan: {element_id}")
    start, end, _ = found
    return source[:start] + replacement.strip() + source[end:]


def find_function_block(source: str, function_name: str):
    pattern = re.compile(
        rf"(?m)^[ \t]*(?:async[ \t]+)?function[ \t]+"
        rf"{re.escape(function_name)}[ \t]*\("
    )
    match = pattern.search(source)
    if not match:
        return None

    opening_brace = source.find("{", match.end())
    if opening_brace == -1:
        return None

    depth = 0
    quote = None
    escaped = False
    in_line_comment = False
    in_block_comment = False

    index = opening_brace
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
            index += 1
            continue

        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
                index += 2
                continue
            index += 1
            continue

        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue

        if char == "/" and next_char == "/":
            in_line_comment = True
            index += 2
            continue

        if char == "/" and next_char == "*":
            in_block_comment = True
            index += 2
            continue

        if char in ("'", '"', "`"):
            quote = char
            index += 1
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return match.start(), index + 1, source[match.start() : index + 1]

        index += 1

    return None


def replace_function(source: str, function_name: str, replacement: str):
    found = find_function_block(source, function_name)
    if not found:
        raise RuntimeError(f"Fungsi JavaScript tidak ditemukan: {function_name}")
    start, end, _ = found
    return source[:start] + replacement.rstrip() + source[end:]


CSS = r'''
    /* ========================================================
       Functional Workspace Forms
       ======================================================== */

    .qa-page-heading {
      margin-bottom: 16px;
    }

    .qa-page-heading h2 {
      margin-bottom: 5px;
    }

    .qa-page-heading p {
      margin: 0;
      max-width: 820px;
    }

    .qa-form-stack {
      display: grid;
      gap: 14px;
    }

    .qa-form-card {
      padding: 16px;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      background: #ffffff;
    }

    .qa-form-card-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
    }

    .qa-form-card-header h3 {
      margin: 0 0 4px;
      color: #0f172a;
      font-size: 14px;
    }

    .qa-form-card-header p {
      margin: 0;
      color: #64748b;
      font-size: 11px;
      line-height: 1.5;
    }

    .qa-form-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    .qa-form-grid.three-columns {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .qa-field {
      min-width: 0;
    }

    .qa-field.full-width {
      grid-column: 1 / -1;
    }

    .qa-field label {
      display: flex;
      align-items: center;
      gap: 4px;
      margin-bottom: 6px;
      color: #334155;
      font-size: 11px;
      font-weight: 750;
    }

    .qa-required {
      color: #dc2626;
    }

    .qa-field-help {
      margin-top: 5px;
      color: #64748b;
      font-size: 10px;
      line-height: 1.45;
    }

    .qa-field-error {
      margin-top: 5px;
      color: #b91c1c;
      font-size: 10px;
      font-weight: 650;
      line-height: 1.4;
    }

    .qa-field input[aria-invalid="true"],
    .qa-field select[aria-invalid="true"],
    .qa-field textarea[aria-invalid="true"] {
      border-color: #ef4444;
      box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.10);
    }

    .qa-template-library {
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      background: #f8fafc;
    }

    .qa-template-library > summary {
      padding: 12px 14px;
      color: #334155;
      font-size: 11px;
      font-weight: 800;
      cursor: pointer;
      user-select: none;
    }

    .qa-template-content {
      display: grid;
      grid-template-columns: minmax(220px, 1fr) auto;
      gap: 12px;
      padding: 0 14px 14px;
      align-items: end;
    }

    .qa-template-actions,
    .qa-action-row,
    .qa-history-filter-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }

    .qa-template-actions button,
    .qa-action-row button,
    .qa-history-filter-actions button {
      margin: 0;
    }

    .qa-action-row {
      justify-content: space-between;
      padding-top: 2px;
    }

    .qa-action-note {
      max-width: 620px;
      color: #64748b;
      font-size: 10px;
      line-height: 1.45;
    }

    .qa-primary-action {
      min-width: 170px;
    }

    .qa-advanced {
      border-top: 1px solid #e2e8f0;
      padding-top: 12px;
    }

    .qa-advanced > summary {
      color: #475569;
      font-size: 11px;
      font-weight: 750;
      cursor: pointer;
    }

    .qa-advanced-content {
      margin-top: 12px;
    }

    .qa-result-section {
      margin-top: 14px;
    }

    .qa-result-section > h3 {
      margin: 0 0 8px;
      color: #334155;
      font-size: 12px;
    }

    .qa-segmented-control {
      display: inline-grid;
      grid-template-columns: repeat(2, minmax(110px, 1fr));
      padding: 3px;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      background: #f8fafc;
    }

    .qa-segmented-control label {
      position: relative;
      margin: 0;
      cursor: pointer;
    }

    .qa-segmented-control input {
      position: absolute;
      opacity: 0;
      pointer-events: none;
    }

    .qa-segmented-control span {
      display: block;
      padding: 8px 12px;
      border-radius: 7px;
      color: #64748b;
      font-size: 11px;
      font-weight: 750;
      text-align: center;
    }

    .qa-segmented-control input:checked + span {
      background: #ffffff;
      color: #1d4ed8;
      box-shadow: 0 1px 4px rgba(15, 23, 42, 0.12);
    }

    .qa-form-hidden {
      display: none !important;
    }

    .qa-history-filters {
      display: grid;
      grid-template-columns: minmax(240px, 1.5fr) minmax(160px, 0.7fr) minmax(160px, 0.7fr) auto;
      gap: 12px;
      align-items: end;
      margin-bottom: 14px;
      padding: 14px;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      background: #ffffff;
    }

    .qa-history-filter-error {
      grid-column: 1 / -1;
      color: #b91c1c;
      font-size: 10px;
      font-weight: 650;
    }

    .qa-history-project-badge {
      display: inline-flex;
      align-items: center;
      max-width: 180px;
      padding: 4px 8px;
      overflow: hidden;
      border-radius: 999px;
      background: #e0e7ff;
      color: #3730a3;
      font-size: 10px;
      font-weight: 750;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .qa-history-project-badge.legacy {
      background: #f1f5f9;
      color: #64748b;
    }

    .qa-run-detail-overlay {
      position: fixed;
      inset: 0;
      z-index: 1190;
      background: rgba(15, 23, 42, 0.44);
      opacity: 0;
      pointer-events: none;
      transition: opacity 160ms ease;
    }

    .qa-run-detail-overlay.visible {
      opacity: 1;
      pointer-events: auto;
    }

    #runDetailPanel.run-detail-section {
      position: fixed;
      top: 0;
      right: 0;
      bottom: 0;
      z-index: 1200;
      width: min(760px, 92vw);
      margin: 0;
      padding: 20px;
      overflow-y: auto;
      border: none;
      border-left: 1px solid #e2e8f0;
      border-radius: 0;
      background: #ffffff;
      box-shadow: -14px 0 36px rgba(15, 23, 42, 0.18);
      transform: translateX(0);
    }

    #runDetailPanel.run-detail-section.hidden {
      display: block !important;
      transform: translateX(105%);
      pointer-events: none;
    }

    .qa-run-detail-header {
      position: sticky;
      top: -20px;
      z-index: 2;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin: -20px -20px 16px;
      padding: 18px 20px 14px;
      border-bottom: 1px solid #e2e8f0;
      background: rgba(255, 255, 255, 0.97);
      backdrop-filter: blur(8px);
    }

    .qa-run-detail-header h2 {
      margin: 0 0 4px;
    }

    .qa-run-detail-close {
      min-width: 38px;
      padding: 8px 10px;
    }

    body.qa-drawer-open {
      overflow: hidden;
    }

    @media (max-width: 900px) {
      .qa-form-grid,
      .qa-form-grid.three-columns,
      .qa-history-filters {
        grid-template-columns: 1fr;
      }

      .qa-template-content {
        grid-template-columns: 1fr;
      }

      .qa-history-filter-actions {
        justify-content: flex-start;
      }
    }

    @media (max-width: 650px) {
      .qa-form-card {
        padding: 13px;
      }

      .qa-action-row {
        align-items: stretch;
        flex-direction: column;
      }

      .qa-primary-action {
        width: 100%;
      }

      #runDetailPanel.run-detail-section {
        width: 100vw;
      }
    }
'''

if "Functional Workspace Forms" not in text:
    text = text.replace("</style>", CSS + "\n  </style>", 1)
    print("[OK] CSS functional workspace ditambahkan")
else:
    print("[SKIP] CSS functional workspace sudah ada")


REGISTERED_HTML = r'''
<section class="section tab-panel active" id="tab-registered">
  <div class="qa-page-heading">
    <h2>Regression Testing</h2>
    <p class="muted">
      Jalankan pengujian fitur yang telah terdaftar pada project aktif.
    </p>
  </div>

  <div class="qa-form-stack">
    <div class="qa-form-card">
      <div class="qa-form-card-header">
        <div>
          <h3>Test Target</h3>
          <p>Pilih feature dan mode eksekusi yang akan dijalankan.</p>
        </div>
      </div>

      <div class="qa-form-grid">
        <div class="qa-field">
          <label for="registeredFeature">
            Feature <span class="qa-required">*</span>
          </label>
          <select id="registeredFeature" required></select>
          <div class="qa-field-help">
            Daftar feature mengikuti Project Registry yang sedang dipilih.
          </div>
        </div>

        <div class="qa-field">
          <label for="registeredMode">
            Execution Mode <span class="qa-required">*</span>
          </label>
          <select id="registeredMode" required>
            <option value="regression">Regression</option>
            <option value="smoke">Smoke</option>
          </select>
          <div class="qa-field-help">
            Regression menjalankan pemeriksaan lebih lengkap; Smoke untuk validasi cepat.
          </div>
        </div>
      </div>

      <details class="qa-advanced">
        <summary>Advanced Options</summary>
        <div class="qa-advanced-content">
          <div class="qa-field">
            <label for="registeredUrl">Base URL Override</label>
            <input
              id="registeredUrl"
              type="url"
              autocomplete="off"
              placeholder="Kosongkan untuk menggunakan URL project"
            />
            <div class="qa-field-help">
              Isi hanya untuk menjalankan test pada target selain environment default project.
            </div>
          </div>
        </div>
      </details>

      <div class="qa-action-row">
        <div class="qa-action-note">
          Credential tidak ditampilkan pada dashboard dan tetap menggunakan konfigurasi runner/project.
        </div>
        <button
          type="button"
          class="qa-primary-action"
          id="runRegisteredBtn"
          onclick="runRegisteredQA()"
        >
          Run Regression Test
        </button>
      </div>
    </div>
  </div>

  <div class="qa-result-section">
    <h3>Execution Result</h3>
    <div class="result-box" id="registeredResult">No result yet.</div>
  </div>
</section>
'''


CUSTOM_HTML = r'''
<section class="section tab-panel" id="tab-custom">
  <div class="qa-page-heading">
    <h2>UI Testing</h2>
    <p class="muted">
      Jalankan UI smoke test pada route tertentu menggunakan project aktif atau target custom.
    </p>
  </div>

  <div class="qa-form-stack">
    <details class="qa-template-library">
      <summary>Template Library</summary>
      <div class="qa-template-content">
        <div class="qa-field">
          <label for="customTemplateSelect">Saved UI Test Template</label>
          <select id="customTemplateSelect">
            <option value="">No template loaded</option>
          </select>
        </div>

        <div class="qa-template-actions">
          <button type="button" class="secondary" onclick="loadSelectedTemplate('custom_smoke')">Load</button>
          <button type="button" class="secondary" onclick="runSelectedTemplate('custom_smoke')">Run Template</button>
          <button type="button" class="secondary" onclick="deleteSelectedTemplate('custom_smoke')">Delete</button>
          <button type="button" class="secondary" onclick="saveCustomSmokeTemplate()">Save Current Form</button>
        </div>
      </div>
    </details>

    <div class="qa-form-card">
      <div class="qa-form-card-header">
        <div>
          <h3>Test Information</h3>
          <p>Berikan nama yang menjelaskan tujuan pengujian.</p>
        </div>
      </div>

      <div class="qa-form-grid">
        <div class="qa-field">
          <label for="customFeatureName">
            Test Name <span class="qa-required">*</span>
          </label>
          <input
            id="customFeatureName"
            required
            autocomplete="off"
            placeholder="Contoh: Notification Management Smoke"
          />
        </div>

        <div class="qa-field">
          <label for="customMode">
            Execution Mode <span class="qa-required">*</span>
          </label>
          <select id="customMode" required>
            <option value="smoke">Smoke</option>
            <option value="regression">Regression</option>
          </select>
        </div>
      </div>
    </div>

    <div class="qa-form-card">
      <div class="qa-form-card-header">
        <div>
          <h3>Target</h3>
          <p>Gunakan URL project atau masukkan target custom untuk Ad-hoc Testing.</p>
        </div>
      </div>

      <div class="qa-form-grid">
        <div class="qa-field">
          <label for="customUrl">Base URL</label>
          <input
            id="customUrl"
            type="url"
            autocomplete="off"
            placeholder="https://example.com"
          />
          <div class="qa-field-help" id="customUrlHelp">
            Mobospace dapat menggunakan URL project. Ad-hoc membutuhkan Base URL.
          </div>
        </div>

        <div class="qa-field">
          <label for="customRoute">
            Route <span class="qa-required">*</span>
          </label>
          <input
            id="customRoute"
            required
            autocomplete="off"
            placeholder="/dashboard"
          />
          <div class="qa-field-help">Route harus diawali dengan karakter /.</div>
        </div>
      </div>
    </div>

    <div class="qa-form-card">
      <div class="qa-form-card-header">
        <div>
          <h3>Validation</h3>
          <p>Tambahkan teks yang harus terlihat setelah halaman berhasil dibuka.</p>
        </div>
      </div>

      <div class="qa-field">
        <label for="expectedTexts">Expected Visible Text</label>
        <textarea
          id="expectedTexts"
          rows="5"
          placeholder="Satu expected text per baris"
        ></textarea>
        <div class="qa-field-help">
          Field ini opsional. Setiap baris akan divalidasi sebagai expected visible text.
        </div>
      </div>

      <div class="qa-action-row">
        <div class="qa-action-note">
          Credential menggunakan konfigurasi project/environment dan tidak disimpan di template atau History.
        </div>
        <button
          type="button"
          class="qa-primary-action"
          id="runCustomBtn"
          onclick="runCustomSmoke()"
        >
          Run UI Test
        </button>
      </div>
    </div>
  </div>

  <div class="qa-result-section">
    <h3>Execution Result</h3>
    <div class="result-box" id="customResult">No result yet.</div>
  </div>
</section>
'''


CURL_HTML = r'''
<section class="section tab-panel" id="tab-curl">
  <div class="qa-page-heading">
    <h2>API Testing</h2>
    <p class="muted">
      Jalankan positive atau negative API test dari perintah cURL dengan output yang dimasking.
    </p>
  </div>

  <div class="qa-form-stack">
    <details class="qa-template-library">
      <summary>Template Library</summary>
      <div class="qa-template-content">
        <div class="qa-field">
          <label for="curlTemplateSelect">Saved API Test Template</label>
          <select id="curlTemplateSelect">
            <option value="">No template loaded</option>
          </select>
        </div>

        <div class="qa-template-actions">
          <button type="button" class="secondary" onclick="loadSelectedTemplate('api_curl')">Load</button>
          <button type="button" class="secondary" onclick="runSelectedTemplate('api_curl')">Run Template</button>
          <button type="button" class="secondary" onclick="deleteSelectedTemplate('api_curl')">Delete</button>
          <button type="button" class="secondary" onclick="saveCurlTemplate()">Save Current Form</button>
        </div>
      </div>
    </details>

    <div class="qa-form-card">
      <div class="qa-form-card-header">
        <div>
          <h3>Test Case</h3>
          <p>Pilih tipe case. Form validasi akan menyesuaikan secara otomatis.</p>
        </div>
      </div>

      <div class="qa-segmented-control" role="group" aria-label="API test case type">
        <label>
          <input
            type="radio"
            name="qaCurlCaseRadio"
            value="positive"
            checked
            onchange="qaSetApiCaseType('positive')"
          />
          <span>Positive Case</span>
        </label>
        <label>
          <input
            type="radio"
            name="qaCurlCaseRadio"
            value="negative"
            onchange="qaSetApiCaseType('negative')"
          />
          <span>Negative Case</span>
        </label>
      </div>

      <select id="curlCaseType" class="qa-form-hidden" onchange="qaUpdateApiCaseFields()">
        <option value="positive">Positive Case</option>
        <option value="negative">Negative Case</option>
      </select>
    </div>

    <div class="qa-form-card">
      <div class="qa-form-card-header">
        <div>
          <h3>Test Information</h3>
          <p>Nama test akan digunakan pada result, History, dan artifact.</p>
        </div>
      </div>

      <div class="qa-form-grid">
        <div class="qa-field">
          <label for="curlFeatureName">
            Test Name <span class="qa-required">*</span>
          </label>
          <input
            id="curlFeatureName"
            required
            autocomplete="off"
            placeholder="Contoh: Get Customer Detail"
          />
        </div>

        <div class="qa-field">
          <label for="curlExpectedStatus">
            Expected Status <span class="qa-required">*</span>
          </label>
          <input
            id="curlExpectedStatus"
            type="number"
            min="100"
            max="599"
            value="200"
            required
          />
        </div>

        <div class="qa-field full-width qa-form-hidden" id="curlNegativeTitleGroup">
          <label for="curlNegativeCaseTitle">
            Negative Case Scenario <span class="qa-required">*</span>
          </label>
          <input
            id="curlNegativeCaseTitle"
            autocomplete="off"
            placeholder="Contoh: Missing Authorization Token"
          />
        </div>
      </div>
    </div>

    <div class="qa-form-card">
      <div class="qa-form-card-header">
        <div>
          <h3>Request</h3>
          <p>Paste satu perintah cURL lengkap. Authorization akan dimasking pada report.</p>
        </div>
      </div>

      <div class="qa-field">
        <label for="curlCommand">
          cURL Command <span class="qa-required">*</span>
        </label>
        <textarea
          id="curlCommand"
          rows="9"
          required
          spellcheck="false"
          placeholder='curl -X GET "https://api.example.com/resource"'
        ></textarea>
        <div class="qa-field-help">
          Jangan membagikan credential pada screenshot atau chat. Runner akan menggunakan input ini hanya untuk eksekusi.
        </div>
      </div>
    </div>

    <div class="qa-form-card">
      <div class="qa-form-card-header">
        <div>
          <h3>Expected Result</h3>
          <p>Tambahkan potongan teks yang harus ditemukan pada response.</p>
        </div>
      </div>

      <div class="qa-field" id="curlPositiveValidationGroup">
        <label for="curlExpectedContains">Response Must Contain</label>
        <textarea
          id="curlExpectedContains"
          rows="4"
          placeholder="Satu expected value per baris"
        ></textarea>
      </div>

      <div class="qa-field qa-form-hidden" id="curlNegativeValidationGroup">
        <label for="curlExpectedErrorContains">Error Response Must Contain</label>
        <textarea
          id="curlExpectedErrorContains"
          rows="4"
          placeholder="Satu expected error value per baris"
        ></textarea>
      </div>

      <div class="qa-action-row">
        <div class="qa-action-note">
          Positive case memvalidasi response normal. Negative case memvalidasi status dan pesan error yang diharapkan.
        </div>
        <button
          type="button"
          class="qa-primary-action"
          id="runCurlBtn"
          onclick="runCurlTest()"
        >
          Run API Test
        </button>
      </div>
    </div>
  </div>

  <div class="qa-result-section">
    <h3>Execution Result</h3>
    <div class="result-box" id="curlResult">No result yet.</div>
  </div>
</section>
'''


PLANNING_HTML = r'''
<section class="section tab-panel" id="tab-planning">
  <div class="qa-page-heading">
    <h2>Test Planning</h2>
    <p class="muted">
      Generate test scope, acceptance criteria, scenario, dan rekomendasi template dari input aktual.
    </p>
  </div>

  <div class="qa-form-stack">
    <div class="qa-form-card">
      <div class="qa-form-card-header">
        <div>
          <h3>Planning Source</h3>
          <p>Pilih jenis input yang paling sesuai dengan informasi yang tersedia.</p>
        </div>
      </div>

      <div class="qa-form-grid">
        <div class="qa-field">
          <label for="planInputType">
            Input Type <span class="qa-required">*</span>
          </label>
          <select id="planInputType" required onchange="qaUpdatePlanningFields()">
            <option value="requirement">Requirement / User Story</option>
            <option value="route">UI Route</option>
            <option value="api_curl">API cURL</option>
            <option value="mixed">Mixed Input</option>
          </select>
        </div>

        <div class="qa-field">
          <label for="planRiskLevel">
            Risk Level <span class="qa-required">*</span>
          </label>
          <select id="planRiskLevel" required>
            <option value="low">Low</option>
            <option value="medium" selected>Medium</option>
            <option value="high">High</option>
          </select>
        </div>

        <div class="qa-field full-width">
          <label for="planFeatureName">
            Feature / Test Name <span class="qa-required">*</span>
          </label>
          <input
            id="planFeatureName"
            required
            autocomplete="off"
            placeholder="Contoh: Create Shipment"
          />
        </div>
      </div>
    </div>

    <div class="qa-form-card">
      <div class="qa-form-card-header">
        <div>
          <h3>Requirement</h3>
          <p>Jelaskan tujuan, business rule, acceptance criteria, atau perubahan yang perlu diuji.</p>
        </div>
      </div>

      <div class="qa-field">
        <label for="planRequirement">
          Requirement / Description <span class="qa-required">*</span>
        </label>
        <textarea
          id="planRequirement"
          rows="7"
          required
          placeholder="Paste requirement, user story, acceptance criteria, atau deployment note."
        ></textarea>
      </div>
    </div>

    <div class="qa-form-card qa-form-hidden" id="planRouteGroup">
      <div class="qa-form-card-header">
        <div>
          <h3>UI Target</h3>
          <p>Masukkan route halaman yang menjadi target planning.</p>
        </div>
      </div>

      <div class="qa-field">
        <label for="planTargetRoute">Target Route</label>
        <input
          id="planTargetRoute"
          autocomplete="off"
          placeholder="/shipment/create"
        />
      </div>
    </div>

    <div class="qa-form-card qa-form-hidden" id="planApiCurlGroup">
      <div class="qa-form-card-header">
        <div>
          <h3>API Target</h3>
          <p>Paste cURL yang akan digunakan sebagai sumber scenario API.</p>
        </div>
      </div>

      <div class="qa-field">
        <label for="planApiCurl">API cURL</label>
        <textarea
          id="planApiCurl"
          rows="7"
          spellcheck="false"
          placeholder='curl -X GET "https://api.example.com/resource"'
        ></textarea>
      </div>
    </div>

    <div class="qa-action-row">
      <div class="qa-action-note">
        Generator menggunakan rule-based analysis dari data yang dimasukkan dan tidak membuat execution result palsu.
      </div>
      <button
        type="button"
        class="qa-primary-action"
        id="generatePlanBtn"
        onclick="generateTestPlan()"
      >
        Generate Test Plan
      </button>
    </div>
  </div>

  <div id="planResult" class="plan-output"></div>

  <details class="qa-template-library" style="margin-top:14px;">
    <summary>Raw Planning Output</summary>
    <div style="padding:0 14px 14px;">
      <div class="result-box" id="planRawResult">No test plan generated yet.</div>
    </div>
  </details>
</section>
'''


HISTORY_HTML = r'''
<section class="section tab-panel" id="tab-history">
  <div class="qa-page-heading">
    <h2>History</h2>
    <p class="muted">
      Cari execution berdasarkan feature, execution ID, atau rentang tanggal pengujian.
    </p>
  </div>

  <div class="qa-history-filters">
    <div class="qa-field">
      <label for="historySearch">Search</label>
      <input
        id="historySearch"
        type="search"
        autocomplete="off"
        placeholder="Feature name atau execution ID"
        onkeydown="qaHistorySearchKeydown(event)"
      />
    </div>

    <div class="qa-field">
      <label for="historyStartDate">Start Date</label>
      <input id="historyStartDate" type="date" />
    </div>

    <div class="qa-field">
      <label for="historyEndDate">End Date</label>
      <input id="historyEndDate" type="date" />
    </div>

    <div class="qa-history-filter-actions">
      <button type="button" onclick="qaApplyHistoryFilters()">Search</button>
      <button type="button" class="secondary" onclick="qaResetHistoryFilters()">Reset</button>
    </div>

    <div class="qa-history-filter-error qa-form-hidden" id="historyFilterError"></div>
  </div>

  <div class="history-pagination-panel" id="historyPaginationPanel">
    <div class="history-pagination-toolbar">
      <div>
        <strong>Execution History</strong>
        <div class="history-pagination-summary" id="historyPaginationSummary">
          Loading history...
        </div>
      </div>

      <div class="history-page-size">
        <div>
          <label for="historyPageSize">Rows per page</label>
          <select id="historyPageSize" onchange="changeHistoryPageSize(this.value)">
            <option value="10" selected>10</option>
            <option value="20">20</option>
            <option value="50">50</option>
          </select>
        </div>

        <button type="button" class="secondary" onclick="loadPaginatedHistory()">
          Refresh
        </button>
      </div>
    </div>

    <div class="history-table-wrapper">
      <table class="history-pagination-table">
        <thead>
          <tr>
            <th>Execution ID</th>
            <th>Feature</th>
            <th data-qa-project-column="true">Project</th>
            <th>Status</th>
            <th>Environment</th>
            <th>Mode</th>
            <th>Executed At</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody id="paginatedHistoryBody">
          <tr>
            <td colspan="10" class="history-empty-row">Loading history...</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="history-pagination-footer">
      <div class="history-pagination-summary" id="historyPaginationRange">-</div>
      <div class="history-pagination-buttons">
        <button
          type="button"
          class="secondary"
          id="historyPreviousBtn"
          onclick="changeHistoryPage(-1)"
        >
          Previous
        </button>
        <span class="history-page-indicator" id="historyPageIndicator">Page 1 of 1</span>
        <button
          type="button"
          class="secondary"
          id="historyNextBtn"
          onclick="changeHistoryPage(1)"
        >
          Next
        </button>
      </div>
    </div>
  </div>

  <div class="qa-run-detail-overlay" id="qaRunDetailOverlay" onclick="closeRunDetailDrawer()"></div>

  <div class="run-detail-section hidden" id="runDetailPanel" role="dialog" aria-modal="true" aria-labelledby="qaRunDetailTitle">
    <div class="qa-run-detail-header">
      <div>
        <h2 id="qaRunDetailTitle">Run Detail</h2>
        <p class="muted" id="runDetailSubtitle">Select a run to inspect its stored data.</p>
      </div>
      <button
        type="button"
        class="secondary qa-run-detail-close"
        aria-label="Close run detail"
        onclick="closeRunDetailDrawer()"
      >
        Close
      </button>
    </div>

    <div class="run-detail-summary-grid" id="runDetailSummary"></div>

    <div class="run-detail-two-column">
      <div class="run-detail-content-card">
        <h3>Execution Timeline</h3>
        <ul class="run-detail-timeline" id="runDetailTimeline"></ul>
      </div>
      <div class="run-detail-content-card">
        <h3>Analysis Agent</h3>
        <div id="runDetailAnalysis"></div>
      </div>
    </div>

    <div class="run-detail-content-card" style="margin-top:14px;">
      <h3>Feature Results</h3>
      <div id="runDetailFeatures"></div>
    </div>

    <div class="run-detail-two-column">
      <div class="run-detail-content-card">
        <h3>Artifacts</h3>
        <div id="runDetailArtifacts"></div>
      </div>
      <div class="run-detail-content-card">
        <h3>Data Availability</h3>
        <div id="runDetailAvailability"></div>
      </div>
    </div>

    <details style="margin-top:14px;">
      <summary>Stored Testing Summary</summary>
      <div class="result-box" id="runDetailTestingSummary">No stored summary.</div>
    </details>
  </div>

  <div id="runDetailToolbar" class="qa-form-hidden">
    <select id="runDetailExecutionSelect">
      <option value="">No run selected</option>
    </select>
  </div>

  <div id="historyTable" class="qa-form-hidden"></div>
</section>
'''

for element_id, replacement in [
    ("tab-registered", REGISTERED_HTML),
    ("tab-custom", CUSTOM_HTML),
    ("tab-curl", CURL_HTML),
    ("tab-planning", PLANNING_HTML),
    ("tab-history", HISTORY_HTML),
]:
    text = replace_element_by_id(text, element_id, replacement)
    print(f"[OK] Form diganti: {element_id}")


HELPERS_JS = r'''
    // ========================================================
    // Functional form helpers
    // ========================================================

    let qaHistoryAllRuns = [];

    function qaGetValue(id) {
      const element = document.getElementById(id);
      return element ? String(element.value || "").trim() : "";
    }

    function qaClearFieldError(fieldId) {
      const field = document.getElementById(fieldId);
      const error = document.getElementById(fieldId + "Error");

      if (field) {
        field.removeAttribute("aria-invalid");
      }

      if (error) {
        error.remove();
      }
    }

    function qaClearFormErrors(sectionId) {
      const section = document.getElementById(sectionId);
      if (!section) return;

      section.querySelectorAll("[aria-invalid='true']")
        .forEach(element => element.removeAttribute("aria-invalid"));

      section.querySelectorAll(".qa-field-error")
        .forEach(element => element.remove());
    }

    function qaSetFieldError(fieldId, message) {
      const field = document.getElementById(fieldId);
      if (!field) return false;

      qaClearFieldError(fieldId);
      field.setAttribute("aria-invalid", "true");

      const error = document.createElement("div");
      error.className = "qa-field-error";
      error.id = fieldId + "Error";
      error.textContent = message;
      field.insertAdjacentElement("afterend", error);

      return false;
    }

    function qaFocusFirstError(sectionId) {
      const section = document.getElementById(sectionId);
      const field = section && section.querySelector("[aria-invalid='true']");
      if (field) field.focus();
    }

    function qaIsHttpUrl(value) {
      if (!value) return false;

      try {
        const parsed = new URL(value);
        return parsed.protocol === "http:" || parsed.protocol === "https:";
      } catch (_error) {
        return false;
      }
    }

    function qaSetButtonBusy(button, busy, busyText) {
      if (!button) return;

      if (!button.dataset.idleText) {
        button.dataset.idleText = button.textContent.trim();
      }

      button.disabled = Boolean(busy);
      button.textContent = busy
        ? busyText
        : button.dataset.idleText;
      button.setAttribute("aria-busy", busy ? "true" : "false");
    }

    async function qaReadResponse(response) {
      const raw = await response.text();
      let data = {};

      if (raw) {
        try {
          data = JSON.parse(raw);
        } catch (_error) {
          data = {detail: raw};
        }
      }

      if (!response.ok) {
        const detail = data && data.detail;
        const message = typeof detail === "string"
          ? detail
          : JSON.stringify(detail || data || {status: response.status});
        throw new Error(message || ("Request failed with status " + response.status));
      }

      return data;
    }

    function qaCurrentProjectId() {
      return String(
        qaSelectedProjectId
        || (window.qaSelectedProject && window.qaSelectedProject.project_id)
        || document.body.dataset.projectId
        || ""
      );
    }

    function qaValidateRegisteredForm() {
      qaClearFormErrors("tab-registered");
      let valid = true;

      if (!qaGetValue("registeredFeature")) {
        valid = qaSetFieldError("registeredFeature", "Pilih feature yang akan diuji.") && valid;
      }

      const url = qaGetValue("registeredUrl");
      if (url && !qaIsHttpUrl(url)) {
        qaSetFieldError("registeredUrl", "Base URL harus menggunakan http:// atau https://.");
        valid = false;
      }

      if (!valid) qaFocusFirstError("tab-registered");
      return valid;
    }

    function qaValidateCustomForm() {
      qaClearFormErrors("tab-custom");
      let valid = true;

      if (!qaGetValue("customFeatureName")) {
        qaSetFieldError("customFeatureName", "Test Name wajib diisi.");
        valid = false;
      }

      const projectId = qaCurrentProjectId();
      const url = qaGetValue("customUrl");

      if (projectId === "adhoc" && !url) {
        qaSetFieldError("customUrl", "Base URL wajib diisi untuk Ad-hoc Testing.");
        valid = false;
      } else if (url && !qaIsHttpUrl(url)) {
        qaSetFieldError("customUrl", "Base URL harus menggunakan http:// atau https://.");
        valid = false;
      }

      const route = qaGetValue("customRoute");
      if (!route) {
        qaSetFieldError("customRoute", "Route wajib diisi.");
        valid = false;
      } else if (!route.startsWith("/")) {
        qaSetFieldError("customRoute", "Route harus diawali dengan karakter /.");
        valid = false;
      }

      if (!valid) qaFocusFirstError("tab-custom");
      return valid;
    }

    function qaValidateCurlForm() {
      qaClearFormErrors("tab-curl");
      let valid = true;

      if (!qaGetValue("curlFeatureName")) {
        qaSetFieldError("curlFeatureName", "Test Name wajib diisi.");
        valid = false;
      }

      const status = Number.parseInt(qaGetValue("curlExpectedStatus"), 10);
      if (!Number.isInteger(status) || status < 100 || status > 599) {
        qaSetFieldError("curlExpectedStatus", "Expected Status harus berada pada rentang 100–599.");
        valid = false;
      }

      const curl = qaGetValue("curlCommand");
      if (!curl) {
        qaSetFieldError("curlCommand", "cURL Command wajib diisi.");
        valid = false;
      } else if (!/^curl(?:\s|$)/i.test(curl)) {
        qaSetFieldError("curlCommand", "Input harus berupa perintah cURL yang diawali dengan kata curl.");
        valid = false;
      }

      if (qaGetValue("curlCaseType") === "negative" && !qaGetValue("curlNegativeCaseTitle")) {
        qaSetFieldError("curlNegativeCaseTitle", "Negative Case Scenario wajib diisi.");
        valid = false;
      }

      if (!valid) qaFocusFirstError("tab-curl");
      return valid;
    }

    function qaValidatePlanningForm() {
      qaClearFormErrors("tab-planning");
      let valid = true;

      const inputType = qaGetValue("planInputType");

      if (!qaGetValue("planFeatureName")) {
        qaSetFieldError("planFeatureName", "Feature / Test Name wajib diisi.");
        valid = false;
      }

      if (!qaGetValue("planRequirement")) {
        qaSetFieldError("planRequirement", "Requirement / Description wajib diisi.");
        valid = false;
      }

      const route = qaGetValue("planTargetRoute");
      const apiCurl = qaGetValue("planApiCurl");

      if (inputType === "route") {
        if (!route) {
          qaSetFieldError("planTargetRoute", "Target Route wajib diisi untuk input UI Route.");
          valid = false;
        } else if (!route.startsWith("/")) {
          qaSetFieldError("planTargetRoute", "Target Route harus diawali dengan karakter /.");
          valid = false;
        }
      }

      if (inputType === "api_curl") {
        if (!apiCurl) {
          qaSetFieldError("planApiCurl", "API cURL wajib diisi untuk input API cURL.");
          valid = false;
        } else if (!/^curl(?:\s|$)/i.test(apiCurl)) {
          qaSetFieldError("planApiCurl", "Input API harus berupa perintah cURL.");
          valid = false;
        }
      }

      if (inputType === "mixed" && !route && !apiCurl) {
        qaSetFieldError("planTargetRoute", "Mixed Input membutuhkan Target Route atau API cURL.");
        valid = false;
      }

      if (!valid) qaFocusFirstError("tab-planning");
      return valid;
    }

    function qaSetApiCaseType(caseType) {
      const select = document.getElementById("curlCaseType");
      if (select) select.value = caseType;
      qaUpdateApiCaseFields();
    }

    function qaUpdateApiCaseFields() {
      const caseType = qaGetValue("curlCaseType") || "positive";
      const negativeTitle = document.getElementById("curlNegativeTitleGroup");
      const positiveValidation = document.getElementById("curlPositiveValidationGroup");
      const negativeValidation = document.getElementById("curlNegativeValidationGroup");

      if (negativeTitle) negativeTitle.classList.toggle("qa-form-hidden", caseType !== "negative");
      if (positiveValidation) positiveValidation.classList.toggle("qa-form-hidden", caseType === "negative");
      if (negativeValidation) negativeValidation.classList.toggle("qa-form-hidden", caseType !== "negative");

      document.querySelectorAll('input[name="qaCurlCaseRadio"]')
        .forEach(radio => {
          radio.checked = radio.value === caseType;
        });

      if (caseType !== "negative") {
        qaClearFieldError("curlNegativeCaseTitle");
      }
    }

    function qaUpdatePlanningFields() {
      const inputType = qaGetValue("planInputType") || "requirement";
      const routeGroup = document.getElementById("planRouteGroup");
      const apiGroup = document.getElementById("planApiCurlGroup");

      const showRoute = inputType === "route" || inputType === "mixed";
      const showApi = inputType === "api_curl" || inputType === "mixed";

      if (routeGroup) routeGroup.classList.toggle("qa-form-hidden", !showRoute);
      if (apiGroup) apiGroup.classList.toggle("qa-form-hidden", !showApi);

      if (!showRoute) qaClearFieldError("planTargetRoute");
      if (!showApi) qaClearFieldError("planApiCurl");
    }

    function qaApplyProjectFormDefaults() {
      const projectId = qaCurrentProjectId();
      const legacyUrl = "https://mobospace-sandbox.pancaran-group.co.id";
      const registeredUrl = document.getElementById("registeredUrl");
      const customUrl = document.getElementById("customUrl");
      const customName = document.getElementById("customFeatureName");
      const curlCommand = document.getElementById("curlCommand");
      const urlHelp = document.getElementById("customUrlHelp");

      if (registeredUrl) {
        if (registeredUrl.value.trim() === legacyUrl) registeredUrl.value = "";
        registeredUrl.placeholder = projectId === "mobospace"
          ? "Kosongkan untuk menggunakan Mobospace Sandbox"
          : "Base URL override tidak digunakan untuk Ad-hoc regression";
      }

      if (customUrl) {
        if (customUrl.value.trim() === legacyUrl) customUrl.value = "";
        customUrl.placeholder = projectId === "mobospace"
          ? "Kosongkan untuk menggunakan URL project Mobospace"
          : "https://example.com";
      }

      if (urlHelp) {
        urlHelp.textContent = projectId === "mobospace"
          ? "Kosongkan untuk menggunakan URL dan credential project Mobospace."
          : "Base URL wajib diisi untuk Ad-hoc Testing.";
      }

      if (customName && !customName.value.trim()) {
        customName.value = projectId === "mobospace"
          ? "Mobospace UI Smoke Test"
          : "Ad-hoc UI Smoke Test";
      }

      if (curlCommand && curlCommand.value.trim() === ('curl -X GET "' + legacyUrl + '"')) {
        curlCommand.value = "";
      }
    }

    function qaHistoryDateKey(run) {
      const raw = String(run.executed_at || run.created_at || "").trim();
      const direct = raw.match(/^(\d{4}-\d{2}-\d{2})/);
      if (direct) return direct[1];

      const parsed = new Date(raw);
      if (Number.isNaN(parsed.getTime())) return "";

      const year = parsed.getFullYear();
      const month = String(parsed.getMonth() + 1).padStart(2, "0");
      const day = String(parsed.getDate()).padStart(2, "0");
      return year + "-" + month + "-" + day;
    }

    function qaApplyHistoryFilters() {
      const search = qaGetValue("historySearch").toLowerCase();
      const startDate = qaGetValue("historyStartDate");
      const endDate = qaGetValue("historyEndDate");
      const errorBox = document.getElementById("historyFilterError");

      if (errorBox) {
        errorBox.classList.add("qa-form-hidden");
        errorBox.textContent = "";
      }

      if (startDate && endDate && startDate > endDate) {
        if (errorBox) {
          errorBox.textContent = "Start Date tidak boleh lebih besar dari End Date.";
          errorBox.classList.remove("qa-form-hidden");
        }
        return;
      }

      paginatedHistoryRuns = qaHistoryAllRuns.filter(run => {
        const searchable = [
          run.execution_id,
          run.feature,
          run.project_name,
          run.project_id,
          run.mode,
          run.status,
        ].map(value => String(value || "").toLowerCase()).join(" ");

        if (search && !searchable.includes(search)) return false;

        const dateKey = qaHistoryDateKey(run);
        if (startDate && (!dateKey || dateKey < startDate)) return false;
        if (endDate && (!dateKey || dateKey > endDate)) return false;

        return true;
      });

      paginatedHistoryPage = 1;
      renderPaginatedHistory();
    }

    function qaResetHistoryFilters() {
      ["historySearch", "historyStartDate", "historyEndDate"].forEach(id => {
        const field = document.getElementById(id);
        if (field) field.value = "";
      });

      const errorBox = document.getElementById("historyFilterError");
      if (errorBox) {
        errorBox.classList.add("qa-form-hidden");
        errorBox.textContent = "";
      }

      paginatedHistoryRuns = [...qaHistoryAllRuns];
      paginatedHistoryPage = 1;
      renderPaginatedHistory();
    }

    function qaHistorySearchKeydown(event) {
      if (event.key === "Enter") {
        event.preventDefault();
        qaApplyHistoryFilters();
      }
    }

    function qaOpenRunDetailDrawer() {
      const panel = document.getElementById("runDetailPanel");
      const overlay = document.getElementById("qaRunDetailOverlay");
      if (panel) panel.classList.remove("hidden");
      if (overlay) overlay.classList.add("visible");
      document.body.classList.add("qa-drawer-open");
    }

    function closeRunDetailDrawer() {
      const panel = document.getElementById("runDetailPanel");
      const overlay = document.getElementById("qaRunDetailOverlay");
      if (panel) panel.classList.add("hidden");
      if (overlay) overlay.classList.remove("visible");
      document.body.classList.remove("qa-drawer-open");
    }

    async function qaOpenHistoryDetail(executionId) {
      qaOpenRunDetailDrawer();
      try {
        await openPaginatedHistoryDetail(executionId);
      } catch (error) {
        closeRunDetailDrawer();
        throw error;
      }
    }

    function qaSetupFunctionalForms() {
      document.querySelectorAll(
        "#tab-registered input, #tab-registered select, "
        + "#tab-custom input, #tab-custom select, #tab-custom textarea, "
        + "#tab-curl input, #tab-curl select, #tab-curl textarea, "
        + "#tab-planning input, #tab-planning select, #tab-planning textarea"
      ).forEach(element => {
        const eventName = element.tagName === "SELECT" ? "change" : "input";
        element.addEventListener(eventName, () => qaClearFieldError(element.id));
      });

      qaUpdateApiCaseFields();
      qaUpdatePlanningFields();
      qaApplyProjectFormDefaults();

      document.addEventListener("keydown", event => {
        if (event.key === "Escape" && document.body.classList.contains("qa-drawer-open")) {
          closeRunDetailDrawer();
        }
      });
    }

    window.addEventListener("qa-project-changed", () => {
      setTimeout(qaApplyProjectFormDefaults, 50);
    });

    window.addEventListener("load", () => {
      setTimeout(qaSetupFunctionalForms, 250);
    });

'''

if "function qaValidateRegisteredForm" not in text:
    marker = re.search(
        r"(?m)^[ \t]*async function runRegisteredQA[ \t]*\(",
        text,
    )
    if not marker:
        raise RuntimeError("Marker runRegisteredQA tidak ditemukan")
    text = text[: marker.start()] + HELPERS_JS + "\n" + text[marker.start() :]
    print("[OK] Helper JavaScript ditambahkan")
else:
    print("[SKIP] Helper JavaScript sudah ada")


RUN_REGISTERED_JS = r'''
    async function runRegisteredQA() {
      const button = document.getElementById("runRegisteredBtn");
      const resultBox = document.getElementById("registeredResult");

      if (!qaValidateRegisteredForm()) return;

      const payload = {
        feature: qaGetValue("registeredFeature"),
        mode: qaGetValue("registeredMode"),
        url: qaGetValue("registeredUrl") || null,
      };

      qaSetButtonBusy(button, true, "Running Regression...");
      resultBox.textContent = "Running registered QA. Please wait...";
      startAgentFlow("registered");

      try {
        const response = await fetch("/runs", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload),
        });

        const data = await qaReadResponse(response);
        resultBox.textContent = formatResult(data);
        completeAgentFlow(data, "registered");
        await runAnalysisAgent(data);
        await loadPaginatedHistory();
      } catch (error) {
        resultBox.textContent = "Error: " + error.message;
        failAgentFlow(error.message);
      } finally {
        qaSetButtonBusy(button, false, "");
      }
    }
'''

RUN_CUSTOM_JS = r'''
    async function runCustomSmoke() {
      const button = document.getElementById("runCustomBtn");
      const resultBox = document.getElementById("customResult");

      if (!qaValidateCustomForm()) return;

      const expectedTexts = qaGetValue("expectedTexts")
        .split("\n")
        .map(item => item.trim())
        .filter(Boolean);

      const payload = {
        feature_name: qaGetValue("customFeatureName"),
        mode: qaGetValue("customMode"),
        url: qaGetValue("customUrl") || null,
        route: qaGetValue("customRoute"),
        expected_texts: expectedTexts,
      };

      qaSetButtonBusy(button, true, "Running UI Test...");
      resultBox.textContent = "Running UI test. Please wait...";
      startAgentFlow("custom_smoke");

      try {
        const response = await fetch("/custom-smoke", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload),
        });

        const data = await qaReadResponse(response);
        resultBox.textContent = formatResult(data);
        completeAgentFlow(data, "custom_smoke");
        await runAnalysisAgent(data);
        await loadPaginatedHistory();
      } catch (error) {
        resultBox.textContent = "Error: " + error.message;
        failAgentFlow(error.message);
      } finally {
        qaSetButtonBusy(button, false, "");
      }
    }
'''

RUN_CURL_JS = r'''
    async function runCurlTest() {
      const button = document.getElementById("runCurlBtn");
      const resultBox = document.getElementById("curlResult");

      if (!qaValidateCurlForm()) return;

      const expectedContains = qaGetValue("curlExpectedContains")
        .split("\n")
        .map(item => item.trim())
        .filter(Boolean);

      const expectedErrorContains = qaGetValue("curlExpectedErrorContains")
        .split("\n")
        .map(item => item.trim())
        .filter(Boolean);

      const caseType = qaGetValue("curlCaseType");

      const payload = {
        feature_name: qaGetValue("curlFeatureName"),
        mode: "api",
        curl: qaGetValue("curlCommand"),
        expected_status: Number.parseInt(qaGetValue("curlExpectedStatus"), 10),
        expected_contains: caseType === "positive" ? expectedContains : [],
        test_case_type: caseType,
        negative_case_title: caseType === "negative"
          ? qaGetValue("curlNegativeCaseTitle")
          : null,
        expected_error_contains: caseType === "negative"
          ? expectedErrorContains
          : [],
      };

      qaSetButtonBusy(button, true, "Running API Test...");
      resultBox.textContent = "Running API test. Please wait...";
      startAgentFlow("api_curl");

      try {
        const response = await fetch("/curl-test", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload),
        });

        const data = await qaReadResponse(response);
        resultBox.textContent = formatResult(data);
        completeAgentFlow(data, "api_curl");
        await runAnalysisAgent(data);
        await loadPaginatedHistory();
      } catch (error) {
        resultBox.textContent = "Error: " + error.message;
        failAgentFlow(error.message);
      } finally {
        qaSetButtonBusy(button, false, "");
      }
    }
'''

GENERATE_PLAN_JS = r'''
    async function generateTestPlan() {
      const button = document.getElementById("generatePlanBtn");
      const resultBox = document.getElementById("planRawResult");
      const resultPanel = document.getElementById("planResult");

      if (!qaValidatePlanningForm()) return;

      const payload = {
        input_type: qaGetValue("planInputType"),
        feature_name: qaGetValue("planFeatureName"),
        requirement: qaGetValue("planRequirement"),
        target_route: qaGetValue("planTargetRoute") || null,
        api_curl: qaGetValue("planApiCurl") || null,
        risk_level: qaGetValue("planRiskLevel"),
      };

      qaSetButtonBusy(button, true, "Generating Plan...");
      resultBox.textContent = "Generating test plan...";
      resultPanel.innerHTML = "";

      setAgentStep("planning", "running", "Running");
      setAgentStep("scenario", "", "Waiting");
      setAgentStep("template", "", "Waiting");
      setAgentStep("execution", "", "Not Started");
      setAgentStep("evidence", "", "Not Started");
      setAgentStep("analysis", "", "Not Started");
      setAgentStep("report", "", "Not Started");

      try {
        const response = await fetch("/test-plan/generate", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload),
        });

        const data = await qaReadResponse(response);

        if (!data.ok) {
          throw new Error(JSON.stringify(data));
        }

        latestGeneratedPlan = data;

        resultPanel.innerHTML = `
          <div class="plan-card">
            <h3>Test Scope</h3>
            ${renderList(data.test_scope)}
          </div>
          <div class="plan-card">
            <h3>Acceptance Criteria</h3>
            ${renderList(data.acceptance_criteria)}
          </div>
          <div class="plan-card">
            <h3>Suggested Scenarios</h3>
            ${renderScenarios(data.scenarios)}
          </div>
          <div class="plan-card">
            <h3>Recommended Templates</h3>
            ${renderRecommendedTemplates(data.recommended_templates)}
          </div>
        `;

        resultBox.textContent = JSON.stringify(data, null, 2);

        setAgentStep("planning", "completed", "Completed");
        setAgentStep("scenario", "completed", "Generated");
        setAgentStep(
          "template",
          data.recommended_templates && data.recommended_templates.length ? "completed" : "review",
          data.recommended_templates && data.recommended_templates.length ? "Suggested" : "Need Input"
        );
        setAgentStep("report", "completed", "Plan Generated");

        const noteEl = document.getElementById("agentFlowNote");
        if (noteEl) {
          noteEl.textContent = "Test plan generated for: " + data.input.feature_name;
        }
      } catch (error) {
        resultBox.textContent = "Error: " + error.message;
        failAgentFlow(error.message);
      } finally {
        qaSetButtonBusy(button, false, "");
      }
    }
'''

LOAD_HISTORY_JS = r'''
    async function loadPaginatedHistory() {
      const body = document.getElementById("paginatedHistoryBody");
      const summary = document.getElementById("historyPaginationSummary");

      if (body) {
        body.innerHTML = `
          <tr>
            <td colspan="10" class="history-empty-row">Loading history...</td>
          </tr>
        `;
      }

      if (summary) summary.textContent = "Loading history...";

      try {
        const response = await fetch("/history?limit=1000&_=" + Date.now(), {
          cache: "no-store",
        });

        const data = await qaReadResponse(response);
        const runs = Array.isArray(data)
          ? data
          : Array.isArray(data.history)
          ? data.history
          : Array.isArray(data.runs)
          ? data.runs
          : Array.isArray(data.items)
          ? data.items
          : [];

        qaHistoryAllRuns = runs;
        qaApplyHistoryFilters();
      } catch (error) {
        qaHistoryAllRuns = [];
        paginatedHistoryRuns = [];

        if (body) {
          body.innerHTML = `
            <tr>
              <td colspan="10" class="history-empty-row">
                Unable to load execution history: ${hpEscapeHtml(error.message)}
              </td>
            </tr>
          `;
        }

        if (summary) summary.textContent = "History unavailable.";
      }
    }
'''

RENDER_HISTORY_JS = r'''
    function renderPaginatedHistory() {
      const body = document.getElementById("paginatedHistoryBody");
      const summary = document.getElementById("historyPaginationSummary");
      const range = document.getElementById("historyPaginationRange");
      const pageIndicator = document.getElementById("historyPageIndicator");
      const previousButton = document.getElementById("historyPreviousBtn");
      const nextButton = document.getElementById("historyNextBtn");

      if (!body) return;

      const totalItems = paginatedHistoryRuns.length;
      const totalPages = Math.max(1, Math.ceil(totalItems / paginatedHistoryPageSize));

      if (paginatedHistoryPage > totalPages) {
        paginatedHistoryPage = totalPages;
      }

      const startIndex = (paginatedHistoryPage - 1) * paginatedHistoryPageSize;
      const endIndex = Math.min(startIndex + paginatedHistoryPageSize, totalItems);
      const pageItems = paginatedHistoryRuns.slice(startIndex, endIndex);

      if (!pageItems.length) {
        body.innerHTML = `
          <tr>
            <td colspan="10" class="history-empty-row">
              No execution history matches the selected filters.
            </td>
          </tr>
        `;
      } else {
        body.innerHTML = pageItems.map(run => {
          const executionId = String(run.execution_id || "");
          const status = String(run.status || "-");
          const projectName = String(
            run.project_name
            || run.project_id
            || "Legacy / Unassigned"
          );
          const projectClass = run.project_id ? "" : " legacy";
          const encodedExecutionId = encodeURIComponent(executionId);

          return `
            <tr>
              <td class="history-execution-id">${hpEscapeHtml(executionId || "-")}</td>
              <td>${hpEscapeHtml(run.feature || "-")}</td>
              <td>
                <span class="qa-history-project-badge${projectClass}">
                  ${hpEscapeHtml(projectName)}
                </span>
              </td>
              <td>
                <span class="history-status-badge ${hpStatusClass(status)}">
                  ${hpEscapeHtml(status)}
                </span>
              </td>
              <td>${hpEscapeHtml(run.environment_name || run.environment || "-")}</td>
              <td>${hpEscapeHtml(run.mode || "-")}</td>
              <td>${hpEscapeHtml(run.executed_at || run.created_at || "-")}</td>
              <td>${hpEscapeHtml(run.passed ?? 0)}</td>
              <td>${hpEscapeHtml(run.failed ?? 0)}</td>
              <td>
                ${executionId
                  ? `
                    <button
                      type="button"
                      class="secondary"
                      onclick="qaOpenHistoryDetail(decodeURIComponent('${encodedExecutionId}'))"
                    >
                      Detail
                    </button>
                  `
                  : '<span class="muted">Unavailable</span>'
                }
              </td>
            </tr>
          `;
        }).join("");
      }

      if (summary) {
        summary.textContent = totalItems === qaHistoryAllRuns.length
          ? totalItems + " execution run(s) stored."
          : totalItems + " of " + qaHistoryAllRuns.length + " execution run(s) matched.";
      }

      if (range) {
        range.textContent = totalItems
          ? "Showing " + (startIndex + 1) + "–" + endIndex + " of " + totalItems
          : "Showing 0 of 0";
      }

      if (pageIndicator) {
        pageIndicator.textContent = "Page " + paginatedHistoryPage + " of " + totalPages;
      }

      if (previousButton) previousButton.disabled = paginatedHistoryPage <= 1;
      if (nextButton) nextButton.disabled = paginatedHistoryPage >= totalPages;
    }
'''

for function_name, replacement in [
    ("runRegisteredQA", RUN_REGISTERED_JS),
    ("runCustomSmoke", RUN_CUSTOM_JS),
    ("runCurlTest", RUN_CURL_JS),
    ("generateTestPlan", GENERATE_PLAN_JS),
    ("loadPaginatedHistory", LOAD_HISTORY_JS),
    ("renderPaginatedHistory", RENDER_HISTORY_JS),
]:
    text = replace_function(text, function_name, replacement)
    print(f"[OK] Fungsi diganti: {function_name}")


# Keep runner names, template payloads, and stored labels untouched outside
# the replaced workspace sections.
HTML_PATH.write_text(text, encoding="utf-8")

# Lightweight structural verification.
updated = HTML_PATH.read_text(encoding="utf-8")
required_ids = [
    "registeredFeature",
    "registeredUrl",
    "registeredMode",
    "runRegisteredBtn",
    "customTemplateSelect",
    "customFeatureName",
    "customUrl",
    "customRoute",
    "customMode",
    "expectedTexts",
    "runCustomBtn",
    "curlTemplateSelect",
    "curlFeatureName",
    "curlExpectedStatus",
    "curlCaseType",
    "curlNegativeCaseTitle",
    "curlCommand",
    "curlExpectedContains",
    "curlExpectedErrorContains",
    "runCurlBtn",
    "planInputType",
    "planRiskLevel",
    "planFeatureName",
    "planTargetRoute",
    "planRequirement",
    "planApiCurl",
    "generatePlanBtn",
    "historySearch",
    "historyStartDate",
    "historyEndDate",
    "historyPageSize",
    "paginatedHistoryBody",
    "runDetailPanel",
]

errors = []
for element_id in required_ids:
    count = len(re.findall(rf'\bid=["\']{re.escape(element_id)}["\']', updated))
    if count != 1:
        errors.append(f"ID {element_id}: expected 1, found {count}")

required_functions = [
    "qaValidateRegisteredForm",
    "qaValidateCustomForm",
    "qaValidateCurlForm",
    "qaValidatePlanningForm",
    "runRegisteredQA",
    "runCustomSmoke",
    "runCurlTest",
    "generateTestPlan",
    "loadPaginatedHistory",
    "renderPaginatedHistory",
]

for name in required_functions:
    count = len(re.findall(rf"\bfunction\s+{re.escape(name)}\s*\(", updated))
    if count != 1:
        errors.append(f"Function {name}: expected 1, found {count}")

if errors:
    print("\n[ERROR] Verifikasi gagal:")
    for error in errors:
        print(" -", error)
    print("\nRollback otomatis ke backup:", backup_path)
    shutil.copy2(backup_path, HTML_PATH)
    raise SystemExit(1)

print("\n[SUCCESS] Functional Workspace Forms berhasil dipasang")
print("Dashboard :", HTML_PATH)
print("Backup    :", backup_path)
print("\nYang diperbarui:")
print("- Regression Testing: project-aware, URL override, validation")
print("- UI Testing: template, target, validation, project-aware URL")
print("- API Testing: positive/negative conditional form, validation")
print("- Test Planning: conditional route/API input, validation")
print("- History: search, start/end date, pagination, detail drawer")
