/**
 * Settings Component for Enterprise RAG
 * Displays and manages system configuration settings
 */
import { API } from '../api/client.js';

class SettingsComponent extends HTMLElement {
  constructor() {
    super();
    this.settings = null;
    this.originalSettings = null;
  }

  async connectedCallback() {
    await this.loadSettings();
    this.render();
    this.attachEventListeners();
  }

  async loadSettings() {
    try {
      this.settings = await API.getSettings();
      this.originalSettings = JSON.parse(JSON.stringify(this.settings));
    } catch (error) {
      console.error('Failed to load settings:', error);
      this.settings = this.getDefaultSettings();
    }
  }

  getDefaultSettings() {
    return {
      api: { engine_type: 'hybrid', timeout: 30, max_retries: 3 },
      cache: { enabled: true, ttl_seconds: 3600, max_entries: 1000 },
      rate_limiting: { default_tier: 'default', trial_requests: 20 },
      ui_preferences: { theme: 'dark', refresh_interval: 5, compact_mode: false }
    };
  }

  render() {
    this.innerHTML = `
      <div class="flex-1 overflow-y-auto p-8 cyber-bg custom-scrollbar" style="min-height: 0;">
        <div class="max-w-4xl mx-auto pb-4">
          <div class="mb-8">
            <h1 class="text-3xl font-bold gradient-text-pink-cyan">Settings</h1>
            <p class="text-white/60 mt-1">Configure your RAG environment</p>
          </div>

          <div class="space-y-6">
            ${this.renderApiSettings()}
            ${this.renderCacheSettings()}
            ${this.renderRateLimitingSettings()}
            ${this.renderUISettings()}
            ${this.renderActions()}
          </div>
        </div>
      </div>
    `;
  }

  renderApiSettings() {
    const { api } = this.settings;
    return `
      <div class="glass p-6 rounded-2xl border border-white/10">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-secondary">api</span>
          <h3 class="text-lg font-bold text-white">API Configuration</h3>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-xs text-white/40 uppercase tracking-wider mb-2">Engine Type</label>
            <select id="api-engine-type" class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white text-sm focus:border-accent-pink focus:outline-none transition-colors">
              <option value="hybrid" ${api.engine_type === 'hybrid' ? 'selected' : ''}>Hybrid (Vector + Graph)</option>
              <option value="vector" ${api.engine_type === 'vector' ? 'selected' : ''}>Vector Only</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-white/40 uppercase tracking-wider mb-2">Timeout (seconds)</label>
            <input type="number" id="api-timeout" value="${api.timeout}" min="5" max="120"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white text-sm focus:border-accent-pink focus:outline-none transition-colors">
          </div>
          <div>
            <label class="block text-xs text-white/40 uppercase tracking-wider mb-2">Max Retries</label>
            <input type="number" id="api-max-retries" value="${api.max_retries}" min="0" max="10"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white text-sm focus:border-accent-pink focus:outline-none transition-colors">
          </div>
        </div>
      </div>
    `;
  }

  renderCacheSettings() {
    const { cache } = this.settings;
    return `
      <div class="glass p-6 rounded-2xl border border-white/10">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-tertiary">storage</span>
          <h3 class="text-lg font-bold text-white">Cache Settings</h3>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="flex items-center gap-3">
            <input type="checkbox" id="cache-enabled" ${cache.enabled ? 'checked' : ''}
              class="w-5 h-5 accent-cyan-400 rounded border-white/20 bg-white/5 cursor-pointer">
            <label for="cache-enabled" class="text-white/80 text-sm cursor-pointer">Enable Caching</label>
          </div>
          <div>
            <label class="block text-xs text-white/40 uppercase tracking-wider mb-2">TTL (seconds)</label>
            <input type="number" id="cache-ttl" value="${cache.ttl_seconds}" min="60" max="86400"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white text-sm focus:border-accent-pink focus:outline-none transition-colors">
          </div>
          <div>
            <label class="block text-xs text-white/40 uppercase tracking-wider mb-2">Max Entries</label>
            <input type="number" id="cache-max-entries" value="${cache.max_entries}" min="100" max="10000"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white text-sm focus:border-accent-pink focus:outline-none transition-colors">
          </div>
        </div>
      </div>
    `;
  }

  renderRateLimitingSettings() {
    const { rate_limiting } = this.settings;
    return `
      <div class="glass p-6 rounded-2xl border border-white/10">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-primary">speed</span>
          <h3 class="text-lg font-bold text-white">Rate Limiting</h3>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs text-white/40 uppercase tracking-wider mb-2">Default Tier</label>
            <select id="rate-tier" class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white text-sm focus:border-accent-pink focus:outline-none transition-colors">
              <option value="trial" ${rate_limiting.default_tier === 'trial' ? 'selected' : ''}>Trial (20 req/hr)</option>
              <option value="default" ${rate_limiting.default_tier === 'default' ? 'selected' : ''}>Default (100 req/hr)</option>
              <option value="premium" ${rate_limiting.default_tier === 'premium' ? 'selected' : ''}>Premium (1000 req/hr)</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-white/40 uppercase tracking-wider mb-2">Trial Requests</label>
            <input type="number" id="rate-trial-requests" value="${rate_limiting.trial_requests}" min="5" max="100"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white text-sm focus:border-accent-pink focus:outline-none transition-colors">
          </div>
        </div>
      </div>
    `;
  }

