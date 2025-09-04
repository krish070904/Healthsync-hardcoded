/**
 * HealthSync Health Consultation Module
 * 
 * This module handles the health consultation functionality, including loading and displaying
 * consultation data, food-symptom correlations, and health tips.
 */

// Configuration
const CONFIG = {
    // API endpoints
    API: {
        CONSULTATION: '/consultation/user/',
        CORRELATIONS: '/consultation/user/',
        HEALTH_TIPS: '/consultation/health-tips/'
    },
    // DOM element IDs
    ELEMENTS: {
        CONSULTATION: {
            LOADING: 'consultation-loading',
            CONTENT: 'consultation-content',
            ERROR: 'consultation-error'
        },
        CORRELATIONS: {
            LOADING: 'correlations-loading',
            CONTENT: 'correlations-content',
            ERROR: 'correlations-error'
        },
        HEALTH_TIPS: {
            CATEGORY: 'health-tip-category',
            CONTENT: 'health-tips-content'
        }
    }
};

// State management
const STATE = {
    userId: null,
    consultation: null,
    correlations: null,
    healthTips: {}
};

/**
 * Initialize the health consultation module
 */
function initHealthConsultation() {
    // Get user ID from session storage or URL parameter
    STATE.userId = sessionStorage.getItem('userId') || getUrlParameter('userId');
    
    if (!STATE.userId) {
        showError(CONFIG.ELEMENTS.CONSULTATION.ERROR, 'User ID not found. Please log in again.');
        showError(CONFIG.ELEMENTS.CORRELATIONS.ERROR, 'User ID not found. Please log in again.');
        return;
    }
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial data
    loadConsultation();
    loadCorrelations();
    loadHealthTips('nutrition'); // Load default health tips category
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Health tips category selection
    const categorySelect = document.getElementById(CONFIG.ELEMENTS.HEALTH_TIPS.CATEGORY);
    if (categorySelect) {
        categorySelect.addEventListener('change', (e) => {
            loadHealthTips(e.target.value);
        });
    }
}

/**
 * Load health consultation data
 */
async function loadConsultation() {
    showLoading(CONFIG.ELEMENTS.CONSULTATION.LOADING);
    hideElement(CONFIG.ELEMENTS.CONSULTATION.CONTENT);
    hideElement(CONFIG.ELEMENTS.CONSULTATION.ERROR);
    
    try {
        const response = await fetch(`${CONFIG.API.CONSULTATION}${STATE.userId}`);
        
        if (!response.ok) {
            throw new Error('Failed to load consultation data');
        }
        
        const data = await response.json();
        STATE.consultation = data;
        
        renderConsultation(data);
        hideElement(CONFIG.ELEMENTS.CONSULTATION.LOADING);
        showElement(CONFIG.ELEMENTS.CONSULTATION.CONTENT);
    } catch (error) {
        console.error('Error loading consultation:', error);
        hideElement(CONFIG.ELEMENTS.CONSULTATION.LOADING);
        showError(CONFIG.ELEMENTS.CONSULTATION.ERROR, 'Unable to load your health consultation. Please try again later.');
    }
}

/**
 * Load food-symptom correlations
 */
async function loadCorrelations() {
    showLoading(CONFIG.ELEMENTS.CORRELATIONS.LOADING);
    hideElement(CONFIG.ELEMENTS.CORRELATIONS.CONTENT);
    hideElement(CONFIG.ELEMENTS.CORRELATIONS.ERROR);
    
    try {
        const response = await fetch(`${CONFIG.API.CORRELATIONS}${STATE.userId}/food-symptom-correlations`);
        
        if (!response.ok) {
            throw new Error('Failed to load correlations data');
        }
        
        const data = await response.json();
        STATE.correlations = data;
        
        renderCorrelations(data);
        hideElement(CONFIG.ELEMENTS.CORRELATIONS.LOADING);
        showElement(CONFIG.ELEMENTS.CORRELATIONS.CONTENT);
    } catch (error) {
        console.error('Error loading correlations:', error);
        hideElement(CONFIG.ELEMENTS.CORRELATIONS.LOADING);
        showError(CONFIG.ELEMENTS.CORRELATIONS.ERROR, 'Unable to analyze food-symptom correlations. Please try again later.');
    }
}

