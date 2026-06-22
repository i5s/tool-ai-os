# ZUNO AI OS — Design System Rules

> Auto-generated from Phase 0 (M3 token alignment) + Phase 1 (Svelte 5 shell).
> Source of truth:  `web/src/styles/` + `web/index-legacy.html` (Stitch M3).

---

## 1. Project Overview

| Property     | Value                                             |
| ------------ | ------------------------------------------------- |
| Framework    | Svelte 5 (runes mode) + Vite 6                    |
| Direction    | RTL (Arabic) — `dir="rtl" lang="ar"`              |
| Theme        | Dark (Cognitive OS) by default, Light (Zuno Light) |
| Design Source| Stitch M3 — Material Design 3 Cognitive OS palette|
| Bundle       | ~43KB JS + ~15KB CSS (gzip: ~16KB + ~3KB)         |

---

## 2. Color System

### 2.1 M3 Tokens (Primary)

All colors MUST be referenced via `--md-sys-color-*` CSS custom properties.
Never hardcode hex values.

#### Dark Theme (`:root`)

```
Surface:
  --md-sys-color-background: #111125
  --md-sys-color-surface-dim: #111125
  --md-sys-color-surface-bright: #37374d
  --md-sys-color-surface-container-lowest: #0c0c1f
  --md-sys-color-surface-container-low: #1a1a2e
  --md-sys-color-surface-container: #1e1e32
  --md-sys-color-surface-container-high: #28283d
  --md-sys-color-surface-container-highest: #333348
  --md-sys-color-surface-variant: #333348
  --md-sys-color-on-surface: #e2e0fc
  --md-sys-color-on-surface-variant: #bdc8d1

Primary (Sky Blue):
  --md-sys-color-primary: #8ed5ff
  --md-sys-color-on-primary: #00354a
  --md-sys-color-primary-container: #38bdf8
  --md-sys-color-on-primary-container: #004965
  --md-sys-color-primary-fixed: #c4e7ff
  --md-sys-color-primary-fixed-dim: #7bd0ff
  --md-sys-color-on-primary-fixed: #001e2c
  --md-sys-color-on-primary-fixed-variant: #004c69

Secondary (Purple):
  --md-sys-color-secondary: #cebdff
  --md-sys-color-on-secondary: #381385
  --md-sys-color-secondary-container: #4f319c
  --md-sys-color-on-secondary-container: #bea8ff

Tertiary (Blue-Grey):
  --md-sys-color-tertiary: #c2cde5
  --md-sys-color-on-tertiary: #263143
  --md-sys-color-tertiary-container: #a7b2c9
  --md-sys-color-on-tertiary-container: #394458

Error:
  --md-sys-color-error: #ffb4ab
  --md-sys-color-on-error: #690005
  --md-sys-color-error-container: #93000a
  --md-sys-color-on-error-container: #ffdad6

Outline:
  --md-sys-color-outline: #87929a
  --md-sys-color-outline-variant: #3e484f
```

#### Light Theme (`:root.light`)

```
--md-sys-color-background: #f6faff
--md-sys-color-surface-container-lowest: #ffffff
--md-sys-color-surface-container-low: #f0f4fa
--md-sys-color-surface-container: #eaeef4
--md-sys-color-surface-container-high: #e4e8ee
--md-sys-color-on-surface: #171c20
--md-sys-color-on-surface-variant: #3e4850

--md-sys-color-primary: #006591
--md-sys-color-primary-container: #0ea5e9
--md-sys-color-secondary: #505f76
--md-sys-color-secondary-container: #d0e1fb
--md-sys-color-tertiary: #8a5100
--md-sys-color-tertiary-container: #de8712

--md-sys-color-error: #ba1a1a
--md-sys-color-error-container: #ffdad6
--md-sys-color-outline: #6e7881
--md-sys-color-outline-variant: #bec8d2
```

### 2.2 Legacy Semantic Aliases

These exist for backward compatibility with old code. New code should use M3 tokens directly.

