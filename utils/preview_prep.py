import pandas as pd
from streamlit import cache_data
from streamlit.runtime.uploaded_file_manager import UploadedFile

@cache_data(persist="disk")
def split_processed_data_sheets(file: UploadedFile):
    matches = pd.read_excel(file, sheet_name="Matches", parse_dates=["Match Date"])
    ranking = pd.read_excel(file, sheet_name="Ranking")
    return matches, ranking

@cache_data(persist="disk")
def map_divisions_leagues_images(processed_data: UploadedFile):
    matches = pd.read_excel(processed_data, sheet_name="Matches")
    res = pd.read_csv("data_mapping/leagues_countries_images.csv", sep=";")
    leagues = list(matches["League"].unique())
    res = res[res["League"].isin(leagues)]
    res["Flag Filepaths"] = res["Flag Filename"].map(lambda filename: f"img\\countries\\{filename}")
    res["Division Filepaths"] = res["Division Filename"].map(lambda filename: f"img\\divisions\\{filename}")
    return res

def countries_flags(leagues_mapping: pd.DataFrame):
    countries_flags_map = zip(leagues_mapping["Country"], leagues_mapping["Flag Filepaths"])
    return list(countries_flags_map)

def divisions_logos(leagues_mapping: pd.DataFrame):
    divisions_flags_map = zip(leagues_mapping["League"], leagues_mapping["Division Filepaths"])
    return list(divisions_flags_map)

def group_goals_per_month(matches: pd.DataFrame, at_home: bool):
    res = matches.groupby('Match Date', as_index=False)['Full time home team goals' if at_home else 'Full time away team goals'].sum()
    res = res.groupby(pd.Grouper(key='Match Date', freq='YE')).sum()
    return res.reset_index()

def group_wins_per_team(matches: pd.DataFrame, at_home: bool):
    win_indicator = "H" if at_home else "A"
    res = matches[matches["Full time result"] == win_indicator]
    res = res.groupby("Home Team", as_index=False)["Full time result"].count()
    return res

def most_consistent_team(ranking: pd.DataFrame):
    most_consistent_idx = ranking["Consistency - All"].idxmax()
    most_consist_team = ranking["Teams"].loc[most_consistent_idx]
    most_consistent_value = ranking["Consistency - All"].loc[most_consistent_idx]
    return most_consist_team, most_consistent_value

def highest_elo_team(ranking: pd.DataFrame):
    highest_elo_idx = ranking["Elo"].idxmax()
    highest_elo_team = ranking["Teams"].loc[highest_elo_idx]
    highest_elo_value = ranking["Elo"].loc[highest_elo_idx]
    return highest_elo_team, highest_elo_value