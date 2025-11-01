/**
 * Toast Notification System
 */

class ToastManager {
  constructor() {
    this.toasts = [];
    this.container = null;
    this.setupContainer();
  }

  setupContainer() {
    this.container = document.createElement('div');
    this.container.id = 'toast-container';
    this.container.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9999;
      max-width: 400px;
    `;
    document.body.appendChild(this.container);
  }

  show(message, type = 'info', duration = 4000) {
    const toast = document.createElement('div');
    const toastId = `toast-${Date.now()}`;
    toast.id = toastId;

    // Determine icon based on type
    let icon = 'fas fa-info-circle';
    let bgColor = 'var(--info)';
    let bgLight = 'rgba(6, 182, 212, 0.1)';

    switch (type) {
      case 'success':
        icon = 'fas fa-check-circle';
        bgColor = 'var(--success)';
        bgLight = 'rgba(16, 185, 129, 0.1)';
        break;
      case 'error':
      case 'danger':
        icon = 'fas fa-exclamation-circle';
        bgColor = 'var(--danger)';
        bgLight = 'rgba(239, 68, 68, 0.1)';
        break;
      case 'warning':
        icon = 'fas fa-exclamation-triangle';
        bgColor = 'var(--warning)';
        bgLight = 'rgba(245, 158, 11, 0.1)';
        break;
    }

    toast.innerHTML = `
      <div style="
        background-color: ${bgLight};
        border: 1px solid ${bgColor};
        border-left: 4px solid ${bgColor};
        border-radius: 0.75rem;
        padding: 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        animation: slideInRight 0.3s ease-in-out;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
      ">
        <i class="${icon}" style="color: ${bgColor}; font-size: 1.25rem; flex-shrink: 0;"></i>
        <span style="color: var(--text-primary); flex: 1;">${message}</span>
        <button style="
          background: none;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          padding: 0;
          font-size: 1rem;
          display: flex;
          align-items: center;
        " onclick="document.getElementById('${toastId}').remove()">
          <i class="fas fa-times"></i>
        </button>
      </div>
    `;

    this.container.appendChild(toast);

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        if (toast.parentNode) {
          toast.remove();
        }
      }, duration);
    }

    return toastId;
  }

  success(message, duration = 4000) {
    return this.show(message, 'success', duration);
  }

  error(message, duration = 5000) {
    return this.show(message, 'error', duration);
  }

  warning(message, duration = 4000) {
    return this.show(message, 'warning', duration);
  }

  info(message, duration = 3000) {
    return this.show(message, 'info', duration);
  }
}

// Create global toast instance
window.toast = new ToastManager();

// Add slideInRight animation
const toastStyle = document.createElement('style');
toastStyle.textContent = `
  @keyframes slideInRight {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
`;
document.head.appendChild(toastStyle);
