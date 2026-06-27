/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        orbitron: ["Orbitron", "sans-serif"],
      },
      colors: {
        bg: "#060B18",
        panel: "#0C1426",
        panelBorder: "#1E293B",
        text: "#C5D0E6",
        textDim: "#5A7090",
        cyan: "#00D4FF",
        amber: "#FFB400",
        red: "#FF355E",
        purple: "#9B59FF",
        safe: "#00E676",
      }
    },
  },
  plugins: [],
}
