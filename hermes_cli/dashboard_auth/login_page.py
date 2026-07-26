"""Server-rendered /login page.

No React, no JavaScript dependency. Listed providers come from the
registry; clicking a provider sends a GET to
``/auth/login?provider=<name>``.

Visual styling mirrors the Nous Research design system (the
``@nous-research/ui`` package the React dashboard uses): the same
``Collapse`` / ``Rules Compressed`` typeface, amber-on-dark colour
tokens (``#170d02`` / ``#ffac02`` / ``#fff``), uppercase + wide-tracking
brand chrome, and the inset-bevel button shadow. Fonts are served
out of the SPA's ``/fonts/`` directory which the dashboard-auth gate
already allowlists pre-auth (see ``_GATE_PUBLIC_PREFIXES`` in
``middleware.py``), so the page renders without needing the React
bundle loaded.

Test-stable class names: the existing test suite extracts the
``class="provider-btn"`` anchor href to walk the OAuth flow. That
class name MUST NOT change without updating
``tests/hermes_cli/test_dashboard_auth_401_reauth.py``.
"""
from __future__ import annotations

import html

from hermes_cli.dashboard_auth import list_providers

# Inline minimal CSS. The dashboard's full skin lives in the React
# bundle, which we deliberately do NOT load here — the login page must
# not depend on the SPA build being present or on the injected session
# token.
#
# Single curly braces are placeholders for ``str.format``; CSS curlies
# are doubled (``{{`` / ``}}``).
_LOGIN_HTML_TEMPLATE = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>Sign in — QA Control Center</title>
<style>
  :root {{
    --page: #eef2f7;
    --surface: #ffffff;
    --surface-subtle: #f8fafc;
    --sidebar: #0f172a;
    --sidebar-muted: #94a3b8;
    --text: #111827;
    --muted: #64748b;
    --line: #dbe3ee;
    --line-strong: #cbd5e1;
    --accent: #4f46e5;
    --accent-hover: #4338ca;
    --accent-soft: #eef2ff;
    --success: #0f9f6e;
    --danger: #c2415b;
    --focus: rgba(79, 70, 229, 0.2);
    --shadow:
      0 24px 70px rgba(15, 23, 42, 0.12),
      0 2px 10px rgba(15, 23, 42, 0.05);
  }}

  *, *::before, *::after {{
    box-sizing: border-box;
  }}

  html,
  body {{
    margin: 0;
    min-height: 100%;
  }}

  body {{
    min-height: 100vh;
    background: var(--page);
    color: var(--text);
    font-family:
      Inter,
      ui-sans-serif,
      system-ui,
      -apple-system,
      BlinkMacSystemFont,
      "Segoe UI",
      sans-serif;
    font-size: 16px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }}

  button,
  input {{
    font: inherit;
  }}

  .auth-shell {{
    min-height: 100vh;
    display: grid;
    grid-template-columns:
      minmax(20rem, 0.9fr)
      minmax(30rem, 1.1fr);
  }}

  .product-panel {{
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding:
      clamp(2rem, 5vw, 4.5rem);
    background:
      radial-gradient(
        circle at 12% 15%,
        rgba(99, 102, 241, 0.28),
        transparent 34%
      ),
      radial-gradient(
        circle at 90% 92%,
        rgba(14, 165, 233, 0.16),
        transparent 35%
      ),
      var(--sidebar);
    color: #ffffff;
  }}

  .product-panel::after {{
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background-image:
      linear-gradient(
        rgba(255, 255, 255, 0.03) 1px,
        transparent 1px
      ),
      linear-gradient(
        90deg,
        rgba(255, 255, 255, 0.03) 1px,
        transparent 1px
      );
    background-size: 48px 48px;
    mask-image:
      linear-gradient(
        to bottom right,
        black,
        transparent 78%
      );
  }}

  .brand,
  .product-copy,
  .product-footer {{
    position: relative;
    z-index: 1;
  }}

  .brand {{
    display: flex;
    align-items: center;
    gap: 0.85rem;
    font-size: 0.78rem;
    font-weight: 750;
    letter-spacing: 0.16em;
    text-transform: uppercase;
  }}

  .brand-mark {{
    display: grid;
    place-items: center;
    width: 2.25rem;
    height: 2.25rem;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 0.65rem;
    background:
      linear-gradient(
        145deg,
        #6366f1,
        #0ea5e9
      );
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.22),
      0 12px 30px rgba(15, 23, 42, 0.3);
  }}

  .brand-mark span {{
    font-size: 0.78rem;
    font-weight: 850;
    letter-spacing: -0.04em;
  }}

  .product-copy {{
    max-width: 34rem;
    margin-block: 4rem;
  }}

  .environment-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1.4rem;
    padding: 0.42rem 0.7rem;
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 999px;
    background: rgba(15, 23, 42, 0.3);
    color: #dbeafe;
    font-size: 0.76rem;
    font-weight: 650;
  }}

  .environment-dot {{
    width: 0.48rem;
    height: 0.48rem;
    border-radius: 50%;
    background: #34d399;
    box-shadow: 0 0 0 4px rgba(52, 211, 153, 0.12);
  }}

  .product-copy h1 {{
    max-width: 31rem;
    margin: 0;
    font-size:
      clamp(2.25rem, 5vw, 4.3rem);
    line-height: 1.02;
    letter-spacing: -0.055em;
  }}

  .product-copy > p {{
    max-width: 30rem;
    margin: 1.35rem 0 0;
    color: #cbd5e1;
    font-size: 1.03rem;
    line-height: 1.75;
  }}

  .capability-grid {{
    display: grid;
    grid-template-columns:
      repeat(2, minmax(0, 1fr));
    gap: 0.75rem;
    margin-top: 2.25rem;
  }}

  .capability {{
    min-height: 5.4rem;
    padding: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.8rem;
    background: rgba(255, 255, 255, 0.045);
    backdrop-filter: blur(8px);
  }}

  .capability strong {{
    display: block;
    margin-bottom: 0.35rem;
    font-size: 0.86rem;
  }}

  .capability span {{
    color: var(--sidebar-muted);
    font-size: 0.78rem;
    line-height: 1.5;
  }}

  .product-footer {{
    color: var(--sidebar-muted);
    font-size: 0.78rem;
  }}

  .login-panel {{
    display: grid;
    place-items: center;
    padding:
      clamp(1.5rem, 5vw, 5rem);
    background:
      radial-gradient(
        circle at 85% 10%,
        rgba(99, 102, 241, 0.07),
        transparent 32%
      ),
      var(--surface-subtle);
  }}

  .login-wrap {{
    width: min(100%, 29rem);
  }}

  .mobile-brand {{
    display: none;
  }}

  .login-card {{
    padding:
      clamp(1.5rem, 4vw, 2.4rem);
    border: 1px solid var(--line);
    border-radius: 1rem;
    background: var(--surface);
    box-shadow: var(--shadow);
  }}

  .login-eyebrow {{
    margin: 0 0 0.7rem;
    color: var(--accent);
    font-size: 0.75rem;
    font-weight: 750;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }}

  .login-card h2 {{
    margin: 0;
    font-size:
      clamp(1.75rem, 4vw, 2.25rem);
    line-height: 1.15;
    letter-spacing: -0.035em;
  }}

  .login-subtitle {{
    margin: 0.85rem 0 1.9rem;
    color: var(--muted);
    font-size: 0.94rem;
    line-height: 1.65;
  }}

  .provider-list {{
    display: grid;
    gap: 1rem;
  }}

  .provider-form {{
    display: grid;
    gap: 1rem;
  }}

  .form-title {{
    display: none;
  }}

  .field {{
    display: grid;
    gap: 0.45rem;
  }}

  .field-label {{
    color: #334155;
    font-size: 0.82rem;
    font-weight: 650;
  }}

  .field-input {{
    width: 100%;
    min-height: 3rem;
    padding: 0.72rem 0.85rem;
    border: 1px solid var(--line-strong);
    border-radius: 0.65rem;
    outline: none;
    background: #ffffff;
    color: var(--text);
    transition:
      border-color 0.15s ease,
      box-shadow 0.15s ease,
      background 0.15s ease;
  }}

  .field-input:hover {{
    border-color: #94a3b8;
  }}

  .field-input:focus {{
    border-color: var(--accent);
    box-shadow: 0 0 0 4px var(--focus);
  }}

  .field-password {{
    position: relative;
  }}

  .field-password .field-input {{
    padding-right: 4.7rem;
  }}

  .password-toggle {{
    position: absolute;
    top: 50%;
    right: 0.55rem;
    transform: translateY(-50%);
    min-width: 3.6rem;
    padding: 0.42rem 0.55rem;
    border: 0;
    border-radius: 0.45rem;
    background: transparent;
    color: var(--accent);
    font-size: 0.76rem;
    font-weight: 700;
    cursor: pointer;
  }}

  .password-toggle:hover {{
    background: var(--accent-soft);
  }}

  .form-error {{
    margin: -0.15rem 0 0;
    padding: 0.75rem 0.8rem;
    border: 1px solid #fecdd3;
    border-radius: 0.6rem;
    background: #fff1f2;
    color: var(--danger);
    font-size: 0.82rem;
  }}

  .provider-btn {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 3rem;
    padding: 0.78rem 1rem;
    border: 1px solid var(--accent);
    border-radius: 0.65rem;
    background: var(--accent);
    color: #ffffff;
    font-size: 0.86rem;
    font-weight: 750;
    letter-spacing: 0.01em;
    text-decoration: none;
    cursor: pointer;
    box-shadow:
      0 10px 22px rgba(79, 70, 229, 0.19);
    transition:
      transform 0.12s ease,
      background 0.12s ease,
      border-color 0.12s ease,
      box-shadow 0.12s ease;
  }}

  .provider-btn:hover {{
    border-color: var(--accent-hover);
    background: var(--accent-hover);
    box-shadow:
      0 13px 28px rgba(79, 70, 229, 0.24);
    transform: translateY(-1px);
  }}

  .provider-btn:active {{
    transform: translateY(0);
  }}

  .provider-btn:focus-visible,
  .password-toggle:focus-visible {{
    outline: 3px solid var(--focus);
    outline-offset: 2px;
  }}

  .provider-btn:disabled {{
    cursor: wait;
    opacity: 0.68;
    transform: none;
  }}

  .security-note {{
    display: flex;
    align-items: flex-start;
    gap: 0.65rem;
    margin-top: 1.3rem;
    padding-top: 1.2rem;
    border-top: 1px solid var(--line);
    color: var(--muted);
    font-size: 0.78rem;
    line-height: 1.55;
  }}

  .security-icon {{
    flex: 0 0 auto;
    display: grid;
    place-items: center;
    width: 1.65rem;
    height: 1.65rem;
    border-radius: 0.5rem;
    background: #ecfdf5;
    color: var(--success);
    font-size: 0.78rem;
    font-weight: 800;
  }}

  .login-footer {{
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    margin-top: 1rem;
    color: #94a3b8;
    font-size: 0.72rem;
  }}

  @media (max-width: 900px) {{
    .auth-shell {{
      grid-template-columns: 1fr;
    }}

    .product-panel {{
      display: none;
    }}

    .login-panel {{
      min-height: 100vh;
    }}

    .mobile-brand {{
      display: flex;
      align-items: center;
      gap: 0.7rem;
      margin-bottom: 1.2rem;
      color: var(--text);
      font-size: 0.76rem;
      font-weight: 750;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}

    .mobile-brand .brand-mark {{
      width: 2rem;
      height: 2rem;
      color: #ffffff;
    }}
  }}

  @media (max-width: 520px) {{
    .login-panel {{
      align-items: stretch;
      padding: 1rem;
    }}

    .login-wrap {{
      align-self: center;
    }}

    .login-card {{
      border-radius: 0.8rem;
    }}

    .login-footer {{
      flex-direction: column;
      gap: 0.3rem;
    }}
  }}

  @media (prefers-reduced-motion: reduce) {{
    *,
    *::before,
    *::after {{
      scroll-behavior: auto !important;
      transition-duration: 0.01ms !important;
    }}
  }}

  ::selection {{
    background: #c7d2fe;
    color: #1e1b4b;
  }}
</style>
</head>
<body>
<div class="auth-shell">
  <aside class="product-panel">
    <div class="brand">
      <div class="brand-mark"><span>QA</span></div>
      <span>QA Control Center</span>
    </div>

    <section class="product-copy">
      <div class="environment-pill">
        <span class="environment-dot"></span>
        Secure quality operations workspace
      </div>

      <h1>Build confidence into every release.</h1>
      <p>
        Plan, execute, compare, and deliver test evidence
        from one governed workspace.
      </p>

      <div class="capability-grid">
        <div class="capability">
          <strong>Test operations</strong>
          <span>
            Assets, plans, cycles, execution, and traceability.
          </span>
        </div>
        <div class="capability">
          <strong>Release intelligence</strong>
          <span>
            Comparison, recommendation, and delivery evidence.
          </span>
        </div>
        <div class="capability">
          <strong>Controlled access</strong>
          <span>
            Session-based authentication and role-aware actions.
          </span>
        </div>
        <div class="capability">
          <strong>Reliable persistence</strong>
          <span>
            Server-backed workspace and auditable history.
          </span>
        </div>
      </div>
    </section>

    <div class="product-footer">
      Quality engineering workspace · Development environment
    </div>
  </aside>

  <main class="login-panel">
    <div class="login-wrap">
      <div class="mobile-brand">
        <div class="brand-mark"><span>QA</span></div>
        <span>QA Control Center</span>
      </div>

      <section class="login-card">
        <p class="login-eyebrow">Secure workspace access</p>
        <h2>Sign in to continue</h2>
        <p class="login-subtitle">
          Use your authorized account to access test operations,
          execution history, and release reports.
        </p>

        <div class="provider-list">
{provider_buttons}
        </div>

        <div class="security-note">
          <span class="security-icon">✓</span>
          <span>
            Your session is protected with secure cookies.
            Access is evaluated against the configured role.
          </span>
        </div>
      </section>

      <footer class="login-footer">
        <span>QA Control Center</span>
        <span>Protected workspace · Authorized users only</span>
      </footer>
    </div>
  </main>
</div>
{password_script}
</body>
</html>
"""

_EMPTY_HTML = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign-in unavailable — QA Control Center</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; min-height: 100%; }
  body {
    min-height: 100vh;
    display: grid;
    place-items: center;
    padding: 1.5rem;
    background: #eef2f7;
    color: #111827;
    font-family:
      Inter,
      ui-sans-serif,
      system-ui,
      -apple-system,
      BlinkMacSystemFont,
      "Segoe UI",
      sans-serif;
  }
  main {
    width: min(100%, 34rem);
    padding: 2rem;
    border: 1px solid #dbe3ee;
    border-radius: 1rem;
    background: #ffffff;
    box-shadow:
      0 24px 70px rgba(15, 23, 42, 0.12),
      0 2px 10px rgba(15, 23, 42, 0.05);
  }
  .mark {
    display: grid;
    place-items: center;
    width: 2.4rem;
    height: 2.4rem;
    margin-bottom: 1.2rem;
    border-radius: 0.7rem;
    background:
      linear-gradient(
        145deg,
        #6366f1,
        #0ea5e9
      );
    color: #ffffff;
    font-size: 0.8rem;
    font-weight: 800;
  }
  h1 {
    margin: 0;
    font-size: 1.8rem;
    letter-spacing: -0.035em;
  }
  p {
    margin: 0.9rem 0 0;
    color: #64748b;
    line-height: 1.65;
  }
</style>
</head>
<body>
<main>
  <div class="mark">QA</div>
  <h1>Sign-in is not configured</h1>
  <p>
    This workspace requires an authentication provider.
    Configure the dashboard auth environment variables,
    then restart the backend service.
  </p>
</main>
</body>
</html>
"""

# Inline script that wires every password provider form to POST JSON to
# ``/auth/password-login`` and navigate on success. Emitted ONLY when at
# least one ``supports_password`` provider is listed (OAuth-only login
# pages stay script-free, preserving the no-JS contract for that case).
#
# Plain string (NOT run through ``str.format``), so braces are literal —
# do not double them. A single delegated submit handler covers all forms;
# the provider name is read from the form's ``data-provider`` attribute.
_PASSWORD_FORM_SCRIPT = """\
<script>
(function () {
  function setButtonState(button, loading) {
    if (!button) {
      return;
    }

    if (!button.dataset.defaultText) {
      button.dataset.defaultText =
        button.textContent || 'Sign in';
    }

    button.disabled = loading;
    button.textContent = loading
      ? 'Signing in...'
      : button.dataset.defaultText;
  }

  function wirePasswordToggle(form) {
    var toggle =
      form.querySelector('.password-toggle');
    var input =
      form.querySelector(
        'input[name=password]'
      );

    if (!toggle || !input) {
      return;
    }

    toggle.addEventListener(
      'click',
      function () {
        var showing =
          input.type === 'text';

        input.type =
          showing
            ? 'password'
            : 'text';

        toggle.textContent =
          showing
            ? 'Show'
            : 'Hide';

        toggle.setAttribute(
          'aria-label',
          showing
            ? 'Show password'
            : 'Hide password'
        );

        input.focus();
      }
    );
  }

  function wireSubmit(form) {
    form.addEventListener(
      'submit',
      function (event) {
        event.preventDefault();

        var error =
          form.querySelector(
            '.form-error'
          );
        var button =
          form.querySelector(
            'button[type=submit]'
          );

        if (error) {
          error.hidden = true;
          error.textContent = '';
        }

        setButtonState(
          button,
          true
        );

        var body = {
          provider:
            form.getAttribute(
              'data-provider'
            ) || '',
          username:
            (
              form.querySelector(
                'input[name=username]'
              ) || {}
            ).value || '',
          password:
            (
              form.querySelector(
                'input[name=password]'
              ) || {}
            ).value || '',
          next:
            (
              form.querySelector(
                'input[name=next]'
              ) || {}
            ).value || ''
        };

        fetch(
          '/auth/password-login',
          {
            method: 'POST',
            headers: {
              'Content-Type':
                'application/json'
            },
            body:
              JSON.stringify(body),
            credentials:
              'same-origin'
          }
        )
          .then(function (response) {
            if (response.ok) {
              return response
                .json()
                .then(function (data) {
                  window.location.assign(
                    (data && data.next) ||
                    '/'
                  );
                });
            }

            var message =
              response.status === 429
                ? (
                    'Too many attempts. ' +
                    'Wait a moment and try again.'
                  )
                : (
                    response.status === 401
                      ? (
                          'The username or password ' +
                          'is not valid.'
                        )
                      : (
                          'Sign-in failed. ' +
                          'Please try again.'
                        )
                  );

            if (error) {
              error.textContent =
                message;
              error.hidden = false;
            }

            setButtonState(
              button,
              false
            );
          })
          .catch(function () {
            if (error) {
              error.textContent =
                (
                  'Unable to reach the ' +
                  'authentication service.'
                );
              error.hidden = false;
            }

            setButtonState(
              button,
              false
            );
          });
      }
    );
  }

  var forms =
    document.querySelectorAll(
      'form.provider-form'
    );

  for (
    var index = 0;
    index < forms.length;
    index += 1
  ) {
    wirePasswordToggle(
      forms[index]
    );
    wireSubmit(
      forms[index]
    );
  }
})();
</script>
"""

def render_login_html(*, next_path: str = "") -> str:
    """Return the full HTML for ``GET /login``.

    ``next_path`` — when set, the post-login landing path the user
    originally requested. Threaded into each provider button's ``href``
    as a ``next=`` query parameter so the OAuth round trip carries it
    end-to-end. The caller (``routes.login_page``) is responsible for
    validating ``next_path`` against the same-origin rules before we
    emit it; we still HTML-escape it as defence in depth.
    """
    providers = list_providers()
    if not providers:
        return _EMPTY_HTML

    if next_path:
        # URL-encode then HTML-escape. The URL-encode step matches the
        # gate's ``_safe_next_target`` output shape (also URL-encoded),
        # so a value that round-tripped from /login?next=... back into
        # the button href is byte-identical.
        from urllib.parse import quote
        next_qs = f"&next={html.escape(quote(next_path, safe=''), quote=True)}"
    else:
        next_qs = ""

    buttons = []
    needs_password_script = False
    for p in providers:
        if getattr(p, "supports_password", False):
            needs_password_script = True
            buttons.append(_render_password_form(p, next_path))
        else:
            buttons.append(
                f'      <a class="provider-btn" '
                f'href="/auth/login?provider={html.escape(p.name, quote=True)}{next_qs}">'
                f'Sign in with {html.escape(p.display_name)}</a>'
            )
    script = _PASSWORD_FORM_SCRIPT if needs_password_script else ""
    return _LOGIN_HTML_TEMPLATE.format(
        provider_buttons="\n".join(buttons),
        password_script=script,
    )


def _render_password_form(provider, next_path: str) -> str:
    """Render the password-provider login form."""
    pname = html.escape(
        provider.name,
        quote=True,
    )
    safe_next = (
        html.escape(
            next_path,
            quote=True,
        )
        if next_path
        else ""
    )

    return (
        f'      <form class="provider-form" '
        f'data-provider="{pname}" '
        f'autocomplete="on">\n'
        f'        <div class="form-title">'
        f'Account credentials</div>\n'
        f'        <input type="hidden" '
        f'name="next" value="{safe_next}">\n'
        f'        <label class="field">\n'
        f'          <span class="field-label">'
        f'Username</span>\n'
        f'          <input class="field-input" '
        f'type="text" name="username" '
        f'autocomplete="username" '
        f'autocapitalize="none" '
        f'autocorrect="off" '
        f'spellcheck="false" '
        f'placeholder="Enter your username" '
        f'required>\n'
        f'        </label>\n'
        f'        <label class="field">\n'
        f'          <span class="field-label">'
        f'Password</span>\n'
        f'          <span class="field-password">\n'
        f'            <input class="field-input" '
        f'type="password" name="password" '
        f'autocomplete="current-password" '
        f'placeholder="Enter your password" '
        f'required>\n'
        f'            <button '
        f'class="password-toggle" '
        f'type="button" '
        f'aria-label="Show password">'
        f'Show</button>\n'
        f'          </span>\n'
        f'        </label>\n'
        f'        <div class="form-error" '
        f'role="alert" hidden></div>\n'
        f'        <button class="provider-btn" '
        f'type="submit">'
        f'Sign in</button>\n'
        f'      </form>'
    )
