/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // 深色主题背景
        bg: {
          primary: '#0a0a0b',
          secondary: '#141415',
          tertiary: '#1c1c1e',
          elevated: '#242426',
        },
        // 文字颜色
        text: {
          primary: '#ffffff',
          secondary: '#a1a1aa',
          tertiary: '#71717a',
        },
        // 强调色（蓝紫渐变）
        accent: {
          primary: 'hsl(262 83% 58%)', // #8b5cf6
          hover: 'hsl(262 90% 65%)',
          muted: 'hsl(262 80% 50%)',
        },
        // 边框
        border: {
          default: '#27272a',
          hover: '#3f3f46',
        },
      },
      backgroundImage: {
        'accent-gradient': 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        display: ['Satoshi', 'Plus Jakarta Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
