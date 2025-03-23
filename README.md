# Pool Occupancy Tracker

A Python script that tracks and records the occupancy of the Kraví Hora swimming pool in Brno. The script automatically collects data every 10 minutes during operating hours (4:00-22:00 UTC) using GitHub Actions.

## How It Works

1. The script fetches the current occupancy from the [Kraví Hora swimming pool website](https://www.kravihora-brno.cz/kryta-plavecka-hala)
2. Extracts the occupancy number using regex
3. Records the data in a CSV file with timestamp and day of the week
4. Automatically commits and pushes changes to the repository

## Project Structure

```
.
├── .github/workflows/
│   └── schedule.yml    # GitHub Actions workflow configuration
├── data/
│   └── pool_occupancy.csv    # Collected occupancy data
└── occupancy.py       # Main Python script
```

## Features

- Automated data collection every 10 minutes
- Accurate Prague timezone handling (including daylight saving time)
- Error handling for network issues
- CSV data storage with timestamps
- Automatic Git commits via GitHub Actions
- Runs only during pool operating hours

## Requirements

- Python 3.x
- GitHub Actions (already configured)
- Write permissions for GitHub Actions workflow

## Data Format

The CSV file contains three columns:
- Day: Day of the week
- Time: Time in HH:MM format (Prague timezone)
- Occupancy: Current number of people in the pool

## Setup

1. Ensure GitHub Actions has write permissions:
   - Go to repository Settings
   - Navigate to Actions under Security
   - Set Workflow permissions to "Read and write permissions"

2. The script will automatically run according to the schedule in `.github/workflows/schedule.yml`

## Local Development

To run the script locally:

```bash
python occupancy.py
```

This will create or update the `data/pool_occupancy.csv` file in your local repository.

## Contributing

Feel free to open issues or submit pull requests if you have suggestions for improvements.