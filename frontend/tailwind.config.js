/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: '#2E75B6',
        'primary-dark': '#1F3864',
        'primary-light': '#EEF4FB',
        success: '#1B7A3B',
        danger: '#C0392B',
        warning: '#E67E22',
        neutral: '#6B7280',
      },
      fontFamily: { sans: ['Inter', 'Roboto', 'sans-serif'] },
      borderRadius: { DEFAULT: '8px' },
      keyframes: {
        'slide-in': { '0%': { opacity:'0', transform:'translateX(100%)' }, '100%': { opacity:'1', transform:'translateX(0)' } }
      },
      animation: { 'slide-in': 'slide-in 0.3s ease-out' },
    },
  },
  plugins: [],
}
