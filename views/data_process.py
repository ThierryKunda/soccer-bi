from datetime import datetime

import streamlit as st

from utils.ranking import get_leagues_list, process_input_data

"# Soccer BI - data process"

"## Introduction"

"""
**Soccer BI** is a data application that process datasets containing soccer matches in order to provide
a Data Visualisation dashboard that may be interesting for soccer fans who are interested
in the analytical field of data, or fans that want to define their own betting strategy.
"""

"## DataViz template"

"Here you can download the **PowerBI** template to visualise the processed data :"

with open("dataviz/pbi_template.pbit", "rb") as f:
    st.download_button("Download PBI template (.pbit)", f, file_name=f"soccer-bi_pbi_template.pbit")

"## Page description"

"""
This page allows the user to automatically process all raw data provided by one main source:
[Football-Data.co.uk](https://www.football-data.co.uk).
"""

"## Process options"

"### Leagues"
top_leagues = ["Premier League", "Bundesliga", "LaLiga", "Serie A", "Ligue 1"]
leagues_to_keep = st.multiselect(
    "Select the leagues you want to consider",
    get_leagues_list("data_mapping/leagues_sources.csv"),
    default=top_leagues
)

"### Kickoff dates range"
col1, col2 = st.columns(2)
start_date = col1.date_input("Start date", "2024-08-01")
end_date = col2.date_input("End date", "today")

all_inputs_filled = start_date and end_date

process_button = st.button("Process data") if all_inputs_filled else st.button("Process data", disabled=True)
if process_button:
    with st.spinner("Process in progress...", show_time=True):
        d1 = datetime.combine(start_date, datetime.min.time())
        d2 = datetime.combine(end_date, datetime.max.time())
        process_input_data(leagues_to_keep, d1, d2)
        st.success("Done", icon="✅")
        d = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open("tmp/process_result.xlsx", "rb") as f:
            st.download_button("Download processed data", f, file_name=f"soccer-bi_{d}.xlsx")