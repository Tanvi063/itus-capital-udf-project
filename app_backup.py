from flask import Flask, render_template, request, jsonify
from db_helper import (
    get_quarterly_data,
    get_series,
    get_quarterly_matrix,
    get_all_pat_growth
)
from datetime import datetime
import json
import sqlite3
import os
from pathlib import Path

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
    <html>
    <head>
        <title>Financial Data Viewer</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 1000px; margin: 0 auto; }
            .form-group { margin-bottom: 15px; }
            label { display: inline-block; width: 150px; }
            input, select { padding: 5px; width: 200px; }
            button { padding: 8px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .result { margin-top: 20px; padding: 15px; background: #f9f9f9; border-radius: 5px; }
            .alert { margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Financial Data Viewer</h1>
            
            <div class="form-group">
                <h3>1. Get Quarterly Data</h3>
                <label>Company Code:</label>
                <input type="number" id="code1" value="100186"><br>
                <label>Field:</label>
                <select id="field1">
                    <option value="ttm_pat_yoy_growth">TTM PAT YoY Growth</option>
                    <option value="sector">Sector</option>
                    <option value="mcap_category">Market Cap</option>
                </select><br>
                <label>Date:</label>
                <input type="date" id="date1" value="2023-03-31"><br>
                <button onclick="getQuarterlyData()" class="btn btn-primary">Get Data</button>
                <div id="result1" class="mt-3"></div>
            </div>

            <div class="form-group">
                <h3>2. Get Date Range Data</h3>
                <label>Company Code:</label>
                <input type="number" id="code2" value="100186"><br>
                <label>Start Date:</label>
                <input type="date" id="start_date" value="2022-03-31"><br>
                <label>End Date:</label>
                <input type="date" id="end_date" value="2023-09-30"><br>
                <button onclick="getSeriesData()" class="btn btn-primary">Get Series</button>
                <div id="result2" class="result"></div>
            </div>

            <div class="form-group">
                <h3>3. Get All Companies (on a date)</h3>
                <label>Date:</label>
                <input type="date" id="matrix_date" value="2023-06-30"><br>
                <button onclick="getMatrixData()" class="btn btn-primary">Get All Companies</button>
                <div id="result3" class="result"></div>
            </div>

            <div class="form-group">
                <h3>4. Get All Data for a Company</h3>
                <label>Company Code:</label>
                <input type="number" id="code4" value="100186"><br>
                <button onclick="getAllPatGrowth()" class="btn btn-primary">Get All Data</button>
                <div id="result4" class="result"></div>
            </div>
        </div>

        <script>
        function displayTable(data, containerId) {
            const container = document.getElementById(containerId);
            if (!data || data.length === 0) {
                container.innerHTML = "<div class='alert alert-info'>No data found</div>";
                return;
            }
            
            let html = '<table class="table table-striped table-bordered"><thead class="table-dark"><tr>';
            // Headers
            Object.keys(data[0]).forEach(key => {
                html += `<th>${key}</th>`;
            });
            html += '</tr></thead><tbody>';
            
            // Rows
            data.forEach(row => {
                html += '<tr>';
                Object.values(row).forEach(value => {
                    html += `<td>${value !== null ? value : 'N/A'}</td>`;
                });
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        async function callApi(endpoint, params = {}) {
            try {
                const queryString = new URLSearchParams(params).toString();
                const response = await fetch(`/api/${endpoint}?${queryString}`);
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.message || 'Failed to fetch data');
                }
                return await response.json();
            } catch (error) {
                console.error('API Error:', error);
                throw error;
            }
        }

        async function getQuarterlyData() {
            const code = document.getElementById('code1').value;
            const field = document.getElementById('field1').value;
            const date = document.getElementById('date1').value;
            const resultDiv = document.getElementById('result1');
            
            try {
                // Show loading state
                resultDiv.innerHTML = '<div class="alert alert-info">Loading data...</div>';
                
                const response = await callApi('quarterly_data', {
                    accord_code: code,
                    field: field,
                    date: date
                });

                if (response.status === 'success') {
                    const data = response.data;
                    resultDiv.innerHTML = `
                        <div class="alert alert-success">
                            <h5>Quarterly Data Result</h5>
                            <div class="mt-2">
                                <p><strong>Company Code:</strong> ${data.accord_code}</p>
                                <p><strong>Date:</strong> ${data.date}</p>
                                <p><strong>${field}:</strong> ${data.value !== null ? data.value : 'No data available'}</p>
                            </div>
                        </div>
                    `;
                } else if (response.status === 'error' && response.suggestion) {
                    // Update the date input with the suggested date
                    document.getElementById('date1').value = response.suggestion.split(' ')[0];
                    resultDiv.innerHTML = `
                        <div class="alert alert-warning">
                            <p>${response.message}</p>
                            <button class="btn btn-sm btn-primary mt-2" onclick="getQuarterlyData()">
                                Try with suggested date
                            </button>
                        </div>
                    `;
                } else {
                    throw new Error(response.message || 'No data found');
                }
            } catch (error) {
                console.error('Error:', error);
                resultDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error:</strong> ${error.message || 'An error occurred while fetching data'}
                    </div>
                `;
            }
        }

        async function getSeriesData() {
            const code = document.getElementById('code2').value;
            const start = document.getElementById('start_date').value;
            const end = document.getElementById('end_date').value;
            const resultDiv = document.getElementById('result2');
            
            try {
                resultDiv.innerHTML = '<div class="alert alert-info">Loading data...</div>';
                const response = await callApi('series', {
                    accord_code: code,
                    start_date: start,
                    end_date: end
                });
                
                if (response.status === 'success') {
                    displayTable(response.data, 'result2');
                } else {
                    throw new Error(response.message || 'Failed to fetch data');
                }
            } catch (error) {
                console.error('Error:', error);
                resultDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error:</strong> ${error.message || 'An error occurred while fetching data'}
                    </div>
                `;
            }
        }

        async function getMatrixData() {
            const date = document.getElementById('matrix_date').value;
            const resultDiv = document.getElementById('result3');
            
            try {
                resultDiv.innerHTML = '<div class="alert alert-info">Loading data...</div>';
                const response = await callApi('quarterly_matrix', {
                    date: date
                });
                
                if (response.status === 'success') {
                    displayTable(response.data, 'result3');
                } else {
                    throw new Error(response.message || 'Failed to fetch data');
                }
            } catch (error) {
                console.error('Error:', error);
                resultDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error:</strong> ${error.message || 'An error occurred while fetching data'}
                    </div>
                `;
            }
        }

        async function getAllPatGrowth() {
            const code = document.getElementById('code4').value;
            const resultDiv = document.getElementById('result4');
            
            try {
                resultDiv.innerHTML = '<div class="alert alert-info">Loading data...</div>';
                const response = await callApi('all_pat_growth', {
                    accord_code: code
                });
                
                if (response.status === 'success') {
                    displayTable(response.data, 'result4');
                } else {
                    throw new Error(response.message || 'Failed to fetch data');
                }
            } catch (error) {
                console.error('Error:', error);
                resultDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error:</strong> ${error.message || 'An error occurred while fetching data'}
                    </div>
                `;
            }
        }
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
                SELECT date FROM ttm_pat_yog_growth 
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
        accord_code = int(request.args.get('accord_code'))
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        field = 'ttm_pat_yoy_growth'  # Default field as per requirements
        
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
        }), 400

@app.route('/api/quarterly_matrix')
def api_quarterly_matrix():
    try:
        date = request.args.get('date')
        field = 'ttm_pat_yoy_growth'  # Default field as per requirements
        
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
        }), 400

@app.route('/api/all_pat_growth')
def api_all_pat_growth():
    try:
        accord_code = int(request.args.get('accord_code'))
        field = 'ttm_pat_yoy_growth'  # Default field as per requirements
        
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
        }), 400

if __name__ == '__main__':
    # Create database directory if it doesn't exist
    os.makedirs('database', exist_ok=True)
    app.run(debug=True, port=5000)