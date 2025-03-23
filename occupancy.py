import urllib.request
import re
import csv
import time
from datetime import datetime

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
    now = datetime.now()
    day_of_week = now.strftime('%A')
    time_str = now.strftime('%H:%M')
    
    try:
        with open('pool_occupancy.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([day_of_week, time_str, occupancy])
        print(f"Recorded: {day_of_week} {time_str} - {occupancy}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def main():
    # Create CSV file with headers if it doesn't exist
    try:
        with open('pool_occupancy.csv', 'x', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Day', 'Time', 'Occupancy'])
    except FileExistsError:
        pass

    occupancy = get_occupancy()
    if occupancy is not None:
        save_to_csv(occupancy)

if __name__ == "__main__":
    main()