// Generate random stars
function generateStars(count = 150) {
  const container = document.querySelector('.stars');
  if (!container) return;
  for (let i = 0; i < count; i++) {
    const star = document.createElement('div');
    star.className = 'star';
    const size = Math.random() * 2.5 + 0.5;
    star.style.cssText = `
      width: ${size}px;
      height: ${size}px;
      top: ${Math.random() * 100}%;
      left: ${Math.random() * 100}%;
      --duration: ${Math.random() * 4 + 1.5}s;
      --delay: ${Math.random() * 4}s;
    `;
    container.appendChild(star);
  }
}

// WebSocket client with auto-reconnect
class SpaceSocket {
  constructor(url, handlers) {
    this.url = url;
    this.handlers = handlers;
    this.ws = null;
    this.reconnectDelay = 2000;
    this.connect();
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url);
      this.ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        const handler = this.handlers[data.type];
        if (handler) handler(data);
      };
      this.ws.onclose = () => {
        setTimeout(() => this.connect(), this.reconnectDelay);
      };
      this.ws.onerror = () => this.ws.close();
    } catch (e) {
      setTimeout(() => this.connect(), this.reconnectDelay);
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

// Toast notifications
function showToast(message, type = 'info', duration = 5000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const colors = {
    info: 'border-indigo-500 bg-indigo-900/80',
    success: 'border-green-500 bg-green-900/80',
    error: 'border-red-500 bg-red-900/80',
    warning: 'border-yellow-500 bg-yellow-900/80',
    freeze: 'border-blue-400 bg-blue-900/80',
  };

  const toast = document.createElement('div');
  toast.className = `toast-enter glass border-l-4 ${colors[type] || colors.info} text-white p-4 rounded-lg shadow-2xl max-w-sm text-sm`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.replace('toast-enter', 'toast-exit');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Score flash effect
function flashScore(element) {
  if (!element) return;
  element.classList.add('score-updated');
  setTimeout(() => element.classList.remove('score-updated'), 1000);
}

// Event banner
function showEventBanner(title, description) {
  const banner = document.getElementById('event-banner');
  if (!banner) return;
  document.getElementById('event-title').textContent = title;
  document.getElementById('event-desc').textContent = description;
  banner.classList.remove('hidden');
  setTimeout(() => banner.classList.add('hidden'), 8000);
}

document.addEventListener('DOMContentLoaded', () => {
  generateStars();
});
