from datetime import datetime
from typing import Literal
from io import BytesIO

import pandas as pd
from streamlit.runtime.uploaded_file_manager import UploadedFile

import utils.data_fetching as fetching

def get_leagues_list(leagues_sources_path: str):
    df = pd.read_csv(leagues_sources_path)
    return list(df["League"])

def map_fullname_columns(matches_dataset: pd.DataFrame):
    header_dictionary = pd.read_csv("data_mapping/header_dictionary.csv")
    header_mapping = dict(zip(header_dictionary["Field"], header_dictionary["Fullname"]))
    matches_dataset.rename(columns=header_mapping, inplace=True)

def create_ranking(matches: pd.DataFrame, at_home: bool) -> pd.DataFrame:
    # Creating a ranking from matches that happened between two dates
    # NB : Win = 3 points, Draw = 1 point, Loss = 0 point

    col = "Home Team" if at_home else "Away Team"
    result_mapping = {
        "H": "Win" if at_home else "Loss",
        "D": "Draw",
        "A": "Loss" if at_home else "Win",
    }

    results = matches.groupby([col, "Full time result"])["Match Date"].count().reset_index()
    results = results.pivot(index=col, columns="Full time result", values="Match Date")
    results = results.rename(columns=result_mapping)
    results = results.fillna(0)
    results = results[["Win", "Draw", "Loss"]]
    results["Points"] = results["Win"] * 3 + results["Draw"] * 1
    return results

def create_overall_ranking(matches: pd.DataFrame) -> pd.DataFrame:
    home_ranking = create_ranking(matches, True)
    away_ranking = create_ranking(matches, False)
    combined = pd.concat([home_ranking, away_ranking], axis="index")
    return combined.groupby(combined.index).sum()

def reindexing_ranking(ranking: pd.DataFrame):
    ranking.index.name = "Teams"

# Add an indicator for form consistency
def form_consistency_indicator(results: list[Literal["H", "D", "A"]]) -> float:
    if len(results) <= 1:
        return None
    # Count how much result change between the last match and a previous one
    variation = 0
    prev_res = results[0]
    for i in range(1, len(results)):
        if results[i] != prev_res:
            variation += 1
        prev_res = results[i]
    # Normalize with the total number of possible switches (number of matches played - 1)
    possible_switches = len(results) - 1
    return 1-(variation/possible_switches)

def team_side_consistency(matches: pd.DataFrame, team_name: str, at_home: bool = True):
    col_team = "Home Team" if at_home else "Away Team"
    team_matches = matches[matches[col_team] == team_name]
    team_matches = team_matches.sort_values(by="Match Date", ascending=True)
    return form_consistency_indicator(list(team_matches["Full time result"]))

def team_all_consistency(matches: pd.DataFrame, team_name: str):
    def team_result(team_name: str, home_team: str, ftresult: str):
        inverted_result = {
            'H': 'A',
            'D': 'D',
            'A': 'H',
        }
        if team_name != home_team:
            return inverted_result[ftresult]
        return ftresult
    team_matches = matches[(matches["Home Team"] == team_name) | (matches["Away Team"] == team_name)]
    team_matches = team_matches.sort_values(by="Match Date", ascending=True)
    team_matches["TeamResult"] = team_matches.apply(
        lambda row: team_result(team_name, row["Home Team"], row["Full time result"]),
    axis=1
    )
    return form_consistency_indicator(list(team_matches["TeamResult"]))

def team_consistency(
        matches: pd.DataFrame, team_name: str, side: Literal['home', 'away'] = None):
    if side == 'home':
        return team_side_consistency(matches, team_name, at_home=True)
    elif side == 'away':
        return team_side_consistency(matches, team_name, at_home=False)
    return team_all_consistency(matches, team_name)

def add_consistency_columns(ranking: pd.DataFrame, matches: pd.DataFrame):
    ranking["Consistency - Home"] = ranking.index.map(lambda name: team_consistency(matches, name, side="home"))
    ranking["Consistency - Away"] = ranking.index.map(lambda name: team_consistency(matches, name, side="away"))
    ranking["Consistency - All"] = ranking.index.map(lambda name: team_consistency(matches, name))

def team_side_goals(matches: pd.DataFrame, team_name: str, at_home: bool = True) -> int:
    col_team = "Home Team" if at_home else "Away Team"
    team_matches = matches[matches[col_team] == team_name]
    col_goals = "Full time home team goals" if at_home else "Full time away team goals"
    return int(team_matches[col_goals].sum())

def add_goals_columns(ranking: pd.DataFrame, matches: pd.DataFrame):
    ranking["Goals - Home"] = ranking.index.map(lambda name: team_side_goals(matches, name, at_home=True))
    ranking["Goals - Away"] = ranking.index.map(lambda name: team_side_goals(matches, name, at_home=False))
    ranking["Goals - All"] = ranking.apply(lambda row: row["Goals - Home"] + row["Goals - Away"], axis=1)

def team_side_conceded(matches: pd.DataFrame, team_name: str, at_home: bool = True) -> int:
    col_team = "Home Team" if at_home else "Away Team"
    team_matches = matches[matches[col_team] == team_name]
    col_goals = "Full time away team goals" if at_home else "Full time home team goals"
    return int(team_matches[col_goals].sum())

def add_conceded_columns(ranking: pd.DataFrame, matches: pd.DataFrame):
    ranking["Conceded - Home"] = ranking.index.map(lambda name: team_side_conceded(matches, name, at_home=True))
    ranking["Conceded - Away"] = ranking.index.map(lambda name: team_side_conceded(matches, name, at_home=False))
    ranking["Conceded - All"] = ranking.apply(lambda row: row["Conceded - Home"] + row["Conceded - Away"], axis=1)

