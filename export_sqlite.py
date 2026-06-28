#!/usr/bin/env python3
"""
Export PostgreSQL data to SQLite database.
Connects to the running Docker PostgreSQL container and exports all tables to SQLite.
"""

import os
import sys
import sqlite3
import subprocess
import tempfile
import shutil
import csv
from datetime import datetime

# PostgreSQL connection details (from Docker environment)
PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "odoo"
PG_PASSWORD = "odoo"
PG_DATABASE = "odoo_demo"

# Tables to export (same as export_csv.py)
TABLES = [
    "res_partner",
    "product_product",
    "product_template",
    "product_category",
    "sale_order",
    "sale_order_line",
    "purchase_order",
    "purchase_order_line",
    "stock_picking",
    "stock_move",
    "account_move",
    "account_move_line",
    "account_payment",
    "res_country",
    "account_tax",
    "product_taxes_rel",
    "account_tax_sale_order_line_rel",
    "account_tax_purchase_order_line_rel",
    "uom_uom",
    "stock_warehouse",
    "account_journal",
]


def export_postgres_to_sqlite(output_file="odoo_demo.sqlite"):
    """
    Export PostgreSQL data to SQLite using pg_dump with CSV format for proper escaping.
    """
    print(f"Starting PostgreSQL to SQLite export...")
    print(f"Output file: {output_file}")
    
    # Remove existing SQLite file if it exists
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Removed existing SQLite file: {output_file}")
    
    # Create SQLite database
    conn = sqlite3.connect(output_file)
    cursor = conn.cursor()
    
    # Process each table
    for table in TABLES:
        print(f"  Processing table: {table}")
        
        # Get column information using docker exec
        cmd = [
            "docker", "exec", "powerbiexample-db-1",
            "psql", "-U", PG_USER, "-d", PG_DATABASE,
            "-c", f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """,
            "-t", "-A"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            columns_data = result.stdout.strip().split('\n')
            columns = []
            for line in columns_data:
                if line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        columns.append((parts[0], parts[1], parts[2]))
        except subprocess.CalledProcessError:
            print(f"    Table {table} not found or has no columns")
            continue
        
        if not columns:
            print(f"    Table {table} not found or has no columns")
            continue
        
        # Build CREATE TABLE statement for SQLite
        column_defs = []
        for col_name, data_type, is_nullable in columns:
            sqlite_type = convert_postgres_type_to_sqlite(data_type)
            nullable = "" if is_nullable == "YES" else "NOT NULL"
            column_defs.append(f"{col_name} {sqlite_type} {nullable}")
        
        create_sql = f"CREATE TABLE {table} ({', '.join(column_defs)});"
        cursor.execute(create_sql)
        
        # Get data using psql with COPY TO STDOUT CSV format for proper escaping
        temp_csv_path = tempfile.mktemp(suffix='.csv')
        
        cmd = [
            "docker", "exec", "powerbiexample-db-1",
            "psql", "-U", PG_USER, "-d", PG_DATABASE,
            "-c", f"COPY {table} TO STDOUT WITH CSV HEADER NULL '\\N'"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            with open(temp_csv_path, 'w') as f:
                f.write(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"    Could not fetch data for table {table}: {e}")
            continue
        
        # Import CSV data into SQLite
        try:
            with open(temp_csv_path, 'r') as f:
                csv_reader = csv.reader(f)
                # Skip header row
                header = next(csv_reader)
                column_names = [col[0] for col in columns]
                placeholders = ', '.join(['?'] * len(column_names))
                insert_sql = f"INSERT INTO {table} ({', '.join(column_names)}) VALUES ({placeholders})"
                
                row_count = 0
                for row in csv_reader:
                    # Convert values for SQLite
                    values = []
                    for val in row:
                        if val == '\\N' or val == '':
                            values.append(None)
                        else:
                            values.append(val)
                    
                    try:
                        cursor.execute(insert_sql, values)
                        row_count += 1
                    except sqlite3.Error as e:
                        print(f"    Warning: Failed to insert row: {e}")
                
                conn.commit()
                print(f"    Imported {row_count} rows")
        except Exception as e:
            print(f"    Error importing CSV: {e}")
        finally:
            if os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)
    
    # Get table counts
    print(f"\nTable counts in SQLite:")
    for table in TABLES:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count}")
        except sqlite3.Error:
            print(f"  {table}: (empty or not found)")
    
    conn.close()
    print(f"\nSQLite export completed: {output_file}")
    return output_file


def convert_postgres_type_to_sqlite(pg_type):
    """Convert PostgreSQL data type to SQLite equivalent."""
    type_map = {
        'character varying': 'TEXT',
        'varchar': 'TEXT',
        'text': 'TEXT',
        'integer': 'INTEGER',
        'bigint': 'INTEGER',
        'smallint': 'INTEGER',
        'serial': 'INTEGER',
        'bigserial': 'INTEGER',
        'boolean': 'INTEGER',
        'timestamp without time zone': 'TEXT',
        'timestamp with time zone': 'TEXT',
        'date': 'TEXT',
        'time without time zone': 'TEXT',
        'time with time zone': 'TEXT',
        'numeric': 'REAL',
        'decimal': 'REAL',
        'real': 'REAL',
        'double precision': 'REAL',
        'json': 'TEXT',
        'jsonb': 'TEXT',
        'bytea': 'BLOB',
        'uuid': 'TEXT',
    }
    return type_map.get(pg_type.lower(), 'TEXT')


if __name__ == "__main__":
    output_file = sys.argv[1] if len(sys.argv) > 1 else "odoo_demo.sqlite"
    export_postgres_to_sqlite(output_file)
