# Pool Occupancy and Capacity Tracker

A comprehensive Python-based system that tracks and records both occupancy and capacity data for the Kraví Hora swimming pool complex in Brno. The system automatically collects data using GitHub Actions and provides insights into pool usage patterns.

## Features

### Occupancy Tracking (`occupancy.py`)
- **Indoor Pool**: Tracks real-time occupancy from the covered swimming hall
- **Outdoor Pool**: Tracks real-time occupancy from the outdoor pools (seasonal)
- **Automated Collection**: Runs every 10 minutes during operating hours (6:00-21:59 Prague time)
- **Weekend Hours Handling**: Automatically sets occupancy to 0 outside weekend operating hours (8:00-20:59)
- **Timezone Aware**: Handles Prague timezone including daylight saving time transitions

### Capacity Analysis (`capacity.py`)
- **Lane Availability**: Analyzes swimming lane reservations to calculate maximum theoretical occupancy
- **Weekly Schedule**: Fetches and processes the complete weekly schedule
- **Reservation Parsing**: Identifies reserved, closed, and available time slots
- **Capacity Calculation**: Calculates maximum occupancy based on available lanes (135 people total capacity ÷ 6 lanes)
- **Daily Updates**: Runs once daily at 4:00 Prague time to capture the latest schedule

## How It Works

### Data Collection Process

1. **Occupancy Data**: 
   - Fetches current occupancy from both indoor and outdoor pool websites
   - Records data every 10 minutes during operating hours

2. **Capacity Data**:
   - Scrapes the weekly reservation schedule
   - Generates both daily and weekly capacity reports

### Automation
- **GitHub Actions**: Fully automated using scheduled workflows
- **Git Integration**: Automatically commits and pushes data updates

## Project Structure

```
.
├── .github/workflows/
│   └── schedule.yml           # GitHub Actions workflow configuration
├── data/
│   ├── pool_occupancy.csv     # Indoor pool occupancy data
│   ├── outside_pool_occupancy.csv  # Outdoor pool occupancy data
│   ├── capacity.csv           # Daily capacity data
│   └── week_capacity.csv      # Weekly capacity data
├── occupancy.py               # Real-time occupancy tracking script
├── capacity.py                # Capacity analysis script
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Schedule

### Occupancy Tracking
- **Frequency**: Every 10 minutes
- **Hours**: 6:00-21:59 Prague time (4:00-19:59 UTC)

### Capacity Tracking
- **Frequency**: Once daily
- **Time**: 4:00 Prague time (2:00 UTC)

## Data Formats

### Occupancy Data (`pool_occupancy.csv`, `outside_pool_occupancy.csv`)
- **Date**: DD.MM.YYYY format
- **Day**: Day of the week
- **Time**: HH:MM format (Prague timezone)
- **Occupancy**: Current number of people in the pool

### Capacity Data (`capacity.csv`, `week_capacity.csv`)
- **Date**: DD.MM.YYYY format
- **Day**: Day of the week
- **Hour**: HH:MM format (Prague timezone)
- **Maximum Occupancy**: Theoretical maximum based on available lanes

## Technical Details

### Dependencies
- **Python 3.x**
- **beautifulsoup4**: HTML parsing for capacity analysis
- **tzdata**: Timezone support for accurate Prague time handling

## Setup

### GitHub Actions Configuration
1. Ensure GitHub Actions has write permissions:
   - Go to repository Settings → Actions → General
   - Set Workflow permissions to "Read and write permissions"

2. The workflows will automatically run according to the schedules defined in `.github/workflows/schedule.yml`

### Local Development

To run the scripts locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run occupancy tracking (single execution)
python occupancy.py

# Run capacity analysis (single execution)
python capacity.py
```

## Data Sources

- **Indoor Pool**: https://www.kravihora-brno.cz/kryta-plavecka-hala
- **Outdoor Pool**: https://www.kravihora-brno.cz/venkovni-bazeny
- **Schedule Data**: https://www.kravihora-brno.cz/kryta-plavecka-hala/rozpis

## Frontend

A web frontend for visualizing the data collected by this project is available at:

- **GitHub Repository**: [kravihora-brno-capacity](https://github.com/VitekHub/kravihora-brno-capacity)

The frontend project fetches and displays real-time occupancy and capacity data from this repository, providing an interactive dashboard for users to monitor pool usage and trends.

## Contributing

Feel free to open issues or submit pull requests if you have suggestions for improvements.

## License

This project is for educational and research purposes. Please respect the terms of service of the data sources.