/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#effaf9",
          100: "#d8f3f0",
          500: "#1b9aaa",
          600: "#147d8b",
          700: "#0f6470",
        },
        clinic: {
          50: "#f5fbff",
          100: "#e5f4ff",
          500: "#2f80ed",
          700: "#1559b7",
        },
        leaf: {
          50: "#f1fbf5",
          100: "#dcf6e6",
          500: "#31a66a",
          700: "#207847",
        },
      },
      boxShadow: {
        soft: "0 16px 45px rgba(15, 100, 112, 0.10)",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};

