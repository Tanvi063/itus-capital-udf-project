# Financial Data Analyzer

A Flask-based web application for analyzing financial data with a modern, responsive UI.

## Features

- View quarterly financial data for companies
- Analyze data across date ranges
- Export data to CSV
- Responsive design for all devices
- Error handling and user feedback

## Prerequisites

- Python 3.8+
- SQLite3
- Modern web browser

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/financial-data-analyzer.git
   cd financial-data-analyzer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Database setup:
   - Ensure the `database` directory exists
   - Place your SQLite database file at `database/ttm_pat_yoy_growth.db`

## Usage

1. Start the Flask development server:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Use the web interface to:
   - View quarterly data
   - Analyze date ranges
   - Export data to CSV

## Project Structure

```
financial-data-analyzer/
├── app.py                # Main Flask application
├── db_helper.py          # Database helper functions
├── requirements.txt      # Python dependencies
├── database/             # Database directory
│   └── ttm_pat_yoy_growth.db  # SQLite database
└── README.md             # This file
```

## API Endpoints

- `GET /api/quarterly_data` - Get quarterly data
- `GET /api/series` - Get data series
- `GET /api/quarterly_matrix` - Get quarterly matrix
- `GET /api/all_pat_growth` - Get all PAT growth data

## Error Handling

The application includes comprehensive error handling for:
- Invalid input parameters
- Database connection issues
- Missing data
- Server errors

## Testing

To test the application:

1. Ensure the Flask server is running
2. Open the web interface in your browser
3. Test different queries using the UI
4. Verify data is displayed correctly

## Future Enhancements

- User authentication
- Advanced filtering and sorting
- Data visualization
- Batch processing
- API rate limiting