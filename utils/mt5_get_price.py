import MetaTrader5 as mt5
import sys

def get_latest_price(symbol, price_type="last"):
    """
    Gets the latest price (ask, bid, or last) for a given symbol from MetaTrader 5.

    Args:
        symbol (str): The trading symbol (e.g., "EURUSD").
        price_type (str): The type of price to retrieve ("ask", "bid", or "last"). Defaults to "last".

    Returns:
        float: The latest price if successful, None otherwise.
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

    ticker = mt5.symbol_info_tick(symbol)

    if ticker is None:
        print(f"Could not retrieve ticker information for {symbol}")
        mt5.shutdown()
        return None

    if price_type == "ask":
        price = ticker.ask
    elif price_type == "bid":
        price = ticker.bid
    elif price_type == "last":
        price = ticker.last
    else:
        print(f"Invalid price type: {price_type}.  Must be 'ask', 'bid', or 'last'.")
        mt5.shutdown()
        return None

    mt5.shutdown()
    return price


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python mt5_get_price.py <symbol> [price_type]")
        print("  price_type: Optional.  'ask', 'bid', or 'last'. Defaults to 'last'.")
        sys.exit(1)

    symbol = sys.argv[1]
    price_type = "last"  # Default

    if len(sys.argv) == 3:
        price_type = sys.argv[2].lower()

    price = get_latest_price(symbol, price_type)

    if price is not None:
        print(f"Latest {price_type} price for {symbol}: {price}")
    else:
        print(f"Could not retrieve latest {price_type} price for {symbol}")

    sys.exit(0)