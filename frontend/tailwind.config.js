/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        industrial: {
          bg: '#0B0F17',
          surface: '#111827',
          card: '#1F2937',
          panel: '#1E293B',
          border: '#334155',
          accent: '#0284C7',
          accentHover: '#0369A1',
          warning: '#F59E0B',
          danger: '#EF4444',
          success: '#10B981',
          cyan: '#06B6D4',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Consolas', 'Courier New', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
