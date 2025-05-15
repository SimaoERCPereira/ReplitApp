import os
import requests
from datetime import datetime
from .models import Team, Match
from .extensions import db

FPL_BASE_URL = "https://fantasy.premierleague.com/api/"
FPL_BOOTSTRAP_STATIC_URL = f"{FPL_BASE_URL}bootstrap-static/"
FPL_FIXTURES_URL = f"{FPL_BASE_URL}fixtures/"
TEAM_CREST_URL_TEMPLATE = (
    "https://resources.premierleague.com/premierleague/badges/rb/t{team_code}.svg"
)

def parse_fpl_datetime(datetime_str):
    if not datetime_str:
        return None
    if datetime_str.endswith("Z"):
        datetime_str = datetime_str[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(datetime_str)
    except ValueError:
        return None

def fetch_and_update_fpl_teams_standings():
    try:
        response = requests.get(FPL_BOOTSTRAP_STATIC_URL)
        response.raise_for_status()
        data = response.json()
        teams_data = data.get("teams", [])
        updated_teams = 0
        new_teams = 0
        for team_data in teams_data:
            team = Team.query.filter_by(fpl_id=team_data["id"]).first()
            if not team:
                team = Team.query.filter(
                    db.func.lower(Team.name) == db.func.lower(team_data["name"])
                ).first()
                if not team:
                    team = Team()
                    db.session.add(team)
                    new_teams += 1
            else:
                updated_teams += 1
            team.fpl_id = team_data["id"]
            team.name = team_data["name"]
            team.short_name = team_data["short_name"]
            team.fpl_team_code = team_data["code"]
            team.logo_url = TEAM_CREST_URL_TEMPLATE.format(team_code=team_data["code"])
            team.played = team_data.get("played", 0)
            team.win = team_data.get("win", 0)
            team.draw = team_data.get("draw", 0)
            team.loss = team_data.get("loss", 0)
            team.points = team_data.get("points", 0)
            team.position = team_data.get("position", 0)
            raw_form = team_data.get("form")
            if isinstance(raw_form, str):
                team.form = raw_form
            elif isinstance(raw_form, list) and raw_form:
                try:
                    team.form = ",".join(str(f) for f in raw_form)
                except TypeError:
                    team.form = None
            else:
                team.form = None
        db.session.commit()
        return f"Teams and standings updated: {updated_teams} updated, {new_teams} new."
    except requests.RequestException as e:
        return f"Error fetching FPL team data: {e}"
    except Exception as e:
        db.session.rollback()
        return f"Error processing FPL team data: {e}"

def fetch_and_update_fpl_fixtures():
    try:
        response = requests.get(FPL_FIXTURES_URL)
        response.raise_for_status()
        fixtures_data = response.json()
        updated_count = 0
        new_count = 0
        for fixture_data in fixtures_data:
            match = Match.query.filter_by(fpl_fixture_id=fixture_data["id"]).first()
            if not match:
                match = Match()
                new_count += 1
            else:
                updated_count += 1
            home_team_obj = Team.query.filter_by(
                fpl_id=fixture_data.get("team_h")
            ).first()
            away_team_obj = Team.query.filter_by(
                fpl_id=fixture_data.get("team_a")
            ).first()
            if not home_team_obj or not away_team_obj:
                continue
            match.fpl_fixture_id = fixture_data["id"]
            match.team1_id = home_team_obj.id
            match.team2_id = away_team_obj.id
            match.match_date = parse_fpl_datetime(fixture_data.get("kickoff_time"))
            match.score_team1 = fixture_data.get("team_h_score")
            match.score_team2 = fixture_data.get("team_a_score")
            match.gameweek = fixture_data.get("event")
            if (
                fixture_data.get("started")
                and not fixture_data.get("finished_provisional")
                and not fixture_data.get("finished")
            ):
                match.status = "Live"
            elif fixture_data.get("finished_provisional") or fixture_data.get("finished"):
                match.status = "Finished"
            elif fixture_data.get("kickoff_time"):
                match.status = "Upcoming"
            else:
                match.status = "Scheduled"
            db.session.add(match)
        db.session.commit()
        return f"Fixtures updated: {new_count} new, {updated_count} updated."
    except requests.RequestException as e:
        return f"Error fetching FPL fixture data: {e}"
    except Exception as e:
        db.session.rollback()
        return f"An unexpected error occurred during fixture processing: {e}" 