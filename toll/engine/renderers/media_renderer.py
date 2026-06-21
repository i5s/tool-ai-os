from __future__ import annotations

from ...model.artifact import Artifact


class MediaPreviewRenderer:
    def image_preview(self, artifact: Artifact) -> str:
        media_url = artifact.content.get("media_url", "")
        provider = artifact.content.get("provider", "")
        model = artifact.content.get("model", "")
        prompt = artifact.content.get("prompt", "")
        seed = artifact.content.get("seed")
        width = artifact.content.get("width")
        height = artifact.content.get("height")

        return f"""<!DOCTYPE html>
<html lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{artifact.title} — معاينة</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:system-ui,sans-serif; background:#0f172a; color:#f8fafc; padding:24px; display:flex; justify-content:center; }}
.container {{ max-width:960px; width:100%; }}
img {{ max-width:100%; height:auto; border-radius:12px; margin-bottom:20px; box-shadow:0 4px 24px rgba(0,0,0,.3); }}
.meta {{ background:#1e293b; padding:20px; border-radius:12px; }}
.meta h2 {{ font-size:1.2rem; margin-bottom:12px; color:#38bdf8; }}
table {{ width:100%; border-collapse:collapse; font-size:.85rem; }}
th, td {{ padding:8px 12px; text-align:right; border-bottom:1px solid #334155; }}
th {{ color:#94a3b8; font-weight:400; }}
td {{ color:#f1f5f9; }}
.prompt {{ background:#0f172a; padding:12px; border-radius:8px; margin-top:12px; font-size:.85rem; color:#cbd5e1; direction:ltr; text-align:left; font-family:monospace; }}
a {{ display:inline-block; margin-top:16px; color:#38bdf8; text-decoration:none; }}
</style>
</head>
<body>
<div class="container">
  <img src="{media_url}" alt="{artifact.title}">
  <div class="meta">
    <h2>{artifact.title}</h2>
    <table>
      <tr><th>المزود</th><td>{provider}</td></tr>
      <tr><th>الموديل</th><td>{model}</td></tr>
      <tr><th>الأبعاد</th><td>{width or '?'} × {height or '?'}</td></tr>
      {f'<tr><th>Seed</th><td>{seed}</td></tr>' if seed is not None else ''}
    </table>
    <div class="prompt">{prompt}</div>
  </div>
  <a href="{media_url}" download>تحميل ←</a>
</div>
</body>
</html>"""

    def video_preview(self, artifact: Artifact) -> str:
        media_url = artifact.content.get("media_url", "")
        provider = artifact.content.get("provider", "")
        model = artifact.content.get("model", "")
        prompt = artifact.content.get("prompt", "")
        width = artifact.content.get("width")
        height = artifact.content.get("height")

        return f"""<!DOCTYPE html>
<html lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{artifact.title} — معاينة</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:system-ui,sans-serif; background:#0f172a; color:#f8fafc; padding:24px; display:flex; justify-content:center; }}
.container {{ max-width:960px; width:100%; }}
video {{ max-width:100%; border-radius:12px; margin-bottom:20px; box-shadow:0 4px 24px rgba(0,0,0,.3); }}
.meta {{ background:#1e293b; padding:20px; border-radius:12px; }}
.meta h2 {{ font-size:1.2rem; margin-bottom:12px; color:#38bdf8; }}
table {{ width:100%; border-collapse:collapse; font-size:.85rem; }}
th, td {{ padding:8px 12px; text-align:right; border-bottom:1px solid #334155; }}
th {{ color:#94a3b8; font-weight:400; }}
td {{ color:#f1f5f9; }}
.prompt {{ background:#0f172a; padding:12px; border-radius:8px; margin-top:12px; font-size:.85rem; color:#cbd5e1; direction:ltr; text-align:left; font-family:monospace; }}
a {{ display:inline-block; margin-top:16px; color:#38bdf8; text-decoration:none; }}
</style>
</head>
<body>
<div class="container">
  <video controls width="100%">
    <source src="{media_url}">
    متصفحك لا يدعم تشغيل الفيديو.
  </video>
  <div class="meta">
    <h2>{artifact.title}</h2>
    <table>
      <tr><th>المزود</th><td>{provider}</td></tr>
      <tr><th>الموديل</th><td>{model}</td></tr>
      <tr><th>الأبعاد</th><td>{width or '?'} × {height or '?'}</td></tr>
    </table>
    <div class="prompt">{prompt}</div>
  </div>
  <a href="{media_url}" download>تحميل ←</a>
</div>
</body>
</html>"""
