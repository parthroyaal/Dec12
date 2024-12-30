```python
import pandas as pd
import ta, time
from flask import Flask, render_template, url_for
from flask_socketio import SocketIO, emit
from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

app = Flask(__name__)
socketio = SocketIO(app)

# Function to calculate indicators
def calculate_indicators(df):
    """
    Calculates technical indicators for a given DataFrame.

    Args:
        df (pandas.DataFrame): DataFrame containing financial data.

    Returns:
        pandas.DataFrame: DataFrame with added indicator columns.
    """
    df['sma_12'] = ta.trend.sma_indicator(df['close'], window=12, fillna=False)
    df['sma_24'] = ta.trend.sma_indicator(df['close'], window=24, fillna=False)
    df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50, fillna=False)
    df['sma_200'] = ta.trend.sma_indicator(df['close'], window=200, fillna=False)

    df['rsi'] = ta.momentum.rsi(df['close'], window=14, fillna=False)

    df['macd_histogram'] = ta.trend.macd_diff(df['close'], window_slow=26, window_fast=12, window_sign=9, fillna=False)
    df['macd_fast'] = ta.trend.macd_signal(df['close'], window_slow=26, window_fast=12, window_sign=9, fillna=False)
    df['macd_slow'] = ta.trend.macd(df['close'], window_slow=26, window_fast=12, fillna=False)

    return df

# Function to determine buy/sell signals
def determine_signal(df):
    """
    Determines buy/sell signals based on price action.

    Args:
        df (pandas.DataFrame): DataFrame containing financial data.

    Returns:
        str: "Buy" or "Sell" based on the signal, or None if no signal.
    """
    if df.iloc[-1]['close'] <= df.iloc[-2]['open']:
        return "Sell"
    elif df.iloc[-1]['close'] >= df.iloc[-2]['open']:
        return "Buy"
    return None

# Function to manage trading positions
def manage_position(df, x, entry_price, pct_change, side):
    """
    Manages trading positions based on signals and price changes.

    Args:
        df (pandas.DataFrame): DataFrame containing financial data.
        x (int): Position status (0: closed, 1: open).
        entry_price (float): Price at which the position was opened.
        pct_change (float): Percentage change from entry price.
        side (int): Side of the position (1: Sell, 2: Buy).

    Returns:
        tuple: (int, float, str): Updated x, entry_price, and signal.
    """
    if x == 1:
        pct_change = (df.iloc[-1]['close'] - entry_price) / entry_price * 100

    if side == 1:
        if pct_change <= -0.3:
            x = 0  # Close the position
            entry_price = 0
            return x, entry_price, None  # No new signal as position is closed
    elif side == 2:
        if pct_change >= 0.3:
            x = 0  # Close the position
            entry_price = 0
            return x, entry_price, None  # No new signal as position is closed

    if x == 0:
        signal = determine_signal(df)
        if signal:
            x = 1
            side = 1 if signal == "Sell" else 2
            entry_price = df.iloc[-1]['close']
            df.loc[df.index[-1], 'signal'] = 1  # Mark the signal in the DataFrame
            return x, entry_price, signal
    return x, entry_price, None

# Function to process and emit new data
def process_data():
    """Processes data, generates signals, and emits data to clients."""
    global current_index, dfx, x, entry_price, pct_change, side

    new_df = kline(current_index + 1)
    dfx = pd.concat([dfx, new_df])
    dfx = dfx.fillna(0)

    side = determine_signal(dfx)
    x, entry_price, signal = manage_position(dfx, x, entry_price, pct_change, side)

    if signal:
        order(side, signal, dfx)

    dfx['date'] = dfx['date'].astype(str)
    data_for_index = dfx.iloc[current_index].to_dict()
    current_index += 1
    return data_for_index

# Function to print order details
def order(side, signal, df):
    """Prints order details for debugging."""
    print(f"{side}")
    print(f"{signal}")
    print(f"Close:{df.iloc[-1]['close']} ::: Open:{df.iloc[-2]['open']}")
    print(f"%CloseFromEntry:{pct_change}")
    print("#######################################################################")

# Function to get a kline DataFrame
def kline(index):
    """
    Returns a DataFrame for a specific kline (row).

    Args:
        index (int): Index of the kline to retrieve.

    Returns:
        pandas.DataFrame: DataFrame for the requested kline.
    """
    new_data = df.iloc[index]
    return pd.DataFrame([new_data])

# Function to handle client connections
@socketio.on('connect')
def handle_connect():
    """Handles client connection events."""
    print('Client connected')

# Function to handle client disconnections
@socketio.on('disconnect')
def handle_disconnect():
    """Handles client disconnection events."""
    print('Client disconnected')

# Function to emit new data to clients
def emit_new_data():
    """Emits new data to connected clients."""
    global current_index
    if current_index >= len(df):
        return
    data = process_data()
    socketio.emit('new_data', data, broadcast=True)
    time.sleep(1)

# Initialize global variables
df = pd.read_csv('RHEL.csv')
df.drop(df.columns[0], axis=1, inplace=True)
df.columns = df.columns.str.lower()
df = df.drop('adj close', axis=1)
df['date'] = pd.to_datetime(df['date'], utc=True)
df['date'] = df['date'] + timedelta(hours=5, minutes=30)
df['time'] = df['date'].astype(int) // 10**9
df = calculate_indicators(df)
current_index = 0
dfx = df.head(1)
x = 0  # Position status
entry_price = 0  # Entry price
pct_change = 0  # Percentage change
side = 0  # Position side

# Route for the main page
@app.route('/')
def index():
    """Renders the main HTML template."""
    return render_template("index.html")

# Main execution block
if __name__ == '__main__':
    socketio.start_background_task(emit_new_data)
    sched = BackgroundScheduler(daemon=True)
    sched.start()
    socketio.run(app, debug=False, port=5001)
```