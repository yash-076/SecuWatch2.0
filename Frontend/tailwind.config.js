/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      colors: {
        'soc-bg': '#0a0a0a',
        'soc-sidebar': '#050505',
        'soc-card': '#111111',
        'soc-border': '#1e1e1e',
        'soc-text': '#f0f0f0',
        'soc-secondary': '#8a8a8a',
        'soc-muted': '#555555',
        'soc-critical': '#ef4444',
        'soc-high': '#f97316',
        'soc-medium': '#f59e0b',
        'soc-low': '#22c55e',
        'soc-info': '#e63946',
        'soc-accent': '#e63946',
        'soc-accent-light': '#ff6b6b',
      },
      scale: {
        '102': '1.02',
      },
      animation: {
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
        'pulse-subtle': 'pulseSubtle 2s ease-in-out infinite',
        'glow-pulse': 'glowPulse 3s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'fade-up': 'fadeUp 0.6s ease-out forwards',
        'scale-in': 'scaleIn 0.5s ease-out forwards',
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
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(230, 57, 70, 0.15)' },
          '50%': { boxShadow: '0 0 40px rgba(230, 57, 70, 0.3)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(30px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.9)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
      boxShadow: {
        'soc-sm': '0 1px 3px rgba(0, 0, 0, 0.5)',
        'soc-md': '0 4px 12px rgba(0, 0, 0, 0.6)',
        'soc-lg': '0 8px 24px rgba(0, 0, 0, 0.7)',
        'soc-overlay': '0 20px 40px rgba(0, 0, 0, 0.8)',
        'soc-glow': '0 0 30px rgba(230, 57, 70, 0.2)',
        'soc-glow-strong': '0 0 50px rgba(230, 57, 70, 0.35)',
      },
    },
  },
  plugins: [],
}
