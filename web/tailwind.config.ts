import type { Config } from "tailwindcss";

export default {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      animation: {
        'door-opening': 'doorOpen 7s linear forwards',
        'door-closing': 'doorClose 7s linear forwards',
      },
      keyframes: {
        doorOpen: {
          '0%': { height: '100%' },
          '100%': { height: '10%' },
        },
        doorClose: {
          '0%': { height: '10%' },
          '100%': { height: '100%' },
        },
      },
      transitionDuration: {
        '7000': '7000ms',
      },
    },
  },
  plugins: [],
} satisfies Config;
