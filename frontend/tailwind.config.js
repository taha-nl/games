/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        space: {
          900: '#050810',
          800: '#0a0e1a',
          700: '#0f1629',
          600: '#1a2040',
          500: '#252d55',
        },
        neon: {
          green:  '#00ff88',
          blue:   '#00d4ff',
          purple: '#bf5fff',
          orange: '#ff6b35',
          pink:   '#ff3d9a',
        },
      },
      fontFamily: {
        space: ['"Exo 2"', 'sans-serif'],
      },
      animation: {
        twinkle:         'twinkle var(--duration, 3s) ease-in-out infinite',
        float:           'float 3s ease-in-out infinite',
        'pulse-glow':    'pulse-glow 2s ease-in-out infinite',
        'score-flash':   'score-flash 1s ease-out',
        'freeze-pulse':  'freeze-pulse 1.5s ease-in-out infinite',
        'slide-down':    'slide-down 0.5s ease-out',
        'progress-glow': 'progress-glow 2s ease-in-out infinite',
        'toast-in':      'toast-in 0.3s ease-out',
        'toast-out':     'toast-out 0.3s ease-in forwards',
      },
      keyframes: {
        twinkle: {
          '0%, 100%': { opacity: '0.2', transform: 'scale(1)' },
          '50%':      { opacity: '1',   transform: 'scale(1.3)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-10px)' },
        },
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 5px currentColor' },
          '50%':      { boxShadow: '0 0 20px currentColor, 0 0 40px currentColor' },
        },
        'score-flash': {
          '0%':   { backgroundColor: 'transparent' },
          '30%':  { backgroundColor: 'rgba(0, 255, 136, 0.3)' },
          '100%': { backgroundColor: 'transparent' },
        },
        'freeze-pulse': {
          '0%, 100%': { borderColor: '#60a5fa' },
          '50%':      { borderColor: '#93c5fd', boxShadow: '0 0 15px #60a5fa' },
        },
        'slide-down': {
          from: { transform: 'translateY(-100%)', opacity: '0' },
          to:   { transform: 'translateY(0)',     opacity: '1' },
        },
        'progress-glow': {
          '0%, 100%': { opacity: '0.8' },
          '50%':      { opacity: '1', filter: 'brightness(1.2)' },
        },
        'toast-in': {
          from: { transform: 'translateX(100%)', opacity: '0' },
          to:   { transform: 'translateX(0)',    opacity: '1' },
        },
        'toast-out': {
          from: { transform: 'translateX(0)',    opacity: '1' },
          to:   { transform: 'translateX(100%)', opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}
