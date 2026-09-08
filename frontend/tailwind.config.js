/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Customize zinc background for dark mode to match the design specifications
        zinc: {
          950: '#09090b',
        }
      }
    },
  },
  plugins: [],
}
