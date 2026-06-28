# ERP CSV Schema Reference

All CSV files are exported from the `odoo_demo` PostgreSQL database. The columns are the raw Odoo model fields.

## Key conventions

- **Primary key**: `id` on every table.
- **Foreign keys**: named `<related_model>_id` or `<related_table>_id`.
- **Audit columns**: `create_uid`, `write_uid`, `create_date`, `write_date`.
- **Technical columns**: `active`, `company_id`, `currency_id`.

## Main tables and relationships

| CSV file | Records | Description | Key FK columns |
|----------|---------|-------------|----------------|
| `res_company.csv` | 2 | Legal entities / companies | – |
| `res_partner.csv` | 343 | Customers, suppliers, contacts | `company_id` |
| `res_users.csv` | 8 | Back-office users | `partner_id`, `company_id` |
| `product_category.csv` | 13 | Product categories | `parent_id` |
| `product_template.csv` | 337 | Product master records | `categ_id`, `uom_id`, `uom_po_id`, `company_id` |
| `product_product.csv` | 343 | Product variants (one per template unless variants used) | `product_tmpl_id`, `categ_id`, `company_id` |
| `product_supplierinfo.csv` | 529 | Supplier prices per product | `partner_id`, `product_id`, `product_tmpl_id` |
| `product_pricelist.csv` | 3 | Sales pricelists | `currency_id`, `company_id` |
| `product_pricelist_item.csv` | 4 | Pricelist lines | `pricelist_id`, `product_id`, `product_tmpl_id`, `categ_id` |
| `uom_uom.csv` | 28 | Units of measure | `category_id` |
| `crm_lead.csv` | 44 | Sales opportunities | `partner_id`, `user_id`, `team_id`, `campaign_id`, `medium_id`, `source_id` |
| `project_project.csv` | 0 | Projects (empty marker) | – |
| `project_task.csv` | 0 | Tasks (empty marker) | – |
| `website.csv` | 0 | Webshops (empty marker) | – |
| `sale_order.csv` | 524 | Sales orders | `partner_id`, `partner_invoice_id`, `partner_shipping_id`, `pricelist_id`, `currency_id`, `user_id`, `team_id`, `company_id`, `warehouse_id`, `website_id` |
| `sale_order_line.csv` | 1565 | Sales order lines | `order_id`, `product_id`, `product_uom`, `tax_id` (via `account_tax_sale_order_line_rel`) |
| `purchase_order.csv` | 311 | Purchase orders | `partner_id`, `currency_id`, `user_id`, `company_id`, `picking_type_id` |
| `purchase_order_line.csv` | 903 | Purchase order lines | `order_id`, `product_id`, `product_uom`, `taxes_id` (via `account_tax_purchase_order_line_rel`) |
| `stock_warehouse.csv` | 2 | Warehouses | `company_id`, `partner_id`, `view_location_id`, `lot_stock_id`, `pick_type_id`, `pack_type_id`, `out_type_id`, `in_type_id`, `int_type_id`, `return_type_id` |
| `stock_location.csv` | 33 | Stock locations | `location_id` (parent), `warehouse_id`, `company_id` |
| `stock_picking.csv` | 675 | Pickings (receipts, deliveries, internal) | `picking_type_id`, `location_id`, `location_dest_id`, `partner_id`, `sale_id`, `purchase_id`, `group_id`, `company_id`, `backorder_id` |
| `stock_picking_type.csv` | 16 | Picking types | `warehouse_id`, `sequence_id`, `default_location_src_id`, `default_location_dest_id` |
| `stock_move.csv` | 1724 | Stock moves | `picking_id`, `product_id`, `product_uom`, `location_id`, `location_dest_id`, `location_final_id`, `partner_id`, `group_id`, `rule_id`, `picking_type_id`, `warehouse_id`, `purchase_line_id`, `sale_line_id`, `company_id` |
| `stock_move_line.csv` | 1719 | Stock move detail lines | `move_id`, `picking_id`, `product_id`, `product_uom_id`, `location_id`, `location_dest_id`, `lot_id`, `package_id`, `result_package_id`, `owner_id`, `company_id` |
| `stock_quant.csv` | 38 | Current stock levels | `product_id`, `location_id`, `lot_id`, `package_id`, `owner_id`, `company_id` |
| `stock_lot.csv` | 4 | Lots / serial numbers | `product_id`, `company_id` |
| `stock_valuation_layer.csv` | 626 | Stock valuation entries | `stock_move_id`, `product_id`, `company_id`, `account_move_id` |
| `account_account.csv` | 51 | Chart of accounts | `currency_id`, `company_id`, `group_id` |
| `account_journal.csv` | 8 | Account journals | `company_id`, `default_account_id`, `currency_id`, `sequence_id` |
| `account_tax.csv` | 2 | Taxes | `company_id`, `cash_basis_transition_account_id` |
| `account_move.csv` | 1366 | Journal entries (invoices, bills, credit notes, refunds) | `journal_id`, `company_id`, `currency_id`, `partner_id`, `commercial_partner_id` |
| `account_move_line.csv` | 4909 | Journal entry lines | `move_id`, `account_id`, `partner_id`, `currency_id`, `tax_line_id`, `tax_group_id`, `company_id` |
| `account_payment.csv` | 620 | Customer/vendor payments | `journal_id`, `company_id`, `currency_id`, `partner_id` |
| `account_payment_register.csv` | 620 | Payment registration wizard records | `journal_id`, `company_id`, `currency_id` |
| `account_payment_method_line.csv` | 4 | Payment method lines | `journal_id`, `payment_method_id` |

## Many-to-many link tables

Odoo creates `_rel` link tables for many-to-many relationships. The following link tables are exported:

- `account_tax_sale_order_line_rel` — `sale_order_line` ↔ `account_tax`
- `account_tax_purchase_order_line_rel` — `purchase_order_line` ↔ `account_tax`
- `product_taxes_rel` — `product_template` ↔ `account_tax`
- `account_tax_fiscal_position_rel` — `account_tax` ↔ `account_fiscal_position`
- `stock_route_product` — `stock_route` ↔ `product_template`

Add more to `export_csv.py` if needed.

## Reporting views / legacy tables

The following objects are not present as database tables/views in the Odoo 18 setup used here (`stock_inventory` was removed in Odoo 18; the reporting views are generated differently; the old `sale_order_line_tax_rel` and `purchase_order_line_tax_rel` names are also not used). The CSV files contain an empty marker row:

- `sale_report.csv`
- `purchase_report.csv`
- `account_invoice_report.csv`
- `stock_inventory.csv`
- `stock_inventory_line.csv`
- `project_project.csv`
- `project_task.csv`
- `website.csv`
- `sale_order_line_tax_rel.csv`
- `purchase_order_line_tax_rel.csv`

## Usage tip

Load the CSVs into Power BI / Excel / pandas and join on the `id` columns. For example:

```sql
SELECT so.name, so.date_order, rp.name AS customer, sol.product_id, pt.name AS product, sol.product_uom_qty, sol.price_unit
FROM sale_order so
JOIN res_partner rp ON so.partner_id = rp.id
JOIN sale_order_line sol ON sol.order_id = so.id
JOIN product_template pt ON sol.product_id = pt.id
```