/**
 * Load health tips by category
 * @param {string} category - The category of health tips to load
 */
async function loadHealthTips(category) {
    const contentElement = document.getElementById(CONFIG.ELEMENTS.HEALTH_TIPS.CONTENT);
    
    if (!contentElement) return;
    
    // Check if we already have this category cached
    if (STATE.healthTips[category]) {
        renderHealthTips(STATE.healthTips[category]);
        return;
    }
    
    // Show loading indicator
    contentElement.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-success" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p>Loading health tips...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`${CONFIG.API.HEALTH_TIPS}${category}`);
        
        if (!response.ok) {
            throw new Error(`Failed to load health tips for category: ${category}`);
        }
        
        const data = await response.json();
        STATE.healthTips[category] = data;
        
        renderHealthTips(data);
    } catch (error) {
        console.error(`Error loading health tips for ${category}:`, error);
        contentElement.innerHTML = `
            <div class="alert alert-danger">
                <p>Unable to load health tips. Please try again later.</p>
            </div>
        `;
    }
}

/**
 * Render health consultation data
 * @param {Object} data - The consultation data to render
 */
function renderConsultation(data) {
    const contentElement = document.getElementById(CONFIG.ELEMENTS.CONSULTATION.CONTENT);
    
    if (!contentElement || !data) return;
    
    let html = '';
    
    // General Health Status
    if (data.general_health_status) {
        html += createSectionHtml('General Health Status', data.general_health_status);
    }
    
    // Vital Signs Assessment
    if (data.vital_signs_assessment) {
        html += createSectionHtml('Vital Signs Assessment', data.vital_signs_assessment);
    }
    
    // Symptom Analysis
    if (data.symptom_analysis) {
        html += createSectionHtml('Symptom Analysis', data.symptom_analysis);
    }
    
    // Nutrition Assessment
    if (data.nutrition_assessment) {
        html += createSectionHtml('Nutrition Assessment', data.nutrition_assessment);
    }
    
    // Recommendations
    if (data.recommendations && data.recommendations.length > 0) {
        html += `
            <div class="mb-4">
                <h4>Personalized Recommendations</h4>
                <ul class="list-group">
                    ${data.recommendations.map(rec => `<li class="list-group-item">${rec}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    contentElement.innerHTML = html || '<p>No consultation data available.</p>';
    showElement(contentElement);
}

/**
 * Create HTML for a consultation section
 * @param {string} title - The section title
 * @param {Object} data - The section data
 * @returns {string} The HTML for the section
 */
function createSectionHtml(title, data) {
    if (!data || (typeof data === 'object' && Object.keys(data).length === 0)) {
        return '';
    }
    
    let html = `
        <div class="mb-4">
            <h4>${title}</h4>
    `;
    
    if (data.status === 'insufficient_data') {
        html += `<p class="text-muted">Insufficient data available for ${title.toLowerCase()}.</p>`;
    } else if (typeof data === 'object') {
        html += '<div class="row">';
        
        // Handle different data formats based on section type
        if (title === 'General Health Status') {
            html += renderGeneralHealthHtml(data);
        } else if (title === 'Vital Signs Assessment') {
            html += renderVitalSignsHtml(data);
        } else if (title === 'Symptom Analysis') {
            html += renderSymptomAnalysisHtml(data);
        } else if (title === 'Nutrition Assessment') {
            html += renderNutritionAssessmentHtml(data);
        } else {
            // Generic object rendering
            for (const [key, value] of Object.entries(data)) {
                if (typeof value !== 'object') {
                    html += `
                        <div class="col-md-6 mb-2">
                            <div class="card">
                                <div class="card-body">
                                    <h6 class="card-subtitle mb-2 text-muted">${formatKey(key)}</h6>
                                    <p class="card-text">${value}</p>
                                </div>
                            </div>
                        </div>
                    `;
                }
            }
        }
        
        html += '</div>';
    } else {
        html += `<p>${data}</p>`;
    }
    
    html += '</div>';
    return html;
}

/**
 * Render general health status HTML
 * @param {Object} data - The general health data
 * @returns {string} The HTML for the general health section
 */
function renderGeneralHealthHtml(data) {
    let html = '';
    
    if (data.bmi) {
        const bmiCategory = data.bmi_category ? data.bmi_category.replace('_', ' ') : 'unknown';
        html += `
            <div class="col-md-4 mb-2">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">BMI</h6>
                        <p class="card-text">${data.bmi} (${bmiCategory})</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    if (data.weight_trend) {
        html += `
            <div class="col-md-4 mb-2">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">Weight Trend</h6>
                        <p class="card-text">${data.weight_trend.charAt(0).toUpperCase() + data.weight_trend.slice(1)}</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    if (data.overall_status) {
        html += `
            <div class="col-md-4 mb-2">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">Overall Status</h6>
                        <p class="card-text">${data.overall_status}</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    return html;
}

/**
 * Render vital signs HTML
 * @param {Object} data - The vital signs data
 * @returns {string} The HTML for the vital signs section
 */
function renderVitalSignsHtml(data) {
    let html = '';
    
    if (data.blood_pressure) {
        const bp = data.blood_pressure;
        const category = bp.category ? bp.category.replace('_', ' ') : 'unknown';
        html += `
            <div class="col-md-6 mb-2">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">Blood Pressure</h6>
                        <p class="card-text">${bp.systolic}/${bp.diastolic} mmHg (${category})</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    if (data.blood_sugar) {
        const bs = data.blood_sugar;
        const category = bs.category ? bs.category.replace('_', ' ') : 'unknown';
        html += `
            <div class="col-md-6 mb-2">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">Blood Sugar</h6>
                        <p class="card-text">${bs.value} mg/dL (${category})</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    return html;
}

/**
 * Render symptom analysis HTML
 * @param {Object} data - The symptom analysis data
 * @returns {string} The HTML for the symptom analysis section
 */
function renderSymptomAnalysisHtml(data) {
    let html = '';
    
    if (data.status === 'no_symptoms') {
        return `
            <div class="col-12">
                <p class="text-muted">No symptoms reported.</p>
            </div>
        `;
    }
    
    if (data.most_common && data.most_common.length > 0) {
        html += `
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">Most Common Symptoms</h6>
                        <ul class="list-group list-group-flush">
        `;
        
        data.most_common.forEach(([symptom, info]) => {
            html += `<li class="list-group-item">${symptom} (${info.count} occurrences)</li>`;
        });
        
        html += `
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
    
    if (data.most_severe && data.most_severe.length > 0) {
        html += `
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">Most Severe Symptoms</h6>
                        <ul class="list-group list-group-flush">
        `;
        
        data.most_severe.forEach(([symptom, info]) => {
            html += `<li class="list-group-item">${symptom} (severity: ${info.avg_severity}/3)</li>`;
        });
        
        html += `
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
    
    return html;
}

/**
 * Render nutrition assessment HTML
 * @param {Object} data - The nutrition assessment data
 * @returns {string} The HTML for the nutrition assessment section
 */
function renderNutritionAssessmentHtml(data) {
    let html = '';
    
    if (data.average_daily) {
        const avg = data.average_daily;
        html += `
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">Average Daily Intake</h6>
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item">Calories: ${avg.calories} kcal</li>
                            <li class="list-group-item">Protein: ${avg.protein} g</li>
                            <li class="list-group-item">Carbohydrates: ${avg.carbs} g</li>
                            <li class="list-group-item">Fat: ${avg.fat} g</li>
                            <li class="list-group-item">Fiber: ${avg.fiber} g</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
    
    if (data.macronutrient_ratio) {
        const ratio = data.macronutrient_ratio;
        html += `
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">Macronutrient Ratio</h6>
                        <div class="mt-3">
                            <canvas id="macro-chart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Schedule chart creation after DOM is updated
        setTimeout(() => {
            const ctx = document.getElementById('macro-chart');
            if (ctx) {
                new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: ['Protein', 'Carbs', 'Fat'],
                        datasets: [{
                            data: [ratio.protein, ratio.carbs, ratio.fat],
                            backgroundColor: ['#4e73df', '#1cc88a', '#f6c23e']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return `${context.label}: ${context.raw}%`;
                                    }
                                }
                            }
                        }
                    }
                });
            }
        }, 100);
    }
    
    return html;
}

/**
 * Render food-symptom correlations
 * @param {Object} data - The correlations data to render
 */
function renderCorrelations(data) {
    const contentElement = document.getElementById(CONFIG.ELEMENTS.CORRELATIONS.CONTENT);
    
    if (!contentElement || !data) return;
    
    let html = '';
    
    if (data.correlations && data.correlations.length > 0) {
        html += `
            <div class="mb-3">
                <p class="text-muted">The following food items may be associated with your symptoms:</p>
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Food</th>
                                <th>Symptom</th>
                                <th>Confidence</th>
                                <th>Correlation</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        data.correlations.forEach(corr => {
            const confidenceClass = {
                'low': 'text-muted',
                'medium': 'text-warning',
                'high': 'text-danger'
            }[corr.confidence] || 'text-muted';
            
            const confidenceIcon = {
                'low': '⚪',
                'medium': '🟡',
                'high': '🔴'
            }[corr.confidence] || '⚪';
            
            html += `
                <tr>
                    <td>${corr.food}</td>
                    <td>${corr.symptom}</td>
                    <td class="${confidenceClass}">${confidenceIcon} ${corr.confidence}</td>
                    <td>${corr.correlation_percentage}% (${corr.occurrences} occurrences)</td>
                </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
                <div class="alert alert-info mt-3">
                    <p class="mb-0"><strong>Note:</strong> Correlation does not necessarily imply causation. These associations are based on your logged data and may require further investigation.</p>
                </div>
            </div>
        `;
    } else {
        html = `
            <div class="alert alert-info">
                <p class="mb-0">No significant food-symptom correlations found. Continue logging your meals and symptoms for more insights.</p>
            </div>
        `;
    }
    
    contentElement.innerHTML = html;
    showElement(contentElement);
}

/**
 * Render health tips
 * @param {Array} tips - The health tips to render
 */
function renderHealthTips(tips) {
    const contentElement = document.getElementById(CONFIG.ELEMENTS.HEALTH_TIPS.CONTENT);
    
    if (!contentElement || !tips) return;
    
    if (tips.length === 0) {
        contentElement.innerHTML = '<p class="text-muted">No health tips available for this category.</p>';
        return;
    }
    
    let html = '<div class="accordion" id="healthTipsAccordion">';
    
    tips.forEach((tip, index) => {
        const importanceClass = {
            'high': 'text-danger',
            'medium': 'text-warning',
            'low': 'text-muted'
        }[tip.importance] || 'text-muted';
        
        html += `
            <div class="accordion-item">
                <h2 class="accordion-header" id="heading${index}">
                    <button class="accordion-button ${index > 0 ? 'collapsed' : ''}" type="button" data-bs-toggle="collapse" data-bs-target="#collapse${index}" aria-expanded="${index === 0 ? 'true' : 'false'}" aria-controls="collapse${index}">
                        <span class="${importanceClass}">${tip.importance === 'high' ? '★ ' : ''}${tip.title}</span>
                    </button>
                </h2>
                <div id="collapse${index}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}" aria-labelledby="heading${index}" data-bs-parent="#healthTipsAccordion">
                    <div class="accordion-body">
                        ${tip.description}
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    contentElement.innerHTML = html;
}

/**
 * Format object key for display
 * @param {string} key - The key to format
 * @returns {string} The formatted key
 */
function formatKey(key) {
    return key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Show loading indicator
 * @param {string} elementId - The ID of the loading element
 */
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('d-none');
    }
}

/**
 * Show error message
 * @param {string} elementId - The ID of the error element
 * @param {string} message - The error message to display
 */
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.classList.remove('d-none');
    }
}

/**
 * Show element
 * @param {string|Element} element - The element or element ID to show
 */
function showElement(element) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (el) {
        el.classList.remove('d-none');
    }
}

/**
 * Hide element
 * @param {string|Element} element - The element or element ID to hide
 */
function hideElement(element) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (el) {
        el.classList.add('d-none');
    }
}

/**
 * Get URL parameter value
 * @param {string} name - The parameter name
 * @returns {string|null} The parameter value or null if not found
 */
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// Initialize the module when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initHealthConsultation);