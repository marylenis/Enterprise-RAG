/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.html",
    "./pages/**/*.html"
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "primary": "#00d0ff",
        "secondary": "#9D4EDD",
        "accent-pink": "#FF007A",
        "tertiary": "#10B981",
        "background-light": "#f2f5f8",
        "background-dark": "#0a0e29",
        "cyber-pink": "#ff2d85",
        "cyber-pink-soft": "rgba(255, 45, 133, 0.15)",
        "cyber-green": "#00ff9d",
        "cyber-orange": "#ffaa00",
        "surface-dark": "#161b3d",
        "panel-dark": "rgba(32, 67, 75, 0.2)",
        "cyber-card": "rgba(255, 255, 255, 0.03)",
        "cyber-border": "rgba(0, 208, 255, 0.2)"
      },
      fontFamily: {
        "display": ["Space Grotesk", "sans-serif"]
      },
      borderRadius: {
        "DEFAULT": "0.5rem",
        "lg": "1rem", 
        "xl": "1.5rem",
        "full": "9999px"
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 3s infinite',
        'glow': 'glow 3s ease-in-out infinite alternate'
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 10px rgba(0, 208, 255, 0.3)' },
          '100%': { boxShadow: '0 0 20px rgba(255, 0, 122, 0.6)' }
        }
      }
    },
  },
  plugins: [],
}