| Alias              | Maps To                                         | Usage                 |
| ------------------ | ----------------------------------------------- | --------------------- |
| `--bg`             | `--md-sys-color-background`                     | Page background       |
| `--bg2`            | `--md-sys-color-surface-container-low`          | Secondary background  |
| `--bg3`            | `--md-sys-color-surface-container-high`         | Tertiary background   |
| `--sidebar`        | `--md-sys-color-surface-container-lowest`       | Sidebar background    |
| `--sidebar-hover`  | `--md-sys-color-surface-container-low`          | Sidebar hover state   |
| `--surface`        | `--md-sys-color-surface-container`              | Card/panel background |
| `--surface-hover`  | `--md-sys-color-surface-container-high`         | Card/panel hover      |
| `--primary`        | `--md-sys-color-primary-container`              | Primary accent        |
| `--primary-dim`    | `--md-sys-color-primary-fixed-dim`              | Dimmed primary        |
| `--accent`         | `--md-sys-color-secondary`                      | Secondary accent      |
| `--accent2`        | `--md-sys-color-tertiary`                       | Tertiary accent       |
| `--text`           | `--md-sys-color-on-surface`                     | Primary text          |
| `--text2`          | `--md-sys-color-on-surface-variant`             | Secondary text        |
| `--text3`          | `--md-sys-color-outline-variant`                | Muted text            |
| `--border`         | `--md-sys-color-outline-variant`                | Subtle borders        |
| `--border2`        | `--md-sys-color-outline`                        | Strong borders        |

### 2.3 Semantic Color Usage

```css
/* ✅ DO: Use M3 tokens */
.button {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

/* ❌ DON'T: Hardcode hex */
.button {
  background: #38bdf8;
  color: #004965;
}

/* ✅ DO: Use for theme-aware borders */
.card {
  border: 1px solid var(--border);
}

/* ✅ DO: Use for brand runtime (will be overridden) */
:root {
  --brand-primary: var(--md-sys-color-primary);
}
```

---

## 3. Typography

### 3.1 Font Stack

```
--font-display:    'KO Ghorab', 'DIN Next Arabic', 'IBM Plex Sans Arabic', 'Tajawal', sans-serif
--font-heading:    'KO Ghorab', 'DIN Next Arabic', 'IBM Plex Sans Arabic', 'Tajawal', sans-serif
--font-body:       'DIN Next Arabic', 'IBM Plex Sans Arabic', 'Tajawal', sans-serif
--font-label:      'Geist', 'DIN Next Arabic', system-ui, sans-serif
--font-decorative: 'Dast Nevis', 'KO Ghorab', serif
```

Sources:
- **KO Ghorab** — local `@font-face` (display/headings)
- **DIN Next Arabic** — Google Fonts CDN (body)
- **Geist** — jsdelivr CDN (labels)
- **Dast Nevis** — local `@font-face` (decorative)

**DO NOT** use IBM Plex Arabic despite its presence in fallback stacks.

### 3.2 Typographic Scale

| Class         | Font               | Size    | Weight | Line   | Letter      |
| ------------- | ------------------ | ------- | ------ | ------ | ----------- |
| `.display-xl` | `--font-display`   | 64px    | 700    | 1.1    | -0.03em     |
| `.display-lg` | `--font-display`   | 48px    | 700    | 1.15   | -0.02em     |
| `.display-md` | `--font-display`   | 36px    | 600    | 1.2    | -0.01em     |
| `.headline-xl`| `--font-heading`   | 48px    | 700    | 1.2    | -0.02em     |
| `.headline-lg`| `--font-heading`   | 32px    | 600    | 1.3    | —           |
| `.headline-md`| `--font-heading`   | 24px    | 600    | 1.4    | —           |
| `.headline-sm`| `--font-heading`   | 20px    | 500    | 1.5    | —           |
| `.body-xl`    | `--font-body`      | 18px    | 400    | 1.6    | —           |
| `.body-lg`    | `--font-body`      | 16px    | 400    | 1.6    | —           |
| `.body-md`    | `--font-body`      | 14px    | 400    | 1.5    | —           |
| `.body-sm`    | `--font-body`      | 12px    | 400    | 1.5    | —           |
| `.label-lg`   | `--font-label`     | 14px    | 500    | 1.2    | 0.02em      |
| `.label-md`   | `--font-label`     | 12px    | 500    | 1.2    | —           |
| `.label-sm`   | `--font-label`     | 11px    | 500    | 1.2    | 0.05em      |

### 3.3 Typography Rules

