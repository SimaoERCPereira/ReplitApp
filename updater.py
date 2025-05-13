import os
import time
import schedule
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_URL = os.getenv('APP_URL', 'http://localhost:5000')
CRON_API_KEY = os.getenv('CRON_API_KEY')

def update_data():
    """Fetch and update EPL teams and fixture data"""
    try:
        url = f"{API_URL}/update-data-cron?key={CRON_API_KEY}"
        response = requests.get(url, timeout=300)  # 5 minute timeout
        
        if response.status_code == 200:
            data = response.json()
            print(f"Teams update: {data.get('team_update')}")
            print(f"Fixtures update: {data.get('fixture_update')}")
            print(f"Data updated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error updating data: {e}")

# Schedule updates
# Update league standings every 3 hours
schedule.every(3).hours.do(update_data)

# Also update data when script is first run
update_data()

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute
