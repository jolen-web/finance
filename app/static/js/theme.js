/**
 * Theme Manager - Handles light/dark mode toggling
 */

class ThemeManager {
  constructor() {
    this.STORAGE_KEY = 'finance-theme-preference';
    this.LIGHT_THEME = 'light';
    this.DARK_THEME = 'dark';
    this.SYSTEM_THEME = 'system';
    this.init();
  }

  init() {
    // Get saved preference or detect system preference
    const saved = localStorage.getItem(this.STORAGE_KEY);
    const preference = saved || this.SYSTEM_THEME;

    if (preference === this.SYSTEM_THEME) {
      this.applySystemTheme();
      this.listenToSystemTheme();
    } else {
      this.setTheme(preference);
    }

    // Set up toggle button if it exists
    this.setupToggleButton();
  }

  applySystemTheme() {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    this.setTheme(isDark ? this.DARK_THEME : this.LIGHT_THEME);
  }

  listenToSystemTheme() {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      const saved = localStorage.getItem(this.STORAGE_KEY);
      if (!saved || saved === this.SYSTEM_THEME) {
        this.setTheme(e.matches ? this.DARK_THEME : this.LIGHT_THEME);
      }
    });
  }

  setTheme(theme) {
    const html = document.documentElement;

    if (theme === this.DARK_THEME) {
      html.setAttribute('data-theme', 'dark');
    } else {
      html.removeAttribute('data-theme');
    }

    // Update toggle button icon if it exists
    this.updateToggleButton(theme);
  }

  toggleTheme() {
    const current = this.getCurrentTheme();
    const next = current === this.DARK_THEME ? this.LIGHT_THEME : this.DARK_THEME;
    this.setTheme(next);
    localStorage.setItem(this.STORAGE_KEY, next);
  }

  getCurrentTheme() {
    return document.documentElement.getAttribute('data-theme') || this.LIGHT_THEME;
  }

  setupToggleButton() {
    // Create toggle button if it doesn't exist
    const button = document.getElementById('theme-toggle-btn');
    if (button) {
      button.addEventListener('click', () => {
        this.toggleTheme();
      });
    }
  }

  updateToggleButton(theme) {
    const button = document.getElementById('theme-toggle-btn');
    if (button) {
      const icon = button.querySelector('i');
      if (icon) {
        if (theme === this.DARK_THEME) {
          icon.className = 'fas fa-sun';
          button.title = 'Switch to Light Mode';
        } else {
          icon.className = 'fas fa-moon';
          button.title = 'Switch to Dark Mode';
        }
      }
    }
  }
}

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.themeManager = new ThemeManager();
});
