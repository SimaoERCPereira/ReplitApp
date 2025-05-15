# The People's Pitch - Premier League Football Fan Community

A responsive Flask web application for football fans to follow Premier League matches, view standings, and discuss matches with other supporters.

## Features

- User authentication (register, login, profile pages)
- Premier League match listings and schedule by gameweek
- Live match updates and discussions
- Team standings and statistics
- Team detail pages with news and information
- Auto-updating data from the Fantasy Premier League API
- Mobile-responsive design with dark mode support

## Local Development Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file (see `.env.example` for template)
4. Run the development server:
   ```
   python app.py
   ```

## Production Deployment Options

### Option 1: Railway (Recommended for easy setup)

1. Sign up for [Railway](https://railway.app/)
2. Connect your GitHub repository
3. Set environment variables in Railway:
   - `DATABASE_URL` (will be automatically set by Railway)
   - `SECRET_KEY`
   - `FLASK_ENV=production`
   - `CRON_API_KEY`
4. Add a PostgreSQL database from the Railway dashboard
5. Deploy app with the command: `gunicorn app_production:app`

### Option 2: Docker Deployment

1. Make sure Docker and Docker Compose are installed
2. Update `.env` file with your secure credentials
3. Build and start services:
   ```
   docker-compose up -d
   ```
4. Access the application at http://localhost:5000

### Option 3: Traditional VPS/Cloud Provider

1. Set up a server (Ubuntu recommended) with:
   - Python 3.8+
   - PostgreSQL
   - Nginx
2. Clone the repository
3. Set up a Python virtual environment
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Configure Nginx to proxy to Gunicorn
6. Set up systemd services for the app and updater
7. Start services:
   ```
   sudo systemctl start thepeoplepitch
   sudo systemctl start thepeoplepitch-updater
   ```

## Scheduled Tasks

The application includes an updater script that periodically refreshes data from the Fantasy Premier League API. This ensures that match results, fixtures, and team standings are always up-to-date.

## Security Notes

- Never commit your `.env` file with real credentials
- Change the default admin password immediately
- Use HTTPS in production environments
- Consider adding rate limiting for API endpoints

## License

MIT License
=======
# The-Peoples-Pitch
>>>>>>> 6d64619c40e857e0fb07d08cc38b70454284cc4a
