# Theme Integration Guide

This guide explains how to integrate the new professional grayscale light theme and enhanced dark mode with animations into your React application.

## Features

- ✅ **Professional Grayscale Light Theme** - Clean, minimal, professional appearance
- ✅ **Enhanced Dark Mode** - Rich colors with glow effects and gradients
- ✅ **Smooth Animations** - Fade, slide, pulse, and ripple effects
- ✅ **Theme Persistence** - Remembers user preference
- ✅ **System Theme Detection** - Automatically detects OS theme preference

## Quick Start

### 1. Import Theme Styles

In your main entry file (e.g., `main.jsx` or `App.jsx`):

```jsx
import './styles/themes.css';
import './styles/animations.css';
import { initTheme, initAnimations } from './utils/theme';
import { initAnimations } from './utils/animations';

// Initialize on app start
initTheme();
initAnimations();
```

### 2. Add Theme Toggle Component

```jsx
import ThemeToggle from './components/ThemeToggle';

function App() {
  return (
    <div className="app">
      <header>
        <ThemeToggle />
      </header>
      {/* Your app content */}
    </div>
  );
}
```

### 3. Use Theme Variables in Your Components

```css
.my-component {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border);
}
```

## Available CSS Variables

### Background Colors
- `--bg-primary` - Main background
- `--bg-secondary` - Secondary background (cards, panels)
- `--bg-tertiary` - Tertiary background (hover states)

### Text Colors
- `--text-primary` - Main text
- `--text-secondary` - Secondary text
- `--text-tertiary` - Tertiary text (muted)

### Accent Colors
- `--accent` - Primary accent color
- `--accent-hover` - Accent hover state

### Borders & Shadows
- `--border` - Border color
- `--shadow` - Standard shadow
- `--shadow-lg` - Large shadow

### Status Colors
- `--success` - Success state
- `--danger` - Error/danger state
- `--warning` - Warning state
- `--info` - Info state

## Animation Utilities

### JavaScript Animations

```javascript
import { fadeIn, slideIn, staggerChildren, animateNumber } from './utils/animations';

// Fade in element
fadeIn(element, duration, delay);

// Slide in from direction
slideIn(element, 'left' | 'right' | 'up' | 'down', duration);

// Stagger children animation
staggerChildren(container, delay);

// Animate number counter
animateNumber(element, targetValue, duration, prefix, suffix);
```

### CSS Animation Classes

```html
<!-- Fade in -->
<div className="fade-in">Content</div>

<!-- Slide in -->
<div className="slide-in">Content</div>

<!-- Pulse -->
<div className="pulse">Content</div>

<!-- Reveal on scroll -->
<div className="reveal">Content</div>

<!-- Hover lift -->
<div className="hover-lift card">Card</div>
```

## Theme API

### Get Current Theme

```javascript
import { getTheme } from './utils/theme';

const currentTheme = getTheme(); // 'light' or 'dark'
```

### Set Theme

```javascript
import { setTheme } from './utils/theme';

setTheme('light'); // or 'dark'
```

### Toggle Theme

```javascript
import { toggleTheme } from './utils/theme';

const newTheme = toggleTheme(); // Returns 'light' or 'dark'
```

### Get Theme Colors

```javascript
import { getThemeColors } from './utils/theme';

const colors = getThemeColors();
// Returns: { theme, bgPrimary, bgSecondary, textPrimary, ... }
```

## Component Examples

### Card Component

```jsx
function Card({ children }) {
  return (
    <div className="card hover-lift">
      {children}
    </div>
  );
}
```

### Button Component

```jsx
function Button({ children, onClick }) {
  return (
    <button 
      className="btn btn-primary btn-press"
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```

### Animated List

```jsx
function AnimatedList({ items }) {
  return (
    <ul className="fade-in-stagger">
      {items.map((item, index) => (
        <li key={index} className="reveal">
          {item}
        </li>
      ))}
    </ul>
  );
}
```

## Dark Mode Enhancements

The dark mode includes special enhancements:

- **Gradient backgrounds** on cards
- **Glow effects** on interactive elements
- **Enhanced shadows** with accent colors
- **Smooth transitions** between states

These are automatically applied when `data-theme="dark"` is set on the HTML element.

## Light Mode (Grayscale)

The light mode uses a professional grayscale palette:

- Clean white backgrounds
- Subtle gray borders and shadows
- High contrast text for readability
- Minimal color accents

## Best Practices

1. **Always use CSS variables** instead of hardcoded colors
2. **Test both themes** during development
3. **Use animation utilities** for consistent animations
4. **Respect user preference** - don't force a theme
5. **Test accessibility** - ensure sufficient contrast in both themes

## Troubleshooting

### Theme not persisting
- Check that `localStorage` is available
- Verify theme initialization runs on page load

### Animations not working
- Ensure `initAnimations()` is called after DOM is ready
- Check that elements have the correct classes

### Colors not updating
- Verify `data-theme` attribute is set on `<html>` element
- Check that CSS variables are imported

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- IE11: ❌ Not supported (use polyfills if needed)

