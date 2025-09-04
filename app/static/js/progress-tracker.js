/**
 * HealthSync Progress Tracker Module
 * 
 * This module provides functionality for visualizing and interacting with
 * user health progress data including weight, blood pressure, and other metrics.
 */

const ProgressTracker = {
    // Configuration
    config: {
        apiBase: '/progress',
        chartColors: {
            weight: '#4CAF50',
            bloodPressureSystolic: '#F44336',
            bloodPressureDiastolic: '#9C27B0',
            bloodSugar: '#FF9800'
        },
        defaultDays: 30
    },
    
    // State
    state: {
        userId: null,
        charts: {},
        currentMetric: 'weight',
        currentDays: 30
    },
    
    /**
     * Initialize the progress tracker module
     * @param {string} userId - The user ID
     */
    init: function(userId) {
        this.state.userId = userId;
        this.setupEventListeners();
        this.loadWeightTrend();
        
        // Initialize tabs
        document.querySelector('#weight-tab').classList.add('active');
        document.querySelector('#weight-content').classList.add('active');
    },
    
    /**
     * Set up event listeners for user interactions
     */
    setupEventListeners: function() {
        // Tab switching
        document.querySelectorAll('.progress-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Remove active class from all tabs and content
                document.querySelectorAll('.progress-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                const tabId = e.target.id;
                const contentId = tabId.replace('-tab', '-content');
                
                document.querySelector(`#${tabId}`).classList.add('active');
                document.querySelector(`#${contentId}`).classList.add('active');
                
                // Load data based on tab
                if (tabId === 'weight-tab') {
                    this.loadWeightTrend();
                } else if (tabId === 'blood-pressure-tab') {
                    this.loadBloodPressureTrend();
                } else if (tabId === 'goals-tab') {
                    this.loadGoalProgress();
                } else if (tabId === 'report-tab') {
                    this.loadHealthReport();
                }
            });
        });
        
        // Time range selector
        document.querySelectorAll('.time-range-selector').forEach(selector => {
            selector.addEventListener('change', (e) => {
                const days = parseInt(e.target.value);
                this.state.currentDays = days;
                
                // Reload current tab data
                const activeTab = document.querySelector('.progress-tab.active').id;
                if (activeTab === 'weight-tab') {
                    this.loadWeightTrend();
                } else if (activeTab === 'blood-pressure-tab') {
                    this.loadBloodPressureTrend();
                }
            });
        });
        
        // Goal type selector
        document.querySelector('#goal-type-selector').addEventListener('change', (e) => {
            const goalType = e.target.value;
            const targetInput = document.querySelector('#goal-target-value');
            
            // Update placeholder based on goal type
            if (goalType === 'weight') {
                targetInput.placeholder = 'Target weight in kg';
            } else if (goalType === 'blood_sugar') {
                targetInput.placeholder = 'Target blood sugar level';
            } else if (goalType === 'blood_pressure') {
                targetInput.placeholder = 'Target systolic blood pressure';
            }
        });
        
        // Goal tracking form
        document.querySelector('#goal-tracking-form').addEventListener('submit', (e) => {
            e.preventDefault();
            
            const goalType = document.querySelector('#goal-type-selector').value;
            const targetValue = parseFloat(document.querySelector('#goal-target-value').value);
            
            if (isNaN(targetValue)) {
                alert('Please enter a valid target value');
                return;
            }
            
            this.trackGoalProgress(goalType, targetValue);
        });
        
        // Log progress form
        document.querySelector('#log-progress-form').addEventListener('submit', (e) => {
            e.preventDefault();
            
            const weightInput = document.querySelector('#weight-input');
            const systolicInput = document.querySelector('#systolic-input');
            const diastolicInput = document.querySelector('#diastolic-input');
            const bloodSugarInput = document.querySelector('#blood-sugar-input');
            const notesInput = document.querySelector('#progress-notes');
            
            const progressData = {
                user_id: this.state.userId,
                weight_kg: weightInput.value ? parseFloat(weightInput.value) : null,
                blood_pressure_systolic: systolicInput.value ? parseInt(systolicInput.value) : null,
                blood_pressure_diastolic: diastolicInput.value ? parseInt(diastolicInput.value) : null,
                blood_sugar: bloodSugarInput.value ? parseFloat(bloodSugarInput.value) : null,
                notes: notesInput.value || null
            };
            
            this.logProgress(progressData);
        });
    },
    
    /**
     * Load weight trend data and visualize it
     */
    loadWeightTrend: function() {
        const url = `${this.config.apiBase}/user/${this.state.userId}/weight-trend?days=${this.state.currentDays}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.renderWeightChart(data);
                    this.renderWeightInsights(data);
                } else {
                    document.querySelector('#weight-chart-container').innerHTML = 
                        `<div class="alert alert-info">${data.message}</div>`;
                    document.querySelector('#weight-insights').innerHTML = '';
                }
            })
            .catch(error => {
                console.error('Error loading weight trend:', error);
                document.querySelector('#weight-chart-container').innerHTML = 
                    '<div class="alert alert-danger">Error loading weight data. Please try again later.</div>';
            });
    },
    
    /**
     * Render weight chart using chart.js
     * @param {Object} data - Weight trend data
     */
    renderWeightChart: function(data) {
        const chartContainer = document.querySelector('#weight-chart-container');
        chartContainer.innerHTML = '<canvas id="weight-chart"></canvas>';
        
        const ctx = document.querySelector('#weight-chart').getContext('2d');
        
        // Extract data points for chart
        const weightData = [];
        const labels = [];
        
        // Assuming data contains first_measurement, latest_measurement, and potentially more points
        if (data.first_measurement && data.latest_measurement) {
            // Add first measurement
            labels.push(new Date(data.first_measurement.date).toLocaleDateString());
            weightData.push(data.first_measurement.weight_kg);
            
            // Add latest measurement if different from first
            if (data.first_measurement.date !== data.latest_measurement.date) {
                labels.push(new Date(data.latest_measurement.date).toLocaleDateString());
                weightData.push(data.latest_measurement.weight_kg);
            }
        }
        
        // Create chart
        if (this.state.charts.weightChart) {
            this.state.charts.weightChart.destroy();
        }
        
        this.state.charts.weightChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Weight (kg)',
                    data: weightData,
                    backgroundColor: this.config.chartColors.weight,
                    borderColor: this.config.chartColors.weight,
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    },
    
    /**
     * Render weight insights
     * @param {Object} data - Weight trend data
     */
    renderWeightInsights: function(data) {
        const insightsContainer = document.querySelector('#weight-insights');
        
        let html = '<div class="card">';
        html += '<div class="card-header">Weight Insights</div>';
        html += '<div class="card-body">';
        
        if (data.status === 'success') {
            html += `<p><strong>Total Change:</strong> ${data.total_change_kg} kg (${data.percent_change}%)</p>`;
            html += `<p><strong>Weekly Change Rate:</strong> ${data.weekly_change_rate_kg} kg/week</p>`;
            html += `<p><strong>Trend:</strong> ${data.trend.charAt(0).toUpperCase() + data.trend.slice(1)}</p>`;
            
            if (data.insights && data.insights.length > 0) {
                html += '<h5>Insights:</h5>';
                html += '<ul>';
                data.insights.forEach(insight => {
                    html += `<li>${insight}</li>`;
                });
                html += '</ul>';
            }
        } else {
            html += `<p>${data.message}</p>`;
        }
        
        html += '</div></div>';
        
        insightsContainer.innerHTML = html;
    },
    
    /**
     * Load blood pressure trend data and visualize it
     */
    loadBloodPressureTrend: function() {
        const url = `${this.config.apiBase}/user/${this.state.userId}/blood-pressure-trend?days=${this.state.currentDays}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.renderBloodPressureChart(data);
                    this.renderBloodPressureInsights(data);
                } else {
                    document.querySelector('#bp-chart-container').innerHTML = 
                        `<div class="alert alert-info">${data.message}</div>`;
                    document.querySelector('#bp-insights').innerHTML = '';
                }
            })
            .catch(error => {
                console.error('Error loading blood pressure trend:', error);
                document.querySelector('#bp-chart-container').innerHTML = 
                    '<div class="alert alert-danger">Error loading blood pressure data. Please try again later.</div>';
            });
    },
    
    /**
     * Render blood pressure chart
     * @param {Object} data - Blood pressure trend data
     */
    renderBloodPressureChart: function(data) {
        const chartContainer = document.querySelector('#bp-chart-container');
        chartContainer.innerHTML = '<canvas id="bp-chart"></canvas>';
        
        const ctx = document.querySelector('#bp-chart').getContext('2d');
        
        // Create chart with average, min, and max values
        if (this.state.charts.bpChart) {
            this.state.charts.bpChart.destroy();
        }
        
        this.state.charts.bpChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Systolic', 'Diastolic'],
                datasets: [
                    {
                        label: 'Average',
                        data: [data.average_systolic, data.average_diastolic],
                        backgroundColor: [
                            this.config.chartColors.bloodPressureSystolic,
                            this.config.chartColors.bloodPressureDiastolic
                        ],
                        borderWidth: 1
                    },
                    {
                        label: 'Min',
                        data: [data.min_systolic, data.min_diastolic],
                        backgroundColor: [
                            this.config.chartColors.bloodPressureSystolic + '80',
                            this.config.chartColors.bloodPressureDiastolic + '80'
                        ],
                        borderWidth: 1
                    },
                    {
                        label: 'Max',
                        data: [data.max_systolic, data.max_diastolic],
                        backgroundColor: [
                            this.config.chartColors.bloodPressureSystolic + 'B0',
                            this.config.chartColors.bloodPressureDiastolic + 'B0'
                        ],
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    },
    
    /**
     * Render blood pressure insights
     * @param {Object} data - Blood pressure trend data
     */
    renderBloodPressureInsights: function(data) {
        const insightsContainer = document.querySelector('#bp-insights');
        
        let html = '<div class="card">';
        html += '<div class="card-header">Blood Pressure Insights</div>';
        html += '<div class="card-body">';
        
        if (data.status === 'success') {
            // Map category to human-readable text
            const categoryMap = {
                'normal': 'Normal',
                'elevated': 'Elevated',
                'hypertension_stage_1': 'Hypertension Stage 1',
                'hypertension_stage_2': 'Hypertension Stage 2',
                'hypertensive_crisis': 'Hypertensive Crisis',
                'unknown': 'Unknown'
            };
            
            html += `<p><strong>Average:</strong> ${data.average_systolic}/${data.average_diastolic} mmHg</p>`;
            html += `<p><strong>Category:</strong> ${categoryMap[data.category] || data.category}</p>`;
            html += `<p><strong>Data Points:</strong> ${data.data_points}</p>`;
            
            if (data.insights && data.insights.length > 0) {
                html += '<h5>Insights:</h5>';
                html += '<ul>';
                data.insights.forEach(insight => {
                    html += `<li>${insight}</li>`;
                });
                html += '</ul>';
            }
        } else {
            html += `<p>${data.message}</p>`;
        }
        
        html += '</div></div>';
        
        insightsContainer.innerHTML = html;
    },
    
    /**
     * Track progress toward a specific health goal
     * @param {string} goalType - Type of goal (weight, blood_sugar, blood_pressure)
     * @param {number} targetValue - Target value for the goal
     */
    trackGoalProgress: function(goalType, targetValue) {
        const url = `${this.config.apiBase}/user/${this.state.userId}/goal-progress?goal_type=${goalType}&target_value=${targetValue}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                this.renderGoalProgress(data);
            })
            .catch(error => {
                console.error('Error tracking goal progress:', error);
                document.querySelector('#goal-progress-container').innerHTML = 
                    '<div class="alert alert-danger">Error tracking goal progress. Please try again later.</div>';
            });
    },
    
    /**
     * Render goal progress
     * @param {Object} data - Goal progress data
     */
    renderGoalProgress: function(data) {
        const progressContainer = document.querySelector('#goal-progress-container');
        
        if (data.status === 'success') {
            let html = '<div class="card">';
            html += '<div class="card-header">Goal Progress</div>';
            html += '<div class="card-body">';
            
            // Map goal type to human-readable text
            const goalTypeMap = {
                'weight': 'Weight',
                'blood_sugar': 'Blood Sugar',
                'blood_pressure': 'Blood Pressure'
            };
            
            html += `<p><strong>Goal Type:</strong> ${goalTypeMap[data.goal_type] || data.goal_type}</p>`;
            html += `<p><strong>Target Value:</strong> ${data.target_value}</p>`;
            html += `<p><strong>Initial Value:</strong> ${data.initial_value}</p>`;
            html += `<p><strong>Current Value:</strong> ${data.current_value}</p>`;
            
            // Progress bar
            html += '<div class="progress" style="height: 25px;">';
            html += `<div class="progress-bar" role="progressbar" style="width: ${data.progress_percentage}%" `;
            html += `aria-valuenow="${data.progress_percentage}" aria-valuemin="0" aria-valuemax="100">`;
            html += `${data.progress_percentage}%</div></div>`;
            html += '<p class="mt-2"></p>';
            
            if (data.insights && data.insights.length > 0) {
                html += '<h5>Insights:</h5>';
                html += '<ul>';
                data.insights.forEach(insight => {
                    html += `<li>${insight}</li>`;
                });
                html += '</ul>';
            }
            
            html += '</div></div>';
            
            progressContainer.innerHTML = html;
        } else {
            progressContainer.innerHTML = `<div class="alert alert-info">${data.message}</div>`;
        }
    },
    
    /**
     * Load comprehensive health report
     */
    loadHealthReport: function() {
        const url = `${this.config.apiBase}/user/${this.state.userId}/health-report`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                this.renderHealthReport(data);
            })
            .catch(error => {
                console.error('Error loading health report:', error);
                document.querySelector('#health-report-container').innerHTML = 
                    '<div class="alert alert-danger">Error loading health report. Please try again later.</div>';
            });
    },
    
    /**
     * Render comprehensive health report
     * @param {Object} data - Health report data
     */
    renderHealthReport: function(data) {
        const reportContainer = document.querySelector('#health-report-container');
        
        if (data.status === 'success') {
            let html = '<div class="health-report">';
            
            // User info section
            html += '<div class="card mb-3">';
            html += '<div class="card-header">User Information</div>';
            html += '<div class="card-body">';
            html += `<p><strong>Name:</strong> ${data.user_info.name}</p>`;
            if (data.user_info.age) {
                html += `<p><strong>Age:</strong> ${data.user_info.age}</p>`;
            }
            html += `<p><strong>Gender:</strong> ${data.user_info.gender}</p>`;
            html += `<p><strong>Height:</strong> ${data.user_info.height_cm} cm</p>`;
            if (data.user_info.current_weight_kg) {
                html += `<p><strong>Current Weight:</strong> ${data.user_info.current_weight_kg} kg</p>`;
            }
            html += '</div></div>';
            
            // Summary section
            html += '<div class="card mb-3">';
            html += '<div class="card-header">Summary</div>';
            html += '<div class="card-body">';
            html += `<p><strong>Report Date:</strong> ${new Date(data.report_date).toLocaleDateString()}</p>`;
            html += `<p><strong>Data Points Collected:</strong> ${data.summary.data_points_collected}</p>`;
            html += `<p><strong>Days Tracked:</strong> ${data.summary.days_tracked}</p>`;
            html += `<p><strong>Metrics Tracked:</strong> ${data.summary.metrics_tracked.join(', ')}</p>`;
            html += '</div></div>';
            
            // Weight analysis section (if available)
            if (data.weight_analysis) {
                html += '<div class="card mb-3">';
                html += '<div class="card-header">Weight Analysis</div>';
                html += '<div class="card-body">';
                html += `<p><strong>Total Change:</strong> ${data.weight_analysis.total_change_kg} kg (${data.weight_analysis.percent_change}%)</p>`;
                html += `<p><strong>Weekly Change Rate:</strong> ${data.weight_analysis.weekly_change_rate_kg} kg/week</p>`;
                html += `<p><strong>Trend:</strong> ${data.weight_analysis.trend.charAt(0).toUpperCase() + data.weight_analysis.trend.slice(1)}</p>`;
                html += '</div></div>';
            }
            
            // Blood pressure analysis section (if available)
            if (data.blood_pressure_analysis) {
                html += '<div class="card mb-3">';
                html += '<div class="card-header">Blood Pressure Analysis</div>';
                html += '<div class="card-body">';
                html += `<p><strong>Average:</strong> ${data.blood_pressure_analysis.average_systolic}/${data.blood_pressure_analysis.average_diastolic} mmHg</p>`;
                
                // Map category to human-readable text
                const categoryMap = {
                    'normal': 'Normal',
                    'elevated': 'Elevated',
                    'hypertension_stage_1': 'Hypertension Stage 1',
                    'hypertension_stage_2': 'Hypertension Stage 2',
                    'hypertensive_crisis': 'Hypertensive Crisis',
                    'unknown': 'Unknown'
                };
                
                html += `<p><strong>Category:</strong> ${categoryMap[data.blood_pressure_analysis.category] || data.blood_pressure_analysis.category}</p>`;
                html += '</div></div>';
            }
            
            // Nutrition summary section (if available)
            if (data.nutrition_summary && data.nutrition_summary.status === 'success') {
                html += '<div class="card mb-3">';
                html += '<div class="card-header">Nutrition Summary</div>';
                html += '<div class="card-body">';
                html += `<p><strong>Average Daily Calories:</strong> ${data.nutrition_summary.average_daily_calories}</p>`;
                html += `<p><strong>Days Tracked:</strong> ${data.nutrition_summary.days_tracked}</p>`;
                
                // Meal frequency
                if (data.nutrition_summary.meal_frequency) {
                    html += '<p><strong>Meal Frequency:</strong></p>';
                    html += '<ul>';
                    for (const [mealType, count] of Object.entries(data.nutrition_summary.meal_frequency)) {
                        html += `<li>${mealType.charAt(0).toUpperCase() + mealType.slice(1)}: ${count}</li>`;
                    }
                    html += '</ul>';
                }
                html += '</div></div>';
            }
            
            // Symptom patterns section (if available)
            if (data.symptom_patterns && data.symptom_patterns.status === 'success') {
                html += '<div class="card mb-3">';
                html += '<div class="card-header">Symptom Patterns</div>';
                html += '<div class="card-body">';
                
                // Most frequent symptoms
                if (data.symptom_patterns.most_frequent_symptoms && data.symptom_patterns.most_frequent_symptoms.length > 0) {
                    html += '<p><strong>Most Frequent Symptoms:</strong></p>';
                    html += '<ul>';
                    data.symptom_patterns.most_frequent_symptoms.forEach(([symptom, count]) => {
                        html += `<li>${symptom}: ${count} occurrences</li>`;
                    });
                    html += '</ul>';
                }
                
                // Time patterns
                if (data.symptom_patterns.time_patterns && data.symptom_patterns.time_patterns.length > 0) {
                    html += '<p><strong>Time Patterns:</strong></p>';
                    html += '<ul>';
                    data.symptom_patterns.time_patterns.forEach(pattern => {
                        html += `<li>${pattern.symptom} tends to occur in the ${pattern.time}</li>`;
                    });
                    html += '</ul>';
                }
                html += '</div></div>';
            }
            
            // Recommendations section
            if (data.recommendations && data.recommendations.length > 0) {
                html += '<div class="card mb-3">';
                html += '<div class="card-header">Recommendations</div>';
                html += '<div class="card-body">';
                html += '<ul>';
                data.recommendations.forEach(recommendation => {
                    html += `<li>${recommendation}</li>`;
                });
                html += '</ul>';
                html += '</div></div>';
            }
            
            html += '</div>'; // Close health-report div
            
            reportContainer.innerHTML = html;
        } else {
            reportContainer.innerHTML = `<div class="alert alert-info">${data.message}</div>`;
        }
    },
    
    /**
     * Log a new progress entry
     * @param {Object} progressData - Progress data to log
     */
    logProgress: function(progressData) {
        fetch(`${this.config.apiBase}/log`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(progressData)
        })
        .then(response => response.json())
        .then(data => {
            // Show success message
            const messageContainer = document.querySelector('#progress-log-message');
            messageContainer.innerHTML = '<div class="alert alert-success">Progress logged successfully!</div>';
            
            // Clear form
            document.querySelector('#log-progress-form').reset();
            
            // Reload current tab data after a short delay
            setTimeout(() => {
                const activeTab = document.querySelector('.progress-tab.active').id;
                if (activeTab === 'weight-tab') {
                    this.loadWeightTrend();
                } else if (activeTab === 'blood-pressure-tab') {
                    this.loadBloodPressureTrend();
                }
                
                // Clear message
                messageContainer.innerHTML = '';
            }, 2000);
        })
        .catch(error => {
            console.error('Error logging progress:', error);
            const messageContainer = document.querySelector('#progress-log-message');
            messageContainer.innerHTML = '<div class="alert alert-danger">Error logging progress. Please try again.</div>';
        });
    }
};