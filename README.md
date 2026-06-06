# Pool Occupancy and Capacity Tracker

Python system that tracks and records occupancy and capacity data for swimming pools in Brno, Czech Republic. Data is automatically collected via GitHub Actions and provides insights into pool usage patterns.

## Supported Pools

- **Kraví Hora** (indoor & outdoor)
- **Koupaliště Dobrák**
- **Koupaliště Riviéra**
- **Koupaliště Zábrdovice**
- **Aquapark Kohoutovice**
- **Bazény Lužánky**

## Quick Start

### Docker (Recommended)

1. Copy the environment template and fill in your bot identity:

```bash
cp .env.example .env
# Edit .env with your BOT_NAME, BOT_VERSION, BOT_URL, and BOT_EMAIL
```

2. a) Start the tracker - either with the interactive script:

```bash
chmod +x run-docker.sh
./run-docker.sh
# Choose option 1
```

2. b) Or directly with Docker Compose:

```bash
docker compose up -d --build
```

This starts automated tracking (occupancy every 10 min, 6-22, capacity daily at 4:00 AM).

### Local Development

1. Copy the environment template and fill in your bot identity:

```bash
cp .env.example .env
# Edit .env with your details
```

2. Install dependencies and run:

```bash
pip install -r requirements.txt

python occupancy.py          # Fetch current occupancy
python capacity.py           # Analyze lane capacity
python -m pool_aggregation   # Generate aggregated JSON data
python scheduler.py          # Run all on schedule (for local/Docker)
```

## Project Structure

```
.
├── .github/workflows/schedule.yml   # GitHub Actions CI schedule
├── .env.example                    # Template for environment variables
├── data/
│   ├── pool_occupancy_config.json   # Pool configuration
│   ├── *.csv                        # Raw occupancy data
│   ├── overall/*.json               # Aggregated overall stats
│   └── weekly/*.json                # Aggregated weekly stats
├── pool_aggregation/                 # Aggregation module
│   ├── __main__.py                  # Entry point for `python -m pool_aggregation`
│   ├── cli.py                       # CLI interface
│   ├── aggregation/                 # Data processing logic
│   ├── io/                          # CSV/JSON readers and writers
│   ├── models/                      # Data models
│   └── utils/                       # Helpers (rounding, timezones)
├── occupancy.py                      # Occupancy scraper
├── capacity.py                       # Capacity analyzer
├── http_utils.py                     # Bot user-agent, robots.txt, URL fetching
├── scheduler.py                      # Scheduling entrypoint (for Docker)
├── Dockerfile
└── docker-compose.yml
```

## Configuration

### Pool Settings

Pool settings are in `data/pool_occupancy_config.json`. Set `collectStats: true` to enable tracking for a pool.

### Environment Variables

The scripts identify themselves to websites via a `User-Agent` header. These variables are **required** - the scripts will not start without them.

| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_NAME` | Bot name | `PoolOccupancyBot` |
| `BOT_VERSION` | Bot version | `1.0` |
| `BOT_URL` | Project/repository URL | `https://github.com/you/repo` |
| `BOT_EMAIL` | Contact email | `you@example.com` |

For local/Docker use, set these in a `.env` file (copy from `.env.example`). For GitHub Actions, they're configured as repository variables in Settings → Variables.

## Data Output

| File | Description |
|------|-------------|
| `data/*_occupancy.csv` | Raw occupancy readings |
| `data/overall/*.json` | Historical overall statistics |
| `data/weekly/*.json` | Weekly aggregated data |
| `data/capacity.csv` | Daily lane capacity |
| `data/week_capacity.csv` | Weekly capacity forecast |

## Schedule

| Task | Frequency | Time (Prague) |
|------|-----------|---------------|
| Occupancy + Aggregation | Every 10 minutes | 6-22 (first run 6:10) |
| Capacity | Once daily | 4:00 AM |

- **GitHub Actions**: defined in `.github/workflows/schedule.yml`
- **Docker**: managed by `scheduler.py` with the `schedule` library

## Frontend

Dashboard: [pool-occupancy-dashboard-nuxt](https://github.com/VitekHub/pool-occupancy-dashboard-nuxt)
Live Demo: [Pool Occupancy Dashboard](https://vitekhub.github.io/pool-occupancy-dashboard-nuxt/)

## Contributing

Feel free to open issues or submit pull requests if you have suggestions for improvements or want to add support for additional pools.

## License

This project is for educational and research purposes. Please respect the terms of service of the data sources.