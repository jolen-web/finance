/**
 * Chart Utilities - Wrapper for Chart.js with theme support
 */

class ChartManager {
  constructor() {
    this.charts = {};
    this.scriptLoaded = false;
    this.loadChartLibrary();
  }

  loadChartLibrary() {
    if (window.Chart) {
      this.scriptLoaded = true;
      this.setupThemeListener();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0';
    script.onload = () => {
      this.scriptLoaded = true;
      this.setupThemeListener();
      window.dispatchEvent(new Event('chartsLoaded'));
    };
    script.onerror = () => {
      console.error('Failed to load Chart.js');
    };
    document.head.appendChild(script);
  }

  setupThemeListener() {
    // Listen for theme changes
    const observer = new MutationObserver(() => {
      this.updateAllCharts();
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });
  }

  getThemeColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
      textColor: isDark ? '#f5f5f5' : '#111827',
      gridColor: isDark ? '#3d3d3d' : '#e5e7eb',
      backgroundColor: isDark ? '#1a1a1a' : '#ffffff',
      borderColor: isDark ? '#2d2d2d' : '#d1d5db',
    };
  }

  createLineChart(canvasId, data, options = {}) {
    if (!this.scriptLoaded) {
      console.error('Chart.js not loaded yet');
      return;
    }

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const colors = this.getThemeColors();
    const ctx = canvas.getContext('2d');

    // Default options
    const defaultOptions = {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          labels: { color: colors.textColor, font: { size: 12, weight: '500' } },
        },
        tooltip: {
          backgroundColor: colors.borderColor,
          titleColor: colors.textColor,
          bodyColor: colors.textColor,
          borderColor: colors.gridColor,
          padding: 12,
          titleFont: { size: 13, weight: 'bold' },
          bodyFont: { size: 12 },
        },
      },
      scales: {
        x: {
          grid: { color: colors.gridColor, drawBorder: false },
          ticks: { color: colors.textColor },
        },
        y: {
          grid: { color: colors.gridColor, drawBorder: false },
          ticks: { color: colors.textColor },
        },
      },
    };

    // Merge options
    const mergedOptions = { ...defaultOptions, ...options };

    // Destroy existing chart if it exists
    if (this.charts[canvasId]) {
      this.charts[canvasId].destroy();
    }

    this.charts[canvasId] = new Chart(ctx, {
      type: 'line',
      data: data,
      options: mergedOptions,
    });

    return this.charts[canvasId];
  }

  createDoughnutChart(canvasId, data, options = {}) {
    if (!this.scriptLoaded) {
      console.error('Chart.js not loaded yet');
      return;
    }

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const colors = this.getThemeColors();
    const ctx = canvas.getContext('2d');

    const defaultOptions = {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          labels: { color: colors.textColor, font: { size: 12, weight: '500' } },
          position: 'bottom',
        },
        tooltip: {
          backgroundColor: colors.borderColor,
          titleColor: colors.textColor,
          bodyColor: colors.textColor,
          borderColor: colors.gridColor,
          padding: 12,
          titleFont: { size: 13, weight: 'bold' },
          bodyFont: { size: 12 },
          callbacks: {
            label: function (context) {
              const label = context.label || '';
              const value = context.parsed || 0;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = ((value / total) * 100).toFixed(1);
              return `${label}: $${value.toFixed(2)} (${percentage}%)`;
            },
          },
        },
      },
    };

    const mergedOptions = { ...defaultOptions, ...options };

    if (this.charts[canvasId]) {
      this.charts[canvasId].destroy();
    }

    this.charts[canvasId] = new Chart(ctx, {
      type: 'doughnut',
      data: data,
      options: mergedOptions,
    });

    return this.charts[canvasId];
  }

  createBarChart(canvasId, data, options = {}) {
    if (!this.scriptLoaded) {
      console.error('Chart.js not loaded yet');
      return;
    }

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const colors = this.getThemeColors();
    const ctx = canvas.getContext('2d');

    const defaultOptions = {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          labels: { color: colors.textColor, font: { size: 12, weight: '500' } },
        },
        tooltip: {
          backgroundColor: colors.borderColor,
          titleColor: colors.textColor,
          bodyColor: colors.textColor,
          borderColor: colors.gridColor,
          padding: 12,
          titleFont: { size: 13, weight: 'bold' },
          bodyFont: { size: 12 },
        },
      },
      scales: {
        x: {
          grid: { color: colors.gridColor, drawBorder: false },
          ticks: { color: colors.textColor },
        },
        y: {
          grid: { color: colors.gridColor, drawBorder: false },
          ticks: { color: colors.textColor },
        },
      },
    };

    const mergedOptions = { ...defaultOptions, ...options };

    if (this.charts[canvasId]) {
      this.charts[canvasId].destroy();
    }

    this.charts[canvasId] = new Chart(ctx, {
      type: 'bar',
      data: data,
      options: mergedOptions,
    });

    return this.charts[canvasId];
  }

  updateAllCharts() {
    Object.values(this.charts).forEach((chart) => {
      if (chart) {
        chart.update();
      }
    });
  }
}

// Global instance
window.chartManager = new ChartManager();
