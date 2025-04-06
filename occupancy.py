import urllib.request
import re
import csv
from datetime import datetime
from datetime import timezone
from zoneinfo import ZoneInfo
import os

def get_occupancy():
    try:
        # Get the webpage content
        url = "https://www.kravihora-brno.cz/kryta-plavecka-hala"
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        
        # Find occupancy using regex
        pattern = r'<p>obsazenost:<strong>\s*(\d+)\s*/\s*\d+</strong></p>'
        match = re.search(pattern, html)
        
        if match:
            return int(match.group(1))
        return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def save_to_csv(occupancy):
    # Get current UTC time
    now = datetime.now(timezone.utc)
    prague_time = now.astimezone(ZoneInfo("Europe/Prague"))
    
    # Format the time in Prague timezone
    date_str = prague_time.strftime('%d.%m.%Y')
    day_of_week = now.strftime('%A')
    time_str = prague_time.strftime('%H:%M')
    
    # Ensure we're using the correct path in GitHub Actions
    csv_path = 'data/pool_occupancy.csv'
    os.makedirs('data', exist_ok=True)
    
    # Check if file exists and create with headers if needed
    if not os.path.exists(csv_path):
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Day', 'Time', 'Occupancy'])
    
    try:
        with open(csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date_str, day_of_week, time_str, occupancy])
        print(f"Recorded: {day_of_week} {time_str} - {occupancy}")
        return True
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False

def main():
    occupancy = get_occupancy()
    if occupancy is not None:
        return save_to_csv(occupancy)
    return False

if __name__ == "__main__":
    main()