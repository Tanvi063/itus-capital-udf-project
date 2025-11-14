# run.py
from flask import Flask, jsonify
import sqlite3
import os
import sys
from pathlib import Path

app = Flask(__name__)

def get_absolute_db_path():
    """Get the absolute path to the database file."""
    db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database')
    db_path = os.path.join(db_dir, 'ttm_pat_yoy_growth.db')
    return db_path

def get_db_connection():
    """Get a database connection with better error handling."""
    db_path = get_absolute_db_path()
    try:
        print(f"Attempting to connect to database at: {db_path}")  # Debug print
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found at: {db_path}")
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")  # Debug print
        raise

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Financial Data Analyzer</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1>Financial Data Analyzer</h1>
            <div class="card mt-4">
                <div class="card-header">
                    <h3>Database Test</h3>
                </div>
                <div class="card-body">
                    <button onclick="testConnection()" class="btn btn-primary">Test Database Connection</button>
                    <div id="result" class="mt-3"></div>
                </div>
            </div>
        </div>
        <script>
            async function testConnection() {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = '<div class="spinner-border text-primary" role="status"></div> Testing connection...';
                
                try {
                    const response = await fetch('/test');
                    const data = await response.json();
                    if (data.status === 'success') {
                        resultDiv.innerHTML = `
                            <div class="alert alert-success mt-3">
                                <h4>Success!</h4>
                                <p>Database connection successful!</p>
                                <p>Found tables: ${data.tables.map(t => t.name).join(', ')}</p>
                            </div>
                        `;
                    } else {
                        throw new Error(data.message || 'Unknown error occurred');
                    }
                } catch (error) {
                    resultDiv.innerHTML = `
                        <div class="alert alert-danger mt-3">
                            <h4>Error</h4>
                            <p>${error.message}</p>
                            <p>Database path: ${window.location.origin}/database_path</p>
                        </div>
                    `;
                }
            }
        </script>
    </body>
    </html>
    """

@app.route('/database_path')
def get_db_path():
    """Endpoint to get the database path for debugging."""
    return jsonify({
        "status": "success",
        "path": get_absolute_db_path(),
        "exists": os.path.exists(get_absolute_db_path())
    })

@app.route('/test')
def test_connection():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        # Convert Row objects to dictionaries
        tables_list = [dict(row) for row in tables]
        
        return jsonify({
            "status": "success",
            "tables": tables_list
        })
    except Exception as e:
        error_message = str(e)
        print(f"Error in test_connection: {error_message}")  # Debug print
        return jsonify({
            "status": "error",
            "message": error_message,
            "db_path": get_absolute_db_path(),
            "db_exists": os.path.exists(get_absolute_db_path())
        }), 500

if __name__ == '__main__':
    print("Starting Financial Data Analyzer...")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Database path: {get_absolute_db_path()}")
    print(f"Database exists: {os.path.exists(get_absolute_db_path())}")
    
    app.run(debug=True, port=5000)