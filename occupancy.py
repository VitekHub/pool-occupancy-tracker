import urllib.request
import re
import csv
import json
from datetime import datetime
from datetime import timezone
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
import os

def load_pool_config():
    """Load pool configuration from JSON file."""
    try:
        with open('data/pool_occupancy_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading pool configuration: {e}")
        return []


def fetch_html(url):
    """Fetch HTML content from a given URL."""
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response = urllib.request.urlopen(req)
        return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching HTML from {url}: {e}")
        return None

def is_pool_open(pool_type_config):
    def get_opening_hours(hours):
        opening_hour = int(hours.split("-")[0].strip())
        closing_hour = int(hours.split("-")[1].strip())
        return opening_hour, closing_hour

    now = datetime.now(ZoneInfo("Europe/Prague"))
    is_weekend = now.strftime('%A') in ['Saturday', 'Sunday']
    hour = int(now.strftime('%H'))

    if is_weekend:
        hours = pool_type_config['weekendOpeningHours']
    else:
        hours = pool_type_config['weekdaysOpeningHours']

    opening_hour, closing_hour = get_opening_hours(hours)

    # Check if the current hour is within the opening hours
    return opening_hour <= hour < closing_hour

def fetch_occupancy(url, pattern):
    """Fetch occupancy data from a URL using the given regex pattern."""
    html_content = fetch_html(url)
    if html_content:
        text_content = BeautifulSoup(html_content, 'html.parser').get_text()
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def save_to_csv(occupancy, file_name, pool_name):
    """Save occupancy data to CSV file."""
    # Get current Prague time
    now = datetime.now(ZoneInfo("Europe/Prague"))
    
    # Format the time in Prague timezone
    date_str = now.strftime('%d.%m.%Y')
    day_of_week = now.strftime('%A')
    time_str = now.strftime('%H:%M')
    
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
        print(f"Recorded occupancy for '{pool_name}': {date_str} {day_of_week} {time_str} - {occupancy}")
        return True
    except Exception as e:
        print(f"Error saving to CSV for {pool_name}: {e}")
        return False


def process_pool_type(pool_config, pool_type_key, pool_name):
    """Process a specific pool type (insidePool or outsidePool) for a given pool."""
    pool_type_config = pool_config.get(pool_type_key)
    if not pool_type_config:
        return True  # Skip if this pool type doesn't exist for this pool
    
    # Check if we should collect stats for this pool
    if not pool_type_config.get('collectStats', False):
        print(f"Skipping {pool_name} {pool_type_key} - collectStats is false")
        return True
    
    if not is_pool_open(pool_type_config):
        print(f"{pool_name} {pool_type_key} is closed, skipping occupancy check")
        return True
    
    url = pool_type_config['url']
    pattern = pool_type_config['pattern']
    csv_file = pool_type_config['csvFile']
    
    occupancy = fetch_occupancy(url, pattern)
    
    if occupancy is not None:
        pool_type_name = f"{pool_name} ({'Inside' if pool_type_key == 'insidePool' else 'Outside'} Pool)"
        return save_to_csv(occupancy, csv_file, pool_type_name)
    else:
        print(f"Failed to get occupancy data for {pool_name} {pool_type_key}")
        return False


def main():
    """Main function to process all pool sources."""
    pool_configs = load_pool_config()
    if not pool_configs:
        print("No pool configurations loaded")
        return False
    
    overall_success = True
    
    for pool_config in pool_configs:
        pool_name = pool_config['name']
        
        # Process inside pool if it exists
        success_inside = process_pool_type(pool_config, 'insidePool', pool_name)
        overall_success &= success_inside
        
        # Process outside pool if it exists
        success_outside = process_pool_type(pool_config, 'outsidePool', pool_name)
        overall_success &= success_outside
    
    return overall_success


if __name__ == "__main__":
    main()