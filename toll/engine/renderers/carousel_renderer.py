from __future__ import annotations

from .base import BaseRenderer


class CarouselRenderer(BaseRenderer):
    def render(self, title: str, slides: list[dict]) -> str:
        slides_html = "".join(
            f"""
            <div class="slide">
              <h1>{s.get("title", title)}</h1>
              <div class="sub">{s.get("subtitle", "")}</div>
              <p>{s.get("content", "")}</p>
            </div>"""
            for s in slides
        )
        dots = "".join(
            f'<div class="dot{" active" if i == 0 else ""}" onclick="go({i})"></div>'
            for i in range(len(slides))
        )
        n = len(slides)
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Carousel</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:system-ui,-apple-system,sans-serif; background:#0f172a; color:#f8fafc; display:flex; justify-content:center; align-items:center; min-height:100vh; }}
.carousel {{ position:relative; width:800px; max-width:90vw; overflow:hidden; border-radius:24px; background:linear-gradient(135deg,#1e293b,#334155); box-shadow:0 25px 50px rgba(0,0,0,.5); }}
.slides {{ display:flex; transition:transform .5s ease; }}
.slide {{ min-width:100%; padding:60px 40px; }}
.slide h1 {{ font-size:2rem; margin-bottom:8px; color:#38bdf8; }}
.slide .sub {{ font-size:1rem; color:#94a3b8; margin-bottom:24px; }}
.slide p {{ font-size:1.125rem; line-height:1.8; color:#cbd5e1; }}
.nav {{ display:flex; justify-content:center; gap:12px; padding:20px; }}
.nav button {{ background:#334155; border:none; color:#fff; width:44px; height:44px; border-radius:50%; cursor:pointer; font-size:1.2rem; transition:.2s; }}
.nav button:hover {{ background:#38bdf8; }}
.dots {{ display:flex; justify-content:center; gap:8px; padding:0 20px 20px; }}
.dot {{ width:10px; height:10px; border-radius:50%; background:#475569; cursor:pointer; transition:.3s; }}
.dot.active {{ background:#38bdf8; width:28px; border-radius:5px; }}
</style>
</head>
<body>
<div class="carousel">
  <div class="slides" id="slides">{slides_html}</div>
  <div class="dots" id="dots">{dots}</div>
  <div class="nav">
    <button onclick="prev()">←</button>
    <button onclick="next()">→</button>
  </div>
</div>
<script>
let i=0,n={n};
function go(x){{ i=x; document.getElementById('slides').style.transform=`translateX(${{-i*100}}%)`;
  document.querySelectorAll('.dot').forEach((d,j)=>d.className='dot'+(j===i?' active':'')); }}
function next(){{ go((i+1)%n); }}
function prev(){{ go((i-1+n)%n); }}
</script>
</body>
</html>"""
