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

```bash
chmod +x run-docker.sh
./run-docker.sh
```

Choose option 1 to start automated tracking.

### Local Development

```bash
pip install -r requirements.txt

python occupancy.py       # Fetch current occupancy
python capacity.py        # Analyze lane capacity
python -m pool_aggregation  # Generate aggregated JSON data
```

## Project Structure

```
.
├── .github/workflows/schedule.yml   # GitHub Actions
├── data/
│   ├── pool_occupancy_config.json   # Pool configuration
│   ├── *.csv                        # Raw occupancy data
│   ├── overall/*.json               # Aggregated overall stats
│   └── weekly/*.json                # Aggregated weekly stats
├── pool_aggregation/                 # Aggregation module
│   ├── cli.py                       # CLI entry point
│   └── aggregation/                 # Data processing
├── occupancy.py                      # Occupancy scraper
├── capacity.py                       # Capacity analyzer
├── Dockerfile
└── docker-compose.yml
```

## Configuration

Pool settings are in `data/pool_occupancy_config.json`. Set `collectStats: true` to enable tracking for a pool.

## Data Output

| File | Description |
|------|-------------|
| `data/*_occupancy.csv` | Raw occupancy readings |
| `data/overall/*.json` | Historical overall statistics |
| `data/weekly/*.json` | Weekly aggregated data |
| `data/capacity.csv` | Daily lane capacity |
| `data/week_capacity.csv` | Weekly capacity forecast |

## Schedule

- **Occupancy**: Every 10 minutes (02:00-19:59 UTC)
- **Capacity**: Once daily (02:00 UTC)

## Frontend

Dashboard: [pool-occupancy-dashboard-nuxt](https://github.com/VitekHub/pool-occupancy-dashboard-nuxt)
Live Demo: [Pool Occupancy Dashboard](https://vitekhub.github.io/pool-occupancy-dashboard-nuxt/)

## Contributing

Feel free to open issues or submit pull requests if you have suggestions for improvements or want to add support for additional pools.

## License

This project is for educational and research purposes. Please respect the terms of service of the data sources.