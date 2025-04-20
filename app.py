# import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
import matplotlib.pyplot as plt

# Initialize pytrends
pytrends = TrendReq(hl='de-DE', tz=60, timeout=(10, 25), retries=3, backoff_factor=0.1)

# Fetch Google Trends data
def get_trends_data(keyword, geo='DE-BY', timeframe='today 5-y'):
    try:
        pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
        data = pytrends.interest_over_time()
        if not data.empty:
            data = data.drop(columns=['isPartial'], errors='ignore')
        return data
    except Exception as e:
        st.error(f"Error fetching trends: {e}")
        return pd.DataFrame()
    
def test(keyword, geo='DE-BY', timeframe='today 5-y'):
    pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
    data = pytrends.interest_over_time()
    if not data.empty:
        data = data.drop(columns=['isPartial'], errors='ignore')
    return data
  
test("Kaspar Schmauser Nürnberg")

# # Streamlit app
# st.title("Google Trends for Kaspar Schmauser in Nürnberg")
# keyword = "Vegan Bowl"
# data = get_trends_data(keyword)

# if not data.empty:
#     st.write(f"Search Interest for '{keyword}' in Bavaria (DE-BY)")
#     fig, ax = plt.subplots()
#     data[keyword].plot(ax=ax, title=f"Search Interest: {keyword}")
#     ax.set_xlabel("Date")
#     ax.set_ylabel("Interest (0-100)")
#     st.pyplot(fig)
# else:
#     st.warning("No data available. Try a broader keyword or timeframe.")