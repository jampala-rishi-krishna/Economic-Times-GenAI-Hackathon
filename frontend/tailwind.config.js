/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#FFFFFF',
        'bg-secondary': '#F8FAFC',
        'bg-tertiary': '#F1F5F9',
        'accent-blue': '#2563EB',
        'accent-violet': '#7C3AED',
        'accent-success': '#059669',
        'accent-warning': '#D97706',
        'accent-danger': '#DC2626',
        'accent-gold': '#B45309',
      },
      fontFamily: {
        'mono': ['"JetBrains Mono"', '"Space Mono"', 'monospace'],
        'display': ['"Space Mono"', 'monospace'],
        'sans': ['"DM Sans"', 'sans-serif'],
      },
      boxShadow: {
        'glow-blue': '0 0 20px rgba(37, 99, 235, 0.15)',
        'glow-violet': '0 0 20px rgba(124, 58, 237, 0.15)',
        'glow-success': '0 0 20px rgba(5, 150, 105, 0.15)',
        'glow-danger': '0 0 20px rgba(220, 38, 38, 0.15)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'fade-up': 'fadeUp 0.4s ease-out',
        'count-up': 'countUp 0.8s ease-out',
        'scan': 'scan 2s linear infinite',
        'breathe': 'breathe 2s ease-in-out infinite',
      },
      keyframes: {
        slideInRight: {
          '0%': { transform: 'translateX(20px)', opacity: 0 },
          '100%': { transform: 'translateX(0)', opacity: 1 },
        },
        fadeUp: {
          '0%': { transform: 'translateY(10px)', opacity: 0 },
          '100%': { transform: 'translateY(0)', opacity: 1 },
        },
        scan: {
          '0%': { backgroundPosition: '0% 0%' },
          '100%': { backgroundPosition: '0% 100%' },
        },
        breathe: {
          '0%, 100%': { opacity: 1, transform: 'scale(1)' },
          '50%': { opacity: 0.5, transform: 'scale(0.95)' },
        }
      }
    },
  },
  plugins: [],
}
