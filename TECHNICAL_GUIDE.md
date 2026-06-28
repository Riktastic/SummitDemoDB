# Technical Session Guide - Using Summit Demo DB

This guide provides a comprehensive technical walkthrough for using the Summit Demo DB dataset, including Docker setup, data access methods, and integration with BI tools.

## Prerequisites

- Docker Desktop installed and running
- Python 3.8+ (for running data generation scripts locally)
- Basic familiarity with SQL and database concepts
- 10-15 minutes for initial setup

## Quick Start with Docker

### 1. Clone and Navigate

```bash
cd /path/to/summit-demo-db
```

### 2. Start the Complete System

```bash
./run-all.sh
```

This single command:
- Starts Docker containers (database, ERP system, web UI)
- Initializes the ERP database with demo data
- Generates ERP records
- Exports all tables to CSV format

### 3. Access the Data

After completion, you'll find:
- **CSV files**: `csv_export/` directory
- **SQLite database**: `release/odoo_demo_YYYY.MM.DD.sqlite` (if using `--create-release`)
- **SQL files**: `release/sql/` directory (if using `--create-release`)

## Docker Architecture

The system uses Docker Compose to orchestrate multiple services:

```
┌─────────────────┐
│   web-frontend  │  (ERP web UI - port 8069)
└────────┬────────┘
         │
┌────────▼────────┐
│     database    │  (PostgreSQL - port 5432)
└────────┬────────┘
         │
┌────────▼────────┐
│      web        │  (Initialization - one-time)
└─────────────────┘
```

### Docker Services

**database** (PostgreSQL)
- Port: 5432
- Database: `odoo_demo`
- User: `odoo`
- Password: `odoo`
- Contains all ERP data and relationships

**web** (Initialization)
- Runs once to initialize the ERP system
- Installs required modules (sales, purchase, stock, account, crm)
- Loads base demo data
- Exits when complete

**web-frontend** (ERP Web UI)
- Port: 8069
- Provides web interface to the ERP system
- Access at http://localhost:8069
- Credentials: admin / admin

**exporter** (Data Export)
- Runs Python script to export tables to CSV
- Connects to database container
- Outputs to `csv_export/` directory

## Manual Docker Operations

### Start Only the Database

```bash
docker-compose up -d database
```

### Start the Web UI

```bash
docker-compose up -d web-frontend
```

### Export Data to CSV

```bash
docker-compose up exporter --remove-orphans --force-recreate
```

### Stop All Services

```bash
docker-compose down
```

### Stop and Remove Volumes (Complete Reset)

```bash
docker-compose down -v
```

## Accessing the Data

### Method 1: CSV Files (Simplest)

CSV files are located in `csv_export/` after running the export:

```bash
ls csv_export/
```

**Example: Loading CSV into Python**

```python
import pandas as pd

# Load sales orders
sales_orders = pd.read_csv('csv_export/sale_order.csv')
print(f"Total sales orders: {len(sales_orders)}")

# Load customers
customers = pd.read_csv('csv_export/res_partner.csv')
print(f"Total customers: {len(customers)}")

# Join orders with customers
orders_with_customers = sales_orders.merge(
    customers, 
    left_on='partner_id', 
    right_on='id'
)
```

**Example: Loading CSV into R**

```r
library(readr)

# Load sales orders
sales_orders <- read_csv("csv_export/sale_order.csv")
cat("Total sales orders:", nrow(sales_orders), "\n")

# Load customers
customers <- read_csv("csv_export/res_partner.csv")
cat("Total customers:", nrow(customers), "\n")

# Join orders with customers
library(dplyr)
orders_with_customers <- sales_orders %>%
  inner_join(customers, by = c("partner_id" = "id"))
```

### Method 2: SQLite Database

Create the SQLite database with the release script:

```bash
./create_release.sh
```

Then access the SQLite database:

```python
import sqlite3

conn = sqlite3.connect('release/odoo_demo_2026.06.28.sqlite')
cursor = conn.cursor()

# Query sales orders
cursor.execute("SELECT * FROM sale_order LIMIT 10")
orders = cursor.fetchall()
print(f"Sample orders: {orders}")

# Get table counts
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"{table[0]}: {count} rows")

conn.close()
```

