/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        'soc-bg': '#0f172a',
        'soc-sidebar': '#020617',
        'soc-card': '#1e293b',
        'soc-border': '#334155',
        'soc-text': '#e2e8f0',
        'soc-secondary': '#94a3b8',
        'soc-muted': '#64748b',
        'soc-critical': '#ef4444',
        'soc-high': '#f97316',
        'soc-medium': '#f59e0b',
        'soc-low': '#22c55e',
        'soc-info': '#3b82f6',
      },
      animation: {
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
        'pulse-subtle': 'pulseSubtle 2s ease-in-out infinite',
      },
      keyframes: {
        slideInRight: {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
      },
      boxShadow: {
        'soc-sm': '0 1px 3px rgba(0, 0, 0, 0.3)',
        'soc-md': '0 4px 8px rgba(0, 0, 0, 0.4)',
        'soc-lg': '0 8px 16px rgba(0, 0, 0, 0.5)',
        'soc-overlay': '0 20px 25px -5px rgba(0, 0, 0, 0.6)',
      },
    },
  },
  plugins: [],
}
