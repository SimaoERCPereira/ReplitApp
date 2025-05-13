# The People's Pitch - Application Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [Application Architecture](#application-architecture)
3. [Data Model](#data-model)
4. [Application Flow](#application-flow)
5. [External Services](#external-services)
6. [Deployment Architecture](#deployment-architecture)
7. [Security Considerations](#security-considerations)
8. [Scalability Considerations](#scalability-considerations)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)
10. [Future Enhancements](#future-enhancements)

---

## Overview

The People's Pitch is a Flask-based web application that provides Premier League football fans with a platform to view match schedules, team standings, and discuss matches with other fans. The application integrates with the Fantasy Premier League (FPL) API to automatically update match data and team standings.

### Core Features
- User registration and authentication
- Premier League match listings and schedules by gameweek
- Live match discussions
- Team standings and statistics
- Team detail pages
- Automatic data updates from FPL API
- Responsive design with dark mode support

---

## Application Architecture

The People's Pitch follows a Model-View-Controller (MVC) architecture pattern:

### Technology Stack
- **Frontend**: HTML, CSS, JavaScript
  - Template Engine: Jinja2
  - CSS Framework: Custom CSS with responsive design
  - JavaScript Libraries: Chart.js for data visualization
  
- **Backend**: Python 3.8+ with Flask 2.3.3
  - Flask: Web framework
  - Flask-SQLAlchemy: ORM for database interactions
  - Flask-Login: User authentication management
  
- **Database**: 
  - Development: SQL Server (via pyodbc)
  - Production: PostgreSQL
  
- **External API Integration**:
  - Fantasy Premier League (FPL) API

### Component Diagram

```
┌─────────────────┐       ┌──────────────────┐       ┌────────────────┐
│                 │       │                  │       │                │
│  Web Browser    │◄─────►│  Flask           │◄─────►│  Database      │
│  (Client)       │       │  Application     │       │  (SQL/Postgres)│
│                 │       │                  │       │                │
└─────────────────┘       └──────────┬───────┘       └────────────────┘
                                     │
                                     │
                                     ▼
                          ┌──────────────────┐
                          │                  │
                          │  FPL API         │
                          │  (External)      │
                          │                  │
                          └──────────────────┘
```

### Directory Structure

```
ThePeoplesPitch/
├── app.py                 # Main application file (development)
├── app_production.py      # Production-ready application file
├── updater.py             # Data update service
├── requirements.txt       # Python dependencies
├── Procfile               # For PaaS deployments
├── .env / .env.example    # Environment variables
├── Dockerfile             # Main application container
├── Dockerfile.updater     # Data updater container
├── docker-compose.yml     # Docker services orchestration
├── static/                # Static assets
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript files
│   └── img/               # Images
└── templates/             # Jinja2 HTML templates
    ├── base.html          # Base template with common elements
    ├── index.html         # Home page
    ├── standings.html     # Team standings page
    ├── match_discussion.html # Match discussion page
    ├── team_page.html     # Team detail page
    ├── login.html         # Login page
    ├── register.html      # Registration page
    └── profile.html       # User profile page
```

---

## Data Model

The application uses SQLAlchemy ORM with four primary models:

### User Model

```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    favorite_team = db.Column(db.String(100))
    bio = db.Column(db.Text)
    join_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    comments = db.relationship('Comment', backref='author', lazy=True)
```

### Team Model

```python
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    short_name = db.Column(db.String(10), unique=True, nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    league = db.Column(db.String(100), nullable=True, default='Premier League')
    fpl_id = db.Column(db.Integer, unique=True, nullable=True)
    fpl_team_code = db.Column(db.Integer, nullable=True)
    played = db.Column(db.Integer, default=0)
    win = db.Column(db.Integer, default=0)
    draw = db.Column(db.Integer, default=0)
    loss = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)
    position = db.Column(db.Integer, default=0)
    form = db.Column(db.String(50), nullable=True)
    home_matches = db.relationship('Match', foreign_keys='Match.team1_id', backref='home_team', lazy=True)
    away_matches = db.relationship('Match', foreign_keys='Match.team2_id', backref='away_team', lazy=True)
```

### Match Model

```python
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team1_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team2_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    match_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    status = db.Column(db.String(50), nullable=False, default='Upcoming')
    score_team1 = db.Column(db.Integer)
    score_team2 = db.Column(db.Integer)
    fpl_fixture_id = db.Column(db.Integer, unique=True, nullable=True)
    gameweek = db.Column(db.Integer, nullable=True)
    comments = db.relationship('Comment', backref='match', lazy=True)
```

### Comment Model

```python
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(280), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
```

### Entity Relationship Diagram (ERD)

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   User      │       │   Match     │       │   Team      │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │       │ id          │       │ id          │
│ username    │       │ team1_id ───┼───────► id          │
│ email       │       │ team2_id ───┼───────► id          │
│ password    │       │ match_date  │       │ name        │
│ favorite_team│       │ status      │       │ short_name  │
│ bio         │       │ score_team1 │       │ logo_url    │
│ join_date   │       │ score_team2 │       │ league      │
│ is_admin    │       │ fpl_fixture_│       │ fpl_id      │
└──────┬──────┘       │ gameweek    │       │ fpl_team_code│
       │              └──────┬──────┘       │ played      │
       │                     │              │ win         │
       │                     │              │ draw        │
       │                     │              │ loss        │
       │                     │              │ points      │
       │                     │              │ position    │
       │                     │              │ form        │
       ▼                     ▼              └─────────────┘
┌─────────────┐
│  Comment    │
├─────────────┤
│ id          │
│ text        │
│ timestamp   │
│ user_id     │
│ match_id    │
└─────────────┘
```

---

## Application Flow

### Authentication Flow

1. User visits login or registration page
2. For registration:
   - User enters username, email, password, and optional favorite team
   - System validates input and checks for duplicate username/email
   - If valid, creates user with hashed password and redirects to login
3. For login:
   - User enters email and password
   - System validates credentials
   - If valid, creates a session and redirects to home page
4. Authenticated users can:
   - Post comments on match discussions
   - View their profile
   - Update their profile information
   - Log out to end their session

### Match Listing Flow

1. User visits the home page
2. System retrieves matches from the database, grouped by gameweek
3. System determines the current or next gameweek to display by default
4. User can select a specific gameweek to view matches
5. For each match, the system displays:
   - Home and away teams with logos
   - Match date and time
   - Match status (Upcoming, Live, Finished)
   - Scores for finished or live matches

### Match Discussion Flow

1. User clicks on a match to view discussion
2. System retrieves match details and comments from database
3. Comments are displayed chronologically
4. Authenticated users can add comments to the discussion
5. Comments are limited to 280 characters

### Team Page Flow

1. User clicks on a team name or logo
2. System retrieves team details from database
3. System displays:
   - Team information
   - Current form and statistics
   - Recent news (currently mock data)
   - Fan polls (currently mock data)

### Data Update Flow

1. Scheduled task or admin-triggered update starts
2. System fetches latest data from FPL API
3. For team standings:
   - Retrieves team information and statistics
   - Updates existing teams or creates new ones
4. For fixtures:
   - Retrieves match schedules, scores, and statuses
   - Updates existing matches or creates new ones
5. System confirms update completion and logs results

---

## External Services

### Fantasy Premier League (FPL) API

The application integrates with the FPL API to retrieve team and match data:

- **Bootstrap Static Endpoint**: `/bootstrap-static/`
  - Provides team information and standings
  - Used to populate and update the Team model

- **Fixtures Endpoint**: `/fixtures/`
  - Provides fixture/match information
  - Used to populate and update the Match model

### Integration Implementation

The application includes two key data fetching functions:

1. `fetch_and_update_fpl_teams_standings()`: Updates team information and standings
2. `fetch_and_update_fpl_fixtures()`: Updates fixture/match information

These functions are called:
- On application startup in development mode
- Via scheduled tasks in production
- Manually by admin users via the web interface

---

## Deployment Architecture

The application is designed for flexible deployment across multiple environments. Three primary deployment options are supported:

### 1. Platform as a Service (PaaS) - Railway

```
┌───────────────┐      ┌──────────────┐      ┌─────────────┐
│               │      │              │      │             │
│  Railway      │      │  Flask App   │      │  PostgreSQL │
│  Platform     │──────►  Container   │◄─────►  Database   │
│               │      │              │      │             │
└───────────────┘      └──────┬───────┘      └─────────────┘
                              │
                              │
                              ▼
                      ┌──────────────┐
                      │              │
                      │  FPL API     │
                      │  (External)  │
                      │              │
                      └──────────────┘
```

- **Benefits**: Simple deployment, minimal configuration, automatic scaling
- **Components**: 
  - Web service running `app_production.py`
  - PostgreSQL database
  - Scheduled tasks for data updates

### 2. Docker Deployment

```
┌────────────────────────────────────────────────────────┐
│ Docker Host                                            │
│                                                        │
│  ┌─────────────┐     ┌─────────────┐    ┌────────────┐ │
│  │             │     │             │    │            │ │
│  │  Flask App  │◄───►│  PostgreSQL │    │  Updater   │ │
│  │  Container  │     │  Container  │    │  Container │ │
│  │             │     │             │    │            │ │
│  └─────┬───────┘     └─────────────┘    └────────────┘ │
│        │                                                │
└────────┼────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│                 │
│  FPL API        │
│  (External)     │
│                 │
└─────────────────┘
```

- **Benefits**: Consistent environment, easy horizontal scaling, portability
- **Components**:
  - Web service container running `app_production.py` with Gunicorn
  - PostgreSQL database container
  - Updater service container for scheduled data updates
  - Docker Compose for orchestration

### 3. Traditional VPS Deployment

```
┌────────────────────────────────────────────────────────────┐
│ VPS Host                                                   │
│                                                            │
│  ┌──────────┐    ┌───────────┐    ┌────────────────────┐   │
│  │          │    │           │    │                    │   │
│  │  Nginx   │───►│  Gunicorn │───►│  Flask Application │   │
│  │          │    │           │    │                    │   │
│  └──────────┘    └───────────┘    └─────────┬──────────┘   │
│                                             │              │
│                                             │              │
│  ┌──────────────┐                           │              │
│  │              │                           │              │
│  │  PostgreSQL  │◄──────────────────────────┘              │
│  │  Database    │                                          │
│  │              │                                          │
│  └──────────────┘                                          │
│                                                            │
│  ┌──────────────┐                                          │
│  │              │                                          │
│  │  Updater     │                                          │
│  │  Service     │                                          │
│  │              │                                          │
│  └──────────────┘                                          │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

- **Benefits**: Full control, cost-effective, customizable
- **Components**:
  - Nginx as reverse proxy and static file server
  - Gunicorn as WSGI server
  - Flask application running `app_production.py`
  - PostgreSQL database
  - Systemd service for the updater script

---

## Security Considerations

### Authentication Security

- Password hashing with Werkzeug's `generate_password_hash` and `check_password_hash`
- Session management with Flask-Login
- CSRF protection via Flask's built-in mechanisms
- Secure user registration with validation checks

### Data Security

- Environment variables for sensitive configuration
- Database connection string protection
- Input validation for user-submitted content
- SQL injection protection through ORM

### Production Hardening

- Debug mode disabled in production
- Error logging configuration
- HTTPS enforcement (in production)
- Rate limiting for API endpoints (recommended)

### API Security

- Admin-only access to data update endpoint
- API key verification for scheduled task endpoints

---

## Scalability Considerations

The application is designed with scalability in mind, particularly in its production configuration:

### Current Scalability Features

- **Database Abstraction**: ORM allows switching between database engines
- **Stateless Application**: Enables horizontal scaling behind load balancers
- **Environment Configuration**: Supports different configurations for development/production
- **Production WSGI Server**: Gunicorn supports multi-worker processes

### Future Scalability Enhancements

- **Database Connection Pooling**: For handling higher user loads
- **Caching Layer**: Redis or Memcached for frequently accessed data
- **Read Replicas**: For database read scaling
- **CDN Integration**: For static assets
- **API Rate Limiting**: To prevent abuse
- **Load Balancing**: Multiple application instances behind a load balancer

---

## Monitoring and Maintenance

### Health Checks

The production version includes a `/health` endpoint that:
- Verifies database connectivity
- Reports application status
- Can be used by container orchestration or monitoring tools

### Update Mechanism

Team and fixture data are kept current through:
1. The updater script that runs on a schedule
2. Admin-triggered manual updates through the web interface
3. Automatic updates on application startup (in development)

### Logging

- Development: Verbose logging with debug information
- Production: Reduced logging with focus on important events
- Error tracking for exception handling

---

## Future Enhancements

Potential future improvements to the application architecture:

1. **User Engagement Features**:
   - User notifications for matches
   - Social sharing integration
   - Enhanced profile customization

2. **Technical Enhancements**:
   - Implement WebSockets for real-time updates
   - Add a message queue for better job processing
   - Implement a proper caching layer
   - Add full-text search functionality

3. **Content Enhancements**:
   - Player statistics integration
   - News feed integration from reliable sources
   - Historical data and statistics
   - Performance analytics

4. **Administration**:
   - Admin dashboard for user management
   - Content moderation tools
   - Analytics and reporting

---

*Document prepared on May 13, 2025*

*For inquiries or further documentation, please contact the development team.*