### Method 3: Direct PostgreSQL Access

Connect directly to the running PostgreSQL container:

```bash
docker exec -it powerbiexample-db-1 psql -U odoo -d odoo_demo
```

**SQL Queries:**

```sql
-- Get sales order summary
SELECT 
    COUNT(*) as total_orders,
    SUM(amount_total) as total_revenue,
    AVG(amount_total) as avg_order_value
FROM sale_order;

-- Get top customers by revenue
SELECT 
    p.name,
    COUNT(so.id) as order_count,
    SUM(so.amount_total) as total_spent
FROM sale_order so
JOIN res_partner p ON so.partner_id = p.id
GROUP BY p.id, p.name
ORDER BY total_spent DESC
LIMIT 10;

-- Get product sales performance
SELECT 
    pt.name as product_name,
    COUNT(sol.id) as times_ordered,
    SUM(sol.product_uom_qty) as total_quantity,
    SUM(sol.price_subtotal) as total_revenue
FROM sale_order_line sol
JOIN product_product pp ON sol.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
GROUP BY pt.id, pt.name
ORDER BY total_revenue DESC
LIMIT 10;
```

**Python PostgreSQL Connection:**

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="odoo_demo",
    user="odoo",
    password="odoo"
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM sale_order")
count = cursor.fetchone()[0]
print(f"Total orders: {count}")

conn.close()
```

### Method 4: SQL Dialect Files

For use with other database systems:

```bash
./create_release.sh
```

This creates SQL files in `release/sql/`:
- `odoo_demo_postgres.sql` - PostgreSQL
- `odoo_demo_mssql.sql` - Microsoft SQL Server
- `odoo_demo_mariadb.sql` - MariaDB/MySQL

**Import into MSSQL:**

```sql
-- In SQL Server Management Studio
USE your_database;
GO
-- Open and execute release/sql/odoo_demo_mssql.sql
```

**Import into MariaDB:**

```bash
mysql -u username -p database_name < release/sql/odoo_demo_mariadb.sql
```

## BI Tool Integration

### Power BI

**From CSV:**
1. Open Power BI Desktop
2. Get Data → Text/CSV
3. Select files from `csv_export/`
4. Load and create relationships

**From PostgreSQL:**
1. Get Data → Database → PostgreSQL database
2. Server: localhost
3. Database: odoo_demo
4. User: odoo, Password: odoo
5. Load tables

**From SQLite:**
1. Get Data → Database → SQLite database
2. Browse to `release/odoo_demo_YYYY.MM.DD.sqlite`
3. Load tables

**Example Power BI DAX:**

```dax
// Total Revenue
Total Revenue = SUM(sale_order[amount_total])

// Revenue by Month
Revenue by Month = 
CALCULATE(
    [Total Revenue],
    DATEADD('sale_order'[date_order], 0, MONTH)
)

// Top 5 Customers
Top 5 Customers = 
TOPN(
    5,
    VALUES('res_partner'[name]),
    [Total Revenue],
    DESC
)
```

### Tableau

**From CSV:**
1. Connect → Text File
2. Select CSV files from `csv_export/`
3. Drag tables to canvas
4. Create relationships

**From PostgreSQL:**
1. Connect → To a Server → PostgreSQL
2. Server: localhost
3. Database: odoo_demo
4. Authentication: Username and Password
5. Select tables

### Excel

**From CSV:**
1. Data → Get Data → From File → From Text/CSV
2. Select CSV files
3. Load to worksheet

**From PostgreSQL:**
1. Data → Get Data → From Database → From PostgreSQL Database
2. Server: localhost
3. Database: odoo_demo
4. Load tables

## Data Model Overview

### Key Tables and Relationships

```
res_partner (customers/suppliers)
    ├── sale_order (sales orders)
    │   └── sale_order_line (order lines)
    ├── purchase_order (purchase orders)
    │   └── purchase_order_line (order lines)
    ├── account_move (invoices/bills)
    │   └── account_move_line (invoice lines)
    └── account_payment (payments)

product_template (product templates)
    └── product_product (product variants)
        ├── sale_order_line
        ├── purchase_order_line
        └── stock_move (inventory movements)

