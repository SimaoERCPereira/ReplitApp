# TeamTalk

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables (see .env.example):
   - `SECRET_KEY`
   - `DATABASE_URL` (optional for local dev; defaults to SQLite)
   - `FLASK_ENV`
   - `CRON_API_KEY`
   - `REDIS_URL` (for caching)

   **Note:**
   - By default, the app uses SQLite at `instance/teamtalk.db` for local development.
   - To use Postgres or MySQL, set the `DATABASE_URL` environment variable accordingly.

3. Run the app:
   ```bash
   flask run
   ```

## Docker

1. Build the image:
   ```bash
   docker build -t teamtalk .
   ```
2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env teamtalk
   ```

## Heroku

1. Install the Heroku CLI and login.
2. Create a Heroku app:
   ```bash
   heroku create teamtalk-app
   ```
3. Add Postgres and Redis add-ons:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   heroku addons:create heroku-redis:hobby-dev
   ```
4. Deploy:
   ```bash
   git push heroku main
   ```

## Testing

Run tests with:
```bash
pytest
``` 