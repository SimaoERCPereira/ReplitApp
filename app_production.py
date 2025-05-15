from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    send_from_directory,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    current_user,
    login_required,
)
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder="static")

# Use environment variable for secret key with a fallback
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", os.urandom(24))

# Database Configuration
# For production, use DATABASE_URL environment variable (provided by the hosting platform)
# Fall back to local DB for development
database_url = os.getenv("DATABASE_URL")

# Handle potential "postgres://" to "postgresql://" conversion (needed for some providers)
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Use the environment variable if available, otherwise fall back to local SQL Server
app.config["SQLALCHEMY_DATABASE_URI"] = (
    database_url
    or "mssql+pyodbc://SIMÃO-ASUS-ROG\LOCALSERVER/ThePeoplesPitch?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Set up production configuration
if os.getenv("FLASK_ENV") == "production":
    app.config["DEBUG"] = False
    app.config["TESTING"] = False
    app.config["PROPAGATE_EXCEPTIONS"] = True
    # Reduce stdout log spam in production
    import logging

    logging.basicConfig(level=logging.INFO)
else:
    app.config["DEBUG"] = True

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

# Create database tables at startup (before request handlers are registered)
with app.app_context():
    db.create_all()
    print("Database tables created or verified")


# Rest of your app code follows...
@app.context_processor
def inject_now():
    return {"now": datetime.utcnow()}


# Custom Jinja filter for formatting datetime objects
def format_datetime_filter(value, fmt=None):
    """Formats a datetime object. Default format: Month Day, Year HH:MM."""
    if fmt is None:
        fmt = "%B %d, %Y %H:%M"  # A user-friendly default format
    if hasattr(value, "strftime"):
        return value.strftime(fmt)
    return value  # Return original value if it cannot be formatted


app.jinja_env.filters["date"] = format_datetime_filter


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    favorite_team = db.Column(db.String(100))
    bio = db.Column(db.Text)
    join_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    comments = db.relationship("Comment", backref="author", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    short_name = db.Column(db.String(10), unique=True, nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    league = db.Column(db.String(100), nullable=True, default="Premier League")
    fpl_id = db.Column(db.Integer, unique=True, nullable=True)
    fpl_team_code = db.Column(db.Integer, nullable=True)
    played = db.Column(db.Integer, default=0)
    win = db.Column(db.Integer, default=0)
    draw = db.Column(db.Integer, default=0)
    loss = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)
    position = db.Column(db.Integer, default=0)
    form = db.Column(db.String(50), nullable=True)
    home_matches = db.relationship(
        "Match", foreign_keys="Match.team1_id", backref="home_team", lazy=True
    )
    away_matches = db.relationship(
        "Match", foreign_keys="Match.team2_id", backref="away_team", lazy=True
    )

    def __repr__(self):
        return f"<Team {self.name}>"


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team1_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    team2_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    match_date = db.Column(
        db.DateTime, nullable=False, default=db.func.current_timestamp()
    )
    status = db.Column(db.String(50), nullable=False, default="Upcoming")
    score_team1 = db.Column(db.Integer)
    score_team2 = db.Column(db.Integer)
    fpl_fixture_id = db.Column(db.Integer, unique=True, nullable=True)
    gameweek = db.Column(db.Integer, nullable=True)  # Added gameweek
    comments = db.relationship("Comment", backref="match", lazy=True)

    def __repr__(self):
        return f"<Match {self.home_team.name if self.home_team else 'N/A'} vs {self.away_team.name if self.away_team else 'N/A'}>"


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(280), nullable=False)
    timestamp = db.Column(
        db.DateTime, nullable=False, default=db.func.current_timestamp()
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey("match.id"), nullable=False)

    def __repr__(self):
        return f"<Comment '{self.text[:20]}...'>"


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
        print(
            f"Error: Could not parse datetime string '{datetime_str}' with fromisoformat."
        )
        return None


def fetch_and_update_fpl_teams_standings():
    try:
        response = requests.get(FPL_BOOTSTRAP_STATIC_URL)
        response.raise_for_status()
        data = response.json()

        # In production, reduce logging
        if os.getenv("FLASK_ENV") != "production":
            print(f"DEBUG: FPL Bootstrap API Response Keys: {list(data.keys())}")

        teams_data = data.get("teams", [])

        if not teams_data:
            if os.getenv("FLASK_ENV") != "production":
                print("DEBUG: No 'teams' data found in FPL API response.")
            return "Error: No 'teams' data found in FPL API response."

        # Reduce diagnostic prints in production
        if os.getenv("FLASK_ENV") != "production":
            print(f"DEBUG: Received {len(teams_data)} teams from FPL API.")
            if teams_data:
                print(f"DEBUG: Raw data for the first team from API: {teams_data[0]}")

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

            # Handle 'form' data: FPL API form can be null or a complex object/list.
            # Current logic sets team.form to None if it's not a simple str/int/float, leading to "N/A".
            raw_form = team_data.get("form")
            if isinstance(raw_form, str):  # If API provides a ready-to-use string form
                team.form = raw_form
            elif isinstance(raw_form, list) and raw_form:
                # Attempt to process if it's a list (e.g. of 'W', 'D', 'L' codes or simple results)
                # This part might need adjustment based on actual FPL API list structure for form
                # For now, let's assume it could be a list of strings like ['W', 'D', 'L']
                try:
                    team.form = ",".join(str(f) for f in raw_form)
                except TypeError:
                    if os.getenv("FLASK_ENV") != "production":
                        print(
                            f"DEBUG: Could not convert form list to string for team {team_data.get('name')}: {raw_form}"
                        )
                    team.form = None  # Fallback if conversion fails
            else:  # If form is None, or not a string/list we can easily handle
                team.form = None

            # Enhanced diagnostic print for the first team being processed - only in development
            if (
                os.getenv("FLASK_ENV") != "production"
                and teams_data
                and team_data["id"] == teams_data[0]["id"]
            ):
                print(f"DEBUG: --- Processing Team from API ---")
                print(
                    f"DEBUG: API Raw Data: id={team_data.get('id')}, name='{team_data.get('name')}', short_name='{team_data.get('short_name')}', code={team_data.get('code')}"
                )
                print(
                    f"DEBUG: API Stats: played={team_data.get('played')}, win={team_data.get('win')}, draw={team_data.get('draw')}, loss={team_data.get('loss')}, points={team_data.get('points')}, position={team_data.get('position')}"
                )
                print(f"DEBUG: API Form Raw: {team_data.get('form')}")
                print(f"DEBUG: --- Assigning to DB Model ({team.name}) ---")
                print(
                    f"DEBUG: DB Model Values: fpl_id={team.fpl_id}, name='{team.name}', short_name='{team.short_name}', fpl_team_code={team.fpl_team_code}"
                )
                print(
                    f"DEBUG: DB Model Stats: played={team.played}, win={team.win}, draw={team.draw}, loss={team.loss}, points={team.points}, position={team.position}"
                )
                print(f"DEBUG: DB Model Form: '{team.form}'")
                print(f"DEBUG: --- End Processing First Team ---")

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

            match.fpl_fixture_id = fixture_data["id"]
            home_team_obj = Team.query.filter_by(
                fpl_id=fixture_data.get("team_h")
            ).first()
            away_team_obj = Team.query.filter_by(
                fpl_id=fixture_data.get("team_a")
            ).first()

            if not home_team_obj or not away_team_obj:
                if os.getenv("FLASK_ENV") != "production":
                    print(
                        f"Warning: Could not find one or both teams for fixture ID {fixture_data['id']}. Home FPL ID: {fixture_data.get('team_h')}, Away FPL ID: {fixture_data.get('team_a')}. Skipping this fixture."
                    )
                continue

            match.team1_id = home_team_obj.id
            match.team2_id = away_team_obj.id
            match.match_date = parse_fpl_datetime(fixture_data.get("kickoff_time"))
            match.score_team1 = fixture_data.get("team_h_score")
            match.score_team2 = fixture_data.get("team_a_score")
            match.gameweek = fixture_data.get(
                "event"
            )  # Populate gameweek from FPL API 'event' field

            if (
                fixture_data.get("started")
                and not fixture_data.get("finished_provisional")
                and not fixture_data.get("finished")
            ):
                match.status = "Live"
            elif fixture_data.get("finished_provisional") or fixture_data.get(
                "finished"
            ):
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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
@app.route("/home")
def home():
    selected_gameweek = request.args.get("gameweek", type=int)

    # Get all distinct gameweeks that have matches, ordered
    gameweeks_query = (
        db.session.query(Match.gameweek)
        .filter(Match.gameweek.isnot(None))
        .distinct()
        .order_by(Match.gameweek.asc())
        .all()
    )
    all_gameweeks = [gw[0] for gw in gameweeks_query]

    matches_query = Match.query.order_by(Match.match_date.asc())

    if selected_gameweek is not None:
        matches_query = matches_query.filter(Match.gameweek == selected_gameweek)
    elif all_gameweeks:
        pass  # No specific gameweek filter if none selected via URL

    matches = matches_query.all()

    current_display_gameweek = selected_gameweek
    if current_display_gameweek is None and all_gameweeks:
        now = datetime.now(timezone.utc)
        first_relevant_gameweek = (
            db.session.query(Match.gameweek)
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
        matches_to_display = [
            m for m in matches if m.gameweek == current_display_gameweek
        ]
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


@app.route("/standings")
def standings():
    teams = Team.query.order_by(Team.position.asc()).all()
    return render_template("standings.html", title="Standings", teams=teams)


@app.route("/update-fpl-data")
@login_required
def update_fpl_data_route():
    if not current_user.is_admin:
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("home"))

    flash("Attempting to update FPL teams and standings...", "info")
    team_update_msg = fetch_and_update_fpl_teams_standings()
    flash(team_update_msg, "success" if "Error" not in team_update_msg else "danger")

    flash("Attempting to update FPL fixtures...", "info")
    fixture_update_msg = fetch_and_update_fpl_fixtures()
    flash(
        fixture_update_msg, "success" if "Error" not in fixture_update_msg else "danger"
    )

    return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        favorite_team = request.form.get("favorite_team")

        user_by_username = User.query.filter_by(username=username).first()
        user_by_email = User.query.filter_by(email=email).first()

        if user_by_username:
            flash("Username already exists. Please choose a different one.", "danger")
            return redirect(url_for("register"))
        if user_by_email:
            flash(
                "Email address already registered. Please use a different one or login.",
                "danger",
            )
            return redirect(url_for("register"))

        new_user = User(username=username, email=email, favorite_team=favorite_team)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Your account has been created! You are now able to log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=request.form.get("remember"))
            next_page = request.args.get("next")
            flash("Login successful!", "success")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("Login Unsuccessful. Please check email and password.", "danger")
    return render_template("login.html", title="Login")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/profile/<username>")
@login_required
def profile_page(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template(
        "profile.html", user=user, title=f"{user.username}'s Profile"
    )


@app.route("/match/<int:match_id>", methods=["GET", "POST"])
def match_discussion(match_id):
    match = Match.query.get_or_404(match_id)
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("You need to be logged in to comment.", "warning")
            return redirect(
                url_for("login", next=url_for("match_discussion", match_id=match_id))
            )

        comment_text = request.form.get("comment")
        if comment_text and len(comment_text) <= 280:
            new_comment = Comment(
                text=comment_text, user_id=current_user.id, match_id=match.id
            )
            db.session.add(new_comment)
            db.session.commit()
            flash("Your comment has been posted!", "success")
            return redirect(url_for("match_discussion", match_id=match.id))
        else:
            flash("Comment cannot be empty or exceed 280 characters.", "danger")

    comments = match.comments
    return render_template(
        "match_discussion.html",
        match=match,
        comments=sorted(comments, key=lambda c: c.timestamp),
        title=f"{match.home_team.name} vs {match.away_team.name} Discussion",
    )


@app.route("/team/<team_name>")
def team_page(team_name):
    # First try to get the team from the database
    team = Team.query.filter_by(name=team_name).first()

    if team:
        # If team exists in database, use its data for display
        team_details = {
            "name": team.name,
            "short_name": team.short_name,
            "logo_url": team.logo_url,
            "league": team.league,
            "played": team.played,
            "win": team.win,
            "draw": team.draw,
            "loss": team.loss,
            "points": team.points,
            "position": team.position,
            "form": team.form,
            "news": [
                {
                    "title": "New Player Signed!",
                    "summary": "The team announced the signing of a new striker today.",
                    "date": "May 12",
                },
                {
                    "title": "Captain Injured",
                    "summary": "The captain will be out for 3 weeks due to a knee injury.",
                    "date": "May 11",
                },
                {
                    "title": "Next Match Preview",
                    "summary": "An in-depth look at the upcoming clash.",
                    "date": "May 10",
                },
            ],
            "fans_count": 1250,
            "stadium": "The Great Stadium",
        }
    else:
        # If team doesn't exist in database, use fallback data
        team_details = {
            "name": team_name,
            "news": [
                {
                    "title": "New Player Signed!",
                    "summary": "The team announced the signing of a new striker today.",
                    "date": "May 12",
                },
                {
                    "title": "Captain Injured",
                    "summary": "The captain will be out for 3 weeks due to a knee injury.",
                    "date": "May 11",
                },
                {
                    "title": "Next Match Preview",
                    "summary": "An in-depth look at the upcoming clash.",
                    "date": "May 10",
                },
            ],
            "fans_count": 1250,
            "stadium": "The Great Stadium",
            "played": 0,
            "win": 0,
            "draw": 0,
            "loss": 0,
            "points": 0,
            "position": 0,
            "form": "",
        }

    return render_template(
        "team_page.html", team=team_details, title=f"{team_name} Team Page"
    )


# Add scheduled task handling
@app.route("/update-data-cron", methods=["GET"])
def update_data_cron():
    # Secure this endpoint with an API key
    api_key = request.args.get("key")
    if not api_key or api_key != os.getenv("CRON_API_KEY"):
        return jsonify({"error": "Unauthorized"}), 401

    team_update_msg = fetch_and_update_fpl_teams_standings()
    fixture_update_msg = fetch_and_update_fpl_fixtures()

    return jsonify(
        {"team_update": team_update_msg, "fixture_update": fixture_update_msg}
    )


# Add a simple health check endpoint for monitoring
@app.route("/health")
def health_check():
    try:
        # Try a simple database query to verify connectivity
        from sqlalchemy import text

        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


# Error handlers for better debugging
@app.errorhandler(404)
def page_not_found(e):
    return render_template(
        "error.html", error_code=404, error_message="Page not found"
    ), 404


@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Only populate data at startup in development mode
        if os.getenv("FLASK_ENV") != "production":
            print("Attempting to update FPL teams and standings at startup...")
            team_update_msg = fetch_and_update_fpl_teams_standings()
            print(team_update_msg)
            print("Attempting to update FPL fixtures at startup...")
            fixture_update_msg = fetch_and_update_fpl_fixtures()
            print(fixture_update_msg)

    # Run with debugging in development, securely in production
    if os.getenv("FLASK_ENV") == "production":
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
    else:
        app.run(debug=True)
