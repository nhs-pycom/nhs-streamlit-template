# -------------------------------------------------------------------------
# Copyright (c) 2021 NHS England and NHS Improvement. All rights reserved.
# Licensed under the MIT License. See license.txt in the project root for
# license information.
# -------------------------------------------------------------------------

"""
FILE:           nhstheme.py
DESCRIPTION:    Streamlit NHS Theme Template
CONTRIBUTORS:   Craig Shenton, Mattia Ficarelli   
CONTACT:        craig.shenton@nhs.net
CREATED:        2022-01-19
VERSION:        0.0.1
"""

# Libraries
# -------------------------------------------------------------------------
# python
import json
import time
import base64
import io
import zipfile
import regex as re
from datetime import datetime

# local

# 3rd party:
import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
from streamlit_folium import folium_static
import folium

st.set_page_config(
    page_title="Streamlit NHS Theme Template",
    page_icon="https://www.england.nhs.uk/wp-content/themes/nhsengland/static/img/favicon.ico",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/",
        "Report a bug": "https://github.com/",
        "About": "For more information, including contact details, please refer to: [link](https://github.com/)",
    },
)
padding = 1
st.markdown(
    f""" <style>
    .reportview-container .main .block-container{{
        padding-top: {padding}rem;
    }} </style> """,
    unsafe_allow_html=True,
)

# Functions & Calls
# -------------------------------------------------------------------------

# render svg image
def render_svg(svg):
    """Renders the given svg string."""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    html = r'<img src="data:image/svg+xml;base64,%s"/>' % b64
    st.write(html, unsafe_allow_html=True)


# Download functionality
@st.cache
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")

# Load data and cache
@st.cache  # use Streamlit cache decorator to cache this operation so data doesn't have to be read in everytime script is re-run
def get_data():
    path = "data/2022GPdata.csv"  # file containing the gp practice weighted populations
    df = pd.read_csv(path)
    df = df.rename(
        columns={
            "Practice_Code": "GP Practice code",
            "GP_Practice_Name": "GP Practice name",
            "Practice_Postcode": "GP Practice postcode",
            "CCG21": "CCG code",
            "Former CCG": "CCG name",
            "PCN_Code": "PCN code",
            "PCN_Name": "PCN name",
            "LOC22": "Location code",
            "LOC22name": "Location name",
            "ICS22": "ICB code",
            "ICS22name": "ICB name",
            "R22": "Region code",
            "Region22": "Region name",
            "LAD21": "LA District code",
            "LTLA21": "LA District name",
            "LA21": "LA code",
            "UTLA21": "LA name",
            "Patients": "Registered Patients"
        }
    )
    df = df.fillna(1).replace(0, 1)
    df["practice_display"] = df["GP Practice code"] + ": " + df["GP Practice name"]
    return df


# Store defined places in a list to access them later for place based calculations
@st.cache(allow_output_mutation=True)
def store_data():
    return []

# Sidebar dropdown list
@st.cache
def get_sidebar(data):
    icb = data["ICB name"].unique().tolist()
    icb.sort()
    return icb

def write_table(data):
    return AgGrid(data)

# Markdown
# -------------------------------------------------------------------------
# NHS Logo
svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 16">
            <path d="M0 0h40v16H0z" fill="#005EB8"></path>
            <path d="M3.9 1.5h4.4l2.6 9h.1l1.8-9h3.3l-2.8 13H9l-2.7-9h-.1l-1.8 9H1.1M17.3 1.5h3.6l-1 4.9h4L25 1.5h3.5l-2.7 13h-3.5l1.1-5.6h-4.1l-1.2 5.6h-3.4M37.7 4.4c-.7-.3-1.6-.6-2.9-.6-1.4 0-2.5.2-2.5 1.3 0 1.8 5.1 1.2 5.1 5.1 0 3.6-3.3 4.5-6.4 4.5-1.3 0-2.9-.3-4-.7l.8-2.7c.7.4 2.1.7 3.2.7s2.8-.2 2.8-1.5c0-2.1-5.1-1.3-5.1-5 0-3.4 2.9-4.4 5.8-4.4 1.6 0 3.1.2 4 .6" fill="white"></path>
          </svg>
"""
render_svg(svg)

st.title("Streamlit NHS Theme Template")
st.markdown("Last Updated 19th January 2022")

# Import Data
# -------------------------------------------------------------------------
data = get_data()
icb = get_sidebar(data)

# SIDEBAR
# -------------------------------------------------------------------------
st.sidebar.subheader("Filter GP Practice")

icb_choice = st.sidebar.selectbox("ICB Filter:", icb, help="Select an ICB")
lad = data["LA District name"].loc[data["ICB name"] == icb_choice].unique().tolist()
lad_choice = st.sidebar.multiselect(
    "Local Authority District Filter:", lad, help="Select a Local Authority District"
)
if lad_choice == []:
    practices = (
        data["practice_display"].loc[data["ICB name"] == icb_choice].unique().tolist()
    )
else:
    practices = (
        data["practice_display"].loc[(data["LA District name"].isin(lad_choice)) & (data["ICB name"] == icb_choice)].tolist()
    )

practice_choice = st.sidebar.selectbox(
    "Select GP Practices:",
    practices,
    help="Select GP Practice'",
)

st.sidebar.write("-" * 34)  # horizontal separator line.

# BODY
# -------------------------------------------------------------------------

# MAP
# -------------------------------------------------------------------------

map = folium.Map(location=[52, 0], zoom_start=10, tiles="openstreetmap")
lat = []
long = []

latitude = data["Latitude"].loc[data["practice_display"] == practice_choice].item()
longitude = data["Longitude"].loc[data["practice_display"] == practice_choice].item()
lat.append(latitude)
long.append(longitude)
folium.Marker(
    [latitude, longitude],
    popup=str(practice_choice),
    icon=folium.Icon(color="darkblue", icon="fa-user-md", prefix="fa"),
).add_to(map)

# bounds method https://stackoverflow.com/a/58185815
map.fit_bounds(
    [[min(lat) - 0.05, min(long)], [max(lat) + 0.05, max(long)]]
)  # add buffer to north

# call to render Folium map in Streamlit
folium_static(map, width=700, height=300)

# Group GP practice display
list_of_gps = re.sub(
    "\w+:",
    "",
    str(practice_choice).replace("'", "").replace("[", "").replace("]", ""),
)
st.info("**Selected GP Practice: **" + list_of_gps)

# Downloads
# -------------------------------------------------------------------------
current_date = datetime.now().strftime("%Y-%m-%d")

st.subheader("Download Data")

print_table = st.checkbox("Preview data download", value=True)
if print_table:
    with st.container():
        write_table(data)

csv = convert_df(data)

with open("docs/calculations.txt", "rb") as fh:
    readme_text = io.BytesIO(fh.read())

# https://stackoverflow.com/a/44946732
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
    for file_name, data in [
        ("calculations.csv", io.BytesIO(csv)),
        ("calculations.txt", readme_text)
    ]:
        zip_file.writestr(file_name, data.getvalue())

btn = st.download_button(
    label="Download ZIP",
    data=zip_buffer.getvalue(),
    file_name="nhsstreamlit_%s.zip" % current_date,
    mime="application/zip",
)

st.subheader("Help and Support")
with st.expander("About this app"):
    st.subheader("Streamlit NHS Theme Template")
    st.markdown("Developed for rapid deployment on new streamlit apps. Allows the user to filter to ICB/LAD/GP Practice.")
st.info(
    "For support with using the tool please email: [craig.shenton@nhs.net](mailto:craig.shenton@nhs.net)"
)
