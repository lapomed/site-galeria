/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../../templates/**/*.html',
    '../../**/templates/**/*.html',
    '../../core/templates/**/*.html',
    '../../**/*.py',
    './src/**/*.js',
    './node_modules/flowbite/**/*.js',
  ],
  theme: {
    extend: {
      fontFamily: {
        'serif': ['Cinzel', 'serif'],
        'sans': ['Lato', 'sans-serif'],
      },
      colors: {
        'lapomed-gold': '#f0c300',
      }
    },
  },
  plugins: [
    require('flowbite/plugin'),
    require('daisyui'),
  ],
}
