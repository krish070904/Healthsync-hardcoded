// symptom-prediction.js

/**
 * Symptom Prediction and Analysis Module
 * Provides visualization and interaction with the symptom prediction model
 */
const SymptomPrediction = {
    init: function() {
        // Initialize the module
        this.userId = localStorage.getItem('userId');
        if (!this.userId) {
            document.getElementById('prediction-container').innerHTML = 
                '<div class="alert alert-warning">Please log in to view symptom predictions</div>';
            return;
        }
        
        this.setupEventListeners();
        this.loadPredictions();
        this.loadAnalysis();
    },
    
    setupEventListeners: function() {
        // Set up event listeners for the UI
        const refreshBtn = document.getElementById('refresh-predictions');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadPredictions());
        }
        
        const analysisBtn = document.getElementById('refresh-analysis');
        if (analysisBtn) {
            analysisBtn.addEventListener('click', () => this.loadAnalysis());
        }
    },
    
    loadPredictions: function() {
        // Load symptom predictions from the API
        const predictionContainer = document.getElementById('prediction-results');
        if (!predictionContainer) return;
        
        predictionContainer.innerHTML = '<div class="loading">Loading predictions...</div>';
        
        fetch(`/predictions/symptoms/${this.userId}/future?days_ahead=5`)
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.detail || 'Failed to load predictions');
                    });
                }
                return response.json();
            })
            .then(data => {
                this.renderPredictions(data.predictions);
            })
            .catch(error => {
                predictionContainer.innerHTML = `
                    <div class="alert alert-danger">
                        ${error.message}
                    </div>
                    <p>Try logging more symptoms to improve predictions.</p>
                `;
            });
    },
    
    renderPredictions: function(predictions) {
        // Render the predictions in the UI
        const predictionContainer = document.getElementById('prediction-results');
        if (!predictionContainer) return;
        
        if (!predictions || predictions.length === 0) {
            predictionContainer.innerHTML = '<div class="alert alert-info">No predictions available</div>';
            return;
        }
        
        let html = '<div class="prediction-timeline">';
        
        predictions.forEach(prediction => {
            const date = new Date(prediction.date);
            const formattedDate = date.toLocaleDateString('en-US', { 
                weekday: 'short', 
                month: 'short', 
                day: 'numeric' 
            });
            
            // Determine color based on classification
            let colorClass = 'prediction-normal';
            if (prediction.predicted_classification === 'flu-like') {
                colorClass = 'prediction-warning';
            } else if (prediction.predicted_classification === 'food-intolerance') {
                colorClass = 'prediction-caution';
            }
            
            // Format confidence as percentage
            const confidence = Math.round(prediction.confidence * 100);
            
            html += `
                <div class="prediction-card ${colorClass}">
                    <div class="prediction-date">${formattedDate}</div>
                    <div class="prediction-classification">
                        <strong>${prediction.predicted_classification}</strong>
                        <span class="confidence">${confidence}% confidence</span>
                    </div>
                    <div class="prediction-symptoms">
                        <strong>Possible symptoms:</strong>
                        <ul>
                            ${prediction.possible_symptoms.map(s => `<li>${s}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        html += '<div class="prediction-note">These predictions are based on your symptom history and may change as you log more data.</div>';
        
        predictionContainer.innerHTML = html;
    },
    
    loadAnalysis: function() {
        // Load symptom pattern analysis from the API
        const analysisContainer = document.getElementById('analysis-results');
        if (!analysisContainer) return;
        
        analysisContainer.innerHTML = '<div class="loading">Analyzing symptom patterns...</div>';
        
        fetch(`/predictions/symptoms/${this.userId}/analysis`)
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.detail || 'Failed to load analysis');
                    });
                }
                return response.json();
            })
            .then(data => {
                this.renderAnalysis(data.analysis);
            })
            .catch(error => {
                analysisContainer.innerHTML = `
                    <div class="alert alert-danger">
                        ${error.message}
                    </div>
                    <p>Try logging more symptoms over time to enable pattern analysis.</p>
                `;
            });
    },
    
    renderAnalysis: function(analysis) {
        // Render the symptom pattern analysis in the UI
        const analysisContainer = document.getElementById('analysis-results');
        if (!analysisContainer) return;
        
        if (!analysis || analysis.message) {
            analysisContainer.innerHTML = `<div class="alert alert-info">${analysis.message || 'No analysis available'}</div>`;
            return;
        }
        
        // Create HTML for the analysis
        let html = '<div class="analysis-summary">';
        
        // Symptom frequency chart
        html += '<div class="analysis-section">';
        html += '<h4>Symptom Frequency</h4>';
        html += '<div class="symptom-chart">';
        
        for (const [symptom, count] of Object.entries(analysis.symptom_frequency)) {
            const percentage = Math.round((count / analysis.total_logs) * 100);
            html += `
                <div class="symptom-bar">
                    <div class="symptom-name">${symptom}</div>
                    <div class="symptom-bar-container">
                        <div class="symptom-bar-fill" style="width: ${percentage}%;"></div>
                        <span class="symptom-count">${count}</span>
                    </div>
                </div>
            `;
        }
        
        html += '</div></div>';
        
        // Severity trend
        html += '<div class="analysis-section">';
        html += '<h4>Severity Trend</h4>';
        
        let trendIcon = '→';
        let trendClass = 'trend-stable';
        
        if (analysis.severity_trend.trend === 'increasing') {
            trendIcon = '↑';
            trendClass = 'trend-increasing';
        } else if (analysis.severity_trend.trend === 'decreasing') {
            trendIcon = '↓';
            trendClass = 'trend-decreasing';
        }
        
        html += `
            <div class="severity-trend ${trendClass}">
                <span class="trend-icon">${trendIcon}</span>
                <span class="trend-text">${analysis.severity_trend.trend}</span>
            </div>
            <div class="trend-details">
                <div>First half avg: ${analysis.severity_trend.first_half_avg.toFixed(1)}</div>
                <div>Second half avg: ${analysis.severity_trend.second_half_avg.toFixed(1)}</div>
                <div>Change: ${analysis.severity_trend.change.toFixed(1)}</div>
            </div>
        `;
        
        html += '</div>';
        
        // Day of week pattern
        html += '<div class="analysis-section">';
        html += '<h4>Day of Week Pattern</h4>';
        html += '<div class="day-pattern">';
        
        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        days.forEach(day => {
            const dayData = analysis.day_of_week_pattern[day];
            const severity = dayData.avg_severity;
            let severityClass = 'severity-low';
            
            if (severity >= 7) {
                severityClass = 'severity-high';
            } else if (severity >= 4) {
                severityClass = 'severity-medium';
            }
            
            html += `
                <div class="day-card">
                    <div class="day-name">${day.substring(0, 3)}</div>
                    <div class="day-severity ${severityClass}">
                        ${severity.toFixed(1)}
                    </div>
                    <div class="day-count">${dayData.count} logs</div>
                </div>
            `;
        });
        
        html += '</div></div>';
        
        // Insights and recommendations
        html += '<div class="analysis-section">';
        html += '<h4>Insights</h4>';
        html += '<ul class="insights-list">';
        
        analysis.insights.forEach(insight => {
            html += `<li>${insight}</li>`;
        });
        
        if (analysis.insights.length === 0) {
            html += '<li>No significant patterns detected yet</li>';
        }
        
        html += '</ul>';
        html += '</div>';
        
        html += '<div class="analysis-section">';
        html += '<h4>Recommendations</h4>';
        html += '<ul class="recommendations-list">';
        
        analysis.recommendations.forEach(rec => {
            html += `<li>${rec}</li>`;
        });
        
        if (analysis.recommendations.length === 0) {
            html += '<li>Continue logging your symptoms regularly</li>';
        }
        
        html += '</ul>';
        html += '</div>';
        
        html += '</div>'; // Close analysis-summary
        
        analysisContainer.innerHTML = html;
    }
};

// Initialize the module when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    SymptomPrediction.init();
});