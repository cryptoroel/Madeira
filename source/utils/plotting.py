from mplfinance.original_flavor import candlestick_ohlc
import pandas as pd

import matplotlib.dates as mpdates
import matplotlib.pyplot as plt
# Avoid FutureWarning: Pandas will require you to explicitly register matplotlib converters.
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

# Doesnt give the plot as i expected
def plot_candlestick(df):
    # convert into datetime object
    df['date'] = pd.to_datetime(df.index)

    # apply map function
    df['date'] = df['date'].map(mpdates.date2num)

    # creating Subplots
    fig, ax = plt.subplots()

    # plotting the data
    quotes = [tuple(x) for x in df[['date','open','high','low','close']].values]
    candlestick_ohlc(ax, quotes, width = 0.5,
                 colorup = 'green', colordown = 'red',
                 alpha = 0.8)

    # allow grid
    ax.grid(True)

    # Setting labels
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    # Formatting Date
    date_format = mpdates.DateFormatter('%d-%m-%Y')
    ax.xaxis.set_major_formatter(date_format)
    fig.autofmt_xdate()

    fig.tight_layout()

    # show the plot
    plt.show()