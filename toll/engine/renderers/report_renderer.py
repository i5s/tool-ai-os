from __future__ import annotations

from .base import BaseRenderer


class ReportRenderer(BaseRenderer):
    def render(self, title: str, sections: list[dict]) -> str:
        body = ""
        for sec in sections:
            body += f"""
        <section>
          <h2>{sec.get("heading", "")}</h2>
          <p>{sec.get("body", "")}</p>"""
            for sub in sec.get("subsections", []):
                body += f"""
          <h3>{sub.get("subheading", "")}</h3>
          <p>{sub.get("body", "")}</p>"""
            body += "\n        </section>"

        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Times New Roman',serif; background:#f8f6f0; color:#1a1a1a; padding:40px; }}
.report {{ max-width:900px; margin:auto; background:#fff; padding:60px; border-radius:4px; box-shadow:0 2px 20px rgba(0,0,0,.08); }}
h1 {{ font-size:2.2rem; margin-bottom:8px; border-bottom:3px solid #1a365d; padding-bottom:16px; }}
.meta {{ color:#666; margin-bottom:40px; font-size:.95rem; }}
h2 {{ font-size:1.4rem; margin:32px 0 12px; color:#1a365d; }}
h3 {{ font-size:1.15rem; margin:20px 0 8px; color:#2d4a7a; }}
p {{ line-height:1.9; font-size:1.05rem; margin-bottom:16px; }}
.footer {{ margin-top:48px; padding-top:16px; border-top:1px solid #ddd; color:#888; font-size:.85rem; }}
</style>
</head>
<body>
<div class="report">
  <h1>{title}</h1>
  <div class="meta">تول — تقرير آلي</div>
  {body}
  <div class="footer">تم التوليد بواسطة تول v1.0.0</div>
</div>
</body>
</html>"""
