import urllib.request
import re
import csv
from datetime import datetime
from datetime import timezone
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
import os

WEEKEND_OPENING_HOUR = 8
WEEKEND_CLOSING_HOUR = 21

POOL_SOURCES = [
    {
        'name': 'Kraví Hora Krytá hala',
        'url': 'https://www.kravihora-brno.cz/kryta-plavecka-hala',
        'pattern': r'obsazenost:\s*(\d+)\s*/',
        'csv_file': 'pool_occupancy.csv'
    },
    {
        'name': 'Kraví Hora Venkovní bazény',
        'url': 'https://www.kravihora-brno.cz/venkovni-bazeny',
        'pattern': r'obsazenost:\s*(\d+)',
        'csv_file': 'outside_pool_occupancy.csv'
    },
    {
        'name': 'Koupaliště Dobrák',
        'url': 'https://www.koupalistebrno.cz/',
        'pattern': r'(\d+)\s*počet\s*návštěvníků',
        'csv_file': 'koupaliste_dobrak_occupancy.csv'
    },
    {
        'name': 'Koupaliště Riviéra',
        'url': 'https://riviera.starez.cz/',
        'pattern': r'návštěvnost\s*(\d+)\s*/',
        'csv_file': 'koupaliste_riviera_occupancy.csv'
    },
    {
        'name': 'Koupaliště Zábrdovice',
        'url': 'https://zabrdovice.starez.cz/',
        'pattern': r'návštěvnost\s*(\d+)\s*/',
        'csv_file': 'koupaliste_zabrdovice_occupancy.csv'
    },
    {
        'name': 'Aquapark Kohoutovice',
        'url': 'https://aquapark.starez.cz/',
        'pattern': r'bazény a posilovna\s*(\d+)\s*/',
        'csv_file': 'aquapark_kohoutovice_occupancy.csv'
    },
    {
        'name': 'Bazény Lužánky',
        'url': 'https://bazenyluzanky.starez.cz/',
        'pattern': r'bazény\s*(\d+)\s*/',
        'csv_file': 'bazeny_luzanky_occupancy.csv'
    }
]


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
    # Get current UTC time
    now = datetime.now(timezone.utc)
    prague_time = now.astimezone(ZoneInfo("Europe/Prague"))
    
    # Do not record occupancy outside weekend operating hours
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
        print(f"Recorded occupancy for '{pool_name}': {date_str} {day_of_week} {time_str} - {occupancy}")
        return True
    except Exception as e:
        print(f"Error saving to CSV for {pool_name}: {e}")
        return False


def main():
    """Main function to process all pool sources."""
    overall_success = True
    
    for pool_config in POOL_SOURCES:
        occupancy = fetch_occupancy(pool_config['url'], pool_config['pattern'])
        
        if occupancy is not None:
            success = save_to_csv(occupancy, pool_config['csv_file'], pool_config['name'])
            overall_success &= success
        else:
            print(f"Failed to get occupancy data for {pool_config['name']}")
            overall_success = False
    
    return overall_success


if __name__ == "__main__":
    main()