import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
import matplotlib.pyplot as plt
import time
from retrying import retry
import os
import seaborn as sns

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
    
# Load and process CSV for reviews
# Load and process CSV for reviews
@st.cache_data
def load_reviews_data():
    try:
        csv_path = os.path.join("data", "kaspar_schmauser_all_reviews.csv")  # Fixed path
        if not os.path.exists(csv_path):
            st.error(f"CSV file not found at {csv_path}. Please ensure it exists in the 'data' folder.")
            return pd.DataFrame()
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        df = df.dropna(subset=['rating', 'timestamp'])
        df['location'] = df['location'].str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()


# Create tabs
tab1, tab2 = st.tabs(["Google Trends", "Reviews Analysis"])

# Streamlit app
with tab1:
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
with tab2:
    st.header("Kaspar Schmauser Reviews Analysis")
    
    # Load reviews data
    df = load_reviews_data()

    if not df.empty:
        # Display raw data
        st.subheader("Raw Reviews Data")
        st.dataframe(df, use_container_width=True)

        # Filters
        st.subheader("Filter Reviews")
        locations = st.multiselect("Select Locations", options=df['location'].unique(), default=df['location'].unique(), key="reviews_locations")
        min_rating, max_rating = st.slider("Select Rating Range", min_value=1, max_value=5, value=(1, 5), key="reviews_rating")

        # Filter data
        filtered_df = df[(df['location'].isin(locations)) & (df['rating'].between(min_rating, max_rating))]

        # Rating Distribution
        st.subheader("Rating Distribution")
        fig1, ax1 = plt.subplots()
        sns.histplot(filtered_df['rating'], bins=5, ax=ax1, discrete=True)
        ax1.set_xlabel("Rating")
        ax1.set_ylabel("Count")
        ax1.set_title("Distribution of Ratings")
        st.pyplot(fig1)

        # Average Rating by Location
        st.subheader("Average Rating by Location")
        avg_rating_by_location = filtered_df.groupby('location')['rating'].mean().sort_values(ascending=False)
        fig2, ax2 = plt.subplots()
        sns.barplot(x=avg_rating_by_location.values, y=avg_rating_by_location.index, ax=ax2)
        ax2.set_xlabel("Average Rating")
        ax2.set_ylabel("Location")
        ax2.set_title("Average Rating by Location")
        st.pyplot(fig2)

        # Rating Trend Over Time
        st.subheader("Rating Trend Over Time")
        filtered_df['month_year'] = filtered_df['timestamp'].dt.to_period('M').astype(str)
        avg_rating_by_time = filtered_df.groupby('month_year')['rating'].mean().reset_index()
        fig3, ax3 = plt.subplots()
        sns.lineplot(x='month_year', y='rating', data=avg_rating_by_time, ax=ax3)
        ax3.set_xlabel("Month-Year")
        ax3.set_ylabel("Average Rating")
        ax3.set_title("Average Rating Over Time")
        plt.xticks(rotation=45)
        st.pyplot(fig3)

        # Download filtered data
        st.subheader("Download Filtered Reviews")
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Filtered CSV",
            data=csv,
            file_name="filtered_reviews.csv",
            mime='text/csv'
        )
    else:
        st.warning("No reviews data available. Please ensure 'data/kaspar_schmauser_all_reviews.csv' exists.")  