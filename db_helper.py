import sqlite3
from functools import lru_cache
import configparser
import os
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('query_log.txt'),
        logging.StreamHandler()
    ]
)

# Read configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Database connection
def get_db_connection():
    db_path = os.path.join('database', 'ttm_pat_yoy_growth.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Create necessary tables and indexes if they don't exist
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ttm_pat_yoy_growth (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        accord_code INTEGER NOT NULL,
        company_name TEXT,
        sector TEXT,
        mcap_category TEXT,
        date TEXT,
        ttm_pat_yoy_growth REAL,
        UNIQUE(accord_code, date)
    )
    ''')
    
    # Create index if it doesn't exist
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_accord_code_date 
    ON ttm_pat_yoy_growth (accord_code, date)
    ''')
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

@lru_cache(maxsize=1024)
def get_quarterly_data(accord_code: int, field: str, date: str) -> float:
    """Get a single data point for a company on a specific date"""
    start_time = time.perf_counter()
    result = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Validate field
        valid_fields = ['ttm_pat_yoy_growth', 'sector', 'mcap_category', 'company_name']
        if field not in valid_fields:
            raise ValueError(f"Invalid field. Must be one of: {', '.join(valid_fields)}")
        
        # Convert input date to match database format if needed
        if ' ' not in date and ':' not in date:
            # If date is in YYYY-MM-DD format, add time
            date = f"{date} 00:00:00"
            
        # Try exact match first
        query = f"""
            SELECT {field} 
            FROM ttm_pat_yoy_growth 
            WHERE accord_code = ? AND date = ?
            LIMIT 1
        """
        cursor.execute(query, (accord_code, date))
        result = cursor.fetchone()
        
        # If no exact match, try with date range (YYYY-MM format)
        if not result:
            query = f"""
                SELECT {field} 
                FROM ttm_pat_yoy_growth 
                WHERE accord_code = ? AND date LIKE ?
                ORDER BY date DESC
                LIMIT 1
            """
            month_pattern = f"{date[:7]}%"  # Match YYYY-MM-* pattern
            cursor.execute(query, (accord_code, month_pattern))
            result = cursor.fetchone()
        
        return result[0] if result else None
        
    except Exception as e:
        logging.error(f"Error in get_quarterly_data: {str(e)}")
        raise
    finally:
        elapsed = (time.perf_counter() - start_time) * 1000
        logging.info(
            f"get_quarterly_data - Code: {accord_code}, Field: {field}, "
            f"Date: {date}, Time: {elapsed:.2f}ms, "
            f"Success: {result is not None if 'result' in locals() else False}"
        )
        conn.close()

@lru_cache(maxsize=512)
def get_series(accord_code: int, field: str, start_date: str, end_date: str) -> list:
    """Get time series data for a company between dates"""
    start_time = time.perf_counter()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = f"""
            SELECT date, {field}
            FROM ttm_pat_yoy_growth
            WHERE accord_code = ? 
            AND date BETWEEN ? AND ?
            ORDER BY date
        """
        cursor.execute(query, (accord_code, start_date, end_date))
        results = cursor.fetchall()
        
        return [(row[0], row[1]) for row in results]
        
    except Exception as e:
        logging.error(f"Error in get_series: {str(e)}")
        raise
    finally:
        elapsed = (time.perf_counter() - start_time) * 1000
        logging.info(
            f"get_series - Code: {accord_code}, Field: {field}, "
            f"Range: {start_date} to {end_date}, "
            f"Time: {elapsed:.2f}ms, Rows: {len(results) if 'results' in locals() else 0}"
        )
        conn.close()

@lru_cache(maxsize=512)
def get_quarterly_matrix(date: str, field: str) -> list:
    """Get data for all companies on a specific date"""
    start_time = time.perf_counter()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = f"""
            SELECT accord_code, company_name, sector, mcap_category, {field}
            FROM ttm_pat_yoy_growth
            WHERE date LIKE ? || '%'
        """
        cursor.execute(query, (date,))
        results = cursor.fetchall()
        
        return [tuple(row) for row in results]
        
    except Exception as e:
        logging.error(f"Error in get_quarterly_matrix: {str(e)}")
        raise
    finally:
        elapsed = (time.perf_counter() - start_time) * 1000
        logging.info(
            f"get_quarterly_matrix - Date: {date}, Field: {field}, "
            f"Time: {elapsed:.2f}ms, Rows: {len(results) if 'results' in locals() else 0}"
        )
        conn.close()

@lru_cache(maxsize=512)
def get_all_pat_growth(accord_code: int, field: str) -> list:
    """Get all historical data for a specific company"""
    start_time = time.perf_counter()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = f"""
            SELECT date, {field}
            FROM ttm_pat_yoy_growth
            WHERE accord_code = ?
            ORDER BY date
        """
        cursor.execute(query, (accord_code,))
        results = cursor.fetchall()
        
        return [(row[0], row[1]) for row in results]
        
    except Exception as e:
        logging.error(f"Error in get_all_pat_growth: {str(e)}")
        raise
    finally:
        elapsed = (time.perf_counter() - start_time) * 1000
        logging.info(
            f"get_all_pat_growth - Code: {accord_code}, Field: {field}, "
            f"Time: {elapsed:.2f}ms, Rows: {len(results) if 'results' in locals() else 0}"
        )
        conn.close()

def clear_cache():
    """Clear all cached queries"""
    get_quarterly_data.cache_clear()
    get_series.cache_clear()
    get_quarterly_matrix.cache_clear()
    get_all_pat_growth.cache_clear()
    logging.info("All caches cleared")

def get_cache_info() -> dict:
    """Get cache statistics"""
    return {
        'quarterly_data': {
            'hits': get_quarterly_data.cache_info().hits,
            'misses': get_quarterly_data.cache_info().misses,
            'maxsize': get_quarterly_data.cache_info().maxsize,
            'currsize': get_quarterly_data.cache_info().currsize
        },
        'series': {
            'hits': get_series.cache_info().hits,
            'misses': get_series.cache_info().misses,
            'maxsize': get_series.cache_info().maxsize,
            'currsize': get_series.cache_info().currsize
        },
        'quarterly_matrix': {
            'hits': get_quarterly_matrix.cache_info().hits,
            'misses': get_quarterly_matrix.cache_info().misses,
            'maxsize': get_quarterly_matrix.cache_info().maxsize,
            'currsize': get_quarterly_matrix.cache_info().currsize
        },
        'all_pat_growth': {
            'hits': get_all_pat_growth.cache_info().hits,
            'misses': get_all_pat_growth.cache_info().misses,
            'maxsize': get_all_pat_growth.cache_info().maxsize,
            'currsize': get_all_pat_growth.cache_info().currsize
        }
    }