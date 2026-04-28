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
import matplotlib
import mplfinance as mpf
import subprocess
import sys
import simulator

matplotlib.use("Agg")
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

plot_type = st.text_input("Enter plot type (renko, line, candle, pnf):", key = "plotType")
col1, col2 = st.columns(2)
with col1:
    number = st.number_input("History duration", value=3) 
with col2:
    unit_time = st.text_input("Unit (mo/d)", value="d")
print("NUMBER: ", number, type(number))
print("Unit: ", unit_time)
# --- Define Tabs ---
tab_chart, tab_chart_norm, tab_cnbc, tab_results, tab_announcements, tab_pf, tab_opt = st.tabs(["Stock Charts", "Chart Normalized",  "CNBC News", "Results", "Announcements", "Portfolio", "Optimizer"])

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
port_placeholder = tab_pf.empty()

with tab_cnbc:
    st.subheader("CNBC Market Feed")
    cnbc_placeholders = [st.empty() for _ in range(15)]

with tab_results:
    st.subheader("Results")
    results_placeholders = {t: st.empty() for t in ticker_list}

with tab_announcements:
    st.subheader("Announcements")
    announce_placeholders = {t: st.empty() for t in ticker_list}




cnbc_url = "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/market.xml"
with tab_pf:
   if 'clicked' not in st.session_state:
       st.session_state.clicked = False

   def set_clicked():
       st.session_state.clicked = True

   st.button("Upload Portfolio", on_click = set_clicked)
   if st.session_state.clicked:
      pf_file = st.file_uploader("Choose a file")
   try:
        df_pf = pd.read_csv(pf_file)
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
        #plt.tight_layout()
        with port_placeholder.container():
            st.pyplot(fig_bar)
            plt.close(fig_bar) # Close to free up memory
            st.subheader("Raw Portfolio Data")
            # Displaying the dataframe from pf.csv
            st.dataframe(df_pf, width='stretch')
   except FileNotFoundError:
        port_placeholder.error("pf.csv not found in the current directory.")
   except Exception as e:
        port_placeholder.error(f"Error loading portfolio data: {e}")
            
with tab_opt:
      if 'opt_clicked' not in st.session_state:
          st.session_state.opt_clicked = False
      def set_opt_clicked():
          st.session_state.opt_clicked = True
      amount_invest = st.number_input("Planned investment value in INR", value=100000) 

      st.button("Optimizer data", on_click = set_opt_clicked)
      if st.session_state.opt_clicked == True:
        st.subheader("PF optimization")
        df_opt, allocation = simulator.run_sim(df_pf, amount_invest)
        st.dataframe(df_opt, width='stretch')
        st.write("Allocation: " + str(allocation))
      st.write("Note: This calculation is based on 200 days data")  
    


for i in range(1000):
    # Update CNBC (Every 10 cycles)

        # Display the bar chart in the dedicated tab placeholder
        #port_placeholder.pyplot(fig_bar)

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
                ax.set_title(t)
                mpf.plot(curr_data, type = plot_type, ax = ax, style = "binance")
                sma = curr_data["Low"].mean()
                ax.axhline(y=float(sma), color = "g", linestyle = "-.")
                ax_n = axes_norm_flat[idx]
                ax_n.clear()
                ax_n.plot(ist_data, (np.asarray(curr_data["Low"]) / curr_data.iloc[0]["Low"]) * 100 - 100.0, label="Price", color='#1f77b4')
                ax_n.set_title(f"{t} (IST)", fontsize=16, fontweight='bold')
                ax_n.tick_params(axis='x', rotation=45)
                ax_n.axhline( (sma / (float(curr_data.iloc[0]["Low"]))) * 100 - 100, color = "g", linestyle = "-.")
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
    plt.close(fig)
    plt.close(fig_norm)
    time.sleep(2)
