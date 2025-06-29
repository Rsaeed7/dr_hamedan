# IRANSansWeb Local Fonts Implementation

## Overview
This document describes the implementation of local IRANSansWeb fonts in the Dr. Turn project, replacing external font dependencies with locally hosted font files.

## What Was Done

### 1. Font Files Structure
The project now uses the following IRANSansWeb font files located in `static/css/fonts/`:
- **IRANSansWeb.ttf/woff/woff2/eot** - Regular (400)
- **IRANSansWeb_Light.ttf/woff/woff2/eot** - Light (300)
- **IRANSansWeb_Medium.ttf/woff/woff2/eot** - Medium (500)
- **IRANSansWeb_Bold.ttf/woff/woff2/eot** - Bold (700)
- **IRANSansWeb_UltraLight.ttf/woff/woff2/eot** - Ultra Light (200)

### 2. CSS Font Definitions
Created `fonts.css` files in both `assets/css/` and `static/css/` directories containing:
- `@font-face` declarations for all font weights
- Cross-browser compatibility (WOFF2, WOFF, TTF, EOT)
- `font-display: swap` for better performance
- Consistent font-family declarations for all elements

### 3. Template Updates
Updated `templates/base.html`:
- ✅ Removed the TODO comment about using assets fonts
- ✅ Added link to `fonts.css` stylesheet
- ✅ Updated body font-family from 'Vazirmatn' to 'IRANSansWeb'

### 4. Font Weight Classes
Added utility classes for different font weights:
```css
.font-ultra-light { font-weight: 200; }
.font-light { font-weight: 300; }
.font-regular { font-weight: 400; }
.font-medium { font-weight: 500; }
.font-bold { font-weight: 700; }
```

### 5. Persian Text Optimization
- Added `.persian-text` class for RTL text with proper font settings
- Updated all heading elements (h1-h6) to use IRANSansWeb
- Added font smoothing for better rendering

## How to Use

### Basic Usage
All text will automatically use IRANSansWeb font family. No additional classes needed for basic text.

### Font Weights
Use the provided classes to control font weight:
```html
<p class="font-light">متن نازک</p>
<p class="font-regular">متن معمولی</p>
<p class="font-medium">متن متوسط</p>
<p class="font-bold">متن ضخیم</p>
<p class="font-ultra-light">متن خیلی نازک</p>
```

### Persian Text
For guaranteed RTL layout and proper Persian text handling:
```html
<div class="persian-text">
    <p>این متن فارسی با تنظیمات بهینه نمایش داده می‌شود</p>
</div>
```

### Headings
All headings automatically use appropriate font weights:
- h1, h2: Bold (700)
- h3, h4: Medium (500)
- h5, h6: Regular (400)

## Testing
A test page has been created to verify font loading:
- **URL**: `/doctors/test-fonts/`
- **Template**: `templates/test_fonts.html`
- **Purpose**: Visual verification of all font weights and styles

### How to Test
1. Start the Django development server
2. Visit `http://localhost:8000/doctors/test-fonts/`
3. Check browser console for font loading status
4. Visually verify different font weights are displaying correctly

## Browser Support
The font implementation supports:
- ✅ Modern browsers (Chrome, Firefox, Safari, Edge)
- ✅ Internet Explorer 9+
- ✅ Mobile browsers (iOS Safari, Android Chrome)

## File Structure
```
project/
├── assets/css/
│   └── fonts.css                 # Development font definitions
├── static/css/
│   ├── fonts.css                 # Production font definitions
│   └── fonts/                    # Font files directory
│       ├── IRANSansWeb.ttf
│       ├── IRANSansWeb.woff
│       ├── IRANSansWeb.woff2
│       ├── IRANSansWeb.eot
│       └── ... (all other weights)
└── templates/
    ├── base.html                 # Updated with font imports
    └── test_fonts.html           # Font testing page
```

## Performance Considerations
- **Font Display**: Uses `font-display: swap` for better loading performance
- **Format Priority**: WOFF2 → WOFF → TTF → EOT for optimal compression
- **Local Loading**: No external font requests, improving page load speed
- **Browser Caching**: Font files are cached by browsers for subsequent visits

## Fallback Fonts
Font stack includes fallbacks:
```css
font-family: 'IRANSansWeb', 'Tahoma', 'Arial', sans-serif;
```

If IRANSansWeb fails to load, the browser will fall back to:
1. Tahoma (good Persian support)
2. Arial (standard fallback)
3. Generic sans-serif

## Troubleshooting

### Fonts Not Loading
1. Check browser console for 404 errors
2. Verify `python manage.py collectstatic` has been run
3. Ensure font files exist in `static/css/fonts/` directory
4. Check MIME types are configured for font files on server

### Font Weights Not Working
1. Verify font files for specific weights exist
2. Check CSS font-weight values match @font-face declarations
3. Test in browser developer tools

### RTL Issues
1. Ensure `dir="rtl"` is set on html element
2. Use `.persian-text` class for guaranteed RTL layout
3. Check CSS direction and text-align properties

## Maintenance
- Font files should be kept in sync between `assets/` and `static/` directories
- Update `fonts.css` if new font weights are added
- Run `collectstatic` after any font file changes
- Test font loading after any CSS changes

## Benefits of Local Fonts
1. **Performance**: No external HTTP requests
2. **Reliability**: No dependency on external CDNs
3. **Privacy**: No tracking by font providers
4. **Offline**: Works without internet connection
5. **Control**: Full control over font versions and updates 