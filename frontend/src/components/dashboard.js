/**
 * Dashboard Main Component - Aggregated from all pages
 */

import { API } from '../api/client.js';

class DashboardComponent extends HTMLElement {
  constructor() {
    super();
    this.stats = {};
    this.refreshInterval = 30000; // 30 seconds
  }

  connectedCallback() {
    this.render();
    this.loadDashboardData();
    this.startAutoRefresh();
  }

  disconnectedCallback() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
  }

  render() {
    this.innerHTML = `
      <div class="flex-1 overflow-hidden relative">
        <div class="absolute inset-0 cyber-bg -z-10"></div>
        
        <!-- Floating elements -->
        <div class="absolute top-[10%] left-[20%] sparkle"></div>
        <div class="absolute top-[30%] left-[80%] sparkle"></div>
        <div class="absolute top-[70%] left-[15%] sparkle"></div>
        <div class="absolute top-[50%] left-[45%] sparkle"></div>
        <div class="absolute top-[85%] left-[65%] sparkle"></div>
        <div class="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/5 rounded-full blur-[120px]"></div>
        <div class="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent-pink/10 rounded-full blur-[120px]"></div>

        <div class="p-8 h-full overflow-y-auto custom-scrollbar">
          <!-- Header Section -->
          <div class="mb-8">
            <h1 class="text-3xl font-bold text-white mb-2">Enterprise RAG Dashboard</h1>
            <p class="text-white/60">Monitor and manage your knowledge base system</p>
          </div>

          <!-- Quick Actions -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="glass-panel rounded-2xl p-6 border border-primary/20 hover:border-primary/40 transition-all cursor-pointer group" onclick="window.location.href='/chat.html'">
              <div class="flex items-center gap-4">
                <div class="size-12 rounded-xl bg-gradient-to-br from-primary to-cyan-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span class="material-symbols-outlined text-white text-xl">chat</span>
                </div>
                <div>
                  <h3 class="text-white font-semibold text-lg">New Query</h3>
                  <p class="text-white/60 text-sm">Ask questions to your knowledge base</p>
                </div>
              </div>
            </div>

            <div class="glass-panel rounded-2xl p-6 border border-tertiary/20 hover:border-tertiary/40 transition-all cursor-pointer group" onclick="window.location.href='/documents.html'">
              <div class="flex items-center gap-4">
                <div class="size-12 rounded-xl bg-gradient-to-br from-tertiary to-green-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span class="material-symbols-outlined text-white text-xl">upload_file</span>
                </div>
                <div>
                  <h3 class="text-white font-semibold text-lg">Upload Documents</h3>
                  <p class="text-white/60 text-sm">Add new content to the system</p>
                </div>
              </div>
            </div>

            <div class="glass-panel rounded-2xl p-6 border border-secondary/20 hover:border-secondary/40 transition-all cursor-pointer group" onclick="window.location.href='/analytics.html'">
              <div class="flex items-center gap-4">
                <div class="size-12 rounded-xl bg-gradient-to-br from-secondary to-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span class="material-symbols-outlined text-white text-xl">analytics</span>
                </div>
                <div>
                  <h3 class="text-white font-semibold text-lg">View Analytics</h3>
                  <p class="text-white/60 text-sm">System performance and usage metrics</p>
                </div>
              </div>
            </div>
          </div>

          <!-- System Status Cards -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="glass-panel rounded-2xl p-6 border border-white/10">
              <div class="flex items-center justify-between mb-4">
                <span class="material-symbols-outlined text-primary text-xl">query_stats</span>
                <span class="text-xs text-primary font-bold bg-primary/10 px-2 py-1 rounded">LIVE</span>
              </div>
              <div class="text-2xl font-bold text-white mb-1" id="queries-today">-</div>
              <div class="text-sm text-white/60">Queries Today</div>
              <div class="mt-3 h-1 bg-white/10 rounded-full overflow-hidden">
                <div class="h-full bg-primary rounded-full transition-all duration-1000" id="queries-progress" style="width: 0%"></div>
              </div>
            </div>

            <div class="glass-panel rounded-2xl p-6 border border-white/10">
              <div class="flex items-center justify-between mb-4">
                <span class="material-symbols-outlined text-tertiary text-xl">token</span>
                <span class="text-xs text-tertiary font-bold bg-tertiary/10 px-2 py-1 rounded">OPTIMAL</span>
              </div>
              <div class="text-2xl font-bold text-white mb-1" id="tokens-used">-</div>
              <div class="text-sm text-white/60">Tokens Used</div>
              <div class="text-xs text-white/40 mt-2" id="tokens-percentage">0% of limit</div>
            </div>

            <div class="glass-panel rounded-2xl p-6 border border-white/10">
              <div class="flex items-center justify-between mb-4">
                <span class="material-symbols-outlined text-accent-pink text-xl">savings</span>
                <span class="text-xs text-accent-pink font-bold bg-accent-pink/10 px-2 py-1 rounded">ACTIVE</span>
              </div>
              <div class="text-2xl font-bold text-white mb-1" id="cache-hit-rate">-</div>
              <div class="text-sm text-white/60">Cache Hit Rate</div>
              <div class="text-xs text-white/40 mt-2" id="cache-saved">-$0.00 saved</div>
            </div>

            <div class="glass-panel rounded-2xl p-6 border border-white/10">
              <div class="flex items-center justify-between mb-4">
                <span class="material-symbols-outlined text-secondary text-xl">cloud_done</span>
                <span class="text-xs text-secondary font-bold bg-secondary/10 px-2 py-1 rounded">HEALTHY</span>
              </div>
              <div class="text-2xl font-bold text-white mb-1" id="system-health">100%</div>
              <div class="text-sm text-white/60">System Health</div>
              <div class="text-xs text-white/40 mt-2">All services operational</div>
            </div>
          </div>

          <!-- Recent Activity -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <!-- Recent Queries -->
            <div class="glass-panel rounded-2xl p-6 border border-white/10">
              <h3 class="text-white font-semibold text-lg mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined">history</span>
                Recent Queries
              </h3>
              <div class="space-y-3" id="recent-queries">
                <!-- Will be populated by API -->
              </div>
            </div>

            <!-- Document Processing -->
            <div class="glass-panel rounded-2xl p-6 border border-white/10">
              <h3 class="text-white font-semibold text-lg mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined">description</span>
                Document Processing
              </h3>
              <div class="space-y-3" id="document-processing">
                <!-- Will be populated by API -->
              </div>
            </div>
          </div>

          <!-- Quality Overview -->
          <div class="glass-panel rounded-2xl p-6 border border-white/10">
            <h3 class="text-white font-semibold text-lg mb-4 flex items-center gap-2">
              <span class="material-symbols-outlined">shield_with_heart</span>
              Quality Metrics Overview
            </h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-6" id="quality-metrics">
              <!-- Will be populated by API -->
            </div>
          </div>
        </div>
      </div>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    // Quick action buttons already have onclick handlers
  }

  async loadDashboardData() {
    try {
      await Promise.all([
        this.loadUsageStats(),
        this.loadRecentActivity(),
        this.loadQualityMetrics(),
        this.loadSystemHealth()
      ]);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  }

  async loadUsageStats() {
    try {
      const [usageStats, costStats, cacheStats] = await Promise.all([
        API.getUsageStats(),
        API.getCostStats(),
        API.getCacheStats()
      ]);

      this.updateQueriesToday(usageStats);
      this.updateTokensUsed(usageStats);
      this.updateCacheHitRate(cacheStats);
      this.updateCostStats(costStats);

    } catch (error) {
      console.error('Failed to load usage stats:', error);
    }
  }

  updateQueriesToday(stats) {
    const queriesEl = document.getElementById('queries-today');
    const progressEl = document.getElementById('queries-progress');
    
    const dailyUsage = stats.rate_limiting?.daily_usage || 0;
    const limit = stats.rate_limiting?.limit || 100;
    const percentage = Math.min((dailyUsage / limit) * 100, 100);
    
    if (queriesEl) queriesEl.textContent = dailyUsage.toLocaleString();
    if (progressEl) progressEl.style.width = `${percentage}%`;
  }

  updateTokensUsed(stats) {
    const tokensEl = document.getElementById('tokens-used');
    const percentageEl = document.getElementById('tokens-percentage');
    
    const dailyUsage = stats.token_usage?.daily_usage || 0;
    const limit = stats.token_usage?.daily_limit || 50000;
    const percentage = Math.min((dailyUsage / limit) * 100, 100);
    
    if (tokensEl) tokensEl.textContent = this.formatNumber(dailyUsage);
    if (percentageEl) percentageEl.textContent = `${percentage.toFixed(1)}% of limit`;
  }

  updateCacheHitRate(stats) {
    const hitRateEl = document.getElementById('cache-hit-rate');
    const savedEl = document.getElementById('cache-saved');
    
    const hitRate = stats.hit_rate_percent || 0;
    const savings = (stats.total_cached_queries || 0) * 0.0001; // $0.0001 per cache hit
    
    if (hitRateEl) hitRateEl.textContent = `${hitRate.toFixed(1)}%`;
    if (savedEl) savedEl.textContent = `-$${savings.toFixed(4)} saved`;
  }

  updateCostStats(stats) {
    // Update cost-related metrics
  }

  async loadRecentActivity() {
    try {
      const auditTrail = await API.getAuditTrail();
      this.updateRecentQueries(auditTrail.slice(0, 5));
      this.updateDocumentProcessing(auditTrail.slice(0, 5));
    } catch (error) {
      console.error('Failed to load recent activity:', error);
    }
  }

  updateRecentQueries(queries) {
    const container = document.getElementById('recent-queries');
    if (!container || !queries.length) {
      container.innerHTML = '<p class="text-white/40 text-sm">No recent queries</p>';
      return;
    }

    container.innerHTML = queries.map(query => `
      <div class="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-all cursor-pointer">
        <div class="flex items-center gap-3">
          <span class="material-symbols-outlined text-primary text-sm">help_outline</span>
          <div>
            <p class="text-white text-sm font-medium line-clamp-1">${query.file_path || 'Unknown query'}</p>
            <p class="text-white/40 text-xs">${new Date(query.timestamp).toLocaleTimeString()}</p>
          </div>
        </div>
        <span class="text-xs text-white/40">${this.getRelativeTime(query.timestamp)}</span>
      </div>
    `).join('');
  }

  updateDocumentProcessing(documents) {
    const container = document.getElementById('document-processing');
    if (!container) return;

    // Simulate document processing status
    const mockProcessing = [
      { name: 'Q3_Report.pdf', status: 'processing', progress: 75 },
      { name: 'Employee_Handbook.docx', status: 'completed', progress: 100 },
      { name: 'Security_Policy.md', status: 'queued', progress: 0 }
    ];

    container.innerHTML = mockProcessing.map(doc => `
      <div class="p-3 rounded-lg bg-white/5">
        <div class="flex items-center justify-between mb-2">
          <p class="text-white text-sm font-medium">${doc.name}</p>
          <span class="text-xs px-2 py-1 rounded ${
            doc.status === 'completed' ? 'bg-tertiary/20 text-tertiary' :
            doc.status === 'processing' ? 'bg-accent-pink/20 text-accent-pink' :
            'bg-white/10 text-white/40'
          }">${doc.status}</span>
        </div>
        ${doc.status === 'processing' ? `
          <div class="h-1 bg-white/10 rounded-full overflow-hidden">
            <div class="h-full bg-accent-pink rounded-full transition-all duration-1000" style="width: ${doc.progress}%"></div>
          </div>
        ` : ''}
      </div>
    `).join('');
  }

  async loadQualityMetrics() {
    try {
      const qualityData = await API.compareEngines();
      this.updateQualityMetrics(qualityData);
    } catch (error) {
      console.error('Failed to load quality metrics:', error);
    }
  }

  updateQualityMetrics(data) {
    const container = document.getElementById('quality-metrics');
    if (!container) return;

    const metrics = [
      { name: 'Faithfulness', value: 0.85, color: 'primary' },
      { name: 'Relevancy', value: 0.78, color: 'tertiary' },
      { name: 'Precision', value: 0.82, color: 'secondary' },
      { name: 'Recall', value: 0.76, color: 'accent-pink' }
    ];

    container.innerHTML = metrics.map(metric => `
      <div class="text-center">
        <div class="relative w-20 h-20 mx-auto mb-3">
          <svg class="w-full h-full transform -rotate-90">
            <circle cx="40" cy="40" fill="transparent" r="36" stroke="rgba(255,255,255,0.1)" stroke-width="6"></circle>
            <circle cx="40" cy="40" fill="transparent" r="36" 
                    stroke="var(--color-${metric.color})" 
                    stroke-dasharray="226" 
                    stroke-dashoffset="${226 * (1 - metric.value)}" 
                    stroke-linecap="round" 
                    stroke-width="6"
                    style="--color-primary: #00d0ff; --color-secondary: #9D4EDD; --color-tertiary: #10B981; --color-accent-pink: #FF007A;"
                    class="transition-all duration-1000"></circle>
          </svg>
          <div class="absolute inset-0 flex flex-col items-center justify-center">
            <span class="text-xl font-bold text-white">${(metric.value * 100).toFixed(0)}%</span>
          </div>
        </div>
        <p class="text-white/60 text-sm font-medium">${metric.name}</p>
      </div>
    `).join('');
  }

  async loadSystemHealth() {
    try {
      const health = await API.getHealth();
      document.getElementById('system-health').textContent = '100%';
    } catch (error) {
      document.getElementById('system-health').textContent = 'Degraded';
    }
  }

  formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
  }

  getRelativeTime(timestamp) {
    const now = new Date();
    const past = new Date(timestamp);
    const diff = Math.floor((now - past) / 1000); // seconds

    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  }

  startAutoRefresh() {
    this.refreshTimer = setInterval(() => {
      this.loadDashboardData();
    }, this.refreshInterval);
  }
}

customElements.define('dashboard-component', DashboardComponent);