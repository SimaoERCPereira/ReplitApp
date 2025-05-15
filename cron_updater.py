import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_data():
    """Fetch and update EPL teams and fixture data"""
    API_URL = os.getenv('APP_URL', 'http://localhost:5000')
    CRON_API_KEY = os.getenv('CRON_API_KEY')
    
    try:
        url = f"{API_URL}/update-data-cron?key={CRON_API_KEY}"
        print(f"Sending update request to: {url}")
        response = requests.get(url, timeout=300)  # 5 minute timeout
        
        if response.status_code == 200:
            data = response.json()
            print(f"Teams update: {data.get('team_update')}")
            print(f"Fixtures update: {data.get('fixture_update')}")
            print("Update completed successfully!")
            return True
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Error updating data: {e}")
        return False

if __name__ == "__main__":
    print("Starting EPL data update...")
    success = update_data()
    print("Update process finished.")
    # Exit with appropriate status code
    exit(0 if success else 1)
