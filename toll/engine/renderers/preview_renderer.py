from __future__ import annotations

import json

from ...model.artifact import Artifact, ArtifactType


class PreviewRenderer:
    def carousel_preview(self, artifact: Artifact) -> str:
        slides = artifact.content.get("slides", [])
        first = slides[0] if slides else {"title": artifact.title, "content": ""}
        total = len(slides)
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{artifact.title} — معاينة</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:system-ui,sans-serif; background:#0f172a; color:#f8fafc; display:flex; justify-content:center; align-items:center; min-height:100vh; }}
.card {{ width:600px; max-width:90vw; padding:40px; background:linear-gradient(135deg,#1e293b,#334155); border-radius:24px; text-align:center; }}
h2 {{ color:#38bdf8; font-size:1.5rem; margin-bottom:8px; }}
p {{ color:#cbd5e1; font-size:1rem; line-height:1.7; margin-bottom:16px; }}
.meta {{ color:#64748b; font-size:.85rem; }}
.badge {{ display:inline-block; background:#334155; padding:4px 12px; border-radius:12px; font-size:.8rem; color:#94a3b8; margin-bottom:16px; }}
a {{ display:inline-block; margin-top:16px; color:#38bdf8; text-decoration:none; font-weight:600; }}
a:hover {{ text-decoration:underline; }}
</style>
</head>
<body>
<div class="card">
  <div class="badge">Carousel — {total} شرائح</div>
  <h2>{first.get("title", artifact.title)}</h2>
  {f'<p>{first.get("content", "")}</p>' if first.get("content") else ''}
  <div class="meta">تم الإنشاء: {artifact.created_at[:10]}</div>
  <a href="index.html">عرض الكامل ←</a>
</div>
</body>
</html>"""

    def report_preview(self, artifact: Artifact) -> str:
        sections = artifact.content.get("sections", [])
        toc = "".join(f"<li>{s.get('heading', '')}</li>" for s in sections[:6])
        first = sections[0] if sections else {}
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{artifact.title} — معاينة</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Times New Roman',serif; background:#f8f6f0; color:#1a1a1a; padding:40px; }}
.card {{ max-width:700px; margin:auto; background:#fff; padding:40px; border-radius:8px; box-shadow:0 2px 12px rgba(0,0,0,.06); }}
h2 {{ font-size:1.5rem; color:#1a365d; margin-bottom:4px; }}
.meta {{ color:#666; font-size:.9rem; margin-bottom:20px; }}
.badge {{ display:inline-block; background:#e2e8f0; padding:2px 10px; border-radius:10px; font-size:.8rem; color:#475569; margin-bottom:12px; }}
ul {{ padding-right:20px; }}
li {{ line-height:1.8; }}
p {{ line-height:1.8; color:#334155; margin-top:16px; }}
a {{ display:inline-block; margin-top:20px; color:#1a365d; font-weight:600; }}
</style>
</head>
<body>
<div class="card">
  <div class="badge">تقرير — {len(sections)} أقسام</div>
  <h2>{artifact.title}</h2>
  <div class="meta">{artifact.created_at[:10]}</div>
  {f"<p>{first.get('body', '')[:200]}...</p>" if first.get("body") else ""}
  {f"<ul>{toc}</ul>" if toc else ""}
  <a href="index.html">عرض التقرير كامل ←</a>
</div>
</body>
</html>"""

    def presentation_preview(self, artifact: Artifact) -> str:
        slides = artifact.content.get("slides", [])
        first = slides[0] if slides else {}
        total = len(slides)
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{artifact.title} — معاينة</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:system-ui,sans-serif; background:#0f172a; color:#f8fafc; display:flex; justify-content:center; align-items:center; min-height:100vh; }}
.card {{ width:600px; max-width:90vw; padding:40px; background:linear-gradient(135deg,#1e293b,#0f172a); border-radius:24px; text-align:center; }}
h2 {{ color:#f8fafc; font-size:1.8rem; margin-bottom:8px; }}
p {{ color:#94a3b8; font-size:1rem; line-height:1.7; }}
.meta {{ color:#475569; font-size:.85rem; margin-top:16px; }}
.badge {{ display:inline-block; background:#1e293b; padding:4px 12px; border-radius:12px; font-size:.8rem; color:#94a3b8; margin-bottom:16px; }}
a {{ display:inline-block; margin-top:20px; color:#38bdf8; text-decoration:none; font-weight:600; }}
a:hover {{ text-decoration:underline; }}
</style>
</head>
<body>
<div class="card">
  <div class="badge">عرض تقديمي — {total} شرائح</div>
  <h2>{first.get("title", artifact.title)}</h2>
  {f'<p>{first.get("content", "")}</p>' if first.get("content") else ''}
  <div class="meta">{total} شرائح • {artifact.created_at[:10]}</div>
  <a href="index.html">عرض كامل ←</a>
</div>
</body>
</html>"""

    def code_preview(self, artifact: Artifact) -> str:
        code = artifact.content.get("code", "")
        lines = code.strip().split("\n")[:10]
        snippet = "\n".join(lines)
        remaining = len(code.strip().split("\n")) - 10
        lang = artifact.content.get("language", "")
        return f"""<!DOCTYPE html>
<html lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{artifact.title} — معاينة</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'SF Mono','Fira Code',monospace; background:#0d1117; color:#c9d1d9; padding:20px; }}
pre {{ background:#161b22; padding:16px; border-radius:8px; font-size:.85rem; }}
.badge {{ display:inline-block; background:#30363d; padding:2px 8px; border-radius:4px; font-size:.75rem; color:#8b949e; margin-bottom:8px; }}
h2 {{ font-size:1rem; color:#f0f6fc; margin-bottom:8px; }}
a {{ display:inline-block; margin-top:12px; color:#58a6ff; text-decoration:none; }}
</style>
</head>
<body>
  {f'<div class="badge">{lang}</div>' if lang else ''}
  <h2>{artifact.title}</h2>
  <pre>{snippet}</pre>
  {f'<div style="color:#8b949e;font-size:.8rem;margin-top:4px;">... {remaining} سطر إضافي</div>' if remaining > 0 else ''}
  <a href="index.html">عرض الكود كامل ←</a>
</body>
</html>"""

    def generic_preview(self, artifact: Artifact) -> str:
        return f"""<!DOCTYPE html>
<html lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{artifact.title}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:system-ui,sans-serif; background:#f8f6f0; padding:40px; display:flex; justify-content:center; }}
.card {{ max-width:500px; background:#fff; padding:32px; border-radius:12px; box-shadow:0 2px 12px rgba(0,0,0,.06); }}
h2 {{ margin-bottom:8px; }}
.meta {{ color:#666; font-size:.85rem; }}
a {{ display:inline-block; margin-top:16px; }}
</style>
</head>
<body>
<div class="card">
  <h2>{artifact.title}</h2>
  <div class="meta">{artifact.type.value} • {artifact.created_at[:10]}</div>
  <a href="index.html">فتح ←</a>
</div>
</body>
</html>"""

    def json_preview(self, artifact: Artifact) -> dict:
        return {
            "id": artifact.id,
            "type": artifact.type.value,
            "title": artifact.title,
            "status": artifact.status.value,
            "version": artifact.version,
            "created_at": artifact.created_at,
            "provider": artifact.provider,
            "model": artifact.model,
            "intent": artifact.intent,
            "tags": artifact.tags,
            "workspace_type": artifact.workspace_type,
            "workspace_id": artifact.workspace_id,
            "summary": self._summarize(artifact),
            "full_url": f"/data/artifacts/{artifact.id}/index.html",
            "preview_url": f"/data/artifacts/{artifact.id}/preview.html",
        }

    def research_preview(self, artifact: Artifact) -> str:
        content = artifact.content
        query = content.get("query", "")
        sources = content.get("sources", [])
        source_count = content.get("source_count", len(sources))
        citations = content.get("citations", [])
        synopsis = content.get("synopsis", "")
        key_findings = content.get("key_findings", [])
        style = content.get("style", "apa")
        toc = "".join(
            f"<li>{s.get('title', '')[:60]}</li>"
            for s in sources[:5]
        )
        kf_html = "".join(
            f"<li>{k}</li>" for k in key_findings[:3]
        ) if key_findings else ""
        cite_sample = (
            f"<blockquote>{citations[0][:120]}…</blockquote>"
            if citations else ""
        )
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{artifact.title} — معاينة بحث</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:system-ui,sans-serif; background:#f0f4f8; color:#1a1a2e; padding:24px; }}
.card {{ max-width:720px; margin:auto; background:#fff; border-radius:16px; padding:32px; box-shadow:0 2px 12px rgba(0,0,0,.06); }}
h2 {{ font-size:1.4rem; margin-bottom:4px; color:#1a365d; }}
.badge {{ display:inline-block; background:#e2e8f0; padding:2px 10px; border-radius:10px; font-size:.8rem; color:#475569; margin-bottom:12px; }}
.meta {{ color:#64748b; font-size:.85rem; margin-bottom:16px; }}
.synopsis {{ background:#f8fafc; padding:16px; border-radius:8px; margin:12px 0; line-height:1.7; color:#334155; }}
blockquote {{ border-right:3px solid #3b82f6; padding:8px 16px; margin:8px 0; background:#f8fafc; color:#475569; font-size:.9rem; }}
ul {{ padding-right:20px; }}
li {{ line-height:1.8; font-size:.95rem; }}
a {{ display:inline-block; margin-top:16px; color:#3b82f6; text-decoration:none; font-weight:600; }}
</style>
</head>
<body>
<div class="card">
  <div class="badge">بحث — {style.upper()} • {source_count} مصدر</div>
  <h2>{artifact.title}</h2>
  {f'<p class="meta">{query[:100]}</p>' if query else f'<div class="meta">{artifact.created_at[:10]}</div>'}
  {f'<div class="synopsis">{synopsis[:300]}…</div>' if synopsis else ''}
  {f'<ul>{kf_html}</ul>' if kf_html else ''}
  {cite_sample}
  {f'<ul>{toc}</ul>' if toc else ''}
  <a href="index.html">عرض البحث كامل ←</a>
</div>
</body>
</html>"""

    def _summarize(self, artifact: Artifact) -> str:
        if artifact.type == ArtifactType.CAROUSEL:
            slides = artifact.content.get("slides", [])
            return f"Carousel: {len(slides)} slides"
        if artifact.type == ArtifactType.REPORT:
            sections = artifact.content.get("sections", [])
            return f"Report: {len(sections)} sections"
        if artifact.type == ArtifactType.PRESENTATION:
            slides = artifact.content.get("slides", [])
            return f"Presentation: {len(slides)} slides"
        if artifact.type == ArtifactType.CODE:
            code = artifact.content.get("code", "")
            return f"Code: {len(code.strip().split(chr(10)))} lines"
        if artifact.type == ArtifactType.RESEARCH:
            sources = artifact.content.get("sources", [])
            return f"Research: {len(sources)} sources"
        if artifact.type == ArtifactType.IMAGE_GEN:
            prompt = artifact.content.get("prompt", "")
            return f"Generated Image: {prompt[:50]}…" if len(prompt) > 50 else f"Generated Image: {prompt}"
        if artifact.type == ArtifactType.VIDEO:
            prompt = artifact.content.get("prompt", "")
            return f"Generated Video: {prompt[:50]}…" if len(prompt) > 50 else f"Generated Video: {prompt}"
        return f"{artifact.type.value}: {artifact.title}"
