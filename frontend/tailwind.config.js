/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["Figtree", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      colors: {
        forest: {
          950: "#0c1a12",
          900: "#12241a",
          800: "#1a3326",
          700: "#234536",
          600: "#2d5c46",
          500: "#3a7458",
        },
        emerald: {
          800: "#1a5c3d",
          700: "#1f6b48",
          600: "#2a8a5c",
          500: "#3a9d6e",
          400: "#5bb888",
          100: "#dcefe4",
        },
        sage: {
          50: "#f3f6f1",
          100: "#e8efe6",
          200: "#d4e0d0",
          400: "#8aa88a",
          600: "#5c7a5c",
          700: "#486148",
        },
        olive: {
          400: "#9aaa58",
          500: "#7a8b3e",
          700: "#5a6a2e",
        },
        cream: {
          50: "#fffcf7",
          100: "#f7f3e8",
          200: "#efe8d4",
          300: "#e4d9bc",
        },
        gold: {
          300: "#e2cc8e",
          400: "#d4b36a",
          500: "#c4a35a",
          600: "#a88840",
        },
        charcoal: {
          600: "#5c5850",
          700: "#3f3c36",
          800: "#2c2a26",
          900: "#1a1916",
        },
        alert: {
          DEFAULT: "#b42318",
          soft: "#fde8e6",
        },
      },
      boxShadow: {
        panel: "0 18px 50px -24px rgba(18, 36, 26, 0.35)",
        gold: "0 0 0 1px rgba(196, 163, 90, 0.35)",
      },
      borderRadius: {
        organ: "1.75rem",
      },
      keyframes: {
        "scan-line": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(180px)" },
        },
        breathe: {
          "0%, 100%": { opacity: "0.55" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        "scan-line": "scan-line 2.4s ease-in-out infinite",
        breathe: "breathe 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