stock_warehouse (warehouses)
    └── stock_picking (shipments/receipts)
        └── stock_move (inventory movements)

account_journal (accounting journals)
    ├── account_move
    └── account_payment
```

### Primary Keys and Foreign Keys

- **Primary Keys**: All tables use `id` as the primary key
- **Foreign Keys**: Follow the pattern `<related_model>_id` (e.g., `partner_id`, `product_id`, `order_id`)

## Common Analysis Patterns

### Sales Analysis

```sql
-- Monthly sales trend
SELECT 
    DATE_TRUNC('month', date_order) as month,
    COUNT(*) as order_count,
    SUM(amount_total) as revenue
FROM sale_order
WHERE state = 'sale'
GROUP BY DATE_TRUNC('month', date_order)
ORDER BY month;
```

### Customer Segmentation

```sql
-- Customer segments by spending
SELECT 
    CASE 
        WHEN total_spent > 10000 THEN 'High Value'
        WHEN total_spent > 5000 THEN 'Medium Value'
        ELSE 'Low Value'
    END as segment,
    COUNT(*) as customer_count
FROM (
    SELECT 
        partner_id,
        SUM(amount_total) as total_spent
    FROM sale_order
    WHERE state = 'sale'
    GROUP BY partner_id
) customer_spending
GROUP BY segment;
```

### Inventory Analysis

```sql
-- Stock movements by product
SELECT 
    pt.name as product_name,
    SUM(CASE WHEN sm.location_dest_id LIKE '%stock%' THEN sm.product_uom_qty ELSE 0 END) as received,
    SUM(CASE WHEN sm.location_id LIKE '%stock%' THEN sm.product_uom_qty ELSE 0 END) as shipped,
    SUM(CASE WHEN sm.location_dest_id LIKE '%stock%' THEN sm.product_uom_qty ELSE 0 END) - 
    SUM(CASE WHEN sm.location_id LIKE '%stock%' THEN sm.product_uom_qty ELSE 0 END) as net_change
FROM stock_move sm
JOIN product_product pp ON sm.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
GROUP BY pt.id, pt.name
ORDER BY net_change DESC;
```

## Troubleshooting

### Docker Issues

**Container won't start:**
```bash
# Check Docker is running
docker info

# Check container logs
docker-compose logs database
docker-compose logs web-frontend
```

**Port conflicts:**
```bash
# Check what's using port 8069
netstat -ano | findstr :8069  # Windows
lsof -i :8069  # Linux/Mac

# Change port in docker-compose.yml if needed
```

### Database Connection Issues

**Can't connect to PostgreSQL:**
```bash
# Check if database container is running
docker ps | grep powerbiexample-db

# Test connection from host
docker exec -it powerbiexample-db-1 psql -U odoo -d odoo_demo -c "SELECT 1"
```

### Data Export Issues

**CSV export fails:**
```bash
# Check exporter logs
docker-compose logs exporter

# Re-run export
docker-compose up exporter --remove-orphans --force-recreate
```

## Performance Tips

### For Large Datasets

1. **Use database instead of CSV** for better performance
2. **Create indexes** on frequently joined columns
3. **Use LIMIT** when exploring data
4. **Filter by date ranges** to reduce dataset size

### Python Optimization

```python
# Use chunking for large CSV files
chunksize = 10000
for chunk in pd.read_csv('csv_export/sale_order.csv', chunksize=chunksize):
    process_chunk(chunk)
```

## Next Steps

1. **Explore the data**: Start with CSV files for quick exploration
2. **Build visualizations**: Use Power BI, Tableau, or your preferred BI tool
3. **Create dashboards**: Build sales, inventory, and customer analytics dashboards
4. **Extend the data**: Modify `generate_data.py` to create larger datasets
5. **Share insights**: Use the release package to share data with your team

## Additional Resources

- [COMPANY_STORY.md](COMPANY_STORY.md) - Learn about Summit Electronics
- [README.md](README.md) - Project overview and setup
- [SCHEMA.md](SCHEMA.md) - Detailed database schema documentation
- [docs/index.html](docs/index.html) - Interactive ERD visualization

---

*For questions or issues, refer to the project documentation or create an issue in the repository.*
