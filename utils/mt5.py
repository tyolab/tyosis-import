import MetaTrader5 as mt5
import pandas as pd
import sys
from datetime import datetime, date
import os

def download_mt5_eod_data(symbol, year):
    """
    Downloads historical EOD data from MetaTrader 5 for a given symbol and year.

    Args:
        symbol (str): The trading symbol (e.g., "EURUSD").
        year (int): The year for which to download data.

    Returns:
        None. Saves the data to a file named YYYY.txt.
    """

    # Initialize MetaTrader 5
    if not mt5.initialize():
        print("initialize() failed")
        mt5.shutdown()
        return

    # Get market information (if available) -  This part needs to be adapted based on how you determine the market from the symbol.
    # For example, you might have a dictionary or a function that maps symbols to markets.
    # Here's a placeholder:
    market = get_market_from_symbol(symbol)  # Replace with your actual logic

    # Prepare file path
    directory = f"data/{market}/{symbol}" if market else f"data/{symbol}"
    os.makedirs(directory, exist_ok=True)  # Create directory if it doesn't exist
    filename = os.path.join(directory, f"{year}.txt")
    filepath = os.path.abspath(filename)

    # Determine date range
    from_date = datetime(year, 1, 1)
    to_date = datetime(year, 12, 31) if year < date.today().year else datetime.now()

    # Check if file exists and adjust from_date if necessary
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                last_line = f.readlines()[-1]
                last_date_str = last_line.split(',')[1]
                from_date = datetime.strptime(last_date_str, "%d/%m/%Y")
                from_date = from_date + pd.Timedelta(days=1)  # Start from the next day
        except (IndexError, ValueError):
            print(f"Warning: Could not read last date from {filepath}. Downloading data for the entire year.")

    # Download data
    rates = mt5.copy_rates_range(symbol, from_date, to_date)

    if rates is None or len(rates) == 0:
        print(f"No data found for {symbol} in {year} from {from_date.strftime('%d/%m/%Y')} to {to_date.strftime('%d/%m/%Y')}")
        mt5.shutdown()
        return

    # Convert to DataFrame
    df = pd.DataFrame(rates)

    # Format date and select columns
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['date'] = df['time'].dt.strftime("%d/%m/%Y")
    df = df[['date', 'open', 'high', 'low', 'close', 'tick_volume']]
    df.insert(0, 'symbol', symbol)

    # Append to file or create new file
    if os.path.exists(filepath):
        df.to_csv(filepath, mode='a', header=False, index=False, date_format="%d/%m/%Y")
    else:
        df.to_csv(filepath, index=False, date_format="%d/%m/%Y")

    print(f"Data for {symbol} in {year} saved to {filepath}")

    # Shutdown MetaTrader 5
    mt5.shutdown()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <symbol> <year>")
        sys.exit(1)

    symbol = sys.argv[1]
    try:
        year = int(sys.argv[2])
    except ValueError:
        print("Error: Invalid year format. Please provide a valid year (e.g., 2023).")
        sys.exit(1)

    download_mt5_eod_data(symbol, year)


# Placeholder function - replace with your actual market determination logic
def get_market_from_symbol(symbol):
    # Example:  If symbols starting with "EUR" are in the "forex" market
    if symbol.startswith("EUR"):
        return "forex"
    return None  # Or your default market if none is found
