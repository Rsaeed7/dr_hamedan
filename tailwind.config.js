/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./templates/**/*.{html,js}",
        "./*/templates/**/*.{html,js}",
        "./assets/js/**/*.js",
        "./static/js/**/*.js",
        "./**/templates/**/*.{html,js}"
    ],
    theme: {
        extend: {
            maxWidth: {
                xxs: "18rem",
                lxxs: "15rem",
            },
            colors: {
                // Legacy colors
                main: "rgb(77, 68, 139)",
                btnblue: "rgb(168, 242, 254)",
                btnpurple: "rgb(77, 70, 140)",
                
                // Bootstrap-compatible colors (from homepage usage)
                info: {
                    DEFAULT: '#17a2b8',
                    50: '#e5f7f9',
                    100: '#bee5eb',
                    200: '#abdde5',
                    300: '#7dd3dd',
                    400: '#4fc3d2',
                    500: '#17a2b8',
                    600: '#138496',
                    700: '#117a8b',
                    800: '#10707f',
                    900: '#0c5460'
                },
                success: {
                    DEFAULT: '#28a745',
                    50: '#d4edda',
                    100: '#c3e6cb',
                    200: '#b1dfbb',
                    300: '#7bc881',
                    400: '#51b865',
                    500: '#28a745',
                    600: '#218838',
                    700: '#1e7e34',
                    800: '#1c7430',
                    900: '#155724'
                },
                warning: {
                    DEFAULT: '#ffc107',
                    50: '#fff3cd',
                    100: '#ffeeba',
                    200: '#ffe8a1',
                    300: '#ffdc7a',
                    400: '#ffd653',
                    500: '#ffc107',
                    600: '#e0a800',
                    700: '#d39e00',
                    800: '#c69500',
                    900: '#856404'
                },
                danger: {
                    DEFAULT: '#dc3545',
                    50: '#f8d7da',
                    100: '#f5c6cb',
                    200: '#f1b0b7',
                    300: '#ec7d88',
                    400: '#e74a5c',
                    500: '#dc3545',
                    600: '#c82333',
                    700: '#bd2130',
                    800: '#b21f2d',
                    900: '#721c24'
                },
                secondary: {
                    DEFAULT: '#6c757d',
                    50: '#f8f9fa',
                    100: '#e9ecef',
                    200: '#dee2e6',
                    300: '#ced4da',
                    400: '#adb5bd',
                    500: '#6c757d',
                    600: '#545b62',
                    700: '#495057',
                    800: '#343a40',
                    900: '#212529'
                },
                dark: {
                    DEFAULT: '#343a40',
                    50: '#f8f9fa',
                    100: '#e9ecef',
                    200: '#dee2e6',
                    300: '#ced4da',
                    400: '#adb5bd',
                    500: '#6c757d',
                    600: '#495057',
                    700: '#343a40',
                    800: '#23272b',
                    900: '#1d2124'
                },
                light: {
                    DEFAULT: '#f8f9fa',
                    50: '#ffffff',
                    100: '#f8f9fa',
                    200: '#e9ecef',
                    300: '#dee2e6',
                    400: '#ced4da',
                    500: '#adb5bd',
                    600: '#6c757d',
                    700: '#495057',
                    800: '#343a40',
                    900: '#212529'
                },
                
                // Dr. Hamedan custom colors
                'dr-primary': {
                    DEFAULT: '#263189',
                    50: '#e8eaf7',
                    100: '#c5ccec',
                    200: '#a1ade0',
                    300: '#7d8ed4',
                    400: '#596fc8',
                    500: '#263189',
                    600: '#1f2a7a',
                    700: '#19236b',
                    800: '#121c5c',
                    900: '#0c154d'
                },
                'dr-secondary': '#71dd8a',
                'dr-tertiary': '#3f4079',
                'dr-blue': 'rgba(36, 76, 154, 0.55)',
                'dr-turquoise': 'rgb(100, 250, 255)',
                
                // Light background variants
                'light-green': '#e0f9df',
                'light-blue': '#e5f1f9',
                'light-violet': '#f6ecfb',
                'light-yellow': '#f8ffc7',
                'light-blue2': 'rgba(187, 231, 243, 0.73)',
                'light-red': 'rgba(253, 154, 154, 0.8)',
                'bluelight': 'rgba(239, 251, 252, 0.47)',
                
                // Gradient colors
                'gradient-start': 'rgba(255, 255, 255, 0.03)',
                'gradient-middle': 'rgba(144, 185, 227, 0.03)',
                'gradient-end': 'rgba(36, 76, 154, 0.11)',
            },
            screens: {
                sm: "420px",
                md: "500px",
                lg: "768px",
                xlg: "900px",
                xl: "1180px",
                "2xl": "1280px",
                "3xl": "1536px",
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
                // Persian fonts - IRANSansWeb family
                'iran-sans': ['IRANSansWeb', 'Tahoma', 'Arial', 'sans-serif'],
                'primary': ['IRANSansWeb', 'Tahoma', 'Arial', 'sans-serif'],
                'persian': ['IRANSansWeb', 'Tahoma', 'Arial', 'sans-serif'],
                
                // Keep existing fonts if needed
                moasser: ["moasser"],
                shabnam: ["shabnam"],
                
                // Override default sans with Persian fonts
                'sans': ['IRANSansWeb', 'ui-sans-serif', 'system-ui', 'sans-serif'],
                'serif': ['ui-serif', 'Georgia', 'Cambria', 'Times New Roman', 'Times', 'serif'],
                'mono': ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
            },
            fontWeight: {
                'ultra-light': '200',
                'light': '300',
                'normal': '400',
                'medium': '500',
                'semibold': '600',
                'bold': '700',
                'extrabold': '800',
                'black': '900',
            },
            container: {
                center: true,
                padding: {
                    DEFAULT: '1rem',
                    sm: '2rem',
                    lg: '4rem',
                    xl: '5rem',
                    '2xl': '6rem',
                },
            },
            spacing: {
                '18': '4.5rem',
                '88': '22rem',
                '128': '32rem',
                '144': '36rem',
                
                // Custom project spacing
                '50': '12.5rem',    // 200px
                '60': '15rem',      // 240px
                '120': '30rem',     // 480px
                '150': '37.5rem',   // 600px
                
                // Homepage specific spacing
                'margin-60-35': '3.75rem', // 60px top, 35px bottom equivalent
                'margin-50-35': '3.125rem', // 50px top, 35px bottom equivalent
                'margin-120-95': '7.5rem',  // 120px top, 95px bottom equivalent
                'margin-30-20': '1.875rem', // 30px top, 20px bottom equivalent
            },
            fontSize: {
                '2xs': ['0.625rem', { lineHeight: '0.75rem' }],
                '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
                '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
                '5xl': ['3rem', { lineHeight: '1' }],
                '6xl': ['3.75rem', { lineHeight: '1' }],
                '7xl': ['4.5rem', { lineHeight: '1' }],
                '8xl': ['6rem', { lineHeight: '1' }],
                '9xl': ['8rem', { lineHeight: '1' }],
            },
            
            // Background gradients
            backgroundImage: {
                'gradient-custom': 'linear-gradient(to bottom, rgba(255, 255, 255, 0.03), rgba(144, 185, 227, 0.03))',
                'gradient-custom2': 'linear-gradient(to bottom, rgba(144, 185, 227, 0.03), rgba(255, 255, 255, 0.04))',
                'gradient-custom3': 'linear-gradient(to bottom, rgba(255, 255, 255, 0.01), rgba(36, 76, 154, 0.11))',
                'article-bg': 'rgba(73, 158, 102, 0.8)',
                'dr-bg': '#384291',
                'aside-border': 'linear-gradient(to bottom, rgba(214, 224, 238, 0.14), rgba(255, 255, 255, 0.04))',
            },
            
            // Border radius variations
            borderRadius: {
                '5': '5px',
                '10': '10px',
                '20': '20px',
                '50': '50%',
                'custom': '0.25rem',
            },
            
            // Box shadows
            boxShadow: {
                'custom': '0px 0px 15px 0px rgba(0, 0, 0, 0.05)',
                'hover': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
                'story': '0 -2px 5px rgba(0, 0, 0, 0.1)',
            },
            
            // Transform utilities
            transform: {
                'translate-hover': 'translateY(5px)',
                'translate-center': 'translate(-50%, -50%)',
            },
            
            // Animation durations
            transitionDuration: {
                '300': '300ms',
                '600': '600ms',
            },
            
            // Z-index scale
            zIndex: {
                '1000': '1000',
                '2': '2',
            },
            
            // Minimum widths
            minWidth: {
                '200': '200px',
                '280': '280px',
            },
            
            // Maximum heights
            maxHeight: {
                '250': '250px',
                '300': '300px',
            },
        },
    },
    plugins: [
        require('tailwindcss-animated'),
    ],
    // RTL support
    future: {
        hoverOnlyWhenSupported: true,
    },
}