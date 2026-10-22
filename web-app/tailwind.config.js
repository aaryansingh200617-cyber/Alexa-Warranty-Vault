/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: '#131921', charcoal: '#232F3E', brand: '#FF9900', ai: '#00C8E8',
        canvas: '#F7F8FA', slate: '#667085', line: '#E5E7EB',
        ok: '#16803C', warn: '#B45309', bad: '#C62828',
      },
      fontFamily: { sans: ['"Amazon Ember"', 'Inter', 'system-ui', 'sans-serif'] },
      keyframes: {
        ring: { '0%': { transform: 'scale(1)', opacity: '.55' }, '100%': { transform: 'scale(1.9)', opacity: '0' } },
        dots: { '0%,80%,100%': { opacity: '.25' }, '40%': { opacity: '1' } },
      },
      animation: { ring: 'ring 1.4s ease-out infinite', dots: 'dots 1.2s infinite' },
    },
  },
  plugins: [],
}
