# run_flask.py
from flask import Flask, jsonify
import sqlite3
import os
from pathlib import Path

app = Flask(__name__)

def get_db_connection():
    db_path = Path("database/ttm_pat_yoy_growth.db")
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at: {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Financial Data Analyzer</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { padding: 20px; }
            .card { margin-top: 20px; }
            pre { background: #f8f9fa; padding: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Financial Data Analyzer</h1>
            <div class="card">
                <div class="card-header">
                    <h3>Database Connection Test</h3>
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
                resultDiv.innerHTML = `
                    <div class="alert alert-info">
                        <div class="spinner-border spinner-border-sm" role="status"></div>
                        Testing database connection...
                    </div>`;
                
                try {
                    const response = await fetch('/test');
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        let tablesHtml = data.tables.map(table => `
                            <div class="card mt-3">
                                <div class="card-header">
                                    Table: ${table.name}
                                </div>
                                <div class="card-body">
                                    <p>Columns: ${table.columns.join(', ')}</p>
                                    <p>Sample data (first 3 rows):</p>
                                    <pre>${JSON.stringify(table.sample_data, null, 2)}</pre>
                                </div>
                            </div>
                        `).join('');
                        
                        resultDiv.innerHTML = `
                            <div class="alert alert-success">
                                <h4>✅ Connection Successful!</h4>
                                <p>Found ${data.tables.length} tables in the database.</p>
                                ${tablesHtml}
                            </div>`;
                    } else {
                        throw new Error(data.message || 'Unknown error occurred');
                    }
                } catch (error) {
                    resultDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <h4>❌ Connection Failed</h4>
                            <p>${error.message}</p>
                            <p>Database path: ${window.location.origin}/dbinfo</p>
                        </div>`;
                }
            }
        </script>
    </body>
    </html>
    """

@app.route('/test')
def test_connection():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        result = []
        for table in tables:
            table_name = table['name']
            
            # Get columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col['name'] for col in cursor.fetchall()]
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample_data = [dict(row) for row in cursor.fetchall()]
            
            result.append({
                'name': table_name,
                'columns': columns,
                'sample_data': sample_data
            })
        
        conn.close()
        return jsonify({
            'status': 'success',
            'tables': result
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'db_path': str(Path("database/ttm_pat_yoy_growth.db").absolute()),
            'exists': Path("database/ttm_pat_yoy_growth.db").exists()
        }), 500

@app.route('/dbinfo')
def db_info():
    db_path = Path("database/ttm_pat_yoy_growth.db").absolute()
    return jsonify({
        'path': str(db_path),
        'exists': db_path.exists(),
        'size': f"{db_path.stat().st_size / (1024*1024):.2f} MB" if db_path.exists() else 'N/A'
    })

if __name__ == '__main__':
    print("Starting Financial Data Analyzer...")
    print("=" * 50)
    print("IMPORTANT: Make sure the database file exists at:")
    print(f"  {Path('database/ttm_pat_yoy_growth.db').absolute()}")
    print("\nIf you see any errors, please check:")
    print("1. Is the database file in the correct location?")
    print("2. Does the application have permission to read the file?")
    print("3. Is the database file not corrupted?")
    print("\n" + "=" * 50)
    print("Visit http://localhost:5000 in your web browser")
    print("Press Ctrl+C to stop the server")
    print("=" * 50 + "\n")
    
    # Run the app
    app.run(debug=True, port=5000)