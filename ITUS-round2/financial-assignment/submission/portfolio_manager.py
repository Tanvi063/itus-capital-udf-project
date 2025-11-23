import pandas as pd
import numpy as np
import yfinance as yf
import logging
from datetime import datetime, timedelta
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('portfolio_analysis.log'),
        logging.StreamHandler()
    ]
)

class PortfolioManager:
    def __init__(self, universe_path, prices_path, start_date, end_date, benchmark_ticker="^NSEI"):
        """Initialize the PortfolioManager with file paths and date range."""
        self.universe_path = universe_path
        self.prices_path = prices_path
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        self.benchmark_ticker = benchmark_ticker
        self.universe = None
        self.prices = None
        self.benchmark = None
        self.portfolio_metrics = {}
        os.makedirs('logs', exist_ok=True)
        logging.info(f"PortfolioManager initialized for period {start_date} to {end_date}")

    def _load_files(self):
        """Load and preprocess the input files."""
        try:
            # Load and clean universe data
            self.universe = pd.read_csv(self.universe_path)
            self.universe = self.universe.rename(columns={
                'Accord Code': 'accord_code',
                'Company Name': 'company_name',
                'Sector': 'sector'
            })
            
            # Load and clean price data
            self.prices = pd.read_csv(self.prices_path)
            self.prices = self.prices.rename(columns={
                'date': 'date',
                'price': 'price'
            })
            self.prices['date'] = pd.to_datetime(self.prices['date'])
            self.prices = self.prices.sort_values(['accord_code', 'date'])
            self.prices['price'] = pd.to_numeric(self.prices['price'], errors='coerce')
            
            logging.info(f"Loaded {len(self.universe)} stocks and {len(self.prices)} price records")
            
        except Exception as e:
            logging.error(f"Error loading files: {str(e)}")
            raise

    def _validate_universe(self):
        """Check for duplicate accord codes in the universe."""
        if self.universe is None:
            raise ValueError("Universe data not loaded. Call _load_files() first.")
            
        duplicate_codes = self.universe['accord_code'].duplicated()
        if duplicate_codes.any():
            dup_codes = self.universe[duplicate_codes]['accord_code'].unique()
            error_msg = f"Duplicate accord codes found: {', '.join(dup_codes)}"
            logging.error(error_msg)
            raise ValueError(error_msg)
            
        logging.info("Universe validation passed - no duplicate accord codes found")

    def _get_last_price_on_or_before(self, target_date):
        """Get the last available price on or before the target date for each stock."""
        if self.prices is None:
            raise ValueError("Price data not loaded. Call _load_files() first.")
            
        mask = self.prices['date'] <= target_date
        if not mask.any():
            raise ValueError(f"No price data found on or before {target_date}")
            
        filtered = self.prices[mask]
        latest_idx = filtered.groupby('accord_code')['date'].idxmax()
        result = filtered.loc[latest_idx, ['accord_code', 'date', 'price']]
        result = result.rename(columns={
            'date': 'matched_date',
            'price': 'matched_price'
        })
        return result

    def compute_weights(self):
        """Compute equal weights for all stocks in the universe."""
        if self.universe is None:
            raise ValueError("Universe data not loaded. Call _load_files() first.")
            
        n_stocks = len(self.universe)
        self.universe['weight'] = 1.0 / n_stocks
        logging.info(f"Computed equal weights for {n_stocks} stocks (1/{n_stocks} each)")

    def _fetch_benchmark(self):
        """Download benchmark data using yfinance with proper date handling."""
        try:
            # Get data with buffer days to ensure we have the required dates
            start = (self.start_date - pd.Timedelta(days=30)).strftime('%Y-%m-%d')
            end = (self.end_date + pd.Timedelta(days=30)).strftime('%Y-%m-%d')
            
            logging.info(f"Downloading benchmark data for {self.benchmark_ticker} from {start} to {end}")
            
            bench = yf.download(
                self.benchmark_ticker,
                start=start,
                end=end,
                progress=False
            )
            
            if bench.empty:
                raise ValueError(f"No benchmark data found for {self.benchmark_ticker}")
                
            # Keep only the 'Close' column and rename it
            self.benchmark = bench[['Close']].copy()
            self.benchmark.columns = ['bench_close']
            
            # Calculate daily returns
            self.benchmark['bench_ret'] = self.benchmark['bench_close'].pct_change()
            
            # Get the benchmark price on start and end dates
            self.benchmark_start_price = self._get_last_price_on_or_before_benchmark(self.start_date)
            self.benchmark_end_price = self._get_last_price_on_or_before_benchmark(self.end_date)
            
            logging.info(f"Successfully downloaded {len(self.benchmark)} days of benchmark data")
            logging.info(f"Benchmark price on {self.start_date.date()}: {self.benchmark_start_price}")
            logging.info(f"Benchmark price on {self.end_date.date()}: {self.benchmark_end_price}")
            
        except Exception as e:
            logging.error(f"Error downloading benchmark data: {str(e)}")
            raise
            
    def _get_last_price_on_or_before_benchmark(self, target_date):
        """Get the last available benchmark price on or before the target date."""
        if self.benchmark is None:
            self._fetch_benchmark()
        
        # Get all dates on or before target date
        mask = self.benchmark.index <= target_date
        if not mask.any():
            raise ValueError(f"No benchmark data found on or before {target_date}")
        
        # Get the latest date's close price
        last_date = self.benchmark[mask].index.max()
        return self.benchmark.loc[last_date, 'bench_close']

    def compute_returns(self):
        """Compute returns for each stock between start and end dates."""
        if self.universe is None or self.prices is None:
            raise ValueError("Data not loaded. Call _load_files() first.")
            
        # Get prices for start and end dates
        start_prices = self._get_last_price_on_or_before(self.start_date)
        end_prices = self._get_last_price_on_or_before(self.end_date)
        
        # Rename columns for clarity
        start_prices = start_prices.rename(columns={
            'matched_date': 'date_start_matched',
            'matched_price': 'price_start'
        })

        end_prices = end_prices.rename(columns={
            'matched_date': 'date_end_matched',
            'matched_price': 'price_end'
        })
        
        # Merge with universe
        self.universe = self.universe.merge(
            start_prices,
            on='accord_code',
            how='left'
        )
        
        self.universe = self.universe.merge(
            end_prices,
            on='accord_code',
            how='left'
        )
        
        # Calculate absolute returns
        self.universe['abs_return'] = (self.universe['price_end'] / self.universe['price_start']) - 1
        
        # Log any missing prices
        missing_start = self.universe[self.universe['price_start'].isna()]
        missing_end = self.universe[self.universe['price_end'].isna()]
        
        if not missing_start.empty or not missing_end.empty:
            os.makedirs('logs', exist_ok=True)
            missing_start[['accord_code', 'company_name']].to_csv('logs/missing_start_prices.csv', index=False)
            missing_end[['accord_code', 'company_name']].to_csv('logs/missing_end_prices.csv', index=False)
            
            logging.warning(
                f"{len(missing_start)} stocks missing start prices, "
                f"{len(missing_end)} missing end prices. "
                "Check logs/missing_*_prices.csv for details."
            )
        
        logging.info(
            f"Computed returns for {len(self.universe) - len(missing_start) - len(missing_end)} stocks"
        )

    def compute_beta(self):
        """Compute beta for each stock relative to the benchmark."""
        if self.benchmark is None:
            self._fetch_benchmark()
            
        if self.prices is None:
            raise ValueError("Price data not loaded. Call _load_files() first.")
            
        try:
            # Calculate daily returns for each stock
            self.prices['stock_ret'] = self.prices.groupby('accord_code')['price'].pct_change()
            
            # Prepare stock returns
            stock_rets = self.prices[['date', 'accord_code', 'stock_ret']].dropna()
            stock_rets['date'] = pd.to_datetime(stock_rets['date'])
            
            # Prepare benchmark returns - keep the index as date
            bench_rets = self.benchmark[['bench_ret']].copy()
            bench_rets = bench_rets.reset_index()  # Convert index to column
            bench_rets = bench_rets.rename(columns={'Date': 'date'})  # yfinance uses 'Date' as index name
            
            # Ensure date columns are in datetime format
            bench_rets['date'] = pd.to_datetime(bench_rets['date'])
            
            # Drop any rows with NaN values
            bench_rets = bench_rets.dropna(subset=['bench_ret'])
            
            logging.info(f"Benchmark returns sample:\n{bench_rets.head()}")
            logging.info(f"Stock returns sample:\n{stock_rets.head()}")
            
            # Debug: Print the columns in bench_rets
            logging.info(f"Benchmark columns: {bench_rets.columns.tolist()}")
            logging.info(f"Sample benchmark data:\n{bench_rets.head()}")
            
            # Ensure we have enough data points
            if len(bench_rets) < 5:
                raise ValueError("Insufficient benchmark data points for beta calculation")
                
            # Ensure we have stock returns
            if stock_rets.empty:
                raise ValueError("No stock returns data available for beta calculation")
            
            # Merge stock returns with benchmark returns
            merged = pd.merge(
                stock_rets,
                bench_rets,
                on='date',
                how='inner'
            )
            
            # Log merge results
            logging.info(f"Merged data shape: {merged.shape}")
            logging.info(f"Unique stocks in merged data: {merged['accord_code'].nunique()}")
            
            # Calculate beta for each stock
            betas = []
            for accord_code, group in merged.groupby('accord_code'):
                if len(group) >= 5:  # Require at least 5 observations
                    try:
                        cov_matrix = np.cov(group['stock_ret'], group['bench_ret'])
                        if cov_matrix[1, 1] != 0:  # Avoid division by zero
                            beta = cov_matrix[0, 1] / cov_matrix[1, 1]
                            betas.append({'accord_code': accord_code, 'beta': beta})
                    except Exception as e:
                        logging.warning(f"Error calculating beta for {accord_code}: {str(e)}")
            
            if not betas:
                raise ValueError("No valid betas could be calculated for any stock")
                
            betas_df = pd.DataFrame(betas)
            
            # Ensure we don't have duplicate columns before merging
            if 'beta' in self.universe.columns:
                self.universe = self.universe.drop(columns=['beta'])
            
            # Merge betas back to universe
            self.universe = self.universe.merge(betas_df, on='accord_code', how='left')
            
            # Log any stocks with NaN beta
            nan_beta = self.universe[self.universe['beta'].isna()]
            if not nan_beta.empty:
                os.makedirs('logs', exist_ok=True)
                nan_beta[['accord_code', 'company_name']].to_csv('logs/nan_beta_stocks.csv', index=False)
                logging.warning(
                    f"Could not calculate beta for {len(nan_beta)} stocks. "
                    "Check logs/nan_beta_stocks.csv"
                )
            
            logging.info(f"Computed beta for {len(self.universe) - len(nan_beta)} stocks")
            
            # Calculate weighted beta
            self.universe['weighted_beta'] = self.universe['beta'] * self.universe['weight']
            
        except Exception as e:
            logging.error(f"Error in compute_beta: {str(e)}", exc_info=True)
            if 'merged' in locals():
                logging.info(f"Merged data sample:\n{merged.head()}")
                if not merged.empty:
                    logging.info(f"Unique stocks in merged data: {merged['accord_code'].nunique()}")
                    logging.info(f"Date range in merged data: {merged['date'].min()} to {merged['date'].max()}")
            raise

    def compute_weighted_metrics(self):
        """Compute weighted return and beta for each stock."""
        if ('weight' not in self.universe.columns or 
            'abs_return' not in self.universe.columns or 
            'beta' not in self.universe.columns):
            raise ValueError("Weights, returns, and beta must be computed first")
            
        self.universe['weighted_return'] = self.universe['abs_return'] * self.universe['weight']
        self.universe['weighted_beta'] = self.universe['beta'] * self.universe['weight']
        
        logging.info("Computed weighted metrics")

    def sector_aggregation(self):
        """Aggregate metrics by sector."""
        if ('sector' not in self.universe.columns or 
            'weighted_return' not in self.universe.columns):
            raise ValueError("Sector information and weighted metrics must be computed first")
            
        sector_agg = self.universe.groupby('sector').agg({
            'weight': 'sum',
            'weighted_return': 'sum',
            'weighted_beta': 'sum'
        }).reset_index()
        
        sector_agg['sector_beta'] = sector_agg['weighted_beta'] / sector_agg['weight']
        
        sector_agg = sector_agg.rename(columns={
            'weight': 'sector_weight',
            'weighted_return': 'sector_weighted_return',
            'weighted_beta': 'sector_sum_weighted_beta'
        })
        
        logging.info(f"Aggregated metrics for {len(sector_agg)} sectors")
        return sector_agg

    def portfolio_aggregation(self):
        """Compute portfolio-level metrics."""
        if ('weighted_return' not in self.universe.columns or 
            'weighted_beta' not in self.universe.columns):
            raise ValueError("Weighted metrics must be computed first")
            
        portfolio_return = self.universe['weighted_return'].sum()
        portfolio_beta = self.universe['weighted_beta'].sum()
        
        self.portfolio_metrics = {
            'Portfolio Return': portfolio_return,
            'Portfolio Beta': portfolio_beta
        }
        
        logging.info(f"Portfolio return: {portfolio_return:.2%}, beta: {portfolio_beta:.2f}")
        
        summary = pd.DataFrame({
            'Metric': ['Portfolio Return', 'Portfolio Beta'],
            'Value': [portfolio_return, portfolio_beta]
        })
        
        return summary

    def export_excel(self, filename='output.xlsx'):
        """Export results to an Excel file with multiple sheets."""
        if self.universe is None:
            raise ValueError("No data to export. Run the analysis first.")
            
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            # Stock Level sheet
            stock_cols = [
                'accord_code', 'company_name', 'sector', 'weight',
                'price_start', 'date_start_matched',
                'price_end', 'date_end_matched',
                'abs_return', 'beta', 'weighted_return', 'weighted_beta'
            ]
            
            stock_df = self.universe[stock_cols].copy()
            stock_df.to_excel(writer, sheet_name='Stock Level', index=False)
            
            # Sector Aggregates sheet
            sector_agg = self.sector_aggregation()
            sector_agg[['sector', 'sector_weight', 'sector_weighted_return', 'sector_beta']].to_excel(
                writer, sheet_name='Aggregates', index=False
            )
            
            # Summary sheet
            summary = self.portfolio_aggregation()
            summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Formatting
            workbook = writer.book
            stock_worksheet = writer.sheets['Stock Level']
            
            # Define formats
            num_format = workbook.add_format({'num_format': '0.00'})
            pct_format = workbook.add_format({'num_format': '0.00%'})
            date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
            
            # Apply formats to columns
            stock_worksheet.set_column('A:A', 15)  # accord_code
            stock_worksheet.set_column('B:B', 30)  # company_name
            stock_worksheet.set_column('C:C', 20)  # sector
            stock_worksheet.set_column('D:D', 10, pct_format)  # weight
            stock_worksheet.set_column('E:E', 12, num_format)  # start_price
            stock_worksheet.set_column('F:F', 12, date_format)  # start_date
            stock_worksheet.set_column('G:G', 12, num_format)  # end_price
            stock_worksheet.set_column('H:H', 12, date_format)  # end_date
            stock_worksheet.set_column('I:I', 12, pct_format)  # abs_return
            stock_worksheet.set_column('J:J', 12, num_format)  # beta
            stock_worksheet.set_column('K:K', 12, pct_format)  # weighted_return
            stock_worksheet.set_column('L:L', 12, num_format)  # weighted_beta
            
            logging.info(f"Results exported to {filename}")

    def run_all(self):
        """Run the complete analysis pipeline."""
        try:
            logging.info("Starting portfolio analysis...")
            
            # Load and validate data
            self._load_files()
            self._validate_universe()
            
            # Compute metrics
            self.compute_weights()
            self.compute_returns()
            self.compute_beta()
            self.compute_weighted_metrics()
            
            # Generate results
            sector_agg = self.sector_aggregation()
            summary = self.portfolio_aggregation()
            
            # Export to Excel
            self.export_excel('output.xlsx')
            
            logging.info("Analysis completed successfully!")
            
            return {
                'stock_level': self.universe,
                'sector_aggregates': sector_agg,
                'portfolio_summary': summary
            }
            
        except Exception as e:
            logging.error(f"Error in analysis: {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    manager = PortfolioManager(
        universe_path='universe.csv',
        prices_path='price_history.csv',
        start_date='2023-11-01',
        end_date='2024-11-01'
    )
    results = manager.run_all()