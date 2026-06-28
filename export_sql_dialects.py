#!/usr/bin/env python3
"""
Export PostgreSQL data to SQL files for different database dialects.
Uses SQLAlchemy to generate dialect-specific SQL files for PostgreSQL, MSSQL, and MariaDB.
"""

import os
import sys
import subprocess
import tempfile
from datetime import datetime
import psycopg2
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, Float, Boolean, DateTime, inspect
from sqlalchemy.dialects import postgresql, mssql, mysql
from sqlalchemy.schema import CreateTable, CreateIndex

# PostgreSQL connection details
PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "odoo"
PG_PASSWORD = "odoo"
PG_DATABASE = "odoo_demo"

# Tables to export
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


def get_postgres_connection():
    """Create a connection to the PostgreSQL database via Docker."""
    # Use docker exec to run psql and pipe through a local connection
    # For now, we'll use a simpler approach: read data via docker exec
    return None  # We'll use docker exec directly instead


def export_postgres_sql(output_file="odoo_demo_postgres.sql"):
    """
    Export PostgreSQL data to a native PostgreSQL SQL file using pg_dump.
    """
    print(f"Exporting PostgreSQL SQL to: {output_file}")
    
    # Build pg_dump command with separate --table arguments
    pg_dump_cmd = [
        "docker", "exec", "powerbiexample-db-1",
        "pg_dump", "-U", PG_USER, "-d", PG_DATABASE,
        "--no-owner", "--no-privileges",
        "--format=plain"
    ]
    # Add each table as a separate --table argument
    for table in TABLES:
        pg_dump_cmd.extend(["--table", table])
    
    try:
        result = subprocess.run(
            pg_dump_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        with open(output_file, 'w') as f:
            f.write(result.stdout)
        
        print(f"PostgreSQL SQL export completed: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error running pg_dump: {e}")
        print(f"stderr: {e.stderr}")
        return None


def export_mssql_sql(output_file="odoo_demo_mssql.sql"):
    """
    Export PostgreSQL data to MSSQL-compatible SQL file using docker exec.
    """
    print(f"Exporting MSSQL SQL to: {output_file}")
    
    # Get schema and data
    sql_statements = []
    sql_statements.append("-- MSSQL-compatible SQL export from Odoo demo database")
    sql_statements.append(f"-- Generated: {datetime.now().isoformat()}")
    sql_statements.append("")
    
    for table in TABLES:
        print(f"  Processing table: {table}")
        
        # Get column information using docker exec
        cmd = [
            "docker", "exec", "powerbiexample-db-1",
            "psql", "-U", PG_USER, "-d", PG_DATABASE,
            "-c", f"""
                SELECT column_name, data_type, is_nullable, column_default
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
                    if len(parts) >= 4:
                        columns.append((parts[0], parts[1], parts[2], parts[3]))
        except subprocess.CalledProcessError:
            print(f"    Table {table} not found or has no columns")
            continue
        
        if not columns:
            print(f"    Table {table} not found or has no columns")
            continue
        
        # Build CREATE TABLE statement for MSSQL
        sql_statements.append(f"-- Table: {table}")
        sql_statements.append(f"IF OBJECT_ID('{table}', 'U') IS NOT NULL")
        sql_statements.append(f"DROP TABLE {table};")
        sql_statements.append(f"GO")
        sql_statements.append(f"CREATE TABLE {table} (")
        
        column_defs = []
        for col_name, data_type, is_nullable, default_val in columns:
            mssql_type = convert_postgres_type_to_mssql(data_type)
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            column_defs.append(f"    {col_name} {mssql_type} {nullable}")
        
        sql_statements.append(",\n".join(column_defs))
        sql_statements.append(");")
        sql_statements.append("GO")
        
        # Get data using docker exec
        cmd = [
            "docker", "exec", "powerbiexample-db-1",
            "psql", "-U", PG_USER, "-d", PG_DATABASE,
            "-c", f"SELECT * FROM {table}",
            "-t", "-A"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            rows_data = result.stdout.strip().split('\n')
            rows = []
            for line in rows_data:
                if line:
                    rows.append(line.split('\t'))
        except subprocess.CalledProcessError:
            print(f"    Could not fetch data for table {table}")
            rows = []
        
        if rows:
            column_names = [col[0] for col in columns]
            for row in rows:
                values = []
                for val in row:
                    if val == '\\N' or val == '':
                        values.append("NULL")
                    elif isinstance(val, str):
                        # Escape single quotes
                        escaped = val.replace("'", "''")
                        values.append(f"'{escaped}'")
                    elif isinstance(val, bool):
                        values.append("1" if val else "0")
                    else:
                        values.append(str(val))
                
                insert_sql = f"INSERT INTO {table} ({', '.join(column_names)}) VALUES ({', '.join(values)});"
                sql_statements.append(insert_sql)
            
            sql_statements.append("GO")
        
        sql_statements.append("")
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(sql_statements))
    
    print(f"MSSQL SQL export completed: {output_file}")
    return output_file


def export_mariadb_sql(output_file="odoo_demo_mariadb.sql"):
    """
    Export PostgreSQL data to MariaDB/MySQL-compatible SQL file using docker exec.
    """
    print(f"Exporting MariaDB SQL to: {output_file}")
    
    # Get schema and data
    sql_statements = []
    sql_statements.append("-- MariaDB/MySQL-compatible SQL export from Odoo demo database")
    sql_statements.append(f"-- Generated: {datetime.now().isoformat()}")
    sql_statements.append("")
    
    for table in TABLES:
        print(f"  Processing table: {table}")
        
        # Get column information using docker exec
        cmd = [
            "docker", "exec", "powerbiexample-db-1",
            "psql", "-U", PG_USER, "-d", PG_DATABASE,
            "-c", f"""
                SELECT column_name, data_type, is_nullable, column_default
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
                    if len(parts) >= 4:
                        columns.append((parts[0], parts[1], parts[2], parts[3]))
        except subprocess.CalledProcessError:
            print(f"    Table {table} not found or has no columns")
            continue
        
        if not columns:
            print(f"    Table {table} not found or has no columns")
            continue
        
        # Build CREATE TABLE statement for MariaDB
        sql_statements.append(f"-- Table: {table}")
        sql_statements.append(f"DROP TABLE IF EXISTS {table};")
        sql_statements.append(f"CREATE TABLE {table} (")
        
        column_defs = []
        for col_name, data_type, is_nullable, default_val in columns:
            mariadb_type = convert_postgres_type_to_mariadb(data_type)
            nullable = "" if is_nullable == "YES" else "NOT NULL"
            column_defs.append(f"    {col_name} {mariadb_type} {nullable}")
        
        sql_statements.append(",\n".join(column_defs))
        sql_statements.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;")
        
        # Get data using docker exec
        cmd = [
            "docker", "exec", "powerbiexample-db-1",
            "psql", "-U", PG_USER, "-d", PG_DATABASE,
            "-c", f"SELECT * FROM {table}",
            "-t", "-A"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            rows_data = result.stdout.strip().split('\n')
            rows = []
            for line in rows_data:
                if line:
                    rows.append(line.split('\t'))
        except subprocess.CalledProcessError:
            print(f"    Could not fetch data for table {table}")
            rows = []
        
        if rows:
            column_names = [col[0] for col in columns]
            for row in rows:
                values = []
                for val in row:
                    if val == '\\N' or val == '':
                        values.append("NULL")
                    elif isinstance(val, str):
                        # Escape single quotes and backslashes
                        escaped = val.replace("\\", "\\\\").replace("'", "\\'")
                        values.append(f"'{escaped}'")
                    elif isinstance(val, bool):
                        values.append("1" if val else "0")
                    else:
                        values.append(str(val))
                
                insert_sql = f"INSERT INTO {table} ({', '.join(column_names)}) VALUES ({', '.join(values)});"
                sql_statements.append(insert_sql)
        
        sql_statements.append("")
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(sql_statements))
    
    print(f"MariaDB SQL export completed: {output_file}")
    return output_file


def convert_postgres_type_to_mssql(pg_type):
    """Convert PostgreSQL data type to MSSQL equivalent."""
    type_map = {
        'character varying': 'NVARCHAR(MAX)',
        'varchar': 'NVARCHAR(MAX)',
        'text': 'NVARCHAR(MAX)',
        'integer': 'INT',
        'bigint': 'BIGINT',
        'smallint': 'SMALLINT',
        'serial': 'INT IDENTITY(1,1)',
        'bigserial': 'BIGINT IDENTITY(1,1)',
        'boolean': 'BIT',
        'timestamp without time zone': 'DATETIME',
        'timestamp with time zone': 'DATETIMEOFFSET',
        'date': 'DATE',
        'time without time zone': 'TIME',
        'time with time zone': 'TIME',
        'numeric': 'DECIMAL(19,6)',
        'decimal': 'DECIMAL(19,6)',
        'real': 'REAL',
        'double precision': 'FLOAT',
        'json': 'NVARCHAR(MAX)',
        'jsonb': 'NVARCHAR(MAX)',
        'bytea': 'VARBINARY(MAX)',
        'uuid': 'UNIQUEIDENTIFIER',
    }
    return type_map.get(pg_type.lower(), 'NVARCHAR(MAX)')


def convert_postgres_type_to_mariadb(pg_type):
    """Convert PostgreSQL data type to MariaDB/MySQL equivalent."""
    type_map = {
        'character varying': 'VARCHAR(255)',
        'varchar': 'VARCHAR(255)',
        'text': 'TEXT',
        'integer': 'INT',
        'bigint': 'BIGINT',
        'smallint': 'SMALLINT',
        'serial': 'INT AUTO_INCREMENT',
        'bigserial': 'BIGINT AUTO_INCREMENT',
        'boolean': 'TINYINT(1)',
        'timestamp without time zone': 'DATETIME',
        'timestamp with time zone': 'DATETIME',
        'date': 'DATE',
        'time without time zone': 'TIME',
        'time with time zone': 'TIME',
        'numeric': 'DECIMAL(19,6)',
        'decimal': 'DECIMAL(19,6)',
        'real': 'FLOAT',
        'double precision': 'DOUBLE',
        'json': 'JSON',
        'jsonb': 'JSON',
        'bytea': 'LONGBLOB',
        'uuid': 'CHAR(36)',
    }
    return type_map.get(pg_type.lower(), 'VARCHAR(255)')


if __name__ == "__main__":
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Export to different dialects
    postgres_file = os.path.join(output_dir, "odoo_demo_postgres.sql")
    mssql_file = os.path.join(output_dir, "odoo_demo_mssql.sql")
    mariadb_file = os.path.join(output_dir, "odoo_demo_mariadb.sql")
    
    export_postgres_sql(postgres_file)
    export_mssql_sql(mssql_file)
    export_mariadb_sql(mariadb_file)
    
    print(f"\nAll SQL exports completed in: {output_dir}")
