/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#F6F8FB",
        surface: "#FFFFFF",
        ink: "#172033",
        muted: "#667085",
        border: "#E4E7EC",
        brand: {
          DEFAULT: "#2563EB",
          50: "#EFF4FF",
          600: "#2563EB",
          700: "#1D4ED8",
        },
        teal: {
          DEFAULT: "#0F9D8A",
          50: "#E7F6F3",
        },
        risk: {
          DEFAULT: "#E45756",
          50: "#FEECEC",
        },
        warn: {
          DEFAULT: "#F59E0B",
          50: "#FEF3E2",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      borderRadius: {
        card: "8px",
        btn: "6px",
      },
    },
  },
  plugins: [],
};