# The People's Pitch - Streamlit App

This is a Streamlit version of the original Flask web application for Premier League football fans to follow matches, view standings, and discuss matches with other supporters.

## Features

- User authentication (register, login, profile pages)
- Premier League match listings
- Match discussions
- Team standings
- Mobile-responsive design with dark mode support

## Running the app locally

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Create a `.env` file (optional, for environment variables)
3. Run the Streamlit app:
   ```
   streamlit run streamlit_app.py
   ```

## Streamlit Cloud Deployment

The app is already configured to work with Streamlit Cloud. It uses SQLite as the default database for simplicity, but you can configure it to use PostgreSQL by setting the `DATABASE_URL` environment variable in your Streamlit Cloud settings.

### How to deploy on Streamlit Cloud:

1. Make sure your GitHub repository is public or that you've connected Streamlit Cloud to your private repository
2. In Streamlit Cloud, create a new app and point it to:
   - Repository: Your GitHub repository URL
   - Branch: main (or your preferred branch)
   - Main file path: streamlit_app.py
3. (Optional) Configure environment variables:
   - Set `DATABASE_URL` if you want to use a custom database
   - Set `SECRET_KEY` for added security

## Database Configuration

The app automatically uses SQLite for local development and testing. For production, you can configure a PostgreSQL database by setting the `DATABASE_URL` environment variable.

Supported database URL formats:
- PostgreSQL: `postgresql://username:password@hostname/database`
- SQLite (default): Uses the local file at `instance/teamtalk.db`

## Notes for Streamlit Deployment

- The app has been redesigned to work with Streamlit's stateful components
- Session management is handled via Streamlit's session state
- The database is managed directly with SQLAlchemy (without Flask-SQLAlchemy)
- The UI has been adapted to Streamlit's component system

## Credits

Original Flask application: The People's Pitch
Streamlit conversion: [Your Name]
