/** @type {import('tailwindcss').Config} */
const v = (name) => `rgb(var(--${name}) / <alpha-value>)`;
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: ["class", '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        bg: v("bg"), panel: v("panel"), panel2: v("panel2"), line: v("line"),
        ink: v("ink"), sub: v("sub"), faint: v("faint"),
        brand: v("brand"), brand2: v("brand2"),
        good: v("good"), warn: v("warn"), bad: v("bad"), info: v("info"),
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["'Space Grotesk'", "Inter", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 1px 0 rgb(255 255 255 / 0.03) inset, 0 8px 24px -12px rgb(0 0 0 / 0.35)",
        glow: "0 0 0 1px rgb(var(--brand) / 0.35), 0 8px 30px -8px rgb(var(--brand) / 0.45)",
      },
      keyframes: {
        rise: { from: { opacity: 0, transform: "translateY(6px)" }, to: { opacity: 1, transform: "none" } },
        shimmer: { "0%": { backgroundPosition: "-400px 0" }, "100%": { backgroundPosition: "400px 0" } },
        pulseDot: { "0%,100%": { opacity: 1 }, "50%": { opacity: 0.35 } },
      },
      animation: {
        rise: "rise .35s ease-out both",
        shimmer: "shimmer 1.4s linear infinite",
        pulseDot: "pulseDot 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
