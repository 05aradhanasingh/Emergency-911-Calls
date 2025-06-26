import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
import plotly.express as px
from streamlit_folium import st_folium

st.cache_data.clear()

st.set_page_config(page_title="911 Calls Dashboard", layout="wide")

@st.cache_data
def load_data(path):
    try:
        df = pd.read_csv(path, compression='gzip')
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    expected_cols = {'lat', 'lng', 'desc', 'zip', 'title', 'timeStamp', 'twp', 'addr', 'e'}
    missing = expected_cols - set(df.columns)
    if missing:
        st.error(f"Missing expected columns: {', '.join(missing)}")
        st.stop()

    if 'Category' not in df.columns:
        df['Category'] = df['title'].astype(str).apply(
            lambda x: x.split(':')[0] if ':' in x else x
        )

    df['timeStamp'] = pd.to_datetime(df['timeStamp'], errors='coerce')
    df = df.dropna(subset=['timeStamp', 'lat', 'lng'])
    return df

df = load_data("compressed_data.csv.gz")

assert 'Category' in df.columns, "'Category' column creation failed"

st.title("911 Calls Dashboard")
st.markdown("Data provided by montcoalert.org")

st.subheader("Filters")

categories = st.multiselect(
    "Emergency Categories",
    options=sorted(df['Category'].unique()),
    default=sorted(df['Category'].unique())
)

min_date = df['timeStamp'].min().date()
max_date = df['timeStamp'].max().date()

date_range = st.date_input(
    "Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

sample_size = st.slider(
    "Sample Size for Scatter Plot",
    min_value=100, max_value=5000, value=1000, step=100
)

filtered = df[
    (df['Category'].isin(categories)) &
    (df['timeStamp'].dt.date.between(date_range[0], date_range[1]))
]

if filtered.empty:
    st.warning("No data found for the selected filters.")
    st.stop()

st.subheader("Data Preview")
st.dataframe(filtered.head())

st.subheader("Heatmap of 911 Calls")
heat_data = filtered[['lat', 'lng']].dropna().astype(float).values.tolist()

if heat_data:
    heatmap_map = folium.Map(
        location=[filtered['lat'].mean(), filtered['lng'].mean()],
        zoom_start=9,
        tiles='CartoDB positron'
    )
    HeatMap(heat_data, radius=10, blur=25).add_to(heatmap_map)
    st_folium(heatmap_map, width=700, height=500)
else:
    st.warning("No data to show on heatmap.")

st.subheader("Scatter Geo Plot by Category")

philly_lat = 39.9526
philly_lon = -75.1652
scatter_sample = filtered.sample(min(len(filtered), sample_size), random_state=42)

scatter_fig = px.scatter_geo(
    scatter_sample,
    lat='lat',
    lon='lng',
    color='Category',
    title='911 Calls by Category',
    hover_data=['desc', 'zip', 'twp'],
    scope='usa',
    height=600
)

scatter_fig.update_geos(
    center={"lat": philly_lat, "lon": philly_lon},
    projection_type="azimuthal equal area",
    lataxis_range=[39.8, 40.1],
    lonaxis_range=[-75.3, -74.9]
)

st.plotly_chart(scatter_fig, use_container_width=True)

st.subheader("Call Volume by Day of Week")
dow_fig = px.histogram(
    filtered.assign(day=filtered['timeStamp'].dt.day_name()),
    x='day',
    category_orders={'day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']},
    title="Call Volume by Day"
)
st.plotly_chart(dow_fig, use_container_width=True)

st.subheader("Summary Statistics")
st.write(filtered[['Category', 'timeStamp', 'zip', 'twp']].describe(include='all'))

st.markdown(
    """
    <div style='text-align: center; padding-top: 30px; font-size: 14px; color: #333;'>
        Developed by Aradhana Singh
    </div>
    """,
    unsafe_allow_html=True
)
