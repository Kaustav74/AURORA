/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        space: {
          900: '#060913',
          800: '#0b1120',
          700: '#111b33',
          600: '#182747',
          500: '#233863',
        },
        telemetry: {
          cyan: '#00f0ff',
          green: '#00ff88',
          amber: '#ffaa00',
          red: '#ff3344',
          purple: '#9d4edd',
        }
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      }
    },
  },
  plugins: [],
}
