/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.{html,js}","./assets/**/*.{html,js}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        
        primary: {
          100: '#c784e5', // Light green for message backgrounds
          400: '#bd61e7', // Soft Sky Blue
          500: '#9e55c0', // Navy Blue
          600: '#75418d', // Green accent
        },
        accent: {
          500: '#57B894',
          600: '#FF6B6B',
        },
        'custom-gray': {
          50: '#F8F9FA',
          100: '#E9ECEF',
          200: '#DEE2E6', // Added
          300: '#CED4DA', // Added for borders
          400: '#ADB5BD', // Added
          500: '#6C757D', // Added
          600: '#495057', // Added
          700: '#343A40', // Added
          800: '#212529', // Added
          900: '#333333',
        }
      },
      borderWidth: {
        '3': '3px', // For border-b-3
        '6': '6px'  // For border-b-6
      },
      // Dark mode variants for your custom colors
      darkMode: {
        colors: {
          'custom-gray': {
            50: '#1a1a1a', // Dark background
            100: '#2d2d2d', // Dark borders
            900: '#e5e5e5', // Light text
          }
        }
      },
      maxWidth: {
        xxs: "18rem",
        '3xs': "15rem", // Renamed for Tailwind consistency
      },
      ringColor: {
        DEFAULT: 'hsl(245, 34%, 41%)'
      },
      screens: {
        'xs': '420px',
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px'
      },
      animation: {
        'infinite-scroll': 'infinite-scroll 25s linear infinite',
      },
      keyframes: {
        'infinite-scroll': {
          from: { transform: 'translateX(0)' },
          to: { transform: 'translateX(-100%)' },
        }
      },
      fontFamily: {
        sans: ["Anjoman", "sans-serif"] , // Unified font family declaration
        Farsan: ["Farsan", "sans-serif"]  // Unified font family declaration
      },
      spacing: {
        18: '4.5rem',
        15: '3.75rem'
      },
      container: {
        center: true,
        padding: '1rem',
        screens: {
          sm: '100%',
          md:'430px',
          lg: '1024px',
          xl: '1280px'
        }
      },
    },
  },
  plugins: [
    require('tailwindcss-animated'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/container-queries')
  ],
}