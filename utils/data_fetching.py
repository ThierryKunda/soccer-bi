from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import icalendar as ical
import requests as req

import pandas as pd
import numpy as np

def fetch_matches_data():
    leagues_sources = pd.read_csv("data_mapping/leagues_sources.csv")
    leagues_headers = dict(zip(leagues_sources["League"], leagues_sources["Source"]))
    leagues_headers = {league_name: pd.read_csv(leagues_headers[league_name], nrows=1) for league_name in leagues_headers}
    # Get columns of each league
    leagues_columns = {league_name: list(leagues_headers[league_name].columns) for league_name in leagues_headers}
    # Convert result as list of sets
    leagues_columns_list = [set(leagues_columns[league_name]) for league_name in leagues_columns]
    # Leagues
    common_columns = list(set.intersection(*leagues_columns_list))

    selected_columns = common_columns + ["Country", "League"]
    global_dataset = pd.DataFrame()
    for i in range(len(leagues_sources)):
        df_current_league = pd.read_csv(leagues_sources["Source"].loc[i], parse_dates=["Date"], dayfirst=True)
        df_current_league["Country"] = leagues_sources["Country"].loc[i]
        df_current_league["League"] = leagues_sources["League"].loc[i]
        global_dataset = pd.concat([global_dataset, df_current_league[selected_columns]], axis=0)
    return global_dataset

def fetch_elo_data():
    now = datetime.now().strftime("%Y-%m-%d")
    return pd.read_csv(f"http://api.clubelo.com/{now}", parse_dates=["From", "To"])


def add_country_column(elo: pd.DataFrame, matches: pd.DataFrame):
    home_team_countries = matches[["Home Team", "Country"]]
    away_team_countries = matches[["Away Team", "Country"]]
    home_team_countries = home_team_countries.rename({"Home Team": "Team"}, axis=1)
    away_team_countries = away_team_countries.rename({"Away Team": "Team"}, axis=1)
    all_teams_countries = pd.concat([home_team_countries, away_team_countries], axis=0, ignore_index=True)
    all_teams_countries.drop_duplicates(inplace=True)
    teams_countries_mapping = dict(zip(all_teams_countries["Team"], all_teams_countries["Country"]))
    def map_country_to_team(row):
        if row["Club"] in teams_countries_mapping:
            return teams_countries_mapping[row["Club"]]
        return row["Country Alias"]
    elo.rename({"Country": "Country Alias"}, axis=1, inplace=True)
    elo["Country"] = elo.apply(map_country_to_team, axis=1)

def add_league_column(elo: pd.DataFrame, matches: pd.DataFrame):
    home_team_leagues = matches[["Home Team", "League"]]
    away_team_leagues = matches[["Away Team", "League"]]
    home_team_leagues = home_team_leagues.rename({"Home Team": "Team"}, axis=1)
    away_team_leagues = away_team_leagues.rename({"Away Team": "Team"}, axis=1)
    all_teams_leagues = pd.concat([home_team_leagues, away_team_leagues], axis=0, ignore_index=True)
    all_teams_leagues.drop_duplicates(inplace=True)
    teams_leagues_mapping = dict(zip(all_teams_leagues["Team"], all_teams_leagues["League"]))
    def map_league_to_team(row):
        if row["Club"] in teams_leagues_mapping:
            return teams_leagues_mapping[row["Club"]]
        return row["Level"]
    elo["League"] = elo.apply(map_league_to_team, axis=1)

def pre_process_elo_data(elo: pd.DataFrame, matches: pd.DataFrame):

    datasets_mapping = pd.read_csv("data_mapping/team_elo_matches_mapping.csv")
    datasets_mapping.replace({np.nan: None}, inplace=True)
    
    # Update elo team names that are different, looking at the matches dataset
    elo_global_teams_mapping = dict(zip(
        datasets_mapping["Elo team name"],
        datasets_mapping["Global team name"])
    )
    elo.replace(elo_global_teams_mapping, inplace=True)

    # Adding country column to elo dataset
    add_country_column(elo, matches)
    add_league_column(elo, matches)

def get_league_fixtures(league_calendar_url: str):
    calendar_str = req.get(league_calendar_url).text
    calendar_obj = ical.Calendar.from_ical(calendar_str)
    fixtures_dict = {
        "Match Date": [],
        "Home Team": [],
        "Away Team": []
    }
    for event in calendar_obj.events:
        fixtures_dict["Match Date"].append(event.decoded("DTSTART"))
        home_team, away_team = event["SUMMARY"].split(" v ")
        fixtures_dict["Home Team"].append(home_team)
        fixtures_dict["Away Team"].append(away_team)
    return pd.DataFrame(fixtures_dict)

def process_fixtures_data(league_name: str, fixtures_df: pd.DataFrame, assigned_timezone: str):
    today_dt = datetime.today().replace(tzinfo=timezone.utc)
    # Picking monday of the current week
    current_monday = today_dt - timedelta(days=today_dt.weekday())
    # Picking sunday of the current week
    current_sunday = current_monday + timedelta(days=7)
    # Applying dates filters
    current_week_fixtures = fixtures_df[fixtures_df["Match Date"].between(current_monday, current_sunday)].copy()
    # Getting match date time according to locale timezone
    current_week_fixtures["Match Date (locale)"] = current_week_fixtures["Match Date"].map(lambda x: x.astimezone(ZoneInfo(assigned_timezone)).replace(tzinfo=None))
    # Adding blank columns to be filled by the user
    blank_columns = ["Bet prediction", "Bet odd", "Confidence", "Result"]
    for col in blank_columns:   
        current_week_fixtures[col] = pd.Series()
    # Adding a "league" column
    current_week_fixtures["League"] = league_name
    # Reordering columns
    order = ["Match Date (locale)", "League", "Home Team", "Away Team"] + blank_columns
    current_week_fixtures_reord = current_week_fixtures[order]
    current_week_fixtures_reord
    return current_week_fixtures_reord

def get_current_week_fixtures(assigned_timezone: str):
    # Getting all sources
    fixtures_sources_df = pd.read_csv("data_mapping/leagues_sources.csv")
    # Filtering available sources
    fixtures_sources_df = fixtures_sources_df[fixtures_sources_df["Fixtures Source"].notna()]
    # Dictionary from league and sources
    fixtures_sources_dict = dict(zip(fixtures_sources_df["League"], fixtures_sources_df["Fixtures Source"]))
    # Generating a whole dataframe for all fixtures
    all_fixtures_df = pd.DataFrame()
    for league in fixtures_sources_dict:
        league_fixtures = get_league_fixtures(fixtures_sources_dict[league])
        processed_fixtures = process_fixtures_data(league, league_fixtures, assigned_timezone)
        all_fixtures_df = pd.concat([all_fixtures_df, processed_fixtures], axis=0)
    return all_fixtures_df.sort_values(["League", "Match Date (locale)"])

def save_fixtures_as_sheets(current_week_all_fixtures: pd.DataFrame, prediction_sheets_path: str):
    with pd.ExcelWriter(prediction_sheets_path, mode='w') as pred_writer:
        current_week_all_fixtures.to_excel(pred_writer, sheet_name="Full time result", index=False)
        current_week_all_fixtures.to_excel(pred_writer, sheet_name="Win or draw", index=False)
        current_week_all_fixtures.to_excel(pred_writer, sheet_name="Over X goals", index=False)