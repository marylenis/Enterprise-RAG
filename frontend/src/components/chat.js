/**
 * Chat Component extracted from Query Center page
 */

class ChatComponent extends HTMLElement {
  constructor() {
    super();
    this.messages = [];
    this.isTyping = false;
    this.currentEngine = 'hybrid';
  }

  connectedCallback() {
    this.render();
    this.loadHistory();
  }

  render() {
    this.innerHTML = `
      <div class="flex-1 overflow-hidden relative">
        <div class="absolute inset-0 cyber-bg -z-10"></div>
        
        <div class="absolute top-[10%] left-[20%] sparkle"></div>
        <div class="absolute top-[30%] left-[80%] sparkle"></div>
        <div class="absolute top-[70%] left-[15%] sparkle"></div>
        <div class="absolute top-[50%] left-[45%] sparkle"></div>
        <div class="absolute top-[85%] left-[65%] sparkle"></div>
        <div class="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/5 rounded-full blur-[120px]"></div>
        <div class="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent-pink/10 rounded-full blur-[120px]"></div>

        <div class="flex flex-1 overflow-hidden h-full">
          <!-- Chat Area -->
          <main class="flex-1 flex flex-col relative">
            <div class="px-8 py-4 flex items-center justify-between border-b border-white/5 glass">
              <div class="flex items-center gap-2 text-xs font-medium">
                <span class="text-white/40">Nexus</span>
                <span class="text-white/20">/</span>
                <span class="text-white/40">Active Sessions</span>
                <span class="text-white/20">/</span>
                <span class="text-accent-pink font-bold uppercase tracking-widest">Session_${Math.random().toString(36).substr(2, 6)}</span>
              </div>
              <div class="flex items-center gap-4">
                <span class="flex items-center gap-2 text-[10px] text-tertiary font-bold">
                  <span class="size-1.5 bg-tertiary rounded-full animate-pulse"></span>
                  CONNECTED
                </span>
                <button class="material-symbols-outlined text-white/40 hover:text-white transition-colors" id="settings-btn">settings</button>
              </div>
            </div>

            <div class="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar" id="messages-container">
              <!-- Messages will be rendered here -->
            </div>

            <div class="p-8 pt-0">
              <div class="glass rounded-2xl p-2 border border-white/10 relative overflow-hidden group focus-within:neon-border-pink transition-all">
                <div class="absolute inset-0 bg-accent-pink/5 opacity-0 group-focus-within:opacity-100 transition-opacity"></div>
                <textarea 
                  class="w-full bg-transparent border-none focus:ring-0 text-sm text-white placeholder:text-white/20 min-h-[100px] p-4 resize-none" 
                  placeholder="Ask anything about your enterprise knowledge base..."
                  id="message-input"
                ></textarea>
                <div class="flex items-center justify-between p-2 border-t border-white/5">
                  <div class="flex items-center gap-4">
                    <div class="flex items-center gap-2">
                      <span class="text-[10px] font-bold text-white/40 uppercase">Vector</span>
                      <div class="w-10 h-5 bg-accent-pink/20 rounded-full relative p-1 cursor-pointer" id="engine-toggle">
                        <div class="w-3 h-3 bg-accent-pink rounded-full absolute right-1 shadow-[0_0_8px_rgba(255,0,122,0.8)]"></div>
                      </div>
                      <span class="text-[10px] font-bold text-accent-pink uppercase">Hybrid</span>
                    </div>
                    <div class="w-px h-4 bg-white/10"></div>
                    <button class="material-symbols-outlined text-white/40 hover:text-white transition-colors text-xl" id="attach-btn">attach_file</button>
                  </div>
                  <button class="bg-accent-pink hover:bg-accent-pink/80 text-white font-bold text-sm px-6 py-2 rounded-xl flex items-center gap-2 transition-all shadow-[0_0_15px_rgba(255,0,122,0.3)]" id="send-btn">
                    SEND <span class="material-symbols-outlined text-sm">send</span>
                  </button>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    const sendBtn = this.querySelector('#send-btn');
    const messageInput = this.querySelector('#message-input');
    const engineToggle = this.querySelector('#engine-toggle');
    const attachBtn = this.querySelector('#attach-btn');

    // Send message
    sendBtn.addEventListener('click', () => this.sendMessage());
    messageInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Engine toggle
    engineToggle.addEventListener('click', () => this.toggleEngine());

    // File attachment
    attachBtn.addEventListener('click', () => this.attachFile());

    // Settings button
    this.querySelector('#settings-btn')?.addEventListener('click', () => {
      console.log('Open chat settings');
    });
  }

  async sendMessage() {
    const input = this.querySelector('#message-input');
    const message = input.value.trim();
    
    if (!message) return;

    // Add user message
    this.addMessage(message, 'user');
    input.value = '';

    // Show typing indicator
    this.showTypingIndicator();

    try {
      const response = await API.query(message, this.currentEngine);
      this.hideTypingIndicator();
      this.addMessage(response.response, 'assistant', response.sources);
    } catch (error) {
      this.hideTypingIndicator();
      this.addMessage('Sorry, I encountered an error. Please try again.', 'error');
    }
  }

  addMessage(content, sender, sources = []) {
    const messagesContainer = this.querySelector('#messages-container');
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    const messageEl = document.createElement('div');
    
    if (sender === 'user') {
      messageEl.className = 'flex flex-col items-end';
      messageEl.innerHTML = `
        <div class="max-w-[80%] bg-gradient-to-br from-accent-pink to-[#D4006B] text-white p-4 rounded-2xl rounded-tr-none shadow-[0_4px_20px_rgba(255,0,122,0.2)]">
          <p class="text-sm font-medium leading-relaxed">${content}</p>
        </div>
        <span class="text-[10px] text-white/30 mt-2 font-bold uppercase tracking-wider">User · ${timestamp}</span>
      `;
    } else if (sender === 'assistant') {
      messageEl.className = 'flex flex-col items-start';
      messageEl.innerHTML = `
        <div class="flex gap-4 max-w-[85%]">
          <div class="size-8 rounded-lg bg-secondary/20 border border-secondary/40 flex items-center justify-center shrink-0 mt-1">
            <span class="material-symbols-outlined text-secondary text-sm">smart_toy</span>
          </div>
          <div class="glass p-5 rounded-2xl rounded-tl-none border-l-2 border-l-secondary/60">
            <div class="flex items-center gap-2 mb-3">
              <span class="text-[10px] font-bold text-secondary uppercase tracking-widest">Nexus Intelligence</span>
              <span class="size-1 bg-white/20 rounded-full"></span>
              <span class="text-[10px] text-white/30">${sources.length} sources retrieved</span>
            </div>
            <div class="text-sm leading-relaxed text-white/90 mb-4">${this.formatMessage(content)}</div>
            ${sources.length > 0 ? this.renderSources(sources) : ''}
          </div>
        </div>
        <span class="text-[10px] text-white/30 mt-2 ml-12 font-bold uppercase tracking-wider">AI Assistant · ${timestamp}</span>
      `;
    } else if (sender === 'error') {
      messageEl.className = 'flex justify-center';
      messageEl.innerHTML = `
        <div class="glass p-4 rounded-xl border border-red-500/30 max-w-md">
          <p class="text-red-400 text-sm text-center">${content}</p>
        </div>
      `;
    }

    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  formatMessage(content) {
    // Basic markdown-like formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-white/10 px-1 py-0.5 rounded text-xs">$1</code>')
      .replace(/\n/g, '<br>');
  }

  renderSources(sources) {
    return `
      <div class="mt-4 pt-3 border-t border-white/10">
        <p class="text-xs font-bold text-white/50 mb-2">SOURCES:</p>
        ${sources.map((source, index) => `
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs text-primary">${index + 1}.</span>
            <span class="text-xs text-white/60">${source}</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  showTypingIndicator() {
    if (this.isTyping) return;
    
    this.isTyping = true;
    const messagesContainer = this.querySelector('#messages-container');
    const typingEl = document.createElement('div');
    typingEl.id = 'typing-indicator';
    typingEl.className = 'flex gap-4 items-center';
    typingEl.innerHTML = `
      <div class="size-8 rounded-lg bg-white/5 flex items-center justify-center shrink-0">
        <span class="material-symbols-outlined text-white/20 text-sm">smart_toy</span>
      </div>
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    `;
    
    messagesContainer.appendChild(typingEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  hideTypingIndicator() {
    this.isTyping = false;
    const typingIndicator = this.querySelector('#typing-indicator');
    if (typingIndicator) {
      typingIndicator.remove();
    }
  }

  toggleEngine() {
    const toggle = this.querySelector('#engine-toggle');
    const dot = toggle.querySelector('div');
    
    if (this.currentEngine === 'hybrid') {
      this.currentEngine = 'vector';
      dot.style.left = '1px';
      dot.style.right = 'auto';
    } else {
      this.currentEngine = 'hybrid';
      dot.style.right = '1px';
      dot.style.left = 'auto';
    }
  }

  attachFile() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.docx,.txt,.md';
    input.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        console.log('File attached:', file.name);
        // TODO: Implement file upload
      }
    });
    input.click();
  }

  loadHistory() {
    // TODO: Load chat history from localStorage or API
  }

  saveHistory() {
    // TODO: Save chat history to localStorage or API
  }
}

customElements.define('chat-component', ChatComponent);