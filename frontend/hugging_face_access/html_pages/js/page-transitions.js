// Page Transitions Handler

document.addEventListener('DOMContentLoaded', () => {
  // Add page transition class to main content
  const mainContent = document.querySelector('main');
  if (mainContent) {
    mainContent.classList.add('page-transition');
  }

  // Create overlay element for transitions
  const overlay = document.createElement('div');
  overlay.classList.add('page-transition-overlay');
  document.body.appendChild(overlay);

  // Handle all navigation links
  document.querySelectorAll('a[href]:not([href^="#"]):not([href^="javascript:"]):not([target])').
    forEach(link => {
      link.addEventListener('click', (e) => {
        // Only handle internal links
        const href = link.getAttribute('href');
        if (href.startsWith('http') || href.startsWith('//')) {
          return; // External link, let it behave normally
        }

        e.preventDefault();
        const targetUrl = link.href;

        // Show transition overlay
        overlay.classList.add('active');

        // Navigate after transition
        setTimeout(() => {
          window.location.href = targetUrl;
        }, 300);
      });
    });
});

// Add fade-in effect when page loads
window.addEventListener('load', () => {
  // Hide any loading indicators
  const overlay = document.querySelector('.page-transition-overlay');
  if (overlay) {
    overlay.classList.remove('active');
  }
});