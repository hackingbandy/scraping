import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
import matplotlib.pyplot as plt
import time
from retrying import retry
import os
import seaborn as sns
#test

# Initialize pytrends
pytrends = TrendReq(hl='de-DE', tz=60, timeout=(10, 25))

# Retry logic for 429 errors
def retry_if_429(exception):
    return isinstance(exception, Exception) and "429" in str(exception)

# Fetch Google Trends data with retries and delays
@st.cache_data
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000, retry_on_exception=retry_if_429)
def get_trends_data(keyword, geo_list, timeframe='today 5-y'):
    try:
        data_dict = {}
        for geo in geo_list:
            st.write(f"Fetching data for {geo}")
            pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
            data = pytrends.interest_over_time()
            if not data.empty:
                data = data.drop(columns=['isPartial'], errors='ignore')
                data_dict[geo] = data[keyword]
            st.write(f"Data fetched for {geo}")
            time.sleep(30)  # Delay between requests to avoid rate limits
        if data_dict:
            return pd.DataFrame(data_dict)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching trends: {e}")
        return pd.DataFrame()

# Load and process CSV
@st.cache_data
def load_reviews_data(csv_path):
    if not os.path.exists(csv_path):
        st.error(f"CSV file not found at {csv_path}. Please ensure 'kaspar_schmauser_all_reviews.csv' is in the 'data' folder next to this script.")
        return pd.DataFrame()
    try:
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        df = df.dropna(subset=['rating', 'timestamp'])
        df['location'] = df['location'].str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()

def load_un_data(csv2_path):
    if not os.path.exists(csv2_path):
        st.error(f"CSV file not found at {csv2_path}. Please ensure 'un_data.csv' is in the 'data' folder next to this script.")
        return pd.DataFrame()
    try:
        df = pd.read_csv(csv2_path)
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()

# Streamlit app
st.title("Data Analysis App")

# Define CSV path for local add ""develop", "scraping", in path
csv_path = os.path.join("data", "kaspar_schmauser_all_reviews.csv")
st.write("Current working directory:", os.getcwd())
csv2_path = os.path.join("data", "un_data.csv")
st.write("Looking for CSV at:", os.path.abspath(csv_path))
st.write("Looking for CSV at:", os.path.abspath(csv2_path))

# Create tabs
tab1, tab2, tab3 = st.tabs(["Google Trends", "Reviews Analysis", "Unternehmensanalyse"])

# Tab 1: Google Trends
with tab1:
    st.header("Google Trends: Vegan Restaurants in Berlin vs. Nürnberg")
    keyword = "vegan restaurant"
    st.write("Compare search interest for vegan restaurants in Berlin and Nürnberg.")
    geo_list = ["DE-BE", "DE-BY"]  # Berlin, Bavaria (proxy for Nürnberg)
    geo_labels = ["Berlin", "Nürnberg (Bavaria)"]
    timeframe = st.selectbox("Timeframe", ["today 5-y", "today 12-m", "today 3-m"], index=0)
    data = get_trends_data(keyword, geo_list, timeframe)

    if not data.empty:
        # Rename columns to user-friendly labels
        data.columns = geo_labels
        
        # Add a title above the chart
        st.write(f"### Search Interest for '{keyword}' in {', '.join(geo_labels)}")
        
        # Display the line chart
        st.line_chart(data)
        
        # Add axis descriptions below the chart
        st.write("*X-axis: Date, Y-axis: Interest (0-100)*")
        
        # Keep the download button
        st.download_button("Download CSV", data.to_csv(index=True), "vegan_restaurant_trends.csv")
    else:
        st.warning("No data available. Try a broader keyword (e.g., 'vegan restaurant') or different timeframe.")

# Tab 2: Reviews Analysis
with tab2:
    st.header("Kaspar Schmauser Reviews Analysis")
    df = load_reviews_data(csv_path)

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
        rating_counts = filtered_df['rating'].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0).sort_index()
        rating_counts_df = rating_counts.to_frame(name='Count')
        st.bar_chart(rating_counts_df)
        st.write("*X-axis: Rating, Y-axis: Count*")

        import plotly.express as px

        st.subheader("Average Rating by Location")

        avg_rating_by_location = filtered_df.groupby('location')['rating'].mean().sort_values(ascending=False)
        avg_rating_df = avg_rating_by_location.reset_index()

        fig = px.bar(avg_rating_df, x='location', y='rating', labels={'rating': 'Average Rating'})
        fig.update_layout(xaxis_tickangle=45, title="Average Rating by Location")

        st.plotly_chart(fig)

        st.write("*X-axis: Location, Y-axis: Average Rating*")


        # Rating Trend Over Time
        st.subheader("Rating Trend Over Time")
        filtered_df['month_year'] = filtered_df['timestamp'].dt.to_period('M').astype(str)
        avg_rating_by_time = filtered_df.groupby('month_year')['rating'].mean().reset_index()
        avg_rating_by_time = avg_rating_by_time.sort_values('month_year')
        line_data = avg_rating_by_time.set_index('month_year')
        st.line_chart(line_data)
        st.write("*X-axis: Month-Year, Y-axis: Average Rating*")

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
        st.warning("No reviews data available. Please ensure 'kaspar_schmauser_all_reviews.csv' is in the 'data' folder.")

# Tab 3: Unternehmensanalyse
with tab3:
    st.header("Unternehmensanalyse")
    df = load_un_data(csv2_path)
    if not df.empty:
        st.markdown("### Raw Unternehmensanalyse Data")
        st.dataframe(df)
        st.markdown("### Bilanzsumme by Year")
        st.bar_chart(df.set_index('Jahr')['Bilanzsumme'])