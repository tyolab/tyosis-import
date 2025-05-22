import MetaTrader5 as mt5
import pandas as pd
import sys
from datetime import datetime, timedelta

def get_ticks(symbol, count, unit):
    """
    Gets the latest ticks for a given symbol from MetaTrader 5 for a specified period.

    Args:
        symbol (str): The trading symbol (e.g., "EURUSD").
        count (int): The number of units for the period.
        unit (str): The unit of time for the period ("s" for seconds, "m" for minutes, "h" for hours).

    Returns:
        pandas.DataFrame: A DataFrame containing the ticks if successful, None otherwise.
    """

    # Initialize MetaTrader 5
    if not mt5.initialize():
        print("initialize() failed")
        mt5.shutdown()
        return None

    selected = mt5.symbol_select(symbol, True)
    if not selected:
        print(f"Symbol {symbol} not found or not selected.")
        mt5.shutdown()
        return None

    # Calculate the 'from' date based on the specified period
    now = datetime.now()
    if unit == "s":
        time_delta = timedelta(seconds=count)
    elif unit == "m":
        time_delta = timedelta(minutes=count)
    elif unit == "h":
        time_delta = timedelta(hours=count)
    else:
        print(f"Invalid time unit: {unit}. Must be 's', 'm', or 'h'.")
        mt5.shutdown()
        return None

    from_date = now - time_delta

    # Get ticks
    ticks = mt5.copy_ticks_range(symbol, from_date, now, mt5.COPY_TICKS_ALL)

    if ticks is None or len(ticks) == 0:
        print(f"No ticks found for {symbol} in the last {count} {unit}.")
        mt5.shutdown()
        return None

    # Convert to DataFrame
    df = pd.DataFrame(ticks)

    # Format time
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['time'] = df['time'].dt.strftime("%Y-%m-%d %H:%M:%S.%f")

    mt5.shutdown()
    return df


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python mt5_get_ticks.py <symbol> <count> <unit>")
        print("  <symbol>: Trading symbol (e.g., EURUSD)")
        print("  <count>: Number of units for the period")
        print("  <unit>: Unit of time ('s' for seconds, 'm' for minutes, 'h' for hours)")
        sys.exit(1)

    symbol = sys.argv[1]
    try:
        count = int(sys.argv[2])
    except ValueError:
        print("Error: Invalid count format. Please provide an integer.")
        sys.exit(1)

    unit = sys.argv[3].lower()

    ticks_df = get_ticks(symbol, count, unit)

    if ticks_df is not None:
        print(f"Ticks for {symbol} in the last {count} {unit}:")
        print(ticks_df)

        # Example of saving to CSV (optional)
        # filename = f"{symbol}_ticks_{count}{unit}.csv"
        # ticks_df.to_csv(filename, index=False)
        # print(f"Ticks saved to {filename}")
    else:
        print(f"Could not retrieve ticks for {symbol}")

    sys.exit(0)