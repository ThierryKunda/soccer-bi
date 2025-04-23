import streamlit as st

from utils.preview_prep import (
    split_processed_data_sheets,
    map_divisions_leagues_images,
    countries_flags,
    divisions_logos,
    group_goals_per_month,
    group_wins_per_team,
    most_consistent_team,
    highest_elo_team
    )

"# Soccer BI - data preview"

"## Page description"

"""
This page allows the user to preview data with **contextual information** (available leagues, countries represented,...)
and some **key analytical information**.
"""

"## Preview options"

"""
Coming from the [Data process page](/), we assume that you have already downloaded the processed data.
"""

data = st.file_uploader("Drop the processed data here", type="xlsx")

if data:
    with st.spinner(text="Loading data...", show_time=True):
        df_matches, df_ranking = split_processed_data_sheets(data)
        df_leagues = map_divisions_leagues_images(data)

    "## Overall information"
    
    "### KPIs"

    countries = list(df_matches["Country"].unique())
    country_selected = st.selectbox("Country", ["All"] + countries)

    df_country_matches = df_matches[df_matches["Country"] == country_selected] if country_selected != "All" else df_matches

    col1, col2, col3 = st.columns(3)

    oldest_date = df_country_matches["Match Date"].min()
    latest_date = df_country_matches["Match Date"].max()
    matches_days = df_country_matches["Match Date"].unique().size * 1.0
    matches_number = len(df_country_matches)
    leagues_number = df_country_matches["Division"].unique().size
    teams_number = df_country_matches["Home Team"].unique().size

    with col1:
        st.metric("Oldest match", oldest_date.strftime("%Y/%m/%d"), border=True)
        st.metric("Latest match", latest_date.strftime("%Y/%m/%d"), border=True)
    with col2:
        st.metric("Number of matches", matches_number, border=True)
        st.metric("Number of matches per day", round(matches_number/matches_days, 2), border=True)
    with col3:
        st.metric("Number of leagues", leagues_number, border=True)
        st.metric("Number of teams", teams_number, border=True)

    "## Divisions"

    "Countries represented fullnames:"
    countries_images = countries_flags(df_leagues)
    countries_columns = st.columns(3)
    for i in range(len(countries_images)):
        countries_col_idx = i % 3
        countries_columns[countries_col_idx].image(caption=countries_images[i][0], image=countries_images[i][1], width=80)

    "Divisions represented with fullnames:"
    divisions_images = divisions_logos(df_leagues)
    divisions_columns = st.columns(3)
    for i in range(len(divisions_images)):
        divisions_col_idx = i % 3
        divisions_columns[divisions_col_idx].image(caption=divisions_images[i][0], image=divisions_images[i][1], width=80)

    "### Historic goals"
    leagues = list(df_country_matches["League"].unique())
    league_selected = st.selectbox("League", ["All"] + leagues)

    df_league_matches = (
        df_country_matches[df_matches["League"] == league_selected]
        if league_selected != "All"
        else df_country_matches
    )

    "Goals at home:"
    st.bar_chart(data=df_league_matches, x="Home Team", y="Full time home team goals")
    "...away:"
    st.bar_chart(data=df_league_matches, x="Away Team", y="Full time away team goals")
    "Goals per year at home:"
    df_league_goals = group_goals_per_month(df_league_matches, True)
    st.line_chart(data=df_league_goals, x="Match Date", y="Full time home team goals")
    "...away:"
    df_league_goals = group_goals_per_month(df_league_matches, False)
    st.line_chart(data=df_league_goals, x="Match Date", y="Full time away team goals")

    "### Elo"
    highest_elo = df_ranking["Elo"].max()
    lowest_elo = df_ranking["Elo"].min()
    elo_mean = round(df_ranking["Elo"].mean(), 2)
    elo_std_var = round(df_ranking["Elo"].std(), 2)

    stat1_col, stat2_col = st.columns(2)
    with stat1_col:
        st.metric("Highest elo", highest_elo, border=True)
        st.metric("Lowest elo", lowest_elo, border=True)

    with stat2_col:
        st.metric("Mean elo", elo_mean, border=True)
        st.metric("Standard variation of elo", elo_std_var, border=True)

    "### Historic wins"

    "Wins per teams at home:"
    df_league_results_per_team = group_wins_per_team(df_league_matches, True)
    st.bar_chart(data=df_league_results_per_team, x="Home Team", y="Full time result")
    "...away:"
    df_league_results_per_team = group_wins_per_team(df_league_matches, False)
    st.bar_chart(data=df_league_results_per_team, x="Home Team", y="Full time result")

    "## Teams"

    "### Ranking - current season"
    "Key information:"
    consist_team, consist_value = most_consistent_team(df_ranking)
    high_elo_team, high_elo_value = highest_elo_team(df_ranking)

    consist_col, team_elo = st.columns(2)
    with consist_col:
        st.metric("Most consistent team", consist_team, border=True)
        st.metric("Highest consistency ratio", round(consist_value, 2), border=True)
    
    with team_elo:
        st.metric("Highest elo team", high_elo_team, border=True)
        st.metric("Highest elo value", round(high_elo_value, 2), border=True)

    "Overall ranking:"
    st.dataframe(df_ranking[["Teams", "Points", "Win", "Draw", "Loss"]])