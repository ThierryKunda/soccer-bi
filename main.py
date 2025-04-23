import streamlit as st

# Data process page configuration
title_1 = "Data process"
icon_1 = "🔁"
p1 = st.Page("views/data_process.py", title=title_1, icon=icon_1, url_path="data-process")

# Data preview page configuration
title_2 = "Data preview"
icon_2 = "📊"
p2 = st.Page("views/data_preview.py", title=title_2, icon=icon_2, url_path="data-preview")

# Prediction sheet page configuration
title_3 = "Prediction sheets"
icon_3 = "📆"
p3 = st.Page("views/prediction_sheets.py", title=title_3, icon=icon_3, url_path="prediction-sheet")

pg = st.navigation([p1, p2, p3])
pg.run()