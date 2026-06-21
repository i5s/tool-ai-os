import json
from pathlib import Path
from ..core.ai import AI
from ..core.storage import Storage
from ..core.connection_manager import ConnectionManager


class ContentMachine:
    def __init__(self, cm: ConnectionManager | None = None):
        if cm:
            self.ai = AI(cm=cm)
            self.db = Storage(cm=cm)
        else:
            self.ai = AI()
            self.db = Storage(cm=self.ai.settings.db.cm)

    def carousel(self, topic: str) -> str:
        slides = [
            {"title": topic, "subtitle": "مقدمة", "content": "نظرة عامة حول الموضوع"},
            {"title": topic, "subtitle": "النقاط الرئيسية", "content": "أهم المحاور الأساسية"},
            {"title": topic, "subtitle": "التفاصيل", "content": "شرح وافي ومتكامل"},
            {"title": topic, "subtitle": "الخاتمة", "content": "ملخص وتوصيات"},
        ]
        slides_json = json.dumps(slides)
        html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{topic} — Carousel</title>
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
  <div class="slides" id="slides">
    {''.join(f'''
    <div class="slide">
      <h1>{s["title"]}</h1>
      <div class="sub">{s["subtitle"]}</div>
      <p>{s["content"]}</p>
    </div>''' for s in slides)}
  </div>
  <div class="dots" id="dots">
    {''.join(f'<div class="dot{i==0 and " active" or ""}" onclick="go({i})"></div>' for i in range(len(slides)))}
  </div>
  <div class="nav">
    <button onclick="prev()">←</button>
    <button onclick="next()">→</button>
  </div>
</div>
<script>
let i=0,n={len(slides)};
function go(x){{ i=x; document.getElementById('slides').style.transform=`translateX(${{-i*100}}%)`;
  document.querySelectorAll('.dot').forEach((d,j)=>d.className='dot'+(j===i?' active':'')); }}
function next(){{ go((i+1)%n); }}
function prev(){{ go((i-1+n)%n); }}
</script>
</body>
</html>"""
        out = Path.home() / "Claude" / "Projects" / "الموقع" / f"carousel-{topic[:20]}.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        self.db.save_history("content", f"carousel: {topic}", f"HTML ({len(slides)} شرائح)")
        return f"✅ Carousel: {out}"

    def social_post(self, platform: str, topic: str) -> str:
        post = f"""**{topic}**

🚀 خلاصة الموضوع:
• نقطة رئيسية أولى
• نقطة رئيسية ثانية
• نقطة رئيسية ثالثة

#تول #{platform}"""
        self.db.save_history("content", f"social: {platform} - {topic}", post)
        return f"✅ منشور {platform}:\n\n{post}"

    def all(self, task: str) -> list:
        return [self.carousel(task), self.social_post("عام", task)]
