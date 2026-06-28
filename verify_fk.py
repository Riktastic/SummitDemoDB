#!/usr/bin/env python3
"""Spot-check referential integrity between the exported ERP CSVs."""
import csv
import os
import sys
from collections import defaultdict

CSV_DIR = os.environ.get("CSV_DIR", "csv_export")


def load_ids(filename):
    path = os.path.join(CSV_DIR, filename)
    if not os.path.exists(path):
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {int(row["id"]) for row in reader if row.get("id")}


def load_column(filename, column):
    path = os.path.join(CSV_DIR, filename)
    values = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            val = row.get(column)
            if val:
                try:
                    values.append(int(val))
                except ValueError:
                    pass
    return values


def check_fk(child_file, child_col, parent_file, parent_ids, allow_null=True):
    child_vals = load_column(child_file, child_col)
    orphans = [v for v in child_vals if v not in parent_ids]
    ok = not orphans
    print(
        f"{child_file}.{child_col} -> {parent_file}: "
        f"{len(child_vals)} refs, {len(orphans)} orphans "
        f"{'OK' if ok else 'FAIL'}"
    )
    return ok


def main():
    ok = True

    partner_ids = load_ids("res_partner.csv")
    product_ids = load_ids("product_product.csv")
    product_tmpl_ids = load_ids("product_template.csv")
    so_ids = load_ids("sale_order.csv")
    po_ids = load_ids("purchase_order.csv")
    picking_ids = load_ids("stock_picking.csv")
    location_ids = load_ids("stock_location.csv")
    company_ids = load_ids("res_company.csv")
    user_ids = load_ids("res_users.csv")
    warehouse_ids = load_ids("stock_warehouse.csv")
    picking_type_ids = load_ids("stock_picking_type.csv")
    move_ids = load_ids("stock_move.csv")
    tax_ids = load_ids("account_tax.csv")
    account_ids = load_ids("account_account.csv")
    journal_ids = load_ids("account_journal.csv")
    move_entry_ids = load_ids("account_move.csv")
    uom_ids = load_ids("uom_uom.csv")

    ok &= check_fk("sale_order.csv", "partner_id", "res_partner.csv", partner_ids)
    ok &= check_fk("sale_order.csv", "company_id", "res_company.csv", company_ids)
    ok &= check_fk("sale_order.csv", "user_id", "res_users.csv", user_ids)
    ok &= check_fk("sale_order_line.csv", "order_id", "sale_order.csv", so_ids)
    ok &= check_fk("sale_order_line.csv", "product_id", "product_product.csv", product_ids)
    ok &= check_fk("purchase_order.csv", "partner_id", "res_partner.csv", partner_ids)
    ok &= check_fk("purchase_order.csv", "company_id", "res_company.csv", company_ids)
    ok &= check_fk("purchase_order.csv", "user_id", "res_users.csv", user_ids)
    ok &= check_fk("purchase_order_line.csv", "order_id", "purchase_order.csv", po_ids)
    ok &= check_fk("purchase_order_line.csv", "product_id", "product_product.csv", product_ids)
    ok &= check_fk("product_product.csv", "product_tmpl_id", "product_template.csv", product_tmpl_ids)
    ok &= check_fk("stock_picking.csv", "picking_type_id", "stock_picking_type.csv", picking_type_ids)
    ok &= check_fk("stock_picking.csv", "location_id", "stock_location.csv", location_ids)
    ok &= check_fk("stock_picking.csv", "location_dest_id", "stock_location.csv", location_ids)
    ok &= check_fk("stock_move.csv", "picking_id", "stock_picking.csv", picking_ids)
    ok &= check_fk("stock_move.csv", "product_id", "product_product.csv", product_ids)
    ok &= check_fk("stock_move.csv", "location_id", "stock_location.csv", location_ids)
    ok &= check_fk("stock_move.csv", "location_dest_id", "stock_location.csv", location_ids)
    ok &= check_fk("stock_move_line.csv", "move_id", "stock_move.csv", move_ids)
    ok &= check_fk("account_move.csv", "journal_id", "account_journal.csv", journal_ids)
    ok &= check_fk("account_move.csv", "company_id", "res_company.csv", company_ids)
    ok &= check_fk("account_move_line.csv", "move_id", "account_move.csv", move_entry_ids)
    ok &= check_fk("account_move_line.csv", "account_id", "account_account.csv", account_ids)
    ok &= check_fk("product_template.csv", "categ_id", "product_category.csv", load_ids("product_category.csv"))
    ok &= check_fk("product_template.csv", "uom_id", "uom_uom.csv", uom_ids)

    print()
    if ok:
        print("All spot-checked foreign keys are consistent.")
        return 0
    else:
        print("Some foreign-key checks failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
