

# bot deploy 


# Pre
## tech & libs used 
ta
pandas 
json
time
datetime 
flask
python
html 
css
js


## ws basics in python and js client side
### Create WebSocket instance
my_ws = websocket.create_connection(ws_url)
wscat -c wss://stream.bybit.com/v5/public/linear | tee data.json 
wss://stream.bybit.com/v5/private
wss://stream.bybit.com/v5/private/linear 


# Req: 
need stream data endpoint  fin pyhton flask to populate the updateData method of lightweight charts index.html chart from 
wss://stream.bybit.com/v5/public/linear  but it provide tick data so and i need stream at any given moment for all 5sec, 15sec, 30sec, 1min, 3min, 5min, 30min, 1hour, 2hour, 4hour, 6hour, 12hour
 candlestick stream so we  have 2 options 
# tickToTickstream: directly using this 

not convert tick data price and time value 
rather use this code to plot tick data recived from flask server  to candlestick data
import websocket
import json
import pandas as pd
from flask import Flask, render_template_string
from flask_socketio import SocketIO
from datetime import datetime, timedelta

app = Flask(__name__)
socketio = SocketIO(app)

class ChartData:
    def __init__(self):
        self._last_bar = None
        self._current_bar = None
        self._bar_start_time = None

    def _series_datetime_format(self, series: pd.Series):
        series['time'] = pd.to_datetime(series['time'])
        return series

    def update_from_tick(self, series: pd.Series):
        """Updates the data from a tick."""
        series = self._series_datetime_format(series)
        current_time = series['time']

        if self._bar_start_time is None or current_time >= self._bar_start_time + timedelta(minutes=1):
            # Start a new bar
            self._bar_start_time = current_time.replace(second=0, microsecond=0)
            self._current_bar = pd.Series({
                'time': self._bar_start_time.timestamp(),
                'open': series['price'],
                'high': series['price'],
                'low': series['price'],
                'close': series['price']
            })
            if self._last_bar is not None:
                yield self._last_bar.to_dict()
            self._last_bar = self._current_bar
        else:
            # Update current bar
            self._current_bar['high'] = max(self._current_bar['high'], series['price'])
            self._current_bar['low'] = min(self._current_bar['low'], series['price'])
            self._current_bar['close'] = series['price']

        yield self._current_bar.to_dict()

chart_data = ChartData()

ws_url = "wss://stream.bybit.com/v5/public/linear"

def on_message(ws, message):
    tick = json.loads(message)
    if tick.get('topic') == 'publicTrade.BTCUSDT':
        trade_data = tick['data'][0]
        tick_time = pd.to_datetime(trade_data['T'] / 1000, unit='s')
        tick_data = {'time': tick_time, 'price': float(trade_data['p'])}
        for updated_bar in chart_data.update_from_tick(pd.Series(tick_data)):
            socketio.emit('update_chart', updated_bar)

def on_error(ws, error):
    print(f"WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket Closed: {close_status_code} - {close_msg}")

def on_open(ws):
    print("Bybit WebSocket Opened")
    ws.send('{"op": "subscribe","args": ["publicTrade.BTCUSDT"]}')

@app.route('/')
def index():
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Real-time Candlestick Chart (1-minute)</title>
        <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    </head>
    <body>
        <div id="chart" style="width: 800px; height: 400px;"></div>
        <script>
            const chart = LightweightCharts.createChart(document.getElementById('chart'), {
                width: 800,
                height: 400,
                rightPriceScale: {
                    borderVisible: false,
                },
                timeScale: {
                    borderVisible: false,
                    timeVisible: true,
                    secondsVisible: false,
                },
                grid: {
                    horzLines: {
                        color: '#eee',
                    },
                    vertLines: {
                        color: '#eee',
                    },
                },
            });
            const candleSeries = chart.addCandlestickSeries();
            
            const socket = io();
            socket.on('update_chart', function(newBar) {
                candleSeries.update(newBar);
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

if __name__ == '__main__':
    ws = websocket.WebSocketApp(ws_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open)
    
    from threading import Thread
    wst = Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    socketio.run(app, debug=True, use_reloader=False)

will give data 


# tickToCandlestickToStream :
convert the tick  data to cnadlestick data and then for multiple timeframes namely 
5sec, 15sec, 30sec, 1min, 3min, 5min, 30min, 1hour, 2hour, 4hour, 6hour, 12hour


### Subscribe to a specific channel
my_ws.send('{"op": "subscribe","args": ["publicTrade.BTCUSDT"]}')
{"op": "subscribe","args": ["publicTrade.BTCUSDT"]}

## flask basics 

* jinga syntax for variable passing in html tags

```html
{{for i in listx}}

<li> {{i}} </li>

{{endfor}}
```
* flash message using flask 

* static folder url_for  to tell flask location of static ast



## lightweightcharts basics

* basic setData and updateData and custom updatefromtick
* layout of multiple or single charts 
* websocket and set data both use in same chart or multiple  widget 


## pandas pro

* basic iloc and loc use and some other mothiods like .shift etc  for use in row as chart logic  


# Other projects related to pre

## service-02

## service-03v1

## service-04

Order platform like bybit


## service-05


## py/js coder

* in language use of quark for input output requiremnt sys prommt   function creation 



## Snippets 

static resampler block /function for backtest datafolder data
dynamic  resmpaler  for ws data 


tickToCandlestick   block 
v1  using df.ohlc/offset or no offset 
v2 using df. aggr
v3 using custom aggr 

chartslibv1&v2 realtime and static both set data  from candlstick api and ws 


botlogic

botrendere&savingdata&tr
