# Financial Data Analyzer – Equity Portfolio & Beta Analysis

**Candidate:** Tanvi Kailas Sawant  
**GitHub Repository:** https://github.com/Tanvi063/itus-capital-udf-project/tree/main/ITUS-round2/submission

---

## 1. Project Overview

This project implements a **Python-based portfolio analytics tool** for an equity portfolio.  
It is designed to:

- Read a **stock universe** and **historical prices** from CSV files.
- Compute:
  - Equal portfolio weights
  - Stock-level returns between two dates
  - Stock-level beta versus a benchmark index (Nifty 50 – `^NSEI`)
  - Sector-level and portfolio-level metrics
- Export the full analysis to a structured **Excel report** ([output.xlsx]

The solution is modular, reproducible, and suitable for practical use in an investment or risk analytics context.

---

## 2. Features

- **Class-based design** using a [PortfolioManager](cci:2://file:///c:/Users/HP/Downloads/financial_data_analyzer_Tanvi_sawant/financial_data_analyzer_Tanvi_sawant/financial_data_analyzer_Tanvi_sawant/ITUS-round2/financial-assignment/portfolio_manager.py:17:0-351:17) class.
- **Robust data handling**:
  - Validates universe for duplicate tickers.
  - Cleans and types input data (dates, prices).
- **Accurate date matching**:
  - Uses the **last available price on or before** a target date  
    (never uses a future price if the market is closed).
- **Return calculation**:
  - Computes per-stock return between configurable start and end dates.
- **Beta calculation vs. Nifty 50**:
  - Uses daily returns for each stock and the benchmark.
  - Requires at least 5 overlapping observations.
  - Computes beta as:
    \[
    \beta = \frac{\mathrm{Cov}(\text{stock\_ret}, \text{bench\_ret})}{\mathrm{Var}(\text{bench\_ret})}
    \]
- **Aggregation**:
  - Sector-level weights, returns, and sector betas.
  - Portfolio-level return and portfolio beta.
- **Excel output**:
  - `Stock Level`, `Aggregates`, and `Summary` sheets.
  - Clean formatting for dates, percentages, and numbers.
- **Logging**:
  - Logs key steps, data issues, and beta calculation diagnostics.

---

## 3. Technology Stack

- **Language:** Python  
- **Libraries:**
  - `pandas` – data manipulation
  - `numpy` – numerical computations
  - `yfinance` – benchmark (Nifty 50) price data
  - `xlsxwriter` / `openpyxl` – Excel output
  - `logging` – process and error logging

Dependencies are listed in [requirements.txt](cci:7://file:///c:/Users/HP/Downloads/financial_data_analyzer_Tanvi_sawant/financial_data_analyzer_Tanvi_sawant/financial_data_analyzer_Tanvi_sawant/ITUS-round2/financial-assignment/requirements.txt:0:0-0:0).

---

## 4. Project Structure

```text
ITUS-round2/
├── README.md
└── financial-assignment/
    ├── portfolio_manager.py      # Core class-based implementation
    ├── run.py                    # Entry script to run the full pipeline
    ├── universe.csv              # Stock universe
    ├── price_history.csv         # Historical price data
    ├── requirements.txt          # Python dependencies
    └── submission/               # Clean bundle used for final submission
        ├── portfolio_manager.py
        ├── run.py
        ├── universe.csv
        ├── price_history.csv
        ├── requirements.txt
        └── output.xlsx           # Generated Excel report
