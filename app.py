import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
import matplotlib.pyplot as plt
import time
from retrying import retry

# Initialize pytrends without retries parameter
pytrends = TrendReq(hl='de-DE', tz=60, timeout=(10, 25))
time.sleep(1)  # Additional sleep after initialization

# Retry logic for 429 errors
def retry_if_429(exception):
    return isinstance(exception, Exception) and "429" in str(exception)

# Fetch Google Trends data with retries
@st.cache_data
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000, retry_on_exception=retry_if_429)
def get_trends_data(keyword, geo_list, timeframe='today 5-y'):
    try:
        time.sleep(10)  # Increased delay to avoid rate limits
        data_dict = {}
        for geo in geo_list:
            pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
            data = pytrends.interest_over_time()
            if not data.empty:
                data = data.drop(columns=['isPartial'], errors='ignore')
                data_dict[geo] = data[keyword]
        if data_dict:
            return pd.DataFrame(data_dict)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching trends: {e}")
        return pd.DataFrame()

# Streamlit app
st.title("Google Trends: Vegan Restaurants in Berlin vs. Nürnberg")
keyword = "vegan restaurant"
st.write("Compare search interest for vegan restaurants in Berlin and Nürnberg.")
geo_list = ["DE-BE", "DE-BY"]  # Berlin, Bavaria (proxy for Nürnberg)
geo_labels = ["Berlin", "Nürnberg (Bavaria)"]
timeframe = st.selectbox("Timeframe", ["today 5-y", "today 12-m", "today 3-m"], index=0)
data = get_trends_data(keyword, geo_list, timeframe)

if not data.empty:
    st.write(f"Search Interest for '{keyword}' in {', '.join(geo_labels)}")
    fig, ax = plt.subplots()
    data.plot(ax=ax, title=f"Search Interest: {keyword}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Interest (0-100)")
    ax.legend(geo_labels)
    st.pyplot(fig)
    st.download_button("Download CSV", data.to_csv(index=True), "vegan_bowls_trends.csv")
else:
    st.warning("No data available. Try a broader keyword (e.g., 'vegan restaurant') or different timeframe.")