# Summit Demo DB

A realistic ERP dataset based on real system architecture, exported into multiple formats (CSV, SQLite, PostgreSQL, MSSQL, MariaDB) for analytics, data modeling, and BI exercises.

## Quick Start

```bash
./run-all.sh
```

This generates the dataset and exports it to `csv_export/`. Takes 10-15 minutes on first run.

## Download Release

Get the latest release with all formats (CSV, SQLite, SQL files) from the [Releases](https://github.com/Riktastic/SummitDemoDB/releases) page.

## About the Data

The dataset represents **Summit Electronics**, a fictional consumer electronics retailer founded in 2018 in Amsterdam, Netherlands.

- **35 stores** across Europe (Netherlands, Germany, Belgium, France, UK)
- **10 stores** in North America (US, Canada)
- **€50M annual revenue** (2024)
- **Data period**: January 2023 - December 2024

The dataset includes seasonal patterns, regional differences, and realistic business scenarios.

*See [COMPANY_STORY.md](COMPANY_STORY.md) for the complete company profile.*

## What's Included

- **21 interconnected tables** covering sales, purchases, inventory, and accounting
- **200 customers**, 100 suppliers, 300 products
- **500 sales orders**, 300 purchase orders
- **Multi-format exports**: CSV, SQLite, PostgreSQL, MSSQL, MariaDB

## Using the Data

### CSV Files
```python
import pandas as pd
orders = pd.read_csv('csv_export/sale_order.csv')
```

### SQLite Database
```python
import sqlite3
conn = sqlite3.connect('release/odoo_demo_2026.06.28.sqlite')
```

### Direct PostgreSQL
```bash
docker exec -it powerbiexample-db-1 psql -U odoo -d odoo_demo
```

*See [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) for detailed instructions on using the data with Docker, SQL, and BI tools.*

## Custom Data Generation

```bash
export GEN_SALE_ORDERS="5000"
export GEN_PRODUCTS="2000"
./run-all.sh
```

## GitHub Actions

Pushing a tag triggers automatic release generation:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Documentation

- [COMPANY_STORY.md](COMPANY_STORY.md) - Company profile and business context
- [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) - Technical setup and usage guide
- [POWERBI_GUIDE.md](POWERBI_GUIDE.md) - Power BI loading and visualization guide
- [docs/index.html](docs/index.html) - Interactive ERD visualization

## License

MIT
