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
    history = data.history(period=str(duration) + str(unit))
    begin_price = history.iloc[0]["Low"]
    end_price = history.iloc[-1]["Low"]
    gain = (end_price - begin_price) / begin_price
    sma = sum(history["Low"]) / len(history)
    return gain * 100, sma

#def objective(x, cov):
#    return np.dot(x.T, np.dot(cov * 252, x))


def objective(x, cov, individual_vol):
    all_vol = np.sqrt( np.dot(x.T, np.dot(cov, x)) )
    numer = np.sum(x * individual_vol)
    return -numer / all_vol


def problem_config(df, num_pf):

    pcnt_change = df.pct_change().dropna()
    cov = pcnt_change.cov()
    
    individual_vol = np.std(pcnt_change, ddof=1)     

    x0 = np.random.random(num_pf)
    var_const = [1] * num_pf
    linear_constraint = LinearConstraint([var_const], [0], [1])
    bounds = Bounds([0] * num_pf, [1] * num_pf)
    res = minimize(objective, x0, args = (cov, individual_vol), method='trust-constr', bounds = bounds, constraints=[linear_constraint])
    return res

def run_sim(df, amount):
  history_df = pd.DataFrame()  
  ticker_list = []
  gains = []
  smas = []
  duration = 200
  duration_unit = "d"
  for isin in df["ISIN"]:
      ticker_symbol = get_ticker_from_isin(isin)
      stock = yf.Ticker(ticker_symbol)
      history_df[ticker_symbol] = stock.history(period=f"{duration}{duration_unit}", interval = "1d")["Close"]
      ticker_list.append(ticker_symbol)
      gain, sma = get_gain(ticker_symbol, duration, duration_unit)
      gains.append(gain)
      smas.append(sma)
  res = problem_config(history_df, len(ticker_list))
  df["weights"] = res.x
  df["Scrip"] = ticker_list
  df["gain"] = gains
  df["sma"] = smas
  df["Amount"] = np.asarray(res.x) * amount
  return df, sum(res.x)





    





