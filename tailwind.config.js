/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/layouts/*", "./templates/pages/*"],
  theme: {
    extend: { 
      keyframes: {
        slideIn: {
          '0%': { transform: 'translatey(-100%)', opacity: '0' },
          '100%': { transform: 'translatey(0)', opacity: '1' },
        },
        },
        animation: {
          "slide-in": "slideIn 0.1s ease-out forwards"
        },

      fontFamily: {
      primary: ["Roboto"]
      },

      screens: {
       'xsm': '480px',
      },
      backgroundImage: {

        "login-bg": "url('/static/img/login-page/login-page-bg.jpg') !important",
        "login-bg-md": "url('/static/img/login-page/login-page-bg-tb.jpg') !important",
        "login-bg-sm": "url('/static/img/login-page/login-page-bg-m.jpg') !important",

        "register-bg": "url('/static/img/register-page/register-page-bg.jpg') !important",
        "register-bg-md": "url('/static/img/register-page/register-page-bg-tb.jpg') !important",
        "register-bg-sm": "url('/static/img/register-page/register-page-bg-m.jpg') !important",

        "forgot-username-bg": "url('/static/img/forgot-u-page/forgot-u-bg.jpg') !important",
        "forgot-username-bg-md": "url('/static/img/forgot-u-page/forgot-u-bg-tb.jpg') !important",
        "forgot-username-bg-sm": "url('/static/img/forgot-u-page/forgot-u-bg.jpg') !important",

        "forgot-p-bg": "url('/static/img/forgot-p-page/forgot-p-page-bg.jpg') !important",
        "forgot-p-bg-md": "url('/static/img/forgot-p-page/forgot-p-page-bg-tb.jpg') !important",
        "forgot-p-bg-sm": "url('/static/img/forgot-p-page/forgot-p-page-bg-m.jpg') !important",

        "reset-p-bg": "url('/static/img/reset-p-page/reset-p-bg.jpg') !important",
        "reset-p-bg-md": "url('/static/img/reset-p-page/reset-p-bg-tb.jpg') !important",
        "reset-p-bg-sm": "url('/static/img/reset-p-page/reset-p-bg-m.jpg') !important",
      },
      
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
        primary: '#cb5018', // color-primary
        secondary: '#0e2743', // color-secondary
        accent: '#13212E', // color-accent
        background: '#222222', // color-background
        text: '#f7efd3', // color-text
      },
    },
  },
  variants: {},
  plugins: [],
};
