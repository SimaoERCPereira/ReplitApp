from .extensions import db
from flask_login import UserMixin

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
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
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
    gameweek = db.Column(db.Integer, nullable=True)
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