  renderUISettings() {
    const { ui_preferences } = this.settings;
    return `
      <div class="glass p-6 rounded-2xl border border-white/10">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-accent-pink">palette</span>
          <h3 class="text-lg font-bold text-white">UI Preferences</h3>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="flex items-center gap-3">
            <input type="checkbox" id="ui-compact" ${ui_preferences.compact_mode ? 'checked' : ''}
              class="w-5 h-5 accent-cyan-400 rounded border-white/20 bg-white/5 cursor-pointer">
            <label for="ui-compact" class="text-white/80 text-sm cursor-pointer">Compact Mode</label>
          </div>
          <div>
            <label class="block text-xs text-white/40 uppercase tracking-wider mb-2">Refresh Interval (seconds)</label>
            <input type="number" id="ui-refresh" value="${ui_preferences.refresh_interval}" min="1" max="60"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white text-sm focus:border-accent-pink focus:outline-none transition-colors">
          </div>
        </div>
      </div>
    `;
  }

  renderActions() {
    return `
      <div class="flex flex-wrap gap-4 pt-4">
        <button id="save-settings" class="bg-accent-pink hover:bg-accent-pink/80 text-white font-bold text-sm px-6 py-3 rounded-xl flex items-center gap-2 transition-all shadow-[0_0_15px_rgba(255,0,122,0.3)] hover:shadow-[0_0_25px_rgba(255,0,122,0.5)]">
          <span class="material-symbols-outlined text-sm">save</span>
          Save Changes
        </button>
        <button id="reset-settings" class="bg-white/5 hover:bg-white/10 text-white font-semibold text-sm px-6 py-3 rounded-xl flex items-center gap-2 transition-colors border border-white/10">
          <span class="material-symbols-outlined text-sm">restart_alt</span>
          Reset to Defaults
        </button>
      </div>
      <div id="settings-message" class="hidden mt-4 p-4 rounded-xl flex items-center gap-2"></div>
    `;
  }

  attachEventListeners() {
    const saveBtn = this.querySelector('#save-settings');
    const resetBtn = this.querySelector('#reset-settings');

    if (saveBtn) {
      saveBtn.addEventListener('click', () => this.saveSettings());
    }
    if (resetBtn) {
      resetBtn.addEventListener('click', () => this.resetSettings());
    }
  }

  showMessage(text, isError = false) {
    const msg = this.querySelector('#settings-message');
    if (msg) {
      msg.innerHTML = `<span class="material-symbols-outlined">${isError ? 'error' : 'check_circle'}</span><span>${text}</span>`;
      msg.className = `mt-4 p-4 rounded-xl flex items-center gap-2 ${isError ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-green-500/20 text-green-400 border border-green-500/30'}`;
      msg.classList.remove('hidden');
      setTimeout(() => msg.classList.add('hidden'), 3000);
    }
  }

  async saveSettings() {
    try {
      const engineType = this.querySelector('#api-engine-type')?.value;
      const timeout = this.querySelector('#api-timeout')?.value;
      const maxRetries = this.querySelector('#api-max-retries')?.value;
      const cacheEnabled = this.querySelector('#cache-enabled')?.checked;
      const cacheTtl = this.querySelector('#cache-ttl')?.value;
      const cacheMaxEntries = this.querySelector('#cache-max-entries')?.value;
      const rateTier = this.querySelector('#rate-tier')?.value;
      const rateTrialRequests = this.querySelector('#rate-trial-requests')?.value;
      const uiCompact = this.querySelector('#ui-compact')?.checked;
      const uiRefresh = this.querySelector('#ui-refresh')?.value;

      await API.updateSetting('api', 'engine_type', engineType);
      await API.updateSetting('api', 'timeout', parseInt(timeout));
      await API.updateSetting('api', 'max_retries', parseInt(maxRetries));
      await API.updateSetting('cache', 'enabled', cacheEnabled);
      await API.updateSetting('cache', 'ttl_seconds', parseInt(cacheTtl));
      await API.updateSetting('cache', 'max_entries', parseInt(cacheMaxEntries));
      await API.updateSetting('rate_limiting', 'default_tier', rateTier);
      await API.updateSetting('rate_limiting', 'trial_requests', parseInt(rateTrialRequests));
      await API.updateSetting('ui_preferences', 'compact_mode', uiCompact);
      await API.updateSetting('ui_preferences', 'refresh_interval', parseInt(uiRefresh));

      this.showMessage('Settings saved successfully!');
      this.originalSettings = JSON.parse(JSON.stringify(this.settings));
    } catch (error) {
      console.error('Failed to save settings:', error);
      this.showMessage(`Error: ${error.message}`, true);
    }
  }

  async resetSettings() {
    if (!confirm('Are you sure you want to reset all settings to defaults?')) {
      return;
    }

    try {
      await API.resetSettings();
      await this.loadSettings();
      this.render();
      this.attachEventListeners();
      this.showMessage('Settings reset to defaults');
    } catch (error) {
      console.error('Failed to reset settings:', error);
      this.showMessage(`Error: ${error.message}`, true);
    }
  }
}

customElements.define('settings-component', SettingsComponent);
