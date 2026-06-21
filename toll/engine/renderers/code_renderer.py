from __future__ import annotations

import html

from .base import BaseRenderer


class CodeRenderer(BaseRenderer):
    def render(self, title: str, code: str, language: str = "") -> str:
        escaped = html.escape(code)
        return f"""<!DOCTYPE html>
<html lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — كود</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'SF Mono','Fira Code',monospace; background:#0d1117; color:#c9d1d9; padding:20px; }}
pre {{ background:#161b22; padding:24px; border-radius:8px; overflow-x:auto; font-size:.9rem; line-height:1.6; }}
code {{ white-space:pre; }}
.header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }}
h1 {{ font-size:1.2rem; color:#f0f6fc; }}
.lang {{ background:#30363d; padding:4px 12px; border-radius:4px; font-size:.8rem; color:#8b949e; }}
</style>
</head>
<body>
<div class="header">
  <h1>{title}</h1>
  {f'<span class="lang">{html.escape(language)}</span>' if language else ''}
</div>
<pre><code>{escaped}</code></pre>
</body>
</html>"""
