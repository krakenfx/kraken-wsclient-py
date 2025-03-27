# Kraken WebSockets Client in Python

Sample Kraken WebSockets client in Python.  This client was created for
demonstration purposes only.  It is neither maintained nor supported.

## Installation

    pip install kraken-wsclient-py

## Sample Usage

    from kraken_wsclient_py import kraken_wsclient_py as client

    def my_handler(message):
        # Here you can do stuff with the messages
        print(message)

    my_client = client.WssClient()
    my_client.start()

    # Sample public-data subscription:

    my_client.subscribe_public(
        subscription = {
            'name': 'trade'
        },
        pair = ['XBT/USD', 'XRP/USD'],
        callback = my_handler
    )

    # Sample private-data subscription:

    my_client.subscribe_private(
        subscription = {
            'name': 'openOrders',
            'token': '__WS_TOKEN_HERE__'
        },
        callback = my_handler
    )

    # Sample order-entry call:

    my_client.request(
        request = {
            'token': '__WS_TOKEN_HERE__',
            'event': 'addOrder',
            'type': 'buy',
            'ordertype': 'limit',
            'pair': 'XBT/USD',
            'price': '9000',
            'volume': '0.01',
            'userref': '666'
        },
        callback = my_handler
    )

    # Sample usage with process_data_for_tradingview function:

    def process_data_for_tradingview(data):
        # Implement the logic to process incoming data and store it in a format suitable for TradingView
        pass

    my_client.subscribe_public(
        subscription = {
            'name': 'trade'
        },
        pair = ['XBT/USD', 'XRP/USD'],
        callback = process_data_for_tradingview
    )

    # Displaying TradingView chart:

    # Use the TradingView Charting Library to display the chart with the processed data.
    # Refer to the TradingView Charting Library documentation for detailed instructions on how to integrate and display the chart.

    # Using a third-party library to integrate Kraken data with TradingView:

    import ccxt
    import pandas as pd

    def fetch_ohlcv_data():
        exchange = ccxt.kraken()
        ohlcv = exchange.fetch_ohlcv('BTC/USD', timeframe='1m')
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df

    # Use the fetched data to display the TradingView chart.

    # Creating a custom solution to display charts using matplotlib:

    import matplotlib.pyplot as plt

    def plot_ohlcv_data(df):
        fig, ax = plt.subplots()
        ax.plot(df['timestamp'], df['close'])
        plt.show()

    # Fetch the data and plot it using the custom solution.

## Compatibility

This code has been tested on Python 3.7.

## Contributing

Pull requests are not monitored and likely will be ignored.
