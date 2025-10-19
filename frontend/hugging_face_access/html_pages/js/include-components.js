/**
 * HealthSync Component Loader
 * This script dynamically loads HTML components into pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Load all components with the data-component attribute
    const componentElements = document.querySelectorAll('[data-component]');
    
    componentElements.forEach(element => {
        const componentName = element.getAttribute('data-component');
        loadComponent(element, componentName);
    });
});

/**
 * Loads an HTML component into the specified element
 * @param {HTMLElement} element - The element to load the component into
 * @param {string} componentName - The name of the component file (without .html extension)
 */
async function loadComponent(element, componentName) {
    try {
        // Try to fetch from components directory first, then try html_pages/components as fallback
        let response = await fetch(`/components/${componentName}.html`);
        
        if (!response.ok) {
            // Try alternate path
            response = await fetch(`/html_pages/components/${componentName}.html`);
        }
        
        if (!response.ok) {
            // Try direct path as last resort
            response = await fetch(`components/${componentName}.html`);
        }
        
        if (!response.ok) {
            throw new Error(`Failed to load component: ${componentName}`);
        }
        
        const html = await response.text();
        element.innerHTML = html;
        
        // Execute any scripts in the component
        const scripts = element.querySelectorAll('script');
        scripts.forEach(script => {
            // Create a unique ID for each script to avoid duplicate variable declarations
            const scriptId = 'component-script-' + Math.random().toString(36).substr(2, 9);
            const newScript = document.createElement('script');
            newScript.id = scriptId;
            
            // Copy all attributes
            Array.from(script.attributes).forEach(attr => {
                if (attr.name !== 'id') { // Don't copy the original id
                    newScript.setAttribute(attr.name, attr.value);
                }
            });
            
            // Wrap the content in an IIFE to avoid variable collisions
            newScript.textContent = `(function() { ${script.textContent} })();`;
            
            // Replace the old script with the new one
            script.parentNode.replaceChild(newScript, script);
        });
    } catch (error) {
        console.error(error);
        element.innerHTML = `<div class="p-4 text-red-500">Error loading component: ${componentName}</div>`;
    }
}