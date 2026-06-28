#!/usr/bin/env python3
"""Export key Odoo ERP tables to CSV for warehouse + webshop analytics."""
import os
import csv
import psycopg2

HOST = os.environ.get("PGHOST", "localhost")
PORT = os.environ.get("PGPORT", "5432")
DATABASE = os.environ.get("PGDATABASE", "odoo_demo")
USER = os.environ.get("PGUSER", "odoo")
PASSWORD = os.environ.get("PGPASSWORD", "myodoo")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/csv_export")

# Tables to export grouped by business domain.
TABLES = {
    # Master data
    "res_company": "Companies",
    "res_partner": "Customers / Vendors",
    "res_users": "Users",
    "res_currency": "Currencies",
    "product_category": "Product categories",
    "product_template": "Product templates",
    "product_product": "Product variants",
    "uom_uom": "Units of measure",
    "product_supplierinfo": "Supplier prices",
    "product_pricelist": "Pricelists",
    "product_pricelist_item": "Pricelist items",
    "crm_lead": "CRM leads / opportunities",
    "project_project": "Projects",
    "project_task": "Tasks",
    "website": "Websites",
    # Sales
    "sale_order": "Sales orders",
    "sale_order_line": "Sales order lines",
    # Purchase
    "purchase_order": "Purchase orders",
    "purchase_order_line": "Purchase order lines",
    # Warehouse / inventory
    "stock_warehouse": "Warehouses",
    "stock_location": "Stock locations",
    "stock_picking_type": "Picking types",
    "stock_picking": "Stock pickings",
    "stock_move": "Stock moves",
    "stock_move_line": "Stock move lines",
    "stock_quant": "Stock quants",
    "stock_lot": "Lots / serials",
    "stock_inventory": "Inventory adjustments",
    "stock_inventory_line": "Inventory adjustment lines",
    "stock_valuation_layer": "Stock valuation layers",
    "stock_rule": "Stock rules",
    "stock_route": "Stock routes",
    "stock_route_warehouse": "Route warehouse links",
    "stock_route_product": "Route product links",
    # Many-to-many link tables (Odoo 18 uses these exact relation names)
    "account_tax_sale_order_line_rel": "Sale order line taxes",
    "account_tax_purchase_order_line_rel": "Purchase order line taxes",
    "product_taxes_rel": "Product taxes",
    "account_tax_fiscal_position_rel": "Tax fiscal position links",
    # Accounting
    "account_journal": "Account journals",
    "account_account": "Chart of accounts",
    "account_tax": "Taxes",
    "account_move": "Journal entries",
    "account_move_line": "Journal entry lines",
    "account_payment": "Payments",
    "account_payment_register": "Payment registers",
    "account_payment_method_line": "Payment method lines",
    "account_invoice_report": "Invoice analysis",
    "sale_report": "Sales analysis",
    "purchase_report": "Purchase analysis",
}


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def table_exists(cur, name):
    cur.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=%s",
        (name,),
    )
    return cur.fetchone() is not None


def export_table(cur, table_name, output_path):
    cur.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
    count = cur.fetchone()[0]
    if count == 0:
        print(f"  {table_name}: empty, skipping")
        return

    cur.execute(f"SELECT * FROM \"{table_name}\"")
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)

    print(f"  {table_name}: {count} rows -> {output_path}")


def main():
    ensure_dir(OUTPUT_DIR)
    conn = psycopg2.connect(
        host=HOST,
        port=PORT,
        dbname=DATABASE,
        user=USER,
        password=PASSWORD,
    )
    conn.set_client_encoding("UTF8")
    cur = conn.cursor()

    print(f"Connected to {DATABASE} at {HOST}:{PORT}")
    print("Exporting tables...")

    for table, description in TABLES.items():
        output_path = os.path.join(OUTPUT_DIR, f"{table}.csv")
        if not table_exists(cur, table):
            print(f"  {table}: table not found ({description})")
            # Create empty header-only file so downstream scripts know what was missing
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["table_not_found_in_database"])
            continue
        export_table(cur, table, output_path)

    cur.close()
    conn.close()
    print("Export complete.")


if __name__ == "__main__":
    main()
