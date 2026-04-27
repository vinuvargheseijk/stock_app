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


def objective(x, mean_values, cov, in_days):
    risk_free_rate = 0.02
    pf_returns = np.sum(x * mean_values)
    pf_volatility = np.sqrt( np.dot(x.T, np.dot(cov, x)) )
    risk = (pf_returns - risk_free_rate) / pf_volatility
    return -risk



def problem_config(df, duration, unit):
    pcnt_change = df.pct_change().dropna()
    mean_values = pcnt_change.mean()
    print("Change:", pcnt_change)
    print("Mean: ", mean_values)
    cov = pcnt_change.cov()
    print("Covariance: ", cov)
    num_pf = len(mean_values)
    x0 = np.random.random(num_pf)
    var_const = [1] * num_pf
    linear_constraint = LinearConstraint([var_const], [0], [1])
    bounds = Bounds([0] * num_pf, [1] * num_pf)
    if unit == "mo":
        in_days = int(duration) * 60
    else:
        in_days = int(duration)
    res = minimize(objective, x0, args = (mean_values, cov, in_days), method='trust-constr', bounds = bounds, constraints=[linear_constraint])
    return res

def run_sim(df, duration, duration_unit):
  history_df = pd.DataFrame()  
  ticker_list = []
  for isin in df["ISIN"]:
      print(isin)
      ticker_symbol = get_ticker_from_isin(isin)
      print(ticker_symbol)
      stock = yf.Ticker(ticker_symbol)
      print(stock)
      history_df[ticker_symbol] = stock.history(period = str(duration) + str(duration_unit))["Close"]
      ticker_list.append(ticker_symbol)
  res = problem_config(history_df, duration, duration_unit)
  df["weights"] = res.x
  df["Scrip"] = ticker_list
  return df





    





