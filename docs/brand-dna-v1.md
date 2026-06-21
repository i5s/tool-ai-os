# تول (TOOL) — Brand DNA v1

> **Version**: 1.0  
> **Status**: Approved — canonical brand bible  
> **Purpose**: Single source of truth for all brand, design, and content decisions.

---

## 1. Brand Philosophy

### Mission
توحيد — unify creativity, learning, research, productivity, design, and development into a single intelligent workspace.

### Core Belief
Tool is a **collaborative operator**, not a chatbot. It discusses before executing, plans before building, and learns from every interaction.

### Workflow Ethos
```
Discuss → Plan → Approve → Execute → Learn
```

- Never execute large tasks without understanding intent.
- Ask clarifying questions when required.
- Build plans before execution.
- Learn from user decisions.

### Personality
- **Tone**: Professional, academic, design-conscious
- **Language**: Arabic-first, English-secondary
- **Direction**: RTL (right-to-left)
- **Relationship**: Collaborative partner, not a servant

---

## 2. Number Chronicles System

### Version Schema
```
v{major}.{sprint-letter}{sprint-number}-{descriptive-slug}
```
Examples: `v0.6-media-foundation`, `v0.7c-prompt-learning-loop`, `v0.8b-operations-ui`

### Feature Flag Schema
```
{area}_{feature} = True | False
```
Examples: `media_generation`, `prompt_intelligence`, `operations_layer`

### Migration Schema
```
{NNNN}_{description}.sql
```
Examples: `0010_media.sql`, `0012_prompt_intelligence.sql`, `0013_operations_layer.sql`

### Tag Naming
- Semantic versioning: `v{major}.{minor}.{patch}`
- Sprint tags: `v{sprint-number}-{descriptive-slug}`
- All tags are pushed to origin and protected in GitHub Releases

---

## 3. Theme Definitions

### Dark Theme (default)
```
--bg:           #1a1a2e    /* Deep navy background */
--bg2:          #16213e    /* Slightly lighter bg */
--bg3:          #0f3460    /* Accent bg */
--sidebar:      #111827    /* Darkest sidebar */
--sidebar-hover:#1f2937    /* Sidebar item hover */
--surface:      #1f2937    /* Card/surface bg */
--surface-hover:#374151    /* Surface hover */
--primary:      #38bdf8    /* Sky blue accent */
--primary-dim:  #0ea5e9    /* Dimmed primary */
--accent:       #a78bfa    /* Purple accent */
--accent2:      #f472b6    /* Pink accent */
--text:         #f1f5f9    /* Primary text */
--text2:        #94a3b8    /* Secondary text */
--text3:        #64748b    /* Tertiary / muted text */
--border:       #1e293b    /* Subtle borders */
--border2:      #334155    /* Stronger borders */
--send:         #3b82f6    /* Send button blue */
--send-hover:   #2563eb    /* Send button hover */
--radius:       12px       /* Default border radius */
--radius-lg:    20px       /* Large radius */
```

### Light Theme (toggle)
```
--bg:           #f8fafc    /* Off-white */
--bg2:          #f1f5f9    /* Light gray */
--bg3:          #e2e8f0    /* Medium gray */
--sidebar:      #ffffff    /* White sidebar */
--sidebar-hover:#f1f5f9    /* Light hover */
--surface:      #ffffff    /* White surface */
--text:         #0f172a    /* Near-black text */
--text2:        #475569    /* Dark gray */
--text3:        #94a3b8    /* Medium gray */
--border:       #e2e8f0    /* Light borders */
--border2:      #cbd5e1    /* Stronger borders */
```

### Application
- Theme toggles via `classList.toggle('light')` on `:root`
- All components use CSS variables — no hardcoded colors
- Transition: `background .3s, color .3s`

### Status Badge Colors (shared across themes)
```
ok (success):   rgba(34,197,94,.15) bg, #22c55e text
warn (warning): rgba(250,204,21,.15) bg, #eab308 text
err (error):    rgba(239,68,68,.15) bg, #ef4444 text
primary button: var(--primary-dim) bg, #fff text
danger button:  rgba(239,68,68,.8) bg, #fff text
```

---

## 4. Typography System

