import urllib.request
import csv
from datetime import datetime, timedelta
import os
import re
from bs4 import BeautifulSoup

def get_capacity_data(date_str):
    """Fetch capacity data for a given date."""
    try:
        url = f"https://www.kravihora-brno.cz/kryta-plavecka-hala/rozpis?from={date_str}"
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        
        # Use BeautifulSoup to parse the HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all tables - each table represents a day
        tables = soup.find_all('table')
        
        results = []
        
        # Dictionary to translate Czech day names to English
        day_translations = {
            'Pondělí': 'Monday',
            'Úterý': 'Tuesday',
            'Středa': 'Wednesday',
            'Čtvrtek': 'Thursday',
            'Pátek': 'Friday',
            'Sobota': 'Saturday',
            'Neděle': 'Sunday'
        }
        
        for table_idx, table in enumerate(tables):
            # Extract date from caption
            caption = table.find('caption')
            if not caption:
                continue
            
            caption_text = caption.get_text().strip()
            date_match = re.search(r'(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})', caption_text)
            
            if not date_match:
                continue
            
            day, month, year = date_match.groups()
            # Format day and month with leading zeros
            formatted_date = f"{int(day):02d}.{int(month):02d}.{year}"
            
            # Extract day of week
            day_match = re.search(r'–\s*(\w+)', caption_text)
            czech_day = day_match.group(1) if day_match else ""
            
            # Translate day name to English
            day_of_week = day_translations.get(czech_day, czech_day)
            
            # Get all rows for lanes 1-6 (skip header and other equipment rows)
            rows = table.find_all('tr')
            if len(rows) < 7:  # Make sure we have at least 7 rows (header + 6 lanes)
                continue
                
            header_row = rows[0]  # Header row with times
            lane_rows = rows[1:7]  # Only lanes 1-6
            
            # Process each hour from 6:00 to 21:00
            for hour in range(6, 22):
                hour_str = f"{hour:02d}"
                
                # Skip certain hours on weekends
                if day_of_week in ['Saturday', 'Sunday'] and hour in [6, 7, 21]:
                    continue
                
                time = f"{hour_str}:00:00"
                
                # Find cells for this hour across all lanes
                available_lanes = 0
                
                for lane_row in lane_rows:
                    # Get all cells in this row (skip the lane label cell)
                    cells = lane_row.find_all('td')[1:]
                    
                    # Find cells for this hour
                    hour_cell = None
                    next_cell = None
                    
                    for i, cell in enumerate(cells):
                        class_names = cell.get('class', [])
                        hour_class = next((c for c in class_names if c.startswith(f'col-{hour_str}-')), None)
                        
                        if hour_class:
                            hour_cell = cell
                            # If we're not at the last cell, get the next cell for half-hour check
                            if i + 1 < len(cells):
                                next_cell = cells[i + 1]
                            break
                    
                    if hour_cell:
                        # Check if the lane is available for this hour
                        is_available = False
                        
                        # Case 1: Full hour reservation (colspan="2")
                        if 'colspan' in hour_cell.attrs and hour_cell['colspan'] == '2':
                            is_available = 'reserved' not in hour_cell.get('class', [])
                        # Case 2: Two half-hour slots
                        elif next_cell:
                            # Both half-hour slots must be unreserved
                            is_available = ('reserved' not in hour_cell.get('class', []) and 
                                           'reserved' not in next_cell.get('class', []))
                        
                        if is_available:
                            available_lanes += 1
                
                # Calculate maximum occupancy (135 people total capacity divided by 6 lanes)
                max_occupancy = (available_lanes * 135) // 6
                
                results.append([formatted_date, day_of_week, time, max_occupancy])
        
        # Sort results by date and time
        def sort_key(x):
            # Parse date from DD.MM.YYYY format
            day, month, year = map(int, x[0].split('.'))
            # Parse time from HH:MM:SS format
            hour = int(x[2].split(':')[0])
            return datetime(year, month, day, hour)
            
        results.sort(key=sort_key)
        
        return results
        
    except Exception as e:
        print(f"Error fetching data for {date_str}: {e}")
        return []

def write_csv_headers(file):
    """Write headers to a CSV file."""
    writer = csv.writer(file)
    writer.writerow(['Date', 'Day', 'Hour', 'Maximum Occupancy'])

def write_csv_data(file, data):
    """Write data rows to a CSV file."""
    writer = csv.writer(file)
    for row in data:
        writer.writerow(row)

def save_csv_data(data, filename, *, append=False):
    """Save capacity data to a CSV file.
    
    Args:
        data: List of rows to save
        filename: Name of the file (without path)
        append: If True, append to existing file; if False, overwrite
    """
    """Ensure the data directory exists."""
    os.makedirs('data', exist_ok=True)
    csv_path = f'data/{filename}'
    mode = 'a' if append else 'w'
    
    try:
        # Handle append mode with new file
        if append and not os.path.exists(csv_path):
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                write_csv_headers(f)
        
        # Write or append data
        with open(csv_path, mode, newline='', encoding='utf-8') as f:
            if not append:  # Write headers for new files
                write_csv_headers(f)
            write_csv_data(f, data)
        return True
    except Exception as e:
        print(f"Error saving data to {filename}: {e}")
        return False

def save_capacity_to_csv(data):
    """Save capacity data to CSV file."""
    return save_csv_data(data, 'capacity.csv', append=True)

def save_week_capacity_to_csv(data):
    """Save weekly capacity data to CSV file."""
    return save_csv_data(data, 'week_capacity.csv', append=False)

def main():
    # Get data for today
    start_date = datetime.now()
    
    # Calculate Monday of the current week
    days_since_monday = start_date.weekday()  # Monday is 0, Sunday is 6
    monday = start_date - timedelta(days=days_since_monday)
    monday_str = monday.strftime('%Y-%m-%d')
    today_str = start_date.strftime('%d.%m.%Y')

    print(f"Fetching data for {monday_str}")
    data = get_capacity_data(monday_str)
    
    if data:
        # Save full week data
        save_week_capacity_to_csv(data)
        print(f"Saved weekly data starting from {monday_str}")
        
        # Filter and save today's data
        today_data = [row for row in data if row[0] == today_str]
        if today_data:
            save_capacity_to_csv(today_data)
            print(f"Saved today's data for {today_str}")
        else:
            print(f"No data available for today ({today_str})")
    else:
        print(f"No data available for the week of {monday_str}")

if __name__ == "__main__":
    main()