def team_side_shots(matches: pd.DataFrame, team_name: str, at_home: bool = True) -> int:
    col_team = "Home Team" if at_home else "Away Team"
    team_matches = matches[matches[col_team] == team_name]
    col_shots = "Home Team Shots" if at_home else "Away Team Shots"
    return int(team_matches[col_shots].sum())

def add_shots_columns(ranking: pd.DataFrame, matches: pd.DataFrame):
    ranking["Shots - Home"] = ranking.index.map(lambda name: team_side_shots(matches, name, at_home=True))
    ranking["Shots - Away"] = ranking.index.map(lambda name: team_side_shots(matches, name, at_home=False))
    ranking["Shots - All"] = ranking.apply(lambda row: row["Shots - Home"] + row["Shots - Away"], axis=1)

def team_side_shots_conceded(matches: pd.DataFrame, team_name: str, at_home: bool = True) -> int:
    col_team = "Home Team" if at_home else "Away Team"
    team_matches = matches[matches[col_team] == team_name]
    col_shots = "Away Team Shots" if at_home else "Home Team Shots"
    return int(team_matches[col_shots].sum())

def add_shots_conceded_columns(ranking: pd.DataFrame, matches: pd.DataFrame):
    ranking["Shots conceded - Home"] = ranking.index.map(lambda name: team_side_shots_conceded(matches, name, at_home=True))
    ranking["Shots conceded - Away"] = ranking.index.map(lambda name: team_side_shots_conceded(matches, name, at_home=False))
    ranking["Shots conceded - All"] = ranking.apply(lambda row: row["Shots conceded - Home"] + row["Shots conceded - Away"], axis=1)

def team_side_target(matches: pd.DataFrame, team_name: str, at_home: bool = True) -> int:
    col_team = "Home Team" if at_home else "Away Team"
    team_matches = matches[matches[col_team] == team_name]
    col_target = "Home Team Shots on Target" if at_home else "Away Team Shots on Target"
    return int(team_matches[col_target].sum())

def add_target_columns(ranking: pd.DataFrame, matches: pd.DataFrame):
    ranking["Shots on target - Home"] = ranking.index.map(lambda name: team_side_target(matches, name, at_home=True))
    ranking["Shots on target - Away"] = ranking.index.map(lambda name: team_side_target(matches, name, at_home=False))
    ranking["Shots on target - All"] = ranking.apply(lambda row: row["Shots on target - Home"] + row["Shots on target - Away"], axis=1)

def elo(elo_dataset: pd.DataFrame, team_name: str):
    team_elos = elo_dataset[elo_dataset["Club"] == team_name]
    team_elos = team_elos.sort_values("From", ascending=False)
    res = team_elos["Elo"].iloc[0]
    return res

def add_elo_column(ranking: pd.DataFrame, elo_dataset: pd.DataFrame):
    ranking["Elo"] = ranking.index.map(lambda name: elo(elo_dataset, name))

def add_country_league_columns(ranking: pd.DataFrame, matches: pd.DataFrame):
    home_team_country_league = matches[["Home Team", "Country", "League"]]
    home_team_country_league = home_team_country_league.rename({"Home Team": "Team"}, axis="columns")
    away_team_country_league = matches[["Away Team", "Country", "League"]]
    away_team_country_league = away_team_country_league.rename({"Away Team": "Team"}, axis="columns")

    team_country_league = pd.concat([home_team_country_league, away_team_country_league], axis="index", ignore_index=True)
    team_country_league.drop_duplicates(inplace=True)
    country_mapping = dict(zip(team_country_league["Team"], team_country_league["Country"]))
    league_mapping = dict(zip(team_country_league["Team"], team_country_league["League"]))
    
    ranking["Country"] = ranking.index.map(lambda x: country_mapping[x])
    ranking["League"] = ranking.index.map(lambda x: league_mapping[x])
    
    return team_country_league

def process_input_data(
        leagues_to_keep: list[str],
        from_date: datetime, to_date: datetime
    ):
    df_matches = fetching.fetch_matches_data()
    map_fullname_columns(df_matches)

    df_matches = df_matches[df_matches["League"].isin(leagues_to_keep)]
    df_matches = df_matches[df_matches["Match Date"].between(from_date, to_date)]

    df_elo = fetching.fetch_elo_data()
    fetching.pre_process_elo_data(df_elo, df_matches)
    df_elo = df_elo[df_elo["League"].isin(leagues_to_keep)]

    ranking = create_overall_ranking(df_matches)
    reindexing_ranking(ranking)
    add_consistency_columns(ranking, df_matches)
    add_goals_columns(ranking, df_matches)
    add_conceded_columns(ranking, df_matches)
    add_shots_columns(ranking, df_matches)
    add_shots_conceded_columns(ranking, df_matches)
    add_target_columns(ranking, df_matches)
    add_elo_column(ranking, df_elo)
    team_country_league = add_country_league_columns(ranking, df_matches)

    with pd.ExcelWriter("tmp/process_result.xlsx", mode="w") as writer:
        df_matches.to_excel(writer, sheet_name="Matches", index=False)
        ranking.to_excel(writer, sheet_name="Ranking")
        team_country_league.to_excel(writer, sheet_name="Countries and leagues", index=False)

    team_country_league.to_csv("tmp/team_country_league.csv", index=False)