import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time
import matplotlib.pyplot as plt
from datetime import datetime
import feedparser
import pytz
import seaborn as sns
sns.set_context("poster")

# --- Configuration & Inputs ---
# 1. Hardcoded list
hardcoded_tickers = ["KERNEX", "SUZLON", "TMCV", "ZYDUSLIFE", "JINDALSAW", "ASTERDM", "BEL", "BHARATFORG", "CYIENT", "HBLENGINE", "LUPIN", "MARICO", "WELCORP", "DRREDDY", "APOLLO", "ASTRAMICRO", "JBMA", "MAZDOCK", "MCX", "NCC", "SHYAMMETL", "PARAS", "ONESOURCE"]

# 2. Multiselect for known tickers
selected_fixed = st.multiselect("Pick from list:", hardcoded_tickers)

# 3. Text input for custom tickers (User can type "RELIANCE, TATASTEEL")
custom_input = st.text_input("Add custom tickers (comma separated):", "")
custom_tickers = [x.strip().upper() for x in custom_input.split(",") if x.strip()]

# Combine all unique tickers
ticker_list = list(dict.fromkeys(["SUZLON", "BHARATFORG"] + selected_fixed + custom_tickers))

col1, col2 = st.columns(2)
with col1:
    number = st.number_input("History duration", value=1) 
with col2:
    unit_time = st.text_input("Unit (mo/d)", value="d")

# --- Define Tabs ---
tab_chart, tab_chart_norm, tab_cnbc, tab_results, tab_announcements = st.tabs(["Stock Charts", "Chart Normalized",  "CNBC News", "Results", "Announcements"])

# Setup for Stock Data (Dynamic Grid)
columns = 3
rows = (len(ticker_list) // columns) + (1 if len(ticker_list) % columns > 0 else 0)
fig, axes = plt.subplots(nrows=rows, ncols=columns, figsize=(24, rows * 10))
fig_norm, axes_norm = plt.subplots(nrows=rows, ncols=columns, figsize=(24, rows * 10))

# Flatten axes only if there's more than 1 ticker, handle single ticker case
if len(ticker_list) > 1:
    axes_flat = axes.flatten()
    axes_norm_flat = axes_norm.flatten()
else:
    axes_flat = [axes]
    axes_norm_flat = [axes_norm]

# Containers for dynamic updates
chart_placeholder = tab_chart.empty()
chart_placeholder_norm = tab_chart_norm.empty()

with tab_cnbc:
    st.subheader("CNBC Market Feed")
    cnbc_placeholders = [st.empty() for _ in range(15)]

with tab_results:
    st.subheader("Results")
    results_placeholders = {t: st.empty() for t in ticker_list}

with tab_announcements:
    st.subheader("Announcements")
    announce_placeholders = {t: st.empty() for t in ticker_list}


def cal_sma(data):
    sma = np.sum(list(data)) / len(data)
    print(sma)
    return sma

# --- Main Loop ---
cnbc_url = "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/market.xml"
nse_results = "https://nsearchives.nseindia.com/content/RSS/Financial_Results.xml"
announcements = "https://nsearchives.nseindia.com/content/RSS/Online_announcements.xml"

for i in range(1000):
    # Update CNBC (Every 10 cycles)
    if i % 10 == 0:
        cnbc_feed = feedparser.parse(cnbc_url)
        for idx, entry in enumerate(cnbc_feed.entries[:15]):
            cnbc_placeholders[idx].markdown(f"**{entry.title}** \n[Read more]({entry.link})")

        results_feed = feedparser.parse(nse_results)
        for idx, entry in enumerate(results_feed.entries[:15]):
            results_placeholders[idx].markdown(f"**{entry.title}** \n[Read more]({entry.link})")

        announcements_feed = feedparser.parse(announcements)
        for idx, entry in enumerate(announcements_feed.entries[:15]):
            announce_placeholders[idx].markdown(f"**{entry.title}** \n[Read more]({entry.link})")

    # Update Charts with IST
    for idx, t in enumerate(ticker_list):
        try:
            ticker = yf.Ticker(t + ".NS")
            curr_data = ticker.history(period=f"{number}{unit_time}", interval="5m")
            
            if not curr_data.empty:
                # Localize to IST
                if curr_data.index.tz is None:
                    curr_data.index = curr_data.index.tz_localize('UTC')
                ist_data = curr_data.index.tz_convert('Asia/Kolkata')
                
                ax = axes_flat[idx]
                ax.clear()
                ax.plot(ist_data, curr_data["Low"], label="Price", color='#1f77b4')
                ax.set_title(f"{t} (IST)", fontsize=16, fontweight='bold')
                ax.tick_params(axis='x', rotation=45)
                ax.grid(True, linestyle='--', alpha=0.7)
                sma = calc_sma(curr_data["Low"])
                ax.plot(ist_data, [sma] * len(ist_data), "g")
                print(ist_data)  
                ax_n = axes_norm_flat[idx]
                ax_n.clear()
                ax_n.plot(ist_data, (np.asarray(curr_data["Low"]) / curr_data.iloc[0]["Low"]) * 100 - 100.0, label="Price", color='#1f77b4')
                ax_n.set_title(f"{t} (IST)", fontsize=16, fontweight='bold')
                ax_n.tick_params(axis='x', rotation=45)
                ax_n.grid(True, linestyle='--', alpha=0.7)
        except Exception as e:
            continue

    # Hide unused axes
    for j in range(len(ticker_list), len(axes_flat)):
        axes_flat[j].axis('off')

    fig.subplots_adjust(hspace=0.95, wspace=0.4)
    fig_norm.subplots_adjust(hspace=0.95, wspace=0.4)
    plt.tight_layout(pad=3.0)
    
    chart_placeholder.pyplot(fig)
    chart_placeholder_norm.pyplot(fig_norm)
    time.sleep(2)
