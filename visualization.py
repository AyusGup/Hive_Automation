import matplotlib.pyplot as plt
import pandas as pd

def plot_price_trend(trade_details):
    """Plot price trend over time."""
    df = pd.DataFrame(trade_details)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by='timestamp')

    plt.figure(figsize=(10, 6))
    plt.plot(df['timestamp'], df['price'], label='Price (HIVE/HBD)')
    plt.title('Hive Price Trend')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    plt.grid()
    plt.show()
