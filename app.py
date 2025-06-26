import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
import plotly.express as px
from streamlit_folium import st_folium

st.set_page_config(page_title="911 Calls Dashboard", layout="wide")

@st.cache_data
def load_data(path):
    df = pd.read_csv(path, compression='gzip')
    if 'title' not in df.columns:
        st.error("'title' column is missing in the dataset.")
        st.stop()
    df.loc[:, 'Category'] = df['title'].apply(lambda x: x.split(':')[0] if ':' in x else x)
    df['timeStamp'] = pd.to_datetime(df['timeStamp'], errors='coerce')
    return df.dropna(subset=['timeStamp', 'lat', 'lng'])

df = load_data("compressed_data.csv.gz")

st.title("911 Calls Exploratory Dashboard")
st.markdown("##### Acknowledgements: Data provided by montcoalert.org")

st.sidebar.header("Filters")
categories = st.sidebar.multiselect(
    "Select Emergency Categories",
    options=df['Category'].unique(),
    default=df['Category'].unique()
)

date_range = st.sidebar.date_input(
    "Date range",
    [df['timeStamp'].min().date(), df['timeStamp'].max().date()]
)

sample_size = st.sidebar.slider(
    "Sample size for scatter plot",
    min_value=100, max_value=5000, value=1000, step=100
)

filtered = df[
    (df['Category'].isin(categories)) &
    (df['timeStamp'].dt.date.between(date_range[0], date_range[1]))
]

st.markdown("### Data Preview")
st.dataframe(filtered.head())

st.markdown("### Heatmap of All Calls")
heat_data = filtered[['lat', 'lng']].dropna().values.tolist()

if heat_data:
    heatmap_map = folium.Map(
        location=[filtered['lat'].mean(), filtered['lng'].mean()],
        zoom_start=9,
        tiles='CartoDB positron'
    )
    HeatMap(heat_data, radius=10, blur=25).add_to(heatmap_map)
    st_folium(heatmap_map, width=700, height=500)
else:
    st.warning("No data to display on heatmap. Adjust filters or check your dataset.")

st.markdown("### Scatter Geo Plot by Category (Philadelphia Area)")

philly_lat = 39.9526
philly_lon = -75.1652

scatter_sample = filtered.sample(min(len(filtered), sample_size))

scatter_fig = px.scatter_geo(
    scatter_sample,
    lat='lat',
    lon='lng',
    color='Category',
    title='911 Calls Distribution by Category (Philadelphia)',
    hover_data={'lat': True, 'lng': True, 'Category': True},
    scope='usa',
    height=600
)

scatter_fig.update_geos(
    center={"lat": philly_lat, "lon": philly_lon},
    projection_type="azimuthal equal area",
    fitbounds=False,
    resolution=50,
    lataxis_range=[39.8, 40.1],
    lonaxis_range=[-75.3, -74.9],
    showland=True
)

scatter_fig.update_layout(
    margin={"r": 0, "t": 50, "l": 0, "b": 0},
    paper_bgcolor='white',
    plot_bgcolor='white'
)

st.plotly_chart(scatter_fig, use_container_width=True)

st.markdown("### Call Volume by Day of Week")
dow_fig = px.histogram(
    filtered.assign(day=filtered['timeStamp'].dt.day_name()),
    x='day',
    category_orders={'day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']},
    title="Call Volume by Day of Week"
)
st.plotly_chart(dow_fig, use_container_width=True)

st.markdown("### Summary Statistics")
st.write(filtered[['Category', 'timeStamp', 'zip', 'twp']].describe(include='all'))

st.markdown(
    """
    <div style='text-align: center; padding-top: 30px; font-size: 14px; color: #333;'>
        Developed by Aradhana Singh
    </div>
    """,
    unsafe_allow_html=True
)


