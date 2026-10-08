"""HTML sanitizer for XSS mitigation.

Provides a server-side text-escaping utility and a JavaScript injection
helper that can be embedded into the dashboard HTML to centralise
client-side sanitisation.

Usage (server-side, Python)
---------------------------
    from qa_dashboard.infrastructure.security.html_sanitizer import escape_html

    safe = escape_html(user_input)

Usage (client-side, via injected script)
-----------------------------------------
    The string returned by :func:`js_sanitizer_snippet` should be embedded
    once in the <head> of the dashboard HTML.  After that, any dynamic
    insertion of untrusted text must use::

        QaSanitizer.setText(element, untrustedValue)
        // instead of element.innerHTML = untrustedValue

    For cases where HTML is genuinely required (e.g., rendering a Markdown
    report) a restricted-tag allowlist can be passed::

        QaSanitizer.sanitize(untrustedHtml, ['b', 'i', 'em', 'strong', 'br'])
"""

from __future__ import annotations

_HTML_ESCAPE_TABLE: dict[str, str] = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#x27;",
    "/": "&#x2F;",
    "`": "&#x60;",
    "=": "&#x3D;",
}


def escape_html(text: str) -> str:
    """Return *text* with HTML special characters escaped.

    Safe for insertion into HTML element content or attribute values.
    Does NOT allow any HTML tags to pass through.

    Parameters
    ----------
    text:
        Arbitrary string from an untrusted source.

    Returns
    -------
    str
        HTML-entity-encoded version of *text*, safe for innerHTML assignment.
    """
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    return "".join(_HTML_ESCAPE_TABLE.get(ch, ch) for ch in text)


def safe_html(value: object) -> str:
    """Escape *value* as a safe HTML string.

    Thin convenience alias for :func:`escape_html` that also handles
    non-string inputs (None, int, list, etc.) by coercing them to string
    first.

    >>> safe_html('<script>alert(1)</script>')
    '&lt;script&gt;alert(1)&lt;&#x2F;script&gt;'
    """
    if value is None:
        return ""
    return escape_html(str(value))


# ---------------------------------------------------------------------------
# Client-side JavaScript snippet
# ---------------------------------------------------------------------------

def js_sanitizer_snippet() -> str:
    """Return a self-contained JavaScript snippet that defines ``QaSanitizer``.

    The snippet should be embedded once in ``<head>`` of the dashboard HTML.
    It intentionally does NOT depend on any third-party library.

    ``QaSanitizer`` exposes:

    * ``QaSanitizer.setText(element, value)``
      – sets element's ``textContent`` (safest; no HTML rendered).
    * ``QaSanitizer.setAttr(element, attr, value)``
      – sets an element attribute using ``setAttribute`` after escaping.
    * ``QaSanitizer.sanitize(html, allowedTags=[])``
      – strips all tags not in *allowedTags* from *html*.  Use only when
        rendering HTML (e.g., Markdown output) is genuinely required.
    * ``QaSanitizer.escape(text)``
      – returns an HTML-entity-encoded string.
    """
    return r"""
<script id="qa-sanitizer">
/* QaSanitizer – centralised XSS-safe DOM helpers. Version: phase-02 */
;(function (global) {
  'use strict';

  var ESCAPE_MAP = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
    '`': '&#x60;',
    '=': '&#x3D;'
  };

  function escapeChar(c) { return ESCAPE_MAP[c] || c; }

  function escape(text) {
    if (text === null || text === undefined) return '';
    return String(text).replace(/[&<>"'`=\/]/g, escapeChar);
  }

  /** Set element text safely (no HTML rendered). */
  function setText(element, value) {
    if (!element) return;
    element.textContent = (value !== null && value !== undefined) ? String(value) : '';
  }

  /** Set element attribute safely. */
  function setAttr(element, attr, value) {
    if (!element || !attr) return;
    element.setAttribute(attr, escape(value));
  }

  /**
   * Strip all tags not in allowedTags from html string.
   * USE ONLY when HTML rendering is genuinely needed.
   * Prefer setText for plain values.
   */
  function sanitize(html, allowedTags) {
    if (html === null || html === undefined) return '';
    var allowed = Array.isArray(allowedTags) ? allowedTags.map(function(t){ return t.toLowerCase(); }) : [];
    var tmp = document.createElement('div');
    tmp.innerHTML = String(html);
    walkAndStrip(tmp, allowed);
    return tmp.innerHTML;
  }

  function walkAndStrip(node, allowed) {
    var children = Array.prototype.slice.call(node.childNodes);
    for (var i = 0; i < children.length; i++) {
      var child = children[i];
      if (child.nodeType === 1) { /* Element */
        var tag = child.tagName.toLowerCase();
        if (allowed.indexOf(tag) === -1) {
          /* Replace disallowed element with its text content */
          var text = document.createTextNode(child.textContent || '');
          node.replaceChild(text, child);
        } else {
          /* Strip all attributes from allowed tags */
          var attrs = Array.prototype.slice.call(child.attributes);
          for (var j = 0; j < attrs.length; j++) {
            child.removeAttribute(attrs[j].name);
          }
          walkAndStrip(child, allowed);
        }
      }
    }
  }

  global.QaSanitizer = {
    escape: escape,
    setText: setText,
    setAttr: setAttr,
    sanitize: sanitize
  };

})(window);
</script>
"""
