#!/bin/bash
# Create a GitHub release package with all export formats.
# Packages Docker files, CSV exports, SQLite database, and SQL dialect files
# into a release-ready structure for GitHub.

set -e

# Default values
OUTPUT_DIR="release"
VERSION=$(date +%Y.%m.%d)

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--output-dir DIR] [--version VERSION]"
            echo "  --output-dir DIR    Output directory for the release package (default: release)"
            echo "  --version VERSION   Version string for the release (default: YYYY.MM.DD)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Creating GitHub release package..."
echo "Version: $VERSION"
echo "Output directory: $OUTPUT_DIR"

# Create output directory
if [ -d "$OUTPUT_DIR" ]; then
    echo "Removing existing output directory..."
    rm -rf "$OUTPUT_DIR"
fi
mkdir -p "$OUTPUT_DIR"

# Step 1: Copy Docker files (without data)
echo ""
echo "[1/6] Copying Docker files..."
DOCKER_DIR="$OUTPUT_DIR/docker"
mkdir -p "$DOCKER_DIR"

DOCKER_FILES=("docker-compose.yml" "odoo.conf" "init-odoo.sh")

for file in "${DOCKER_FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$DOCKER_DIR/"
        echo "  Copied: $file"
    else
        echo "  Warning: $file not found"
    fi
done

# Step 2: Zip CSV files
echo ""
echo "[2/6] Zipping CSV files..."
CSV_DIR="csv_export"
if [ -d "$CSV_DIR" ]; then
    CSV_ZIP="$OUTPUT_DIR/odoo_demo_csv_$VERSION.zip"
    cd "$CSV_DIR"
    zip -r "../$CSV_ZIP" *
    cd ..
    echo "  Created: $CSV_ZIP"
else
    echo "  Warning: CSV directory not found"
fi

# Step 3: Export SQLite database
echo ""
echo "[3/6] Exporting SQLite database..."
VENV_PATH=".venv"
PYTHON_CMD="$VENV_PATH/bin/python"

if [ -f "$PYTHON_CMD" ]; then
    SQLITE_FILE="$OUTPUT_DIR/odoo_demo_$VERSION.sqlite"
    "$PYTHON_CMD" export_sqlite.py "$SQLITE_FILE"
    if [ $? -eq 0 ]; then
        echo "  Created: $SQLITE_FILE"
    else
        echo "  Warning: SQLite export failed"
    fi
else
    echo "  Warning: Python virtual environment not found at $PYTHON_CMD"
fi

# Step 4: Export SQL dialects
echo ""
echo "[4/6] Exporting SQL dialects..."
if [ -f "$PYTHON_CMD" ]; then
    SQL_DIR="$OUTPUT_DIR/sql"
    mkdir -p "$SQL_DIR"
    
    "$PYTHON_CMD" export_sql_dialects.py "$SQL_DIR"
    if [ $? -eq 0 ]; then
        echo "  Created SQL files in: $SQL_DIR"
    else
        echo "  Warning: SQL dialect export failed"
    fi
else
    echo "  Warning: Python virtual environment not found at $PYTHON_CMD"
fi

# Step 5: Copy documentation
echo ""
echo "[5/6] Copying documentation..."
DOC_FILES=("README.md" "SCHEMA.md")

for file in "${DOC_FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$OUTPUT_DIR/"
        echo "  Copied: $file"
    else
        echo "  Warning: $file not found"
    fi
done

# Step 6: Create release info file
echo ""
echo "[6/6] Creating release info..."
cat > "$OUTPUT_DIR/RELEASE_NOTES.md" << EOF
# Odoo Demo Data Release $VERSION

## Contents

### Docker Files
- docker-compose.yml: Docker Compose configuration
- odoo.conf: Odoo configuration file
- init-odoo.sh: Initialization script

### Data Exports

#### CSV Files
- odoo_demo_csv_$VERSION.zip: All tables exported as CSV files

#### SQLite Database
- odoo_demo_$VERSION.sqlite: SQLite database with all tables

#### SQL Dialects
- sql/odoo_demo_postgres.sql: PostgreSQL-compatible SQL
- sql/odoo_demo_mssql.sql: Microsoft SQL Server-compatible SQL
- sql/odoo_demo_mariadb.sql: MariaDB/MySQL-compatible SQL

### Documentation
- README.md: Setup and usage instructions
- SCHEMA.md: Database schema documentation

## Tables Included

- res_partner: Customers and suppliers
- product_product: Products
- product_template: Product templates
- product_category: Product categories
- sale_order: Sales orders
- sale_order_line: Sales order lines
- purchase_order: Purchase orders
- purchase_order_line: Purchase order lines
- stock_picking: Stock transfers
- stock_move: Stock movements
- account_move: Invoices and bills
- account_move_line: Invoice/bill lines
- account_payment: Payments
- res_country: Countries
- account_tax: Taxes
- product_taxes_rel: Product-tax relationships
- account_tax_sale_order_line_rel: Sales order line tax relationships
- account_tax_purchase_order_line_rel: Purchase order line tax relationships
- uom_uom: Units of measure
- stock_warehouse: Warehouses
- account_journal: Accounting journals

## Generated

- Date: $(date -Iseconds)
- Scale: 200 customers, 100 suppliers, 300 products, 500 sale orders, 300 purchase orders
- Features: Regional deals, seasonal patterns, date distribution

## License

This demo data is provided as-is for testing and development purposes.
EOF

echo "  Created: RELEASE_NOTES.md"

# Summary
echo ""
echo "Release package created successfully!"
echo "Location: $OUTPUT_DIR"

# Show directory structure
echo ""
echo "Directory structure:"
find "$OUTPUT_DIR" -type f | sort | sed 's|'"$OUTPUT_DIR"'/||' | sed 's/^/  /'

echo ""
echo "You can now upload the contents of '$OUTPUT_DIR' to GitHub."
