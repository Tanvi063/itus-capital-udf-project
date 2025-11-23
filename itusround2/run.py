from portfolio_manager import PortfolioManager

def main():
    manager = PortfolioManager(
        universe_path='universe.csv',
        prices_path='price_history.csv',
        start_date='2023-11-01',
        end_date='2024-11-01'
    )
    results = manager.run_all()
    print("Analysis completed! Check output.xlsx for results.")

if __name__ == "__main__":
    main()