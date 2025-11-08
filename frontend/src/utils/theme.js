/**
 * Theme Management Utility
 * Handles theme switching and persistence
 */

const THEME_STORAGE_KEY = 'app-theme';
const DEFAULT_THEME = 'dark';

// Get current theme
export const getTheme = () => {
  if (typeof window === 'undefined') return DEFAULT_THEME;
  
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  
  return stored || systemPreference || DEFAULT_THEME;
};

// Set theme
export const setTheme = (theme) => {
  if (typeof window === 'undefined') return;
  
  const validThemes = ['light', 'dark'];
  if (!validThemes.includes(theme)) {
    console.warn(`Invalid theme: ${theme}. Using default.`);
    theme = DEFAULT_THEME;
  }
  
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem(THEME_STORAGE_KEY, theme);
  
  // Dispatch custom event for theme change
  window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
};

// Toggle theme
export const toggleTheme = () => {
  const currentTheme = getTheme();
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  setTheme(newTheme);
  return newTheme;
};

// Initialize theme on load
export const initTheme = () => {
  if (typeof window === 'undefined') return;
  
  const theme = getTheme();
  setTheme(theme);
  
  // Listen for system theme changes
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  const handleSystemThemeChange = (e) => {
    if (!localStorage.getItem(THEME_STORAGE_KEY)) {
      setTheme(e.matches ? 'dark' : 'light');
    }
  };
  
  mediaQuery.addEventListener('change', handleSystemThemeChange);
  
  return () => {
    mediaQuery.removeEventListener('change', handleSystemThemeChange);
  };
};

// Get theme colors (for programmatic use)
export const getThemeColors = () => {
  if (typeof window === 'undefined') return {};
  
  const root = document.documentElement;
  const theme = getTheme();
  
  return {
    theme,
    bgPrimary: getComputedStyle(root).getPropertyValue('--bg-primary').trim(),
    bgSecondary: getComputedStyle(root).getPropertyValue('--bg-secondary').trim(),
    textPrimary: getComputedStyle(root).getPropertyValue('--text-primary').trim(),
    textSecondary: getComputedStyle(root).getPropertyValue('--text-secondary').trim(),
    accent: getComputedStyle(root).getPropertyValue('--accent').trim(),
    border: getComputedStyle(root).getPropertyValue('--border').trim(),
  };
};

export default {
  getTheme,
  setTheme,
  toggleTheme,
  initTheme,
  getThemeColors
};

