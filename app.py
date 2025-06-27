import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
import plotly.express as px
from streamlit_folium import st_folium

st.set_page_config(page_title="911 Calls Dashboard", layout="wide")

@st.cache_data
def load_data(path):
    try:
        df = pd.read_csv(path, compression='gzip')
    except FileNotFoundError:
        st.error(f"File not found: {path}. Please upload the dataset.")
        st.stop()
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    if 'title' not in df.columns:
        st.error("'title' column is missing in the dataset.")
        st.stop()

    df['Category'] = df['title'].apply(lambda x: x.split(':')[0] if ':' in x else x)
    df['timeStamp'] = pd.to_datetime(df['timeStamp'], errors='coerce')
    return df.dropna(subset=['timeStamp', 'lat', 'lng'])

df = load_data("compressed_data.csv.gz")

st.title("911 Calls Exploratory Dashboard")
st.markdown("##### Acknowledgements: Data provided by montcoalert.org")

years = sorted(df['timeStamp'].dt.year.unique())
selected_year = st.sidebar.selectbox("Select Year", options=years, index=len(years) - 1)

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
    (df['timeStamp'].dt.date.between(date_range[0], date_range[1])) &
    (df['timeStamp'].dt.year == selected_year)
]

st.markdown("### Data Preview")
st.dataframe(filtered.head())

st.markdown("### Heatmap of 911 Calls")
heat_data = filtered[['lat', 'lng']].dropna().values.tolist()

if heat_data:
    heatmap_map = folium.Map(
        location=[filtered['lat'].mean(), filtered['lng'].mean()],
        zoom_start=9,
        tiles='CartoDB positron'
    )
    HeatMap(heat_data, radius=10, blur=25).add_to(heatmap_map)

    legend_html = '''
     <div style="position: fixed;
                 bottom: 50px; left: 50px; width: 160px; height: 90px;
                 border:2px solid grey; z-index:9999; font-size:14px;
                 background-color: white; padding: 10px;">
     <b>Heatmap Intensity</b><br>
     <i style="background: #ffffb2; width: 18px; height: 18px; float: left; margin-right: 5px;"></i> Low<br>
     <i style="background: #fd8d3c; width: 18px; height: 18px; float: left; margin-right: 5px;"></i> Medium<br>
     <i style="background: #e31a1c; width: 18px; height: 18px; float: left; margin-right: 5px;"></i> High
     </div>
     '''
    heatmap_map.get_root().html.add_child(folium.Element(legend_html))
    st_folium(heatmap_map, width=700, height=500)
else:
    st.warning("No data to display on heatmap. Adjust filters or check your dataset.")

st.markdown("### Scatter Geo Plot by Category")
philly_lat = 39.9526
philly_lon = -75.1652

scatter_fig = px.scatter_geo(
    filtered.sample(min(len(filtered), sample_size)),
    lat='lat',
    lon='lng',
    color='Category',
    title='911 Calls Distribution by Category',
    height=600
)
scatter_fig.update_geos(
    projection_scale=25,
    center={"lat": philly_lat, "lon": philly_lon},
    showland=True, fitbounds="locations"
)
st.plotly_chart(scatter_fig, use_container_width=True)

st.markdown("### Call Volume by Hour")
time_fig = px.histogram(
    filtered,
    x=filtered['timeStamp'].dt.hour,
    nbins=24,
    labels={'x': 'Hour of Day', 'count': 'Number of Calls'},
    title="Call Volume by Hour"
)
st.plotly_chart(time_fig, use_container_width=True)

st.markdown("### Call Volume by Day of Week")
dow_fig = px.histogram(
    filtered,
    x=filtered['timeStamp'].dt.day_name(),
    category_orders={'day_name()': ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']},
    title="Call Volume by Day of Week"
)
st.plotly_chart(dow_fig, use_container_width=True)

st.markdown("### Summary Statistics")
st.write(filtered[['Category', 'timeStamp', 'zip', 'twp']].describe(include='all'))

st.markdown(
    """
    <div style='text-align: center; padding-top: 30px; font-size: 18px; color: white;'>
         by Aradhana Singh
    </div>
    """,
    unsafe_allow_html=True
)