```svelte
<!-- ✅ DO: Use utility classes -->
<h1 class="display-md">عنوان رئيسي</h1>
<p class="body-lg">محتوى النص</p>

<!-- ❌ DON'T: Inline font-family -->
<h1 style="font-family: 'KO Ghorab'; font-size: 36px">عنوان رئيسي</h1>

<!-- ✅ DO: Svelte components inherit body font -->
<style>
  .panel-header { font-family: var(--font-heading); }
</style>
```

---

## 4. Spacing & Layout

### 4.1 Layout Tokens

```css
--stitch-sidebar-w: 280px;       /* Sidebar width */
--stitch-context-panel-w: 340px; /* Future context panel */
--stitch-gutter: 24px;           /* Content gutter */

/* Border radius */
--stitch-radius-sm: 4px;
--stitch-radius: 8px;
--stitch-radius-md: 12px;
--stitch-radius-lg: 16px;
--stitch-radius-xl: 24px;
--stitch-radius-full: 9999px;

/* Legacy radius */
--radius: 12px;
--radius-lg: 20px;
```

### 4.2 Shell Architecture

```
┌────────────────────────────────────────────────────┐
│ .sidebar (280px)  │  .main-area (flex: 1)          │
│ ┌──────────────┐  │  ┌──────────────────────────┐  │
│ │ .sidebar-    │  │  │ .top-bar (56px)          │  │
│ │   header     │  │  │ .menu-toggle .title .actions│  │
│ │              │  │  ├──────────────────────────┤  │
│ │ .new-chat-btn│  │  │                           │  │
│ │ .sidebar-    │  │  │ .content-area (flex: 1)   │  │
│ │   search     │  │  │                           │  │
│ │              │  │  │   View panel goes here    │  │
│ │ .sidebar-nav │  │  │                           │  │
│ │ - item 1     │  │  │                           │  │
│ │ - item 2     │  │  │                           │  │
│ │ - ...        │  │  │                           │  │
│ │              │  │  │                           │  │
│ │ .conversations│ │  │                           │  │
│ │              │  │  │                           │  │
│ │ .sidebar-    │  │  │                           │  │
│ │   footer     │  │  │                           │  │
│ └──────────────┘  │  └──────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

### 4.3 Responsive Breakpoints

```css
/* Mobile: ≤768px */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    transform: translateX(100%); /* Hidden (RTL: slide right) */
  }
  .sidebar.collapsed {
    transform: translateX(100%);
  }
  .sidebar-backdrop {
    display: block; /* Overlay behind sidebar */
    background: rgba(0, 0, 0, 0.4);
  }
  .menu-toggle {
    display: flex; /* Hamburger visible */
  }
}
```

---

## 5. Component Patterns

### 5.1 Material Symbols Icons

```svelte
<!-- Imported via CDN in index.html -->
<!-- Default: outlined, 20px, weight 400 -->
<span class="material-symbols-outlined">chat</span>

<!-- Filled variant -->
<span class="material-symbols-outlined fill">auto_awesome</span>

<!-- Sizing modifiers -->
<span class="material-symbols-outlined icon-sm">close</span>   <!-- 16px -->
<span class="material-symbols-outlined">search</span>         <!-- 20px (default) -->
<span class="material-symbols-outlined icon-lg">settings</span><!-- 24px -->
<span class="material-symbols-outlined icon-xl">dashboard</span><!-- 32px -->
```

**Icon selection rules:**
- Navigation items: `.icon-sm` (16px) + their semantic icon name
- Top bar: default 20px
- Empty states: custom size (48px is common)
- **DO NOT use emoji** as structural icons (❌ `💬`, ❌ `📓`)

### 5.2 Glass Components

```svelte
<!-- Glass Panel (full-area blur) -->
<div class="glass-panel">
  <!-- Content with backdrop blur -->
</div>

<!-- Glass Card (surface card with hover glow) -->
<div class="glass-card">
  <h3>Card Title</h3>
  <p>Card content</p>
</div>

<!-- Card Shimmer (no default bg, hover shimmer) -->
<div class="card-shimmer">
  <!-- Content -->
</div>
```

### 5.3 Status Indicators

```svelte
<!-- Status dots -->
<span class="status-dot draft"></span>     <!-- Grey (outline) -->
<span class="status-dot planned"></span>   <!-- Purple (secondary) -->
<span class="status-dot running"></span>   <!-- Blue (primary) -->
<span class="status-dot completed"></span> <!-- Green -->
<span class="status-dot error"></span>     <!-- Red (error) -->

