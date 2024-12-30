# Global Constants
TOTP_KEY = 'T2PX34ABOGB3VZIVENMUAOJ5PQ'
API_KEY = 'kSJIOphE'
USERNAME = 'P547740'
PIN = '8894'
CANDLE_INTERVAL = "ONE_MINUTE"
SYMBOL_LIMIT = 10
FROM_TIME = "09:15"
TO_TIME = "14:30"

# General Imports
from datetime import datetime, date
from logzero import logger

def authenticate():
    """
    Authenticates the user and returns the SmartConnect object.
    """
    # Import used in this function
    from SmartApi import SmartConnect
    from pyotp import TOTP

    try:
        obj = SmartConnect(api_key=API_KEY)
        obj.generateSession(USERNAME, PIN, TOTP(TOTP_KEY).now())
        logger.info("Authentication successful.")
        return obj
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise

def fetch_trading_symbols():
    """
    Fetches trading symbols from the API and filters NSE equity symbols.
    """
    # Import used in this function
    import requests
    import pandas as pd

    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    try:
        data = requests.get(url).json()
        df = pd.DataFrame.from_dict(data)
        df['expiry'] = pd.to_datetime(df['expiry'], errors='coerce')
        df = df.astype({'strike': float}, errors='ignore')
        filtered_df = df[
            (df['exch_seg'] == 'NSE') &
            df['symbol'].str.endswith('-EQ')
        ]
        return filtered_df
    except Exception as e:
        logger.error(f"Failed to fetch trading symbols: {e}")
        raise

def get_candle_data(obj, symbol_info, from_time, to_time):
    """
    Fetches candle data for a given symbol within the specified time range.
    """
    # Import used in this function
    import pandas as pd

    try:
        historic_param = {
            "exchange": symbol_info.exch_seg,
            "symboltoken": symbol_info.token,
            "interval": CANDLE_INTERVAL,
            "fromdate": from_time,
            "todate": to_time,
        }
        response = obj.getCandleData(historic_param)
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        df = pd.DataFrame(response['data'], columns=columns)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%dT%H:%M:%S%z')
        df['symbol'] = symbol_info.symbol
        return df
    except Exception as e:
        logger.error(f"Failed to fetch candle data for {symbol_info.symbol}: {e}")
        return pd.DataFrame()

def process_candle_data(dataframes):
    """
    Processes candle data to generate buy/sell signals based on the last row.
    """
    signals = []
    for df in dataframes:
        if not df.empty:
            last_row = df.iloc[-1]
            if last_row['close'] > last_row['open']:
                df['Signal'] = 2  # Buy signal
                signals.append(last_row['symbol'])
            elif last_row['close'] < last_row['open']:
                df['Signal'] = 1  # Sell signal
            else:
                df['Signal'] = None
        else:
            logger.warning("Empty DataFrame encountered.")
    return signals

def main():
    """
    Main function to orchestrate the fetching and processing of candle data.
    """
    # Authentication
    obj = authenticate()

    # Fetch trading symbols
    trading_symbols = fetch_trading_symbols()

    # Define time range for candle data
    today_date = date.today()
    from_time = datetime(today_date.year, today_date.month, today_date.day, 9, 15).strftime('%Y-%m-%d %H:%M')
    to_time = datetime(today_date.year, today_date.month, today_date.day, 14, 30).strftime('%Y-%m-%d %H:%M')

    # Fetch and process candle data
    dataframes = []
    for i, row in trading_symbols.iterrows():
        if i >= SYMBOL_LIMIT:  # Limit to SYMBOL_LIMIT symbols
            break
        df = get_candle_data(obj, row, from_time, to_time)
        dataframes.append(df)
        time.sleep(0.4)  # Throttle API requests

    # Generate signals
    signals = process_candle_data(dataframes)

    # Output results
    logger.info(f"Signals generated: {signals}")

if __name__ == "__main__":
    main()
