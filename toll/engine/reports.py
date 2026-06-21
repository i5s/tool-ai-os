from __future__ import annotations

from pathlib import Path
from ..core.ai import AI
from ..core.storage import Storage
from ..core.connection_manager import ConnectionManager


class Reports:
    def __init__(self, cm: ConnectionManager | None = None):
        if cm:
            self.ai = AI(cm=cm)
            self.db = Storage(cm=cm)
        else:
            self.ai = AI()
            self.db = Storage(cm=self.ai.settings.db.cm)

    def report(self, title: str, sections: list = None) -> str:
        if sections is None:
            sections = ["الملخص التنفيذي", "المقدمة", "النقاط الرئيسية", "التحليل", "التوصيات", "المراجع"]
        items = "".join(f'<li>{s}</li>' for s in sections)
        html = f"""<!DOCTYPE html>
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
p {{ line-height:1.9; font-size:1.05rem; margin-bottom:16px; }}
ul {{ padding-right:24px; }}
li {{ line-height:1.8; margin-bottom:8px; }}
.footer {{ margin-top:48px; padding-top:16px; border-top:1px solid #ddd; color:#888; font-size:.85rem; }}
</style>
</head>
<body>
<div class="report">
  <h1>{title}</h1>
  <div class="meta">تول — تقرير آلي</div>
  <ul>
    {items}
  </ul>
  <div class="footer">تم التوليد بواسطة تول v1.0.0</div>
</div>
</body>
</html>"""
        out = Path.home() / "Claude" / "Projects" / "الموقع" / f"report-{title[:20]}.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        self.db.save_history("report", title, f"HTML ({len(sections)} أقسام)")
        return f"📄 التقرير: {out}"

    def presentation(self, title: str, slide_count: int = 5) -> str:
        slides_html = ""
        for i in range(1, slide_count + 1):
            slides_html += f"""
    <div class="slide">
      <div class="slide-num">{i}/{slide_count}</div>
      <h2>{'●' if i == 1 else 'الشريحة ' + str(i)}</h2>
      <p>محتوى الشريحة {i} — {title}</p>
    </div>"""

        html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — عرض</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:system-ui,sans-serif; background:#0f172a; display:flex; justify-content:center; align-items:center; min-height:100vh; }}
.deck {{ width:900px; max-width:95vw; height:550px; position:relative; overflow:hidden; border-radius:20px; background:linear-gradient(135deg,#1e293b,#0f172a); box-shadow:0 25px 60px rgba(0,0,0,.5); }}
.slide {{ position:absolute; inset:0; display:flex; flex-direction:column; justify-content:center; align-items:center; padding:60px; opacity:0; transition:opacity .5s; }}
.slide.active {{ opacity:1; }}
.slide-num {{ position:absolute; bottom:20px; left:20px; color:#475569; font-size:.85rem; }}
h2 {{ font-size:2.5rem; color:#f8fafc; margin-bottom:16px; text-align:center; }}
p {{ font-size:1.2rem; color:#94a3b8; text-align:center; line-height:1.7; max-width:600px; }}
.controls {{ position:absolute; bottom:20px; right:20px; display:flex; gap:8px; }}
.controls button {{ background:#334155; border:none; color:#fff; width:40px; height:40px; border-radius:50%; cursor:pointer; font-size:1.1rem; }}
.controls button:hover {{ background:#38bdf8; }}
</style>
</head>
<body>
<div class="deck">
  {slides_html}
  <div class="controls">
    <button onclick="p()">←</button>
    <button onclick="n()">→</button>
  </div>
</div>
<script>
let i=0,s=document.querySelectorAll('.slide'); s[0].classList.add('active');
function n(){{ s[i].classList.remove('active'); i=(i+1)%s.length; s[i].classList.add('active'); }}
function p(){{ s[i].classList.remove('active'); i=(i-1+s.length)%s.length; s[i].classList.add('active'); }}
</script>
</body>
</html>"""
        out = Path.home() / "Claude" / "Projects" / "الموقع" / f"presentation-{title[:20]}.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        self.db.save_history("report", f"presentation: {title}", f"HTML ({slide_count} شرائح)")
        return f"📺 العرض: {out}"

    def all(self, task: str) -> list:
        return [self.report(task), self.presentation(task)]