<!-- Animated ping (for live/active indicators) -->
<span class="status-dot running status-ping"></span>

<!-- Pulse animation -->
<div class="pulse">Updating...</div>
```

### 5.4 Icon Containers

```svelte
<div class="icon-container">        <!-- 48×48, rounded 8px -->
  <span class="material-symbols-outlined">chat</span>
</div>
<div class="icon-container-sm">     <!-- 32×32, rounded 4px -->
  <span class="material-symbols-outlined icon-sm">close</span>
</div>
<div class="icon-container-lg">     <!-- 40×40, rounded 8px -->
  <span class="material-symbols-outlined icon-lg">settings</span>
</div>
```

### 5.5 Sidebar Navigation

```svelte
<!-- DO: Use sidebar-nav-item pattern -->
<script>
  import { activeView, views } from '../lib/view.js'
</script>

<nav class="sidebar-nav">
  {#each views as item}
    <button
      class="sidebar-nav-item"
      class:active={$activeView === item.id}
      onclick={() => activeView.set(item.id)}
      aria-label={item.label}
    >
      <span class="material-symbols-outlined icon-sm">{item.icon}</span>
      <span>{item.label}</span>
    </button>
  {/each}
</nav>
```

### 5.6 Theme Toggle

```svelte
<script>
  import { theme } from '../lib/theme.js'
</script>

<!-- Toggle button -->
<button onclick={() => theme.toggle()} aria-label="تبديل السمة">
  <span class="material-symbols-outlined icon-sm">
    {$theme === 'dark' ? 'light_mode' : 'dark_mode'}
  </span>
</button>
```

---

## 6. Animation

### 6.1 Transitions

```css
/* ✅ DO: Use CSS transitions, prefer transform/opacity */
.element {
  transition: background 0.3s ease, color 0.3s ease;
}

/* ✅ DO: Smooth sidebar slide */
.sidebar {
  transition: transform 0.3s ease, background 0.3s;
}

/* ❌ DON'T: Animate width/height (triggers layout) */
.element {
  transition: width 0.3s ease;  /* ❌ BAD */
}
```

### 6.2 Keyframe Animations

```css
/* Status ping */
@keyframes ping {
  75%, 100% { transform: scale(1.75); opacity: 0; }
}

/* Pulse */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

### 6.3 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 7. RTL Rules

### 7.1 Direction

```css
/* ✅ DO: Use logical properties for margins/paddings */
.sidebar {
  margin-inline-end: 0;    /* Was: margin-right: 0 */
  padding-inline-start: 16px; /* Was: padding-left: 16px */
}

/* ✅ DO: RTL border placement */
.sidebar {
  border-left: 1px solid var(--border); /* Physical side in RTL context */
}
/* In RTL, border-left is the content-facing edge */
```

### 7.2 Transform

```css
/* ✅ DO: Negative transform for RTL hide */
.sidebar.collapsed {
  transform: translateX(100%); /* Slides off to the right in RTL */
}
```

### 7.3 Text Alignment

```svelte
<!-- ✅ DO: Use text-align in RTL context -->
<button style="text-align: right">
  <span class="material-symbols-outlined icon-sm">chat</span>
  <span>الدردشة</span>
</button>
```

---

## 8. Naming Conventions

### 8.1 CSS Classes

| Pattern | Example | Usage |
| ------- | ------- | ----- |
| `kebab-case` | `.sidebar-nav-item` | All CSS classes |
| BEM-like | `.sidebar-nav-item.active` | Modifier states |
| Utility prefix | `.body-lg`, `.icon-sm` | Typography/icon utilities |
| Stitch prefix | `--stitch-*` | Layout tokens from Stitch |

### 8.2 JavaScript/Svelte

| Pattern | Example | Usage |
| ------- | ------- | ----- |
| `camelCase` | `toggleSidebar`, `activeView` | Functions, variables |
| `PascalCase` | `Shell.svelte`, `App.svelte` | Svelte components |
| `$state()` | `let x = $state(0)` | Svelte 5 reactive state |
| `$store` | `$theme`, `$activeView` | Auto-subscribed stores |

### 8.3 CSS Custom Properties

| Pattern | Example | Usage |
| ------- | ------- | ----- |
| `--md-sys-color-*` | `--md-sys-color-primary` | M3 design tokens |
| `--stitch-*` | `--stitch-sidebar-w` | Stitch layout tokens |
| `--font-*` | `--font-display` | Font family tokens |

---

## 9. Lint Rules

### 9.1 Do (✅)
- Use `var(--*)` for ALL colors, never hex/rgb values
- Use `--md-sys-color-*` tokens for new code
- Use Material Symbols for ALL icons (no emoji)
- Use `aria-label` on icon-only buttons
- Use `prefers-reduced-motion` media query
- Use `class:` directive for Svelte conditional classes
- Use `$state()` for Svelte 5 reactive variables
- Use `onclick` (lowercase) for Svelte event handlers
- Use `transform`/`opacity` for animations (not `width`/`height`)
- Keep all token definitions in `src/styles/tokens.css`

### 9.2 Don't (❌)
- No hardcoded hex colors anywhere
- No emoji as structural icons (e.g. `💬`, `📓`, `🤖`)
- No inline `style="font-family: ..."`
- No inline `style="color: ..."` that hardcodes hex
- No `width`/`height` transitions (triggers layout)
- No IBM Plex Arabic font usage
- No `let` for reactive state in Svelte 5 (use `$state()`)
- No `---` fence in Svelte 5 .svelte files
- No `<script module>` or `<script context="module">` (use `<script>` only)

---

## 10. File Structure

```
web/
├── index.html                  # Vite entry (DO NOT EDIT unless changing <head> resources)
├── index-legacy.html           # Original monolithic SPA (backup, DO NOT EDIT)
├── package.json                # Dependencies (svelte, vite, @sveltejs/vite-plugin-svelte)
├── vite.config.js              # Vite config + /api proxy → :8000
├── svelte.config.js            # Svelte compiler options (runes: true)
├── dist/                       # Build output (gitignored)
├── node_modules/               # Dependencies (gitignored)
├── public/
│   ├── manifest.json           # PWA manifest
│   └── sw.js                   # Service worker
└── src/
    ├── main.js                 # App bootstrap (mount App → #app)
    ├── styles.js               # CSS import cascade (tokens → typography → global)
    ├── App.svelte              # Root component (theme init, Shell wrapper)
    ├── styles/
    │   ├── tokens.css          # M3 color tokens (dark/light) + legacy aliases + layout
    │   ├── typography.css      # @font-face + typographic scale utility classes
    │   └── global.css          # Reset, scrollbar, glass, icons, status, animations, reduced motion
    ├── lib/
    │   ├── theme.js            # Theme store (dark/light toggle, localStorage)
    │   ├── view.js             # View router (activeView + views config)
    │   └── store.js            # API helpers + shared stores (conversations, workspaces)
    ├── layouts/
    │   └── Shell.svelte        # Main shell: sidebar + topbar + content area
    └── components/
        └── (future components)
```

---

## 11. View Configuration

```javascript
// src/lib/view.js
export const views = [
  { id: 'chat',        label: 'الدردشة',          icon: 'chat' },
  { id: 'notebooks',   label: 'دفاتر الملاحظات',  icon: 'book_4' },
  { id: 'models',      label: 'النماذج',          icon: 'smart_toy' },
  { id: 'lab',         label: 'المختبر',          icon: 'biotech' },
  { id: 'brand',       label: 'العلامة التجارية', icon: 'palette' },
  { id: 'operations',  label: 'العمليات',         icon: 'monitoring' },
  { id: 'settings',    label: 'الإعدادات',        icon: 'settings' },
]
```

To add a new view:
1. Add entry to `views` array with unique `id`, Arabic `label`, and Material Symbol `icon`
2. Add a panel component in `src/panels/`
3. Add conditional rendering in Shell's content area

---

## 12. API Proxy

```javascript
// vite.config.js — dev server proxies /api → backend
server: {
  proxy: {
    '/api': 'http://localhost:8000',
  },
}
```

For API calls, use the helper in `src/lib/store.js`:
```javascript
import { api } from '../lib/store.js'

const data = await api.get('/workspaces')
const result = await api.post('/chat', { message: '...' })
```

---

*Last updated: Phase 1 commit (2026-06-22). Source: `web/src/styles/`, `web/src/lib/`.*
