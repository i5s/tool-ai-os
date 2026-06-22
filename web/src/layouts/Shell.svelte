<script>
import { theme } from '../lib/theme.js'
import { activeView, views } from '../lib/view.js'
import AgentsPanel from '../components/AgentsPanel.svelte'
import SharedMemoryPanel from '../components/SharedMemoryPanel.svelte'
import TasksPanel from '../components/TasksPanel.svelte'

let sidebarOpen = $state(true)

function toggleSidebar() {
  sidebarOpen = !sidebarOpen
}

function handleNavClick(viewId) {
  activeView.set(viewId)
}
</script>

<div class="shell">
  <aside class="sidebar" class:collapsed={!sidebarOpen}>
    <div class="sidebar-header">
      <div class="logo">
        <span class="material-symbols-outlined fill" style="font-size:18px">auto_awesome</span>
      </div>
      <h1>تول</h1>
      <button class="close-sidebar" onclick={toggleSidebar} aria-label="إغلاق القائمة">
        <span class="material-symbols-outlined icon-sm">close</span>
      </button>
    </div>

    <button class="new-chat-btn" aria-label="محادثة جديدة">
      <span class="material-symbols-outlined icon-sm">add</span>
      <span>محادثة جديدة</span>
    </button>

    <div class="sidebar-search">
      <span class="material-symbols-outlined icon-sm">search</span>
      <input type="text" placeholder="البحث في المحادثات..." aria-label="البحث" />
    </div>

    <nav class="sidebar-nav">
      {#each views as item}
        <button
          class="sidebar-nav-item"
          class:active={$activeView === item.id}
          onclick={() => handleNavClick(item.id)}
          aria-label={item.label}
        >
          <span class="material-symbols-outlined icon-sm">{item.icon}</span>
          <span>{item.label}</span>
        </button>
      {/each}
    </nav>

    <div class="conversations">
      <div class="conv-group-label">مثبّتة</div>
      <div class="conv-group-label">الأحدث</div>
    </div>

    <div class="sidebar-footer">
      <button class="sidebar-nav-item" onclick={() => theme.toggle()} aria-label="تبديل السمة">
        <span class="material-symbols-outlined icon-sm">
          {$theme === 'dark' ? 'light_mode' : 'dark_mode'}
        </span>
        <span>{$theme === 'dark' ? 'الوضع النهاري' : 'الوضع الليلي'}</span>
      </button>
    </div>
  </aside>

  {#if sidebarOpen}
    <button class="sidebar-backdrop" onclick={toggleSidebar} aria-label="إغلاق القائمة"></button>
  {/if}

  <main class="main-area">
    <header class="top-bar">
      <button class="menu-toggle" onclick={toggleSidebar} aria-label="فتح القائمة">
        <span class="material-symbols-outlined">menu</span>
      </button>
      <div class="top-bar-title">
        {views.find(v => v.id === $activeView)?.label || 'تول'}
      </div>
      <div class="top-bar-actions">
        <button class="top-bar-btn" onclick={() => theme.toggle()} aria-label="تبديل السمة">
          <span class="material-symbols-outlined icon-sm">
            {$theme === 'dark' ? 'light_mode' : 'dark_mode'}
          </span>
        </button>
      </div>
    </header>

    <div class="content-area">
      {#if $activeView === 'chat'}
        <div class="placeholder-panel">
          <span class="material-symbols-outlined" style="font-size:48px;color:var(--text3)">chat</span>
          <p class="body-lg" style="color:var(--text2);margin-top:16px">مرحبًا بك في تول</p>
          <p class="body-md" style="color:var(--text3)">اختر محادثة أو ابدأ محادثة جديدة</p>
        </div>
      {:else if $activeView === 'agents'}
        <AgentsPanel />
      {:else if $activeView === 'shared-memory'}
        <SharedMemoryPanel />
      {:else if $activeView === 'tasks'}
        <TasksPanel />
      {:else}
        <div class="placeholder-panel">
          <span class="material-symbols-outlined" style="font-size:48px;color:var(--text3)">{views.find(v => v.id === $activeView)?.icon || 'dashboard'}</span>
          <p class="body-lg" style="color:var(--text2);margin-top:16px">{views.find(v => v.id === $activeView)?.label || ''}</p>
          <p class="body-md" style="color:var(--text3)">قيد التطوير...</p>
        </div>
      {/if}
    </div>
  </main>
</div>

<style>
  .shell {
    display: flex;
    height: 100vh;
    overflow: hidden;
  }

  .sidebar {
    width: var(--stitch-sidebar-w);
    min-width: var(--stitch-sidebar-w);
    background: var(--sidebar);
    border-left: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    transition: transform 0.3s ease, background 0.3s;
    z-index: 100;
    position: relative;
  }

  .sidebar-header {
    padding: 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .logo {
    width: 32px; height: 32px;
    border-radius: 8px;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
  }

  .sidebar-header h1 {
    font-size: 1.15rem;
    font-weight: 600;
    flex: 1;
  }

  .close-sidebar {
    background: none;
    border: none;
    color: var(--text2);
    cursor: pointer;
    font-size: 1.2rem;
    display: none;
    padding: 4px;
    line-height: 1;
  }

  .new-chat-btn {
    margin: 12px 16px;
    padding: 10px;
    border-radius: var(--radius);
    background: var(--bg);
    color: var(--text);
    border: 1px solid var(--border2);
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
    justify-content: center;
    transition: 0.2s;
    font-family: inherit;
  }
  .new-chat-btn:hover {
    background: var(--surface-hover);
  }

  .sidebar-search {
    margin: 0 16px 8px;
    padding: 8px 12px;
    border-radius: 8px;
    background: var(--bg);
    border: 1px solid transparent;
    color: var(--text2);
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .sidebar-search:focus-within {
    border-color: var(--primary);
  }
  .sidebar-search input {
    background: none;
    border: none;
    color: var(--text);
    font-size: 0.85rem;
    flex: 1;
    outline: none;
    font-family: inherit;
  }
  .sidebar-search input::placeholder {
    color: var(--text3);
  }

  .sidebar-nav {
    padding: 4px 12px;
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .sidebar-nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.88rem;
    font-weight: 500;
    color: var(--text2);
    transition: 0.15s;
    border: none;
    background: none;
    width: 100%;
    text-align: right;
    font-family: inherit;
  }
  .sidebar-nav-item:hover {
    background: var(--sidebar-hover);
    color: var(--text);
  }
  .sidebar-nav-item.active {
    background: var(--sidebar-hover);
    color: var(--primary);
  }

  .conversations {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }

  .conv-group-label {
    font-size: 0.75rem;
    color: var(--text3);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 12px 16px 4px;
    font-weight: 600;
  }

  .sidebar-footer {
    border-top: 1px solid var(--border);
    padding: 4px 12px;
  }

  .sidebar-backdrop {
    display: none;
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
  }

  .main-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .top-bar {
    height: 56px;
    min-height: 56px;
    display: flex;
    align-items: center;
    padding: 0 20px;
    border-bottom: 1px solid var(--border);
    background: var(--bg);
    gap: 12px;
  }

  .menu-toggle {
    display: none;
    background: none;
    border: none;
    color: var(--text2);
    cursor: pointer;
    font-size: 1.25rem;
    padding: 4px;
    line-height: 1;
  }

  .top-bar-title {
    flex: 1;
    font-family: var(--font-heading);
    font-size: 1.1rem;
    font-weight: 600;
  }

  .top-bar-actions {
    display: flex;
    gap: 8px;
  }

  .top-bar-btn {
    background: none;
    border: none;
    color: var(--text2);
    cursor: pointer;
    padding: 6px;
    border-radius: 8px;
    line-height: 1;
    transition: 0.15s;
  }
  .top-bar-btn:hover {
    background: var(--surface-hover);
    color: var(--text);
  }

  .content-area {
    flex: 1;
    overflow-y: auto;
  }

  .placeholder-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px 24px;
  }

  @media (max-width: 768px) {
    .sidebar {
      position: fixed;
      top: 0;
      bottom: 0;
      right: 0;
      transform: translateX(0);
    }
    .sidebar.collapsed {
      transform: translateX(100%);
    }
    .sidebar-backdrop {
      display: block;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.4);
      z-index: 99;
    }
    .menu-toggle {
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .close-sidebar {
      display: block;
    }
  }
</style>
