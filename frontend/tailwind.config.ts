import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#05070b",
        panel: "#0b111c",
        panel2: "#111827",
        line: "rgba(255,255,255,0.10)",
        cyan: "#22d3ee",
        blue: "#60a5fa"
      },
      boxShadow: {
        soft: "0 24px 80px rgba(0,0,0,0.35)"
      }
    }
  },
  plugins: []
};

export default config;
