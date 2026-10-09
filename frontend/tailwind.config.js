/** Design tokens for Slither-Web: a plum board with mint (you), sun-yellow food and lilac mystery boxes. */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        page: "#0d0919",
        board: "#17102a",
        ink: "#efe9ff",
        muted: "#a094c6",
        you: "#4cf2c2",
        sun: "#ffd23f",
        lilac: "#b79cff",
        warn: "#ffb020",
        danger: "#ff3b5c",
        ice: "#9fe7ff",
      },
      fontFamily: {
        display: ["Unbounded", "Trebuchet MS", "sans-serif"],
        body: ["Figtree", "system-ui", "sans-serif"],
      },
      keyframes: {
        throb: { from: { opacity: "0.35" }, to: { opacity: "1" } },
        pop: { from: { transform: "translateY(-6px)", opacity: "0" } },
      },
      animation: {
        throb: "throb 0.6s ease-in-out infinite alternate",
        pop: "pop 0.18s ease-out",
      },
    },
  },
  plugins: [],
};