### Font Stack
- **Primary interface**: `system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif`
- **Code/monospace**: `'SF Mono', 'Fira Code', monospace`
- **Reports (print-style)**: `'Times New Roman', serif`

### Size Scale
```
sidebar h1:       1.15rem / 600 weight
panel headers:    1.1rem
card titles:      0.95rem
body text:        0.85rem — 0.9rem
meta/labels:      0.75rem — 0.85rem
stat values:      1.4rem — 1.8rem / 700 weight
badges:           0.75rem
```

### Line Heights
```
body text:    1.7
lists:        1.8
code:         1.5
```

### Usage Rules
- RTL text alignment (text-align: right) for Arabic content
- LTR (text-align: left) for code and English-only content
- No `@font-face` or custom font loading — system fonts only
- Monospace for code previews, serif for report previews

---

## 5. Motion Principles

### Approved Motion Properties
- `transition: .15s` — hover states, color changes, border changes
- `transition: .2s` — button hover, card hover
- `transition: .3s ease` — sidebar open/close, theme toggle
- `transition: height .3s` — bar chart animations

### Prohibited
- No keyframe animations (no `@keyframes`)
- No scroll-triggered animations
- No parallax
- No loading spinners (use text placeholders instead)

---

## 6. Carousel Principles

### Structure
- Each carousel is a series of slides rendered as HTML
- Slides contain: title, content, optional image
- Preview shows first slide + slide count badge

### Design Rules
- Gradient background: `linear-gradient(135deg, #1e293b, #334155)` (dark)
- Centered card layout: `width: 600px, max-width: 90vw`
- Title color: `#38bdf8` (primary)
- Body color: `#cbd5e1`
- Badge: small rounded pill showing total slide count
- "عرض الكامل ←" link to full view

### Content
- Arabic text
- Professional tone
- Each slide self-contained
- No external dependencies

---

## 7. Content Pillars

| Pillar | Description | Example Handler |
|--------|-------------|-----------------|
| **Design & Marketing** | Carousels, product visuals, brand assets, social content | CarouselService, MediaService |
| **Academic Work** | Research papers, reports, presentations, semester management | ResearchService, ReportService, PresentationService |
| **Development** | Code generation, APIs, project planning | — |
| **Research** | Market research, competitive analysis, technical research | ResearchService |
| **Media** | Image generation, video (future), audio (future) | MediaService |
| **Operations** | Usage tracking, cost monitoring, storage cleanup | Operations services |

---

## 8. Visual Language

### Layout Principles
- **Sidebar**: 280px fixed width, left border, flex column
- **Main area**: Flex-grow, chat-width `min(760px, 100%)`
- **Panels**: Full height, hidden by default, activated by class `active`
- **Cards**: Border + background + radius — no shadows
- **Grids**: CSS grid for stat cards (3 columns), flex for toolbars

### Component Patterns
- **Buttons**: Flat, no shadows, border-radius 6-8px, hover background change
- **Inputs**: Border with `:focus-within` primary border color
- **Tables**: Full width, collapsed borders, hover row highlight
- **Badges**: Small inline blocks, colored backgrounds, 6px radius
- **Tabs**: Horizontal bar, active tab gets primary bottom border
- **Charts**: Mini bar charts with `op-mini-chart` class, 8px bars, no libraries

### Icon Usage
- SVG inline icons (24x24 viewBox, fill=none, stroke=currentColor, stroke-width=2)
- Emoji for UI labels and status indicators (✅ ❌ ⚠️ 📊 📓 🤖 🧪 ⚙️)
- No icon libraries — inline SVG or emoji only

### Responsive Behavior
- Sidebar collapses to overlay on mobile (≤768px)
- `.sidebar.open` with `transform: translateX(0)`
- Close button visible on mobile only

### Z-Index Stacking
```
sidebar:          100
modals:           200
notifications:    300
```

---

## 9. Logomark

- **Primary mark**: "ت" — the first letter of تول
- **Rendering**: 32×32px, border-radius 8px
- **Background**: `linear-gradient(135deg, var(--primary), var(--accent))`
- **Text**: White, 700 weight, centered
- **Placement**: Sidebar header, left of "تول" wordmark
