import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time
import matplotlib.pyplot as plt
from datetime import datetime
import feedparser
import pytz

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
tab_chart, tab_cnbc, tab_google, tab_pf = st.tabs(["Stock Charts", "CNBC News", "Google News", "Portfolio"])

# Setup for Stock Data (Dynamic Grid)
columns = 3
rows = (len(ticker_list) // columns) + (1 if len(ticker_list) % columns > 0 else 0)
fig, axes = plt.subplots(nrows=rows, ncols=columns, figsize=(24, rows * 4))

# Flatten axes only if there's more than 1 ticker, handle single ticker case
if len(ticker_list) > 1:
    axes_flat = axes.flatten()
else:
    axes_flat = [axes]

# Containers for dynamic updates
chart_placeholder = tab_chart.empty()
port_placeholder = tab_pf.empty() # Placeholder for the bar chart

with tab_cnbc:
    st.subheader("CNBC Market Feed")
    cnbc_placeholders = [st.empty() for _ in range(15)]

with tab_google:
    st.subheader("Ticker Specific News")
    google_placeholders = {t: st.empty() for t in ticker_list}


# --- Main Loop ---
cnbc_url = "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/market.xml"

for i in range(1000):
    # Update CNBC (Every 10 cycles)
    try:
        df_pf = pd.read_csv("./pf.csv")
        # Calculate Total Cost logic from get_distribution.py
        df_pf["Total Cost"] = df_pf["Quantity"] * df_pf["Average Cost Price"]

        # Group and sort for clarity
        sector_dist = df_pf.groupby('Sector Name')['Total Cost'].sum().sort_values(ascending=False)

        fig_bar, ax_bar = plt.subplots(figsize=(12, 6))
        sector_dist.plot(kind='bar', ax=ax_bar, color='#1f77b4')
        ax_bar.set_title("Portfolio Distribution by Sector", fontsize=14, fontweight='bold')
        ax_bar.set_ylabel("Total Investment (INR)")
        ax_bar.set_xlabel("Sector")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # Display the bar chart in the dedicated tab placeholder
        port_placeholder.pyplot(fig_bar)
    except FileNotFoundError:
        port_placeholder.error("pf.csv not found in the current directory.")
    except Exception as e:
        port_placeholder.error(f"Error loading portfolio data: {e}")

    if i % 10 == 0:
        cnbc_feed = feedparser.parse(cnbc_url)
        for idx, entry in enumerate(cnbc_feed.entries[:15]):
            cnbc_placeholders[idx].markdown(f"**{entry.title}** \n[Read more]({entry.link})")

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
        except Exception as e:
            continue

    # Hide unused axes
    for j in range(len(ticker_list), len(axes_flat)):
        axes_flat[j].axis('off')

    fig.subplots_adjust(hspace=0.6, wspace=0.4)
    plt.tight_layout(pad=3.0)
    
    chart_placeholder.pyplot(fig)
    time.sleep(2)
