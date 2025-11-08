/**
 * Main Entry Point
 * Initializes theme and animations
 */

import { initTheme } from './utils/theme';
import { initAnimations } from './utils/animations';
import './styles/themes.css';
import './styles/animations.css';

// Initialize theme on load
if (typeof window !== 'undefined') {
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initTheme();
      initAnimations();
    });
  } else {
    initTheme();
    initAnimations();
  }
  
  // Re-initialize animations when React mounts (if using React)
  window.addEventListener('load', () => {
    setTimeout(() => {
      initAnimations();
    }, 100);
  });
}

export { initTheme, initAnimations };

