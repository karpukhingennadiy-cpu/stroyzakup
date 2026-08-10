# backend/apps/emails/html_sanitizer.py
# HTML whitelist sanitizer for LLM-generated email bodies (B9).
# Blocks <script>, on* attributes, javascript: URLs. Only allows a safe
# subset of tags used in transactional emails.

import re

ALLOWED_TAGS = {
    'p', 'br', 'b', 'i', 'strong', 'em', 'u',
    'ul', 'ol', 'li',
    'table', 'tr', 'td', 'th', 'thead', 'tbody',
    'a', 'h1', 'h2', 'h3', 'div', 'span',
}

ALLOWED_ATTRS = {'href', 'style', 'title', 'alt', 'target', 'rel'}

_TAG_RE = re.compile(r'<\s*(/?)\s*([a-zA-Z0-9]+)([^>]*)>', re.IGNORECASE)
_ATTR_RE = re.compile(r'([a-zA-Z-]+)\s*=\s*("[^"]*"|[^\s>]+)')


def _sanitize_attrs(raw: str) -> str:
    out = []
    for name, value in _ATTR_RE.findall(raw):
        name = name.strip().lower()
        value = value.strip()
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        if name.startswith('on'):
            continue  # strip all event handlers
        if name not in ALLOWED_ATTRS:
            continue
        if name == 'href' and value.lower().startswith(('javascript:', 'data:')):
            continue
        if name == 'style':
            # drop anything with url( or expression
            if 'url(' in value.lower() or 'expression' in value.lower():
                continue
        value = value.replace('<', '&lt;').replace('>', '&gt;')
        out.append(name + '="' + value + '"')
    return (' ' + ' '.join(out)) if out else ''


def sanitize_html(html_text: str) -> str:
    # Strip comments
    html_text = re.sub(r'<!--.*?-->', '', html_text, flags=re.DOTALL)

    def repl(m):
        closing = m.group(1)
        tag = m.group(2).lower()
        attrs = m.group(3)
        if tag not in ALLOWED_TAGS:
            return ''
        attrs_str = _sanitize_attrs(attrs)
        return '<' + closing + tag + attrs_str + '>'

    sanitized = _TAG_RE.sub(repl, html_text)
    # Escape any leftover angle brackets that are not tags
    sanitized = sanitized.replace('<script', '&lt;script').replace('</script', '&lt;/script')
    return sanitized
