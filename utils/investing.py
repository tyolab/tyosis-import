import argparse
import os
from datetime import datetime
import investpy
import pandas as pd

def get_investing_data(symbol, from_date, to_date, country=None):
    """
    Retrieves historical data for a given symbol from investing.com.

    Args:
        symbol (str): The symbol to retrieve data for (e.g., 'AAPL' for Apple).
        from_date (str): The start date for the data in 'dd/mm/yyyy' format.
        to_date (str): The end date for the data in 'dd/mm/yyyy' format.
        country (str, optional): The country where the symbol is listed. Defaults to None.

    Returns:
        pandas.DataFrame: A DataFrame containing the historical data, or None if an error occurs.
    """
    try:
        data = investpy.get_stock_historical_data(
            stock=symbol,
            country=country,
            from_date=from_date,
            to_date=to_date
        )
        return data
    except Exception as e:
        print(f"Error retrieving data for {symbol}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Retrieve historical data from investing.com.")
    parser.add_argument("symbol", help="The symbol to retrieve data for (e.g., 'AAPL')")
    parser.add_argument("from_date", help="The start date for the data (dd/mm/yyyy)")
    parser.add_argument("to_date", help="The end date for the data (dd/mm/yyyy)")
    parser.add_argument("--country", help="The country where the symbol is listed (optional)", default=None)

    args = parser.parse_args()

    data = get_investing_data(args.symbol, args.from_date, args.to_date, args.country)

    if data is not None:
        # Format date and reorder columns
        data['Date'] = pd.to_datetime(data.index).strftime('%d/%m/%Y')
        data = data[['Date', 'Open', 'High', 'Low', 'Close']]
        data.insert(0, 'Symbol', args.symbol)  # Add symbol column at the beginning

        # Create directory if it doesn't exist
        year = args.to_date.split('/')[-1]
        output_dir = f"/data/tyolab/node/tyosis-import/data/{args.country}/{args.symbol}/{year}"
        os.makedirs(output_dir, exist_ok=True)

        # Save to CSV
        output_file = os.path.join(output_dir, f"{args.symbol}_{year}.txt")
        data.to_csv(output_file, index=False)
        print(f"Data saved to: {output_file}")

if __name__ == "__main__":
    main()
