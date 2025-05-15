import streamlit as st
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables from .env file
load_dotenv()

# Set page config
st.set_page_config(
    page_title="The People's Pitch",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Database Configuration
# For Streamlit deployment, we'll use SQLite as the default database for simplicity
# You can switch to PostgreSQL by setting the DATABASE_URL environment variable

# Try to get database_url from Streamlit secrets first, then environment variable
try:
    database_url = st.secrets["connections"]["db"]["url"]
except (KeyError, FileNotFoundError):
    database_url = os.getenv("DATABASE_URL")

# Handle potential "postgres://" to "postgresql://" conversion (needed for some providers)
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Create the SQLAlchemy engine
if database_url:
    engine = create_engine(database_url)
else:
    # Use SQLite as fallback - works on Streamlit Cloud
    db_path = "instance/teamtalk.db"
    # Make sure the instance directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")

# Create a session factory
Session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()
Base.query = Session.query_property()


# Define models
class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    favorite_team = Column(String(100))
    bio = Column(Text)
    join_date = Column(DateTime, default=func.now())
    is_admin = Column(Boolean, default=False, nullable=False)
    comments = relationship("Comment", backref="author", lazy=True)


class Comment(Base):
    __tablename__ = "comment"
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    match_id = Column(Integer, nullable=False)


# Create tables if they don't exist
Base.metadata.create_all(engine)

# Initialize session state for user authentication
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "page" not in st.session_state:
    st.session_state.page = "home"


# Helper functions
def get_current_user():
    if st.session_state.user_id:
        session = Session()
        user = session.query(User).filter_by(id=st.session_state.user_id).first()
        session.close()
        return user
    return None


def check_database_connection():
    """Function to check database connection and display status"""
    try:
        session = Session()
        # Try to execute a simple query
        session.execute("SELECT 1")
        session.close()
        return True, "Connected to database successfully"
    except Exception as e:
        return False, f"Database connection error: {str(e)}"


def login_user(username, password):
    session = Session()
    user = session.query(User).filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        st.session_state.user_id = user.id
        st.session_state.username = user.username
        st.session_state.is_admin = user.is_admin
        session.close()
        return True
    session.close()
    return False


def register_user(username, email, password):
    session = Session()

    # Check if username or email already exists
    existing_user = (
        session.query(User)
        .filter((User.username == username) | (User.email == email))
        .first()
    )

    if existing_user:
        session.close()
        return False, "Username or email already exists."

    # Create new user
    new_user = User(
        username=username, email=email, password_hash=generate_password_hash(password)
    )

    session.add(new_user)
    try:
        session.commit()
        session.close()
        return True, "Registration successful. Please log in."
    except Exception as e:
        session.rollback()
        session.close()
        return False, f"An error occurred: {str(e)}"


# Sidebar for navigation
def sidebar():
    with st.sidebar:
        st.title("The People's Pitch")

        if st.session_state.user_id:
            st.write(f"Welcome, {st.session_state.username}!")
            if st.button("Logout"):
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.is_admin = False
                st.experimental_rerun()

        st.markdown("### Navigation")
        pages = {
            "Home": "home",
            "Standings": "standings",
            "Match Discussions": "match_discussions",
        }

        selected_page = None
        for page_name, page_id in pages.items():
            if st.button(page_name):
                st.session_state.page = page_id
                selected_page = page_id
                st.experimental_rerun()

        if not selected_page and "page" not in st.session_state:
            st.session_state.page = "home"

        if st.session_state.user_id:
            if st.button("My Profile"):
                st.session_state.page = "profile"
                st.experimental_rerun()

        # Admin section
        if st.session_state.is_admin:
            st.markdown("---")
            st.markdown("### Admin")
            if st.button("Admin Dashboard"):
                st.session_state.page = "admin"
                st.experimental_rerun()


# Login Page
def login_page():
    st.title("Login to The People's Pitch")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            if login_user(username, password):
                st.success("Login successful!")
                st.session_state.page = "home"
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

    with col2:
        st.subheader("Register")
        reg_username = st.text_input("Choose a Username", key="reg_username")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input(
            "Choose a Password", type="password", key="reg_password"
        )
        reg_confirm = st.text_input(
            "Confirm Password", type="password", key="reg_confirm"
        )

        if st.button("Register"):
            if reg_password != reg_confirm:
                st.error("Passwords do not match")
            else:
                success, message = register_user(reg_username, reg_email, reg_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)


# Home Page
def home_page():
    st.title("The People's Pitch - Premier League Fan Community")

    if not st.session_state.user_id:
        st.write("Please login or register to access all features.")
        if st.button("Go to Login"):
            st.session_state.page = "login"
            st.experimental_rerun()

    # Display some featured content
    st.header("Latest Matches")

    # Example data - in a real app, you would fetch this from an API
    matches_data = [
        {"home": "Arsenal", "away": "Chelsea", "date": "2023-05-15", "score": "2-1"},
        {"home": "Man City", "away": "Liverpool", "date": "2023-05-14", "score": "3-2"},
        {
            "home": "Tottenham",
            "away": "Man United",
            "date": "2023-05-13",
            "score": "1-1",
        },
    ]

    matches_df = pd.DataFrame(matches_data)
    st.table(matches_df)

    st.header("Featured Discussions")
    st.write("Join the conversation about recent matches!")


# Standings Page
def standings_page():
    st.title("Premier League Standings")

    # Example data - in a real app, you would fetch this from an API
    standings_data = [
        {"position": 1, "team": "Man City", "played": 36, "points": 89},
        {"position": 2, "team": "Arsenal", "played": 36, "points": 84},
        {"position": 3, "team": "Newcastle", "played": 36, "points": 69},
        {"position": 4, "team": "Man United", "played": 36, "points": 66},
    ]

    standings_df = pd.DataFrame(standings_data)
    st.table(standings_df)


# Match Discussions Page
def match_discussions_page():
    st.title("Match Discussions")

    if not st.session_state.user_id:
        st.warning("Please login to participate in discussions")
        if st.button("Go to Login"):
            st.session_state.page = "login"
            st.experimental_rerun()
        return

    # Example match data
    matches = [
        {"id": 1, "home": "Arsenal", "away": "Chelsea", "date": "2023-05-15"},
        {"id": 2, "home": "Man City", "away": "Liverpool", "date": "2023-05-14"},
        {"id": 3, "home": "Tottenham", "away": "Man United", "date": "2023-05-13"},
    ]

    # Select a match
    match_names = [f"{m['home']} vs {m['away']}" for m in matches]
    selected_match_name = st.selectbox("Select a match", match_names)

    # Find the selected match
    selected_index = match_names.index(selected_match_name)
    selected_match = matches[selected_index]

    st.subheader(
        f"{selected_match['home']} vs {selected_match['away']} - {selected_match['date']}"
    )

    # Display comments
    session = Session()
    comments = session.query(Comment).filter_by(match_id=selected_match["id"]).all()

    if comments:
        for comment in comments:
            user = session.query(User).filter_by(id=comment.user_id).first()
            st.text_area(
                f"{user.username} - {comment.timestamp}",
                comment.content,
                disabled=True,
                key=f"comment_{comment.id}",
            )
    else:
        st.info("No comments yet. Be the first to comment!")

    # Add a comment
    new_comment = st.text_area("Add your comment")
    if st.button("Post Comment"):
        if new_comment:
            comment = Comment(
                content=new_comment,
                user_id=st.session_state.user_id,
                match_id=selected_match["id"],
            )
            session.add(comment)
            session.commit()
            st.success("Comment posted!")
            st.experimental_rerun()

    session.close()


# Profile Page
def profile_page():
    st.title("My Profile")

    if not st.session_state.user_id:
        st.warning("Please login to view your profile")
        if st.button("Go to Login"):
            st.session_state.page = "login"
            st.experimental_rerun()
        return

    user = get_current_user()

    if user:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Profile Information")
            st.write(f"Username: {user.username}")
            st.write(f"Email: {user.email}")
            st.write(f"Joined: {user.join_date}")

            favorite_team = user.favorite_team or "Not set"
            st.write(f"Favorite Team: {favorite_team}")

        with col2:
            st.subheader("Update Profile")
            new_bio = st.text_area("Bio", value=user.bio or "")
            new_team = st.text_input("Favorite Team", value=user.favorite_team or "")

            if st.button("Update Profile"):
                session = Session()
                user_to_update = session.query(User).filter_by(id=user.id).first()
                user_to_update.bio = new_bio
                user_to_update.favorite_team = new_team
                session.commit()
                session.close()
                st.success("Profile updated successfully!")
                st.experimental_rerun()


# Admin Dashboard Page
def admin_dashboard():
    st.title("Admin Dashboard")

    if not st.session_state.user_id or not st.session_state.is_admin:
        st.warning("You need to be logged in as an admin to view this page")
        if st.button("Go to Login"):
            st.session_state.page = "login"
            st.experimental_rerun()
        return

    st.header("System Status")

    # Database connection check
    db_success, db_message = check_database_connection()
    if db_success:
        st.success(db_message)
    else:
        st.error(db_message)

    # User statistics
    st.header("User Statistics")
    session = Session()

    total_users = session.query(User).count()
    st.metric("Total Registered Users", total_users)

    total_comments = session.query(Comment).count()
    st.metric("Total Comments", total_comments)

    # Admin actions
    st.header("Admin Actions")

    # Create admin user
    st.subheader("Create Admin User")
    admin_username = st.text_input("Username", key="admin_user_username")
    admin_email = st.text_input("Email", key="admin_user_email")
    admin_password = st.text_input(
        "Password", type="password", key="admin_user_password"
    )

    if st.button("Create Admin"):
        if admin_username and admin_email and admin_password:
            # Check if user exists
            existing = (
                session.query(User)
                .filter((User.username == admin_username) | (User.email == admin_email))
                .first()
            )

            if existing:
                st.error("Username or email already exists")
            else:
                new_admin = User(
                    username=admin_username,
                    email=admin_email,
                    password_hash=generate_password_hash(admin_password),
                    is_admin=True,
                )
                session.add(new_admin)
                try:
                    session.commit()
                    st.success(f"Admin user {admin_username} created successfully")
                except Exception as e:
                    session.rollback()
                    st.error(f"Error creating admin user: {str(e)}")
        else:
            st.warning("Please fill in all fields")

    session.close()


# Main app logic
def main():
    sidebar()

    # Determine which page to show
    if not st.session_state.user_id and st.session_state.page not in ["home", "login"]:
        login_page()
    elif st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "standings":
        standings_page()
    elif st.session_state.page == "match_discussions":
        match_discussions_page()
    elif st.session_state.page == "profile":
        profile_page()
    elif st.session_state.page == "admin":
        admin_dashboard()
    elif st.session_state.page == "admin":
        admin_dashboard()


if __name__ == "__main__":
    main()
