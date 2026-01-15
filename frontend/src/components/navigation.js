/**
 * Navigation Component extracted from existing pages
 */

class NavigationComponent extends HTMLElement {
  constructor() {
    super();
    this.currentPage = window.location.pathname;
  }

  connectedCallback() {
    this.render();
  }

  render() {
    this.innerHTML = `
      <header class="sticky top-0 z-50 border-b border-white/10 bg-background-dark/80 backdrop-blur-md px-6 py-3">
        <div class="max-w-[1440px] mx-auto flex items-center justify-between">
          <div class="flex items-center gap-8">
            <div class="flex items-center gap-3">
              <div class="size-10 bg-gradient-to-br from-primary to-accent-pink rounded-lg flex items-center justify-center shadow-[0_0_20px_rgba(255,0,122,0.4)]">
                <span class="material-symbols-outlined text-background-dark font-bold">account_tree</span>
              </div>
              <div>
                <h1 class="text-lg font-bold tracking-tight text-white">RAG.OS</h1>
                <p class="text-[10px] uppercase tracking-[0.2em] text-accent-pink/70 font-semibold">Enterprise Core</p>
              </div>
            </div>
            <nav class="hidden md:flex items-center gap-6">
              <a href="/" class="nav-link ${this.currentPage === '/' ? 'active' : ''}" data-page="dashboard">
                <span class="material-symbols-outlined">dashboard</span>
                <span>Dashboard</span>
              </a>
              <a href="/chat.html" class="nav-link ${this.currentPage.includes('chat') ? 'active' : ''}" data-page="chat">
                <span class="material-symbols-outlined">chat</span>
                <span>Query Center</span>
              </a>
              <a href="/documents.html" class="nav-link ${this.currentPage.includes('documents') ? 'active' : ''}" data-page="documents">
                <span class="material-symbols-outlined">folder_open</span>
                <span>Document Hub</span>
              </a>
              <a href="/analytics.html" class="nav-link ${this.currentPage.includes('analytics') ? 'active' : ''}" data-page="analytics">
                <span class="material-symbols-outlined">analytics</span>
                <span>Analytics</span>
              </a>
              <a href="/quality.html" class="nav-link ${this.currentPage.includes('quality') ? 'active' : ''}" data-page="quality">
                <span class="material-symbols-outlined">shield_with_heart</span>
                <span>Quality</span>
              </a>
              <a href="/settings.html" class="nav-link ${this.currentPage.includes('settings') ? 'active' : ''}" data-page="settings">
                <span class="material-symbols-outlined">settings</span>
                <span>Settings</span>
              </a>
            </nav>
          </div>
          <div class="flex items-center gap-4">
            <div class="flex bg-white/5 rounded-xl p-1 border border-white/10">
              <button class="px-3 py-1 text-xs font-bold rounded-lg bg-accent-pink text-white shadow-[0_0_10px_rgba(255,0,122,0.3)]" id="status-live">LIVE</button>
              <button class="px-3 py-1 text-xs font-bold text-white/40" id="status-offline">OFFLINE</button>
            </div>
            <button class="size-10 rounded-full flex items-center justify-center hover:bg-white/5 transition-colors" id="notifications-btn">
              <span class="material-symbols-outlined">notifications</span>
            </button>
            <div class="size-10 rounded-full border border-accent-pink/30 p-0.5 cursor-pointer" id="user-profile">
              <div class="w-full h-full rounded-full bg-cover bg-center" style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuDk2veP0tcVunMBLI-9t7xIAh3DBIXE-fgQhNh7gia3-H3OD4Ka3zaHZtwUAvWjhbEgLmlx00uEBePLAOnNxgSvvPbvpGzAWlqI9jxz3TZSiV2x4WVyHRMXpl5WL_e1oo0OgpQCnsGi0p5eb6Bd3IbP-z-BP3eAhXYZ4WPqQ7Wjw4Rt4Vr7ju1PPYQLipqd82M-UoqCSZmge4SSmev9dv_8bOmL1jNR5KAamzhLnckQfvRoM4CmB338Cs-RePlMzALkQazWbJybo7k')"></div>
            </div>
          </div>
        </div>
      </header>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    // Status toggle
    const liveBtn = this.querySelector('#status-live');
    const offlineBtn = this.querySelector('#status-offline');
    
    liveBtn.addEventListener('click', () => {
      liveBtn.classList.add('bg-accent-pink', 'text-white', 'shadow-[0_0_10px_rgba(255,0,122,0.3)]');
      liveBtn.classList.remove('text-white/40');
      offlineBtn.classList.remove('bg-accent-pink', 'text-white', 'shadow-[0_0_10px_rgba(255,0,122,0.3)]');
      offlineBtn.classList.add('text-white/40');
    });

    // Navigation links
    this.querySelectorAll('.nav-link').forEach(link => {
      link.className = 'flex items-center gap-3 px-4 py-3 rounded-xl text-white/60 hover:text-white hover:bg-white/5 transition-all';
      
      if (link.classList.contains('active')) {
        link.className = 'flex items-center gap-3 px-4 py-3 rounded-xl bg-accent-pink/10 text-accent-pink border border-accent-pink/20 shadow-[0_0_15px_rgba(255,0,122,0.1)] transition-all';
      }

      link.addEventListener('click', (e) => {
        e.preventDefault();
        const href = link.getAttribute('href');
        window.location.href = href;
      });
    });

    // Notifications button
    this.querySelector('#notifications-btn')?.addEventListener('click', () => {
      this.showNotifications();
    });

    // User profile
    this.querySelector('#user-profile')?.addEventListener('click', () => {
      this.showUserMenu();
    });
  }

  showNotifications() {
    // TODO: Implement notifications panel
    console.log('Show notifications');
  }

  showUserMenu() {
    // TODO: Implement user menu
    console.log('Show user menu');
  }

  setActivePage(page) {
    this.querySelectorAll('.nav-link').forEach(link => {
      link.classList.remove('bg-accent-pink/10', 'text-accent-pink', 'border', 'border-accent-pink/20', 'shadow-[0_0_15px_rgba(255,0,122,0.1)]');
      link.classList.add('text-white/60');
    });

    const activeLink = this.querySelector(`[data-page="${page}"]`);
    if (activeLink) {
      activeLink.classList.remove('text-white/60');
      activeLink.classList.add('bg-accent-pink/10', 'text-accent-pink', 'border', 'border-accent-pink/20', 'shadow-[0_0_15px_rgba(255,0,122,0.1)]');
    }
  }
}

customElements.define('nav-component', NavigationComponent);