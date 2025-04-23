from datetime import datetime
from zoneinfo import available_timezones

import streamlit as st

from utils.data_fetching import get_current_week_fixtures, save_fixtures_as_sheets

"# Soccer BI - prediction sheets"

"## Page description"

"""
This page allows the user to generate to-fill prediction sheets, with the three following sections:
1. Full time result
2. Win or draw
3. Over X goals
""" 

"**NB : Only the Top 5 competitions (Premier League, La Liga,...) have been specified in the sheets. Do not hesitate to add other leagues fixtures if needed.**"
"**NB2 : Machine Learning is not used for making automated prediction, yet. I am thinking of ways to use ML efficiently on this app.**"

"## Generation options"

tz = st.selectbox("Choose a timezone for fixtures datetime", available_timezones())

if st.button("Generate prediction sheets"):
    with st.spinner("Fixtures fetching in progess...", show_time=True):
        # Saving fixtures as Excel file
        fixtures = get_current_week_fixtures(tz)
        save_fixtures_as_sheets(fixtures, "tmp/prediction_sheet.xlsx")
    # Displaying download button
    d = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open("tmp/prediction_sheet.xlsx", "rb") as f:
        st.download_button("Download prediction sheets", f, file_name=f"prediction_sheet_{d}.xlsx")