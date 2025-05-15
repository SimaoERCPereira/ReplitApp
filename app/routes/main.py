from flask import Blueprint, render_template, request
from ..models import Match, Team
from ..extensions import cache
from datetime import datetime, timezone

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
@main_bp.route("/home")
@cache.cached(timeout=120)
def home():
    from datetime import datetime
    selected_gameweek = request.args.get("gameweek", type=int)
    now = datetime.now()
    gameweeks_query = (
        Match.query.with_entities(Match.gameweek)
        .filter(Match.gameweek.isnot(None))
        .distinct()
        .order_by(Match.gameweek.asc())
        .all()
    )
    all_gameweeks = [gw[0] for gw in gameweeks_query]
    matches_query = Match.query.order_by(Match.match_date.asc())
    if selected_gameweek is not None:
        matches_query = matches_query.filter(Match.gameweek == selected_gameweek)
    matches = matches_query.all()
    current_display_gameweek = selected_gameweek
    if current_display_gameweek is None and all_gameweeks:
        now = datetime.now(timezone.utc)
        first_relevant_gameweek = (
            Match.query.with_entities(Match.gameweek)
            .filter(Match.gameweek.isnot(None), Match.match_date > now)
            .order_by(Match.gameweek.asc(), Match.match_date.asc())
            .first()
        )
        if first_relevant_gameweek:
            current_display_gameweek = first_relevant_gameweek[0]
        elif all_gameweeks:
            current_display_gameweek = all_gameweeks[-1]
    if selected_gameweek is not None:
        matches_to_display = [m for m in matches if m.gameweek == selected_gameweek]
    elif current_display_gameweek is not None:
        matches_to_display = [m for m in matches if m.gameweek == current_display_gameweek]
        selected_gameweek = current_display_gameweek
    else:
        matches_to_display = matches
    return render_template(
        "index.html",
        title="Home",
        matches=matches_to_display,
        all_gameweeks=all_gameweeks,
        selected_gameweek=selected_gameweek,
    )

@main_bp.route("/standings")
@cache.cached(timeout=120)
def standings():
    teams = Team.query.order_by(Team.position.asc()).all()
    return render_template("standings.html", title="Standings", teams=teams) 