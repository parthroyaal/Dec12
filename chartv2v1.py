
# ```python
# widget.onChartReady(() => {
# 					widget.chart().createStudy('Moving Average', false, false, [7], null, {"Plot.linewidth": 2, "Plot.color": "#FF0000"});
# 				});
# ```
# [[example_ldjflsf]]


# ```python
from flask import Flask, render_template_string, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='charting_library/static')
CORS(app)


@app.route('/charting_library/<path:filename>')
def charting_library_files(filename):
    return send_from_directory('charting_library', filename)


@app.route('/charting_library/datafeeds/udf/<path:filename>')
def datafeeds_files(filename):
    return send_from_directory('charting_library/datafeeds/udf', filename)


# Define the HTML content as a multi-line string
html_content = """
<!DOCTYPE HTML>
<html>
<head>
    <title>TradingView Charting Library demo</title>
    <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,minimum-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=Edge">
    <script type="text/javascript" src="/charting_library/charting_library.min.js"></script>
    <script type="text/javascript" src="/charting_library/datafeeds/udf/dist/polyfills.js"></script>
    <script type="text/javascript" src="/charting_library/datafeeds/udf/dist/bundle.js"></script>
    <script type="text/javascript">
        function getParameterByName(name) {
            name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
            var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
                results = regex.exec(location.search);
            return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
        }

        // Dummy Data for 3 months of 3-minute interval data
        const dummyData = generateDummyData(Date.now() - (3 * 30 * 24 * 60 * 60 * 1000), Date.now(), 3 * 60);

        function generateDummyData(startTime, endTime, interval) {
            let data = [];
            let time = startTime;

            while (time < endTime) {
                data.push({
                    time: time,
                    open: getRandomNumber(100, 150),
                    high: getRandomNumber(100, 150),
                    low: getRandomNumber(90, 140),
                    close: getRandomNumber(100, 150),
                    volume: getRandomNumber(1000, 10000)
                });
                time += interval * 1000; // Convert minutes to milliseconds
            }
            return data;
        }

        function getRandomNumber(min, max) {
            return Math.random() * (max - min) + min;
        }

        TradingView.onready(function() {
            var widget = window.tvWidget = new TradingView.widget({
                // debug: true, // uncomment this line to see Library errors and warnings in the console
                fullscreen: true,
                symbol: 'AAPL',
                interval: '3', // Set default resolution to 3 minutes
                timeframe: '3D', // Request 3 days of data initially (D for Days)
                supported_resolutions: ["3", "15", "30", "60", "240", "D", "1W", "1M"], // Supported resolutions
                container_id: "tv_chart_container",

                // Mock datafeed implementation
                datafeed: {
                    onReady: function (callback) {
                        setTimeout(() => {
                            callback({
                                supported_resolutions: ["3", "15", "30", "60", "240", "D", "1W", "1M"]
                            });
                        }, 0);
                    },
                    resolveSymbol: function (symbolName, onSymbolResolvedCallback, onResolveErrorCallback) {
                        setTimeout(() => {
                            onSymbolResolvedCallback({
                                name: symbolName,
                                description: 'Apple Inc.',
                                type: 'stock',
                                session: '24x7',
                                timezone: 'America/New_York',
                                ticker: symbolName,
                                minmov: 1,
                                pricescale: 100,
                                has_intraday: true,
                                intraday_multipliers: ['3', '15', '30', '60', '240'],
                                supported_resolution: ["3", "15", "30", "60", "240", "D", "1W", "1M"],
                                volume_precision: 8,
                                data_status: 'streaming',
                            });
                        }, 0);
                    },
                    getBars: function (symbolInfo, resolution, from, to, onHistoryCallback, onErrorCallback, firstDataRequest) {
                        let bars = dummyData.filter(bar => bar.time >= from * 1000 && bar.time <= to * 1000);
                        if (bars.length) {
                            onHistoryCallback(bars, {noData: false});
                        } else {
                            onHistoryCallback(bars, {noData: true});
                        }
                    },
                    subscribeBars: function (symbolInfo, resolution, onRealtimeCallback, subscriberUID, onResetCacheNeededCallback) {
                        // Simulate real-time updates (replace with actual implementation)
                        var lastBar;
                        setInterval(function () {
                            const newBar = {
                                time: Date.now(),
                                open: getRandomNumber(100, 150),
                                high: getRandomNumber(100, 150),
                                low: getRandomNumber(90, 140),
                                close: getRandomNumber(100, 150),
                                volume: getRandomNumber(1000, 10000)
                            };

                            if (!lastBar || newBar.time > lastBar.time) {
                                onRealtimeCallback(newBar);
                                lastBar = newBar;
                            }
                        }, resolution * 1000); // Update every `resolution` seconds
                    },
                    unsubscribeBars: function (subscriberUID) {
                        // Unsubscribe from real-time updates (if needed)
                    }
                },
                library_path: "/charting_library/",
                locale: getParameterByName('lang') || "en",
                disabled_features: ["use_localstorage_for_settings"],
                enabled_features: ["study_templates"],
                charts_storage_url: 'http://saveload.tradingview.com',
                charts_storage_api_version: "1.1",
                client_id: 'tradingview.com',
                user_id: 'public_user_id',
                theme: getParameterByName('theme'),
            });
        });
    </script>
</head>
<body style="margin:0px;">
    <div id="tv_chart_container"></div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_content)


if __name__ == '__main__':
    app.run(port=3001, debug=True)

# ```

# ```python
# def simulateCandleData(symbol, resolution, from_time, to_time):
#     interval_seconds = {
#         '1': 60,
#         '5': 300,
#         '15': 900,
#         '30': 1800,
#         '60': 3600,
#         'D': 86400,
#         'W': 604800,  # Roughly 7 days in seconds
#         'M': 2592000  # Roughly 30 days in seconds
# ```

# ```python
# widget.chart().update vs widget.chart().stream()
# ```

## file:///home/caspi/Desktop/2024/Jun29/data.html

