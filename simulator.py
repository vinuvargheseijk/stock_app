import pandas as pd
import numpy as np
from scipy.optimize import minimize, LinearConstraint, Bounds
import yfinance as yf
import requests


def get_ticker_from_isin(isin):
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    # Use a generic user-agent to avoid 403 Forbidden
    headers = {'User-Agent': 'Mozilla/5.0'}
    params = {'q': isin, 'quotesCount': 1, 'newsCount': 0}
    
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    if data['quotes']:
        return data['quotes'][0]['symbol'] # Returns the symbol
    else:
        return None

def get_gain(ticker, duration, unit):
    data = yf.Ticker(ticker)
    history = data.history(period=str(duration) + str(unit), interval = "15m")
    begin_price = history.iloc[0]["Low"] 
    end_price = history.iloc[-1]["Low"] 
    gain = (end_price - begin_price) / begin_price
    sma = sum(history["Low"]) / len(history)
    deviations = np.asarray(history["Low"]) - sma
    max_value = max(deviations)
    min_value = min(deviations)
    return gain * 100, sma, max_value, min_value


def objective(x):
    total = 0
    for d in range(len(df)):
        sensitivity = df.iloc[d]["sensitivity"]
        #total = total + x[d] * df.iloc[d]["gain"] * (1 - sensitivity)
        total = total + x[d] * (1 - sensitivity) + x[d] * df.iloc[d]["gain"]
    return -total    



tickers = []
gains = [] 
sma = []
maxD = []
minD = []
duration = 1
unit = "mo"
df = pd.read_csv("./pf.csv")

for isin in df["ISIN"]:
    ticker_symbol = get_ticker_from_isin(isin)
    tickers.append(ticker_symbol)
    gain_value, sma_value, max_value, min_value = get_gain(ticker_symbol, duration, unit)
    gains.append(gain_value)
    sma.append(sma_value)
    maxD.append(max_value)
    minD.append(min_value)
 
df["tickers"] = tickers
df["gain"] = gains
df["sma"] = sma
df["maxD"] = maxD
df["minD"] = minD
df["sensitivity"] = (np.asarray(maxD) - np.asarray(minD)) / np.asarray(sma)
x0 = np.random.random(len(df))
var_const = [1] * len(df)
bounds = Bounds([0] * len(df), [1] * len(df))
linear_constraint = LinearConstraint([var_const], [0], [1])
res = minimize(objective, x0, method='trust-constr', bounds = bounds, constraints=[linear_constraint])
print(res.x)
print(sum(res.x))
print(df)




    





