import investpy

import argparse
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
        print(data)
        # You can further process the data here, e.g., save it to a CSV file:
        # data.to_csv(f"{args.symbol}_historical_data.csv")

if __name__ == "__main__":
    main()
