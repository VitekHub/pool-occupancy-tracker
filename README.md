# Pool Occupancy and Capacity Tracker

Python-based system that tracks and records both occupancy and capacity data for multiple swimming pools and aquatic facilities in Brno, Czech Republic. The system automatically collects data using GitHub Actions and provides insights into pool usage patterns across the city.

## Features

### Multi-Pool Support
The system now tracks occupancy data from **6 different aquatic facilities** in Brno:
- **Kraví Hora** (indoor and outdoor pools)
- **Koupaliště Dobrák** (outdoor pool)
- **Koupaliště Riviéra** (outdoor pool)
- **Koupaliště Zábrdovice** (outdoor pool)
- **Aquapark Kohoutovice** (indoor pool)
- **Bazény Lužánky** (indoor pool)

### Occupancy Tracking (`occupancy.py`)
- **Real-time Data Collection**: Tracks current occupancy from multiple pool websites
- **Flexible Pool Types**: Supports both indoor and outdoor pools with different configurations
- **Automated Collection**: Runs every 10 minutes during operating hours (6:00-21:59 Prague time)

### Capacity Analysis (`capacity.py`)
- **Lane Availability**: Analyzes swimming lane reservations for pools with lane-based capacity
- **Dynamic Capacity Calculation**: Calculates maximum occupancy based on available lanes and total capacity
- **Daily Updates**: Runs once daily at 4:00 Prague time to capture the latest schedule

### Configuration-Driven Architecture
- **Centralized Configuration**: All pool settings stored in `data/pool_occupancy_config.json`
- **Flexible Data Sources**: Each pool can have different URL patterns and data extraction methods

## How It Works

### Data Collection Process

1. **Configuration Loading**: 
   - Reads pool configurations from `data/pool_occupancy_config.json`
   - Determines which pools to monitor based on `collectStats` setting

2. **Operating Hours Check**:
   - Validates current time against each pool's individual operating hours
   - Skips data collection for closed facilities

3. **Occupancy Data**: 
   - Fetches current occupancy using pool-specific URL patterns
   - Records data every 10 minutes during operating hours
   - Saves to individual CSV files per pool

4. **Capacity Data** (Kraví Hora only):
   - Scrapes the weekly reservation schedule
   - Generates both daily and weekly capacity reports

### Automation
- **GitHub Actions**: Fully automated using scheduled workflows
- **Git Integration**: Automatically commits and pushes data updates

## Project Structure

```
.
├── .github/workflows/
│   └── schedule.yml                    # GitHub Actions workflow configuration
├── data/
│   ├── pool_occupancy_config.json      # Pool configuration file
│   ├── kravi_hora_inside_pool_occupancy.csv    # Kraví Hora indoor pool data
│   ├── kravi_hora_outside_pool_occupancy.csv   # Kraví Hora outdoor pool data
│   ├── koupaliste_dobrak_occupancy.csv         # Dobrák pool data
│   ├── koupaliste_riviera_occupancy.csv        # Riviéra pool data
│   ├── koupaliste_zabrdovice_occupancy.csv     # Zábrdovice pool data
│   ├── aquapark_kohoutovice_occupancy.csv      # Aquapark Kohoutovice data
│   ├── bazeny_luzanky_occupancy.csv            # Lužánky pools data
│   ├── capacity.csv                            # Daily capacity data (Kraví Hora)
│   └── week_capacity.csv                       # Weekly capacity data (Kraví Hora)
├── occupancy.py                        # Real-time occupancy tracking script
├── capacity.py                         # Capacity analysis script (Kraví Hora specific)
├── requirements.txt                    # Python dependencies
└── README.md                          # This file
```

## Pool Configuration

Each pool is configured in `data/pool_occupancy_config.json` with the following structure:

```json
{
    "name": "Pool Name",
    "insidePool": {  // or "outsidePool"
        "url": "https://pool-website.com",
        "pattern": "regex_pattern_for_occupancy",
        "csvFile": "output_filename.csv",
        "maximumCapacity": 135,
        "totalLanes": 6,  // for pools with lanes
        "weekdaysOpeningHours": "6-22",
        "weekendOpeningHours": "8-21",
        "collectStats": true,
        "viewStats": true
    }
}
```

## Schedule

### Occupancy Tracking
- **Frequency**: Every 10 minutes
- **Hours**: Individual operating hours per pool (Prague time)
- **Scope**: All configured pools with `collectStats: true`

### Capacity Tracking
- **Frequency**: Once daily
- **Time**: 4:00 Prague time (2:00 UTC)
- **Scope**: Kraví Hora indoor pool only

## Data Formats

### Occupancy Data (per pool CSV files)
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

### Adding New Pools

To add a new pool to the tracking system:

1. Update `data/pool_occupancy_config.json` with the new pool configuration
2. Set `collectStats: true` to enable data collection
3. The system will automatically start tracking the new pool on the next scheduled run

## Data Sources

### Current Pool Websites
- **Kraví Hora**: https://www.kravihora-brno.cz/
- **Koupaliště Dobrák**: https://www.koupalistebrno.cz/
- **Koupaliště Riviéra**: https://riviera.starez.cz/
- **Koupaliště Zábrdovice**: https://zabrdovice.starez.cz/
- **Aquapark Kohoutovice**: https://aquapark.starez.cz/
- **Bazény Lužánky**: https://bazenyluzanky.starez.cz/

## Frontend

A web frontend for visualizing the data collected by this project is available at:

- **GitHub Repository**: [pool-occupancy-dashboard](https://github.com/VitekHub/pool-occupancy-dashboard)

The frontend project fetches and displays real-time occupancy and capacity data from this repository, providing an interactive dashboard for users to monitor pool usage and trends across all tracked facilities.

## Contributing

Feel free to open issues or submit pull requests if you have suggestions for improvements or want to add support for additional pools.

## License

This project is for educational and research purposes. Please respect the terms of service of the data sources.