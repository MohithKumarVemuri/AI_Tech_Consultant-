/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        card: "var(--card)",
        ink: "var(--ink)",
        "ink-soft": "var(--ink-soft)",
        line: "var(--line)",
        emerald: {
          DEFAULT: "var(--emerald)",
          deep: "var(--emerald-deep)",
          soft: "var(--emerald-soft)",
        },
      },
    },
  },
  plugins: [],
};
