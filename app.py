from flask import Flask, request, jsonify
from db_helper import (
    get_quarterly_data,
    get_series,
    get_quarterly_matrix,
    get_all_pat_growth
)
import sqlite3
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_db_connection():
    """Create and return a database connection."""
    db_path = os.path.join('database', 'ttm_pat_yoy_growth.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Financial Data Analyzer</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #4361ee;
                --primary-light: #eef2ff;
                --secondary: #3f37c9;
                --success: #10b981;
                --warning: #f59e0b;
                --danger: #ef4444;
                --dark: #1f2937;
                --light: #f9fafb;
                --gray: #6b7280;
            }
            
            body {
                font-family: 'Poppins', sans-serif;
                background-color: #f5f7fb;
                color: var(--dark);
                line-height: 1.6;
            }
            
            .navbar-brand {
                font-weight: 700;
                font-size: 1.5rem;
                color: var(--primary) !important;
            }
            
            .card {
                border: none;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                transition: all 0.3s ease;
                margin-bottom: 1.5rem;
                border-left: 4px solid var(--primary);
            }
            
            .card-header {
                background-color: white;
                border-bottom: 1px solid rgba(0, 0, 0, 0.05);
                font-weight: 600;
                color: var(--primary);
                padding: 1.25rem 1.5rem;
                border-radius: 12px 12px 0 0 !important;
            }
            
            .btn-primary {
                background-color: var(--primary);
                border: none;
                padding: 0.6rem 1.5rem;
                border-radius: 8px;
                font-weight: 500;
                transition: all 0.3s;
            }
            
            .btn-primary:hover {
                background-color: var(--secondary);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(67, 97, 238, 0.2);
            }
            
            .form-control, .form-select {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 0.6rem 1rem;
                transition: all 0.3s;
            }
            
            .form-control:focus, .form-select:focus {
                border-color: var(--primary);
                box-shadow: 0 0 0 0.25rem rgba(67, 97, 238, 0.25);
            }
            
            .result-container {
                background: white;
                border-radius: 12px;
                padding: 1.5rem;
                margin-top: 1.5rem;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }
            
            .loading-spinner {
                width: 3rem;
                height: 3rem;
                border-width: 0.25rem;
            }
            
            .feature-icon {
                width: 48px;
                height: 48px;
                border-radius: 12px;
                background-color: var(--primary-light);
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 1rem;
                color: var(--primary);
                font-size: 1.5rem;
            }
            
            .nav-pills .nav-link.active {
                background-color: var(--primary);
            }
            
            .nav-pills .nav-link {
                color: var(--gray);
                font-weight: 500;
                padding: 0.5rem 1rem;
                margin-right: 0.5rem;
                border-radius: 8px;
                transition: all 0.3s;
            }
            
            .nav-pills .nav-link:hover {
                background-color: var(--primary-light);
                color: var(--primary);
            }
            
            .table th {
                font-weight: 600;
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
            }
            
            .table-hover tbody tr:hover {
                background-color: rgba(67, 97, 238, 0.05);
            }
            
            .alert {
                border: none;
                border-radius: 8px;
                padding: 1rem 1.25rem;
            }
            
            .alert i {
                margin-right: 8px;
            }
            
            .export-btn {
                position: absolute;
                right: 1.5rem;
                top: 1.25rem;
                z-index: 1;
            }
        </style>
    </head>
    <body>
        <!-- Navigation -->
        <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
            <div class="container">
                <a class="navbar-brand" href="#">
                    <i class="fas fa-chart-line me-2"></i>Finance Analyzer
                </a>
            </div>
        </nav>

        <!-- Main Content -->
        <div class="container my-5">
            <div class="row">
                <div class="col-12 mb-5 text-center">
                    <h1 class="display-5 fw-bold mb-3">Financial Data Analyzer</h1>
                    <p class="lead text-muted">Access and analyze financial data with ease</p>
                </div>
            </div>

            <div class="row">
                <div class="col-lg-8 mx-auto">
                    <div class="card">
                        <div class="card-header position-relative">
                            <h5 class="mb-0"><i class="fas fa-search me-2"></i>Data Lookup</h5>
                            <button id="exportBtn" class="btn btn-sm btn-outline-primary export-btn" style="display: none;" 
                                    onclick="exportData()">
                                <i class="fas fa-download me-1"></i>Export CSV
                            </button>
                        </div>
                        <div class="card-body">
                            <ul class="nav nav-pills mb-4" id="pills-tab" role="tablist">
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link active" id="quarterly-tab" data-bs-toggle="pill" data-bs-target="#quarterly" type="button">
                                        <i class="fas fa-calendar-alt me-1"></i>Quarterly Data
                                    </button>
                                </li>
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link" id="range-tab" data-bs-toggle="pill" data-bs-target="#range" type="button">
                                        <i class="fas fa-chart-line me-1"></i>Date Range
                                    </button>
                                </li>
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link" id="all-companies-tab" data-bs-toggle="pill" data-bs-target="#all-companies" type="button">
                                        <i class="fas fa-building me-1"></i>All Companies
                                    </button>
                                </li>
                            </ul>
                            
                            <div class="tab-content" id="pills-tabContent">
                                <!-- Quarterly Data Tab -->
                                <div class="tab-pane fade show active" id="quarterly" role="tabpanel">
                                    <div class="mb-3">
                                        <label class="form-label">Company Code</label>
                                        <input type="number" class="form-control" id="code1" value="100186" placeholder="Enter company code">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Data Field</label>
                                        <select class="form-select" id="field1">
                                            <option value="ttm_pat_yoy_growth">TTM PAT YoY Growth</option>
                                            <option value="sector">Sector</option>
                                            <option value="mcap_category">Market Cap</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Date</label>
                                        <input type="date" class="form-control" id="date1" value="2023-03-31">
                                    </div>
                                    <button onclick="getQuarterlyData()" class="btn btn-primary w-100">
                                        <i class="fas fa-search me-2"></i>Get Data
                                    </button>
                                </div>
                                
                                <!-- Date Range Tab -->
                                <div class="tab-pane fade" id="range" role="tabpanel">
                                    <div class="mb-3">
                                        <label class="form-label">Company Code</label>
                                        <input type="number" class="form-control" id="code2" value="100186" placeholder="Enter company code">
                                    </div>
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label">Start Date</label>
                                            <input type="date" class="form-control" id="start_date" value="2022-03-31">
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label">End Date</label>
                                            <input type="date" class="form-control" id="end_date" value="2023-09-30">
                                        </div>
                                    </div>
                                    <button onclick="getSeriesData()" class="btn btn-primary w-100">
                                        <i class="fas fa-chart-line me-2"></i>Get Time Series
                                    </button>
                                </div>
                                
                                <!-- All Companies Tab -->
                                <div class="tab-pane fade" id="all-companies" role="tabpanel">
                                    <div class="mb-3">
                                        <label class="form-label">Date</label>
                                        <input type="date" class="form-control" id="matrix_date" value="2023-06-30">
                                    </div>
                                    <button onclick="getMatrixData()" class="btn btn-primary w-100 mb-3">
                                        <i class="fas fa-building me-2"></i>Get All Companies
                                    </button>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Or get all data for a company</label>
                                        <div class="input-group">
                                            <input type="number" class="form-control" id="code4" value="100186" placeholder="Enter company code">
                                            <button class="btn btn-outline-primary" onclick="getAllPatGrowth()">
                                                <i class="fas fa-search"></i>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div id="result" class="mt-4"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <footer class="bg-light py-4 mt-5">
            <div class="container text-center">
                <p class="text-muted mb-0">© 2023 Financial Data Analyzer. All rights reserved.</p>
            </div>
        </footer>

        <!-- Bootstrap JS Bundle with Popper -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
        // Store current data for export
        let currentData = null;
        let currentExportName = 'financial_data.csv';

        // Display data in a beautiful table
        function displayTable(data, containerId) {
            const container = document.getElementById(containerId || 'result');
            if (!data || data.length === 0) {
                container.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-circle me-2"></i>No data found
                    </div>`;
                document.getElementById('exportBtn').style.display = 'none';
                return;
            }
            
            // Store data for export
            currentData = data;
            document.getElementById('exportBtn').style.display = 'inline-block';
            
            let html = `
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead class="table-light">
                        <tr>`;
            
            // Headers
            Object.keys(data[0]).forEach(key => {
                html += `<th>${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</th>`;
            });
            
            html += `</tr></thead><tbody>`;
            
            // Rows
            data.forEach(row => {
                html += '<tr class="hover-shadow">';
                Object.values(row).forEach(value => {
                    // Format numbers with 2 decimal places if they're numbers
                    const displayValue = typeof value === 'number' && !Number.isInteger(value) 
                        ? value.toFixed(2) 
                        : (value !== null ? value : 'N/A');
                    html += `<td>${displayValue}</td>`;
                });
                html += '</tr>';
            });
            
            html += `</tbody></table></div>`;
            
            container.innerHTML = html;
        }

        // Show loading state
        function showLoading(containerId) {
            const container = document.getElementById(containerId || 'result');
            container.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2 text-muted">Fetching data...</p>
                </div>`;
            document.getElementById('exportBtn').style.display = 'none';
        }

        // Show error message
        function showError(message, containerId) {
            const container = document.getElementById(containerId || 'result');
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                </div>`;
            document.getElementById('exportBtn').style.display = 'none';
        }

        // Show success message
        function showSuccess(message, containerId) {
            const container = document.getElementById(containerId || 'result');
            container.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    ${message}
                </div>`;
            document.getElementById('exportBtn').style.display = 'none';
        }

        // Generic API call function
        async function callApi(endpoint, params = {}) {
            const resultDiv = document.getElementById('result');
            try {
                showLoading();
                const queryString = new URLSearchParams(params).toString();
                const response = await fetch(`/api/${endpoint}?${queryString}`);
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.message || 'Failed to fetch data');
                }
                
                const data = await response.json();
                
                if (data.status === 'error') {
                    throw new Error(data.message || 'An error occurred');
                }
                
                return data;
            } catch (error) {
                console.error('API Error:', error);
                showError(error.message || 'An error occurred while fetching data');
                throw error;
            }
        }

        // Get Quarterly Data
        async function getQuarterlyData() {
            const code = document.getElementById('code1').value;
            const field = document.getElementById('field1').value;
            const date = document.getElementById('date1').value;
            currentExportName = `quarterly_data_${code}_${date}.csv`;
            
            try {
                const response = await callApi('quarterly_data', {
                    accord_code: code,
                    field: field,
                    date: date
                });

                if (response.status === 'success') {
                    const data = response.data;
                    const resultDiv = document.getElementById('result');
                    
                    // Store data for export
                    currentData = [data];
                    
                    // Create a nice card to display the result
                    resultDiv.innerHTML = `
                        <div class="card border-success">
                            <div class="card-header bg-success text-white">
                                <i class="fas fa-chart-pie me-2"></i>Quarterly Data Result
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <p><strong><i class="fas fa-hashtag me-2"></i>Company Code:</strong> ${data.accord_code}</p>
                                        <p><strong><i class="far fa-calendar-alt me-2"></i>Date:</strong> ${new Date(data.date).toLocaleDateString()}</p>
                                        <p><strong><i class="fas fa-tag me-2"></i>Field:</strong> ${field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</p>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="p-3 bg-light rounded text-center">
                                            <h3 class="text-success mb-0">
                                                ${data.value !== null ? data.value + (field === 'ttm_pat_yoy_growth' ? '%' : '') : 'N/A'}
                                            </h3>
                                            <small class="text-muted">${field === 'ttm_pat_yoy_growth' ? 'YoY Growth' : 'Value'}</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>`;
                    document.getElementById('exportBtn').style.display = 'inline-block';
                }
            } catch (error) {
                // Error is already handled by callApi
            }
        }

        // Get Series Data
        async function getSeriesData() {
            const code = document.getElementById('code2').value;
            const start = document.getElementById('start_date').value;
            const end = document.getElementById('end_date').value;
            currentExportName = `series_data_${code}_${start}_to_${end}.csv`;
            
            try {
                const response = await callApi('series', {
                    accord_code: code,
                    start_date: start,
                    end_date: end
                });
                
                if (response.status === 'success') {
                    if (response.data && response.data.length > 0) {
                        displayTable(response.data);
                    } else {
                        showError('No data available for the selected date range');
                    }
                }
            } catch (error) {
                // Error is already handled by callApi
            }
        }

        // Get Matrix Data
        async function getMatrixData() {
            const date = document.getElementById('matrix_date').value;
            currentExportName = `all_companies_${date}.csv`;
            
            try {
                const response = await callApi('quarterly_matrix', {
                    date: date
                });
                
                if (response.status === 'success') {
                    if (response.data && response.data.length > 0) {
                        displayTable(response.data);
                    } else {
                        showError('No data available for the selected date');
                    }
                }
            } catch (error) {
                // Error is already handled by callApi
            }
        }

        // Get All PAT Growth
        async function getAllPatGrowth() {
            const code = document.getElementById('code4').value;
            currentExportName = `all_pat_growth_${code}.csv`;
            
            try {
                const response = await callApi('all_pat_growth', {
                    accord_code: code
                });
                
                if (response.status === 'success') {
                    if (response.data && response.data.length > 0) {
                        displayTable(response.data);
                    } else {
                        showError('No data available for the selected company');
                    }
                }
            } catch (error) {
                // Error is already handled by callApi
            }
        }

        // Export data to CSV
        function exportData() {
            if (!currentData || currentData.length === 0) {
                showError('No data to export');
                return;
            }

            const headers = Object.keys(currentData[0]);
            let csvContent = headers.join(',') + '\\n';
            
            currentData.forEach(row => {
                const values = headers.map(header => {
                    const value = row[header] !== null ? row[header] : '';
                    // Escape quotes and wrap in quotes if contains comma or quote
                    const escaped = String(value).replace(/"/g, '""');
                    return `"${escaped}"`;
                });
                csvContent += values.join(',') + '\\n';
            });

            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.setAttribute('href', url);
            link.setAttribute('download', currentExportName);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        // Add event listeners for better UX
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize tooltips
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });

            // Set default dates to today and one year ago
            const today = new Date();
            const oneYearAgo = new Date();
            oneYearAgo.setFullYear(today.getFullYear() - 1);
            
            document.getElementById('date1').valueAsDate = today;
            document.getElementById('start_date').valueAsDate = oneYearAgo;
            document.getElementById('end_date').valueAsDate = today;
            document.getElementById('matrix_date').valueAsDate = today;

            // Add keyboard support
            document.querySelectorAll('input').forEach(input => {
                input.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        const activeTab = document.querySelector('.tab-pane.active');
                        if (activeTab) {
                            const button = activeTab.querySelector('button:not(.export-btn)');
                            if (button) button.click();
                        }
                    }
                });
            });
        });
        </script>
    </body>
    </html>
    """

# API Endpoints
@app.route('/api/quarterly_data')
def api_quarterly_data():
    try:
        # Get and validate parameters
        accord_code = request.args.get('accord_code')
        field = request.args.get('field', 'ttm_pat_yoy_growth')
        date = request.args.get('date')
        
        # Validate inputs
        if not accord_code or not date:
            return jsonify({
                'status': 'error',
                'message': 'Both accord_code and date are required parameters'
            }), 400
            
        try:
            accord_code = int(accord_code)
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'accord_code must be a number'
            }), 400
        
        # Log the request
        app.logger.info(f"Quarterly data request - Code: {accord_code}, Field: {field}, Date: {date}")
        
        # Get the result from database
        result = get_quarterly_data(accord_code, field, date)
        
        # Log the result for debugging
        app.logger.info(f"Quarterly data result: {result}")
        
        if result is None:
            # If no result, try to get the latest available date for this company
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date FROM ttm_pat_yoy_growth 
                WHERE accord_code = ? 
                ORDER BY date DESC LIMIT 1
            """, (accord_code,))
            latest_date = cursor.fetchone()
            conn.close()
            
            if latest_date:
                return jsonify({
                    'status': 'error', 
                    'message': f'No data found for the specified date. Latest available date is {latest_date[0]}',
                    'suggestion': latest_date[0]
                }), 404
                
            return jsonify({
                'status': 'error', 
                'message': f'No data found for company code: {accord_code}'
            }), 404
            
        # Return successful response with consistent structure
        return jsonify({
            'status': 'success',
            'data': {
                'accord_code': accord_code,
                'date': date,
                'field': field,
                'value': result
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error in api_quarterly_data: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while processing your request',
            'details': str(e)
        }), 500

@app.route('/api/series')
def api_series():
    try:
        accord_code = request.args.get('accord_code')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        field = 'ttm_pat_yoy_growth'  # Default field as per requirements
        
        if not all([accord_code, start_date, end_date]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters'
            }), 400
            
        try:
            accord_code = int(accord_code)
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'accord_code must be a number'
            }), 400
        
        results = get_series(accord_code, field, start_date, end_date)
        
        # Convert results to list of dicts for JSON serialization
        data = [{'date': row[0], 'value': row[1]} for row in results]
        
        return jsonify({
            'status': 'success',
            'data': data
        })
        
    except Exception as e:
        app.logger.error(f"Error in api_series: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/quarterly_matrix')
def api_quarterly_matrix():
    try:
        date = request.args.get('date')
        field = 'ttm_pat_yoy_growth'  # Default field as per requirements
        
        if not date:
            return jsonify({
                'status': 'error',
                'message': 'Date parameter is required'
            }), 400
            
        results = get_quarterly_matrix(date, field)
        
        # Convert results to list of dicts for JSON serialization
        data = [{
            'accord_code': row[0],
            'company_name': row[1],
            'sector': row[2],
            'mcap_category': row[3],
            'value': row[4]
        } for row in results]
        
        return jsonify({
            'status': 'success',
            'data': data
        })
        
    except Exception as e:
        app.logger.error(f"Error in api_quarterly_matrix: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/all_pat_growth')
def api_all_pat_growth():
    try:
        accord_code = request.args.get('accord_code')
        field = 'ttm_pat_yoy_growth'  # Default field as per requirements
        
        if not accord_code:
            return jsonify({
                'status': 'error',
                'message': 'accord_code parameter is required'
            }), 400
            
        try:
            accord_code = int(accord_code)
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'accord_code must be a number'
            }), 400
        
        results = get_all_pat_growth(accord_code, field)
        
        # Convert results to list of dicts for JSON serialization
        data = [{'date': row[0], 'value': row[1]} for row in results]
        
        return jsonify({
            'status': 'success',
            'data': data
        })
        
    except Exception as e:
        app.logger.error(f"Error in api_all_pat_growth: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Create database directory if it doesn't exist
    os.makedirs('database', exist_ok=True)
    app.run(debug=True, port=5000)