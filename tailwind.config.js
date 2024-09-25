/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/layouts/*"],
  theme: {
    extend: { 
      colors: {
        sage: {
          50: '#f3f9f7',
          100: '#e2f0eb',
          200: '#c3e0d8',
          300: '#a4d0c5',
          400: '#85c0b2',
          500: '#96ad9e', // DEFAULT
          600: '#7f9c8a',
          700: '#68877a',
          800: '#516d66',
          900: '#3a4a48', // dark variant
        },
        forest: {
          50: '#e8f1ef',
          100: '#c6d9d6',
          200: '#a4c1be',
          300: '#82a8a7',
          400: '#60908e',
          500: '#141619', // DEFAULT
          600: '#3a4a48', // dark variant
          700: '#2b3b39',
          800: '#1c2c2a',
          900: '#0d1d1c',
        },
        sky: {
          50: '#e4f4fa',
          100: '#b7e1ef',
          200: '#8bcde4',
          300: '#60b9d8',
          400: '#478fb0', // DEFAULT
          500: '#3e80a0',
          600: '#367194',
          700: '#2e617d',
          800: '#274f68',
          900: '#1e3d54',
        },
        sunset: {
          50: '#fef4f0',
          100: '#fce0d0',
          200: '#f9c4a8',
          300: '#f6a682',
          400: '#f27644', // DEFAULT
          500: '#e1683b',
          600: '#d05c31',
          700: '#b75127',
          800: '#9c4722',
          900: '#8a3d1e',
        },
        navy: {
          50: '#e0eff8',
          100: '#b3d5ea',
          200: '#85b9db',
          300: '#579bcf',
          400: '#478fb0', // same as sky
          500: '#1c527e', // DEFAULT
          600: '#164066',
          700: '#123352',
          800: '#0e2743',
          900: '#0a1b34',
        },
        // Functional colors
        primary: '#4b5e5b', // color-primary
        secondary: '#1E1F20', // color-secondary
        accent: '#f27644', // color-accent
        background: '#141619', // color-background
        text: '#f7efd3', // color-text
      },
    },
  },
  variants: {},
  plugins: [],
};
