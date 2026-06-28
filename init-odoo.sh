#!/bin/bash
set -e

DB_NAME="odoo_demo"

# Check whether the database is already initialized; if so, skip the
# expensive module installation so the script can be re-run safely.
PG_USER="${USER:-odoo}"
if psql -U "$PG_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
    echo "[init] Database $DB_NAME already exists; skipping initialization."
    exit 0
fi

# Install the core ERP modules together in one pass so all required
# dependencies (account, analytic, stock) are available.
# Skip demo data (--without-demo) to avoid conflicts with purchase module demo data.
echo "[init] Installing core ERP modules: sale, purchase, stock, account (without demo data)"
odoo --database="$DB_NAME" --init="sale,purchase,stock,account,crm" --load-language=en_US --stop-after-init --without-demo=all

echo "[init] Odoo initialization complete."
