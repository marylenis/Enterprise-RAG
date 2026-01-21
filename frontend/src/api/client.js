/**
 * Unified API Client for Enterprise RAG Frontend
 * Handles all communication with the FastAPI backend
 */

class RAGAPIClient {
  constructor(baseURL = '/api') { // Use relative path when served via Nginx
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'X-API-Tier': localStorage.getItem('apiTier') || 'default'
    };
  }

  /**
   * Generic request method with error handling
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: { ...this.defaultHeaders, ...options.headers },
      ...options
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  /**
   * Query the RAG system
   */
  async query(query, engineType = 'hybrid') {
    return this.request('/query', {
      method: 'POST',
      body: JSON.stringify({
        query,
        engine_type: engineType
      })
    });
  }

  /**
   * Stream query response for real-time chat
   */
  async *queryStream(query, engineType = 'hybrid') {
    const url = `${this.baseURL}/query`;
    const response = await fetch(url, {
      method: 'POST',
      headers: this.defaultHeaders,
      body: JSON.stringify({
        query,
        engine_type: engineType
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') return;

            try {
              yield JSON.parse(data);
            } catch (e) {
              // Skip malformed JSON
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Ingest documents into the system
   */
  async ingest(dataPath = null, author = 'Web User') {
    return this.request('/ingest', {
      method: 'POST',
      body: JSON.stringify({
        data_path: dataPath,
        author
      })
    });
  }

  /**
   * Upload file for ingestion
   */
  async uploadFile(file, author = 'Web User') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('author', author);

    const response = await fetch(`${this.baseURL}/upload`, {
      method: 'POST',
      body: formData,
      headers: {
        'X-API-Tier': this.defaultHeaders['X-API-Tier']
      },
      signal: AbortSignal.timeout(60000) // 60 segundos timeout
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Get audit trail
   */
  async getAuditTrail() {
    return this.request('/audit');
  }

  /**
   * Get cache statistics
   */
  async getCacheStats() {
    return this.request('/stats/cache');
  }

  /**
   * Get cost statistics
   */
  async getCostStats() {
    return this.request('/stats/costs');
  }

  /**
   * Get usage statistics
   */
  async getUsageStats() {
    return this.request('/stats/usage');
  }

  /**
   * Clear cache
   */
  async clearCache(pattern = null) {
    const params = pattern ? `?pattern=${encodeURIComponent(pattern)}` : '';
    return this.request(`/cache${params}`, {
      method: 'DELETE'
    });
  }

  /**
    * Run system evaluation with optional custom queries
    */
  async runEvaluation(queries = null) {
    const options = {
      method: 'POST',
      headers: { ...this.defaultHeaders }
    };

    if (queries && queries.length > 0) {
      options.body = JSON.stringify({ queries });
    }

    return this.request('/evaluate', options);
  }

  /**
   * Compare engine performance
   */
  async compareEngines() {
    return this.request('/evaluate/compare');
  }

  /**
   * Get system health
   */
  async getHealth() {
    return this.request('/health');
  }

  /**
   * Set API tier for rate limiting
   */
  setAPITier(tier) {
    if (['default', 'premium', 'trial'].includes(tier)) {
      this.defaultHeaders['X-API-Tier'] = tier;
      localStorage.setItem('apiTier', tier);
    }
  }

  /**
   * Get current API tier
   */
  getAPITier() {
    return this.defaultHeaders['X-API-Tier'];
  }

  /**
   * WebSocket connection for real-time updates
   */
  createWebSocket(endpoint = '/ws') {
    const wsURL = this.baseURL.replace('http', 'ws') + endpoint;
    return new WebSocket(wsURL);
  }

  /**
   * Batch operations
   */
  async batchQuery(queries, engineType = 'hybrid') {
    const promises = queries.map(query => this.query(query, engineType));
    return Promise.all(promises);
  }

  /**
    * Retry mechanism for failed requests
    */
  async withRetry(requestFn, maxRetries = 3, delay = 1000) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await requestFn();
      } catch (error) {
        if (attempt === maxRetries) throw error;

        console.warn(`Request failed, retrying in ${delay}ms... (attempt ${attempt}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, delay * attempt));
      }
    }
  }

  /**
   * Settings API
   */
  async getSettings() {
    return this.request('/settings');
  }

  async getCategorySettings(category) {
    return this.request(`/settings/${category}`);
  }

  async updateSetting(category, key, value) {
    return this.request('/settings', {
      method: 'PUT',
      body: JSON.stringify({ category, key, value })
    });
  }

  async resetSettings() {
    return this.request('/settings/reset', { method: 'POST' });
  }
}

// Create singleton instance
export const apiClient = new RAGAPIClient();

// Export utility functions
export const API = {
  query: (query, engineType) => apiClient.query(query, engineType),
  queryStream: (query, engineType) => apiClient.queryStream(query, engineType),
  ingest: (dataPath, author) => apiClient.ingest(dataPath, author),
  uploadFile: (file, author) => apiClient.uploadFile(file, author),
  getAuditTrail: () => apiClient.getAuditTrail(),
  getCacheStats: () => apiClient.getCacheStats(),
  getCostStats: () => apiClient.getCostStats(),
  getUsageStats: () => apiClient.getUsageStats(),
  clearCache: (pattern) => apiClient.clearCache(pattern),
  runEvaluation: () => apiClient.runEvaluation(),
  compareEngines: () => apiClient.compareEngines(),
  getHealth: () => apiClient.getHealth(),
  setAPITier: (tier) => apiClient.setAPITier(tier),
  getAPITier: () => apiClient.getAPITier(),
  createWebSocket: (endpoint) => apiClient.createWebSocket(endpoint),
  batchQuery: (queries, engineType) => apiClient.batchQuery(queries, engineType),
  withRetry: (requestFn, maxRetries, delay) => apiClient.withRetry(requestFn, maxRetries, delay),
  getSettings: () => apiClient.getSettings(),
  getCategorySettings: (category) => apiClient.getCategorySettings(category),
  updateSetting: (category, key, value) => apiClient.updateSetting(category, key, value),
  resetSettings: () => apiClient.resetSettings()
};

export default apiClient;