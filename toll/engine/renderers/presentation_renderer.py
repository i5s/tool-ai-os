from __future__ import annotations

from .base import BaseRenderer


class PresentationRenderer(BaseRenderer):
    def render(self, title: str, slides: list[dict]) -> str:
        slides_html = ""
        for i, slide in enumerate(slides):
            active = ' active' if i == 0 else ''
            slides_html += f"""
    <div class="slide{active}">
      <div class="slide-num">{i+1}/{len(slides)}</div>
      <h2>{slide.get("title", title)}</h2>
      <p>{slide.get("content", "")}</p>
    </div>"""

        return f"""<!DOCTYPE html>
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
