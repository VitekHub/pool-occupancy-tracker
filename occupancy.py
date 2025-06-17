import urllib.request
import re
import csv
from datetime import datetime
from datetime import timezone
from zoneinfo import ZoneInfo
import os

WEEKEND_OPENING_HOUR = 8
WEEKEND_CLOSING_HOUR = 21

def fetch_occupancy(url, pattern):
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def get_inside_occupancy():
    url = "https://www.kravihora-brno.cz/kryta-plavecka-hala"
    pattern = r'<p>obsazenost:<strong>\s*(\d+)\s*/\s*\d+</strong></p>'
    return fetch_occupancy(url, pattern)

def get_outside_occupancy():
    url = "https://www.kravihora-brno.cz/venkovni-bazeny"
    pattern = r'<p>Obsazenost:\s*<strong>(\d+)<\/strong><\/p>'
    return fetch_occupancy(url, pattern)

def save_to_csv(occupancy, file_name):
    # Get current UTC time
    now = datetime.now(timezone.utc)
    prague_time = now.astimezone(ZoneInfo("Europe/Prague"))
    
    # Do not record Occupancy outside weekend operating hours
    is_weekend = prague_time.strftime('%A') in ['Saturday', 'Sunday']
    hour = int(prague_time.strftime('%H'))
    if is_weekend and (hour < WEEKEND_OPENING_HOUR or hour >= WEEKEND_CLOSING_HOUR) and occupancy > 0:
        occupancy = 0
    
    # Format the time in Prague timezone
    date_str = prague_time.strftime('%d.%m.%Y')
    day_of_week = now.strftime('%A')
    time_str = prague_time.strftime('%H:%M')
    
    # Ensure we're using the correct path in GitHub Actions
    csv_path = f'data/{file_name}'
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
    inside_occupancy = get_inside_occupancy()
    outside_occupancy = get_outside_occupancy()
    success = True

    if inside_occupancy is not None:
        success &= save_to_csv(inside_occupancy, 'pool_occupancy.csv')
    else:
        success = False

    if outside_occupancy is not None:
        success &= save_to_csv(outside_occupancy, 'outside_pool_occupancy.csv')
    else:
        success = False

    return success

if __name__ == "__main__":
    main()
