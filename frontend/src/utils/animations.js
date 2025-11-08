/**
 * Professional Animation Utilities
 * Enhanced animations for dark mode and smooth interactions
 */

// Fade in animation
export const fadeIn = (element, duration = 300, delay = 0) => {
  if (!element) return;
  
  element.style.opacity = '0';
  element.style.transform = 'translateY(20px)';
  element.style.transition = `opacity ${duration}ms ease-out, transform ${duration}ms ease-out`;
  
  setTimeout(() => {
    element.style.opacity = '1';
    element.style.transform = 'translateY(0)';
  }, delay);
};

// Slide in from direction
export const slideIn = (element, direction = 'left', duration = 400) => {
  if (!element) return;
  
  const directions = {
    left: 'translateX(-30px)',
    right: 'translateX(30px)',
    up: 'translateY(-30px)',
    down: 'translateY(30px)'
  };
  
  element.style.opacity = '0';
  element.style.transform = directions[direction] || directions.left;
  element.style.transition = `opacity ${duration}ms ease-out, transform ${duration}ms ease-out`;
  
  setTimeout(() => {
    element.style.opacity = '1';
    element.style.transform = 'translate(0, 0)';
  }, 10);
};

// Stagger animation for lists
export const staggerChildren = (container, delay = 100) => {
  if (!container) return;
  
  const children = Array.from(container.children);
  children.forEach((child, index) => {
    fadeIn(child, 300, index * delay);
  });
};

// Pulse animation
export const pulse = (element, duration = 1000) => {
  if (!element) return;
  
  element.style.animation = `pulse ${duration}ms ease-in-out infinite`;
};

// Glow effect (for dark mode)
export const glow = (element, color = null) => {
  if (!element) return;
  
  const theme = document.documentElement.getAttribute('data-theme');
  if (theme !== 'dark') return;
  
  const glowColor = color || getComputedStyle(document.documentElement)
    .getPropertyValue('--accent').trim();
  
  element.style.transition = 'box-shadow 0.3s ease';
  element.style.boxShadow = `0 0 10px ${glowColor}, 0 0 20px ${glowColor}`;
  
  return () => {
    element.style.boxShadow = '';
  };
};

// Number counter animation
export const animateNumber = (element, targetValue, duration = 2000, prefix = '', suffix = '') => {
  if (!element) return;
  
  const startValue = parseFloat(element.textContent.replace(/[^0-9.-]/g, '')) || 0;
  const startTime = performance.now();
  
  const animate = (currentTime) => {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // Easing function (ease-out)
    const easeOut = 1 - Math.pow(1 - progress, 3);
    const currentValue = startValue + (targetValue - startValue) * easeOut;
    
    element.textContent = `${prefix}${currentValue.toFixed(2)}${suffix}`;
    
    if (progress < 1) {
      requestAnimationFrame(animate);
    } else {
      element.textContent = `${prefix}${targetValue.toFixed(2)}${suffix}`;
    }
  };
  
  requestAnimationFrame(animate);
};

// Parallax effect
export const parallax = (element, speed = 0.5) => {
  if (!element) return;
  
  const handleScroll = () => {
    const scrolled = window.pageYOffset;
    const rate = scrolled * speed;
    element.style.transform = `translateY(${rate}px)`;
  };
  
  window.addEventListener('scroll', handleScroll);
  
  return () => {
    window.removeEventListener('scroll', handleScroll);
  };
};

// Intersection Observer for scroll animations
export const observeElements = (selector, callback, options = {}) => {
  const defaultOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px',
    ...options
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        callback(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, defaultOptions);
  
  const elements = document.querySelectorAll(selector);
  elements.forEach(el => observer.observe(el));
  
  return observer;
};

// Smooth reveal on scroll
export const revealOnScroll = (selector = '.reveal') => {
  observeElements(selector, (element) => {
    fadeIn(element, 500);
  });
};

// Ripple effect for buttons
export const createRipple = (event) => {
  const button = event.currentTarget;
  const circle = document.createElement('span');
  const diameter = Math.max(button.clientWidth, button.clientHeight);
  const radius = diameter / 2;
  
  const rect = button.getBoundingClientRect();
  circle.style.width = circle.style.height = `${diameter}px`;
  circle.style.left = `${event.clientX - rect.left - radius}px`;
  circle.style.top = `${event.clientY - rect.top - radius}px`;
  circle.classList.add('ripple');
  
  const ripple = button.getElementsByClassName('ripple')[0];
  if (ripple) {
    ripple.remove();
  }
  
  button.appendChild(circle);
  
  setTimeout(() => {
    circle.remove();
  }, 600);
};

// Add ripple effect to all buttons
export const addRippleToButtons = (selector = 'button, .btn') => {
  const buttons = document.querySelectorAll(selector);
  buttons.forEach(button => {
    button.addEventListener('click', createRipple);
  });
};

// Theme transition helper
export const themeTransition = (callback) => {
  document.documentElement.style.transition = 'background-color 0.3s ease, color 0.3s ease';
  callback();
  setTimeout(() => {
    document.documentElement.style.transition = '';
  }, 300);
};

// Initialize animations on page load
export const initAnimations = () => {
  // Reveal elements on scroll
  revealOnScroll();
  
  // Add ripple effects
  addRippleToButtons();
  
  // Fade in main content
  const mainContent = document.querySelector('main, #root > *');
  if (mainContent) {
    fadeIn(mainContent, 400);
  }
  
  // Stagger list items
  const lists = document.querySelectorAll('ul, ol');
  lists.forEach(list => {
    if (list.children.length > 0) {
      staggerChildren(list, 50);
    }
  });
};

// Export all
export default {
  fadeIn,
  slideIn,
  staggerChildren,
  pulse,
  glow,
  animateNumber,
  parallax,
  observeElements,
  revealOnScroll,
  createRipple,
  addRippleToButtons,
  themeTransition,
  initAnimations
};

