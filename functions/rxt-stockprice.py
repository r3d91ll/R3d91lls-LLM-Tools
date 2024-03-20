# filename: rxt-stockprice.py
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress

# Define the stock symbol and the date range
stock_symbol = 'RXT'
buyout_date = '2016-08-26'  # Apollo Global Management announced the buyout on this date

# Download the stock data
stock_data = yf.download(stock_symbol, start=buyout_date)

# Calculate the line of best fit
x = np.arange(len(stock_data.index))
y = stock_data['Adj Close'].values
slope, intercept, r_value, p_value, std_err = linregress(x, y)
best_fit_line = intercept + slope * x

# Plot the adjusted closing price and the line of best fit
plt.figure(figsize=(10, 5))
plt.plot(stock_data.index, stock_data['Adj Close'], label=f'{stock_symbol} Stock Price')
plt.plot(stock_data.index, best_fit_line, label='Line of Best Fit', color='orange')

# Add text on the slope of the line of best fit
plt.text(
    stock_data.index[len(stock_data.index) // 2],
    best_fit_line[len(best_fit_line) // 2],
    f'Slope: {slope:.2f}',
    fontsize=12,
)

# Customize the plot
plt.title(f'{stock_symbol} Stock Price Since Buyout by Apollo (Adjusted Close)', fontweight='bold')
plt.xlabel('Date')
plt.ylabel('Adjusted Close Price (USD)')
plt.legend()
plt.tight_layout()

# Remove grid and outline box
plt.box(False)
plt.grid(False)

# Save the plot as a file
plt.savefig(f'{stock_symbol}_stock_price_since_buyout.png', bbox_inches='tight')

# Show the plot
plt.show()
