# Power BI Guide - Loading Summit Demo DB

This guide provides step-by-step instructions for loading the Summit Demo DB dataset into Power BI, from basic CSV import to advanced data modeling.

## Method 1: CSV Files (Easiest)

### Step 1: Download the Release

1. Go to https://github.com/Riktastic/SummitDemoDB/releases
2. Download the latest `odoo_demo_csv_YYYY.MM.DD.zip`
3. Extract to a folder (e.g., `C:\Data\SummitDemoDB\`)

### Step 2: Import CSV Files into Power BI

**Option A: Import All Tables at Once**

1. Open Power BI Desktop
2. Click **Get Data** → **Text/CSV**
3. Navigate to your extracted folder
4. Select the first CSV file (e.g., `sale_order.csv`)
5. Click **Load**
6. Repeat for each table you need

**Option B: Import via Folder (Power BI Pro/Premium)**

1. Click **Get Data** → **Folder**
2. Select the folder containing CSV files
3. Power BI will detect all CSV files
4. Click **Transform Data** to clean up if needed
5. Click **Close & Apply**

### Step 3: Create Relationships

1. In Power BI Desktop, click **Model View** (left sidebar)
2. Drag from a foreign key column to its related table
3. Example relationships:
   - `sale_order[partner_id]` → `res_partner[id]`
   - `sale_order_line[order_id]` → `sale_order[id]`
   - `sale_order_line[product_id]` → `product_product[id]`

### Step 4: Create Visualizations

**Total Revenue**
```
Total Revenue = SUM(sale_order[amount_total])
```

**Revenue by Customer**
```
Revenue by Customer = 
CALCULATE(
    [Total Revenue],
    USERELATIONSHIP(sale_order[partner_id], res_partner[id])
)
```

**Monthly Sales Trend**
```
Monthly Sales = 
CALCULATE(
    [Total Revenue],
    DATEADD('sale_order'[date_order], 0, MONTH)
)
```

## Method 2: SQLite Database

### Step 1: Download the Release

1. Go to https://github.com/Riktastic/SummitDemoDB/releases
2. Download the latest `odoo_demo_YYYY.MM.DD.sqlite`

### Step 2: Import SQLite into Power BI

1. Open Power BI Desktop
2. Click **Get Data** → **Database** → **SQLite database**
3. Browse to the `.sqlite` file
4. Power BI will show available tables
5. Select the tables you want (use Ctrl+Click for multiple)
6. Click **Load**

**Note**: Power BI automatically detects relationships in SQLite databases.

### Step 3: Verify Relationships

1. Click **Model View**
2. Check that relationships are correctly detected
3. Adjust cardinality if needed (usually 1:many)

## Method 3: Direct PostgreSQL Connection

### Step 1: Start the Database

```bash
cd /path/to/SummitDemoDB
docker-compose up -d database
```

### Step 2: Import PostgreSQL into Power BI

1. Open Power BI Desktop
2. Click **Get Data** → **Database** → **PostgreSQL database**
3. Enter connection details:
   - **Server**: `localhost`
   - **Database**: `odoo_demo`
4. Click **Advanced options** if needed
5. Enter credentials:
   - **User name**: `odoo`
   - **Password**: `odoo`
6. Click **Connect**
7. Select tables from the navigator
8. Click **Load**

### Step 3: Set Refresh Options

1. In Power BI Desktop, click **Transform Data**
2. Right-click the query → **Advanced options**
3. Set refresh options as needed
4. Click **Close & Apply**

## Data Model Best Practices

### Star Schema Approach

Create a star schema for optimal performance:

**Fact Tables (Transaction Data)**
- `sale_order` - Sales orders
- `sale_order_line` - Order line items
- `purchase_order` - Purchase orders
- `purchase_order_line` - Purchase line items
- `stock_move` - Inventory movements
- `account_move` - Accounting entries

**Dimension Tables (Reference Data)**
- `res_partner` - Customers and suppliers
- `product_product` - Products
- `product_category` - Product categories
- `stock_warehouse` - Warehouses
- `account_journal` - Accounting journals

### Recommended Relationships

```
res_partner (Dimension)
    ├── sale_order (Fact)
    │   └── sale_order_line (Fact)
    ├── purchase_order (Fact)
    │   └── purchase_order_line (Fact)
    └── account_move (Fact)

product_product (Dimension)
    ├── sale_order_line (Fact)
    ├── purchase_order_line (Fact)
    └── stock_move (Fact)

stock_warehouse (Dimension)
    └── stock_picking (Fact)
        └── stock_move (Fact)
```

## Common Power BI DAX Measures

### Sales Analysis

```dax
// Total Revenue
Total Revenue = SUM(sale_order[amount_total])

// Total Orders
Total Orders = COUNT(sale_order[id])

// Average Order Value
Avg Order Value = DIVIDE([Total Revenue], [Total Orders])

// Revenue Year to Date
Revenue YTD = 
CALCULATE(
    [Total Revenue],
    DATESYTD('sale_order'[date_order])
)

// Revenue Previous Year
Revenue PY = 
CALCULATE(
    [Total Revenue],
    SAMEPERIODLASTYEAR('sale_order'[date_order])
)

// Year Over Year Growth
YoY Growth % = 
DIVIDE(
    [Total Revenue] - [Revenue PY],
    [Revenue PY],
    0
)
```

### Customer Analysis

```dax
// Total Customers
Total Customers = DISTINCTCOUNT(sale_order[partner_id])

// Top 10 Customers by Revenue
Top 10 Customers Revenue = 
CALCULATE(
    [Total Revenue],
    TOPN(10, VALUES(res_partner[name]), [Total Revenue], DESC)
)

// Customer Segmentation
Customer Segment = 
SWITCH(
    TRUE(),
    [Total Revenue] > 10000, "High Value",
    [Total Revenue] > 5000, "Medium Value",
    "Low Value"
)
```

### Product Analysis

```dax
// Total Products Sold
Total Products Sold = DISTINCTCOUNT(sale_order_line[product_id])

// Top Selling Products
Top Products Revenue = 
CALCULATE(
    SUM(sale_order_line[price_subtotal]),
    TOPN(10, VALUES(product_product[name]), SUM(sale_order_line[price_subtotal]), DESC)
)

// Product Category Revenue
Category Revenue = 
CALCULATE(
    [Total Revenue],
    USERELATIONSHIP(product_product[product_tmpl_id], product_template[id])
)
```

## Creating a Sales Dashboard

### Step 1: Create Measures

Add these measures to your `sale_order` table:

```dax
Total Revenue = SUM(sale_order[amount_total])
Total Orders = COUNT(sale_order[id])
Avg Order Value = DIVIDE([Total Revenue], [Total Orders])
```

### Step 2: Create Visuals

**Card Visuals**
- Total Revenue
- Total Orders
- Average Order Value

**Line Chart**
- X-axis: `sale_order[date_order]` (Month)
- Y-axis: Total Revenue
- Legend: None

**Bar Chart**
- X-axis: `res_partner[name]` (Top 10)
- Y-axis: Total Revenue
- Sort by: Total Revenue (descending)

**Table**
- Columns: Customer Name, Order Date, Order Amount, State
- Sort by: Order Date (descending)

### Step 3: Add Slicers

**Date Slicer**
- Field: `sale_order[date_order]`
- Type: Between

**Customer Slicer**
- Field: `res_partner[name]`
- Type: List

**Product Category Slicer**
- Field: `product_category[name]`
- Type: Dropdown

## Advanced: Power Query Transformations

### Clean Date Columns

```
1. In Power Query Editor, select the date column
2. Right-click → Change Type → Date
3. For datetime columns: Change Type → Date/Time
4. Right-click → Add Column → Date → Year
5. Right-click → Add Column → Date → Month
6. Right-click → Add Column → Date → Month Name
```

### Handle Null Values

```
1. Select the column
2. Right-click → Replace Values
3. Value to find: null
4. Replace with: 0 (for numeric) or "Unknown" (for text)
```

### Create Calculated Columns

```
// Order Status Category
Order Status Category = 
IF(
    sale_order[state] = "sale" || sale_order[state] = "done",
    "Completed",
    IF(
        sale_order[state] = "cancel",
        "Cancelled",
        "In Progress"
    )
)

// Revenue Category
Revenue Category = 
IF(
    sale_order[amount_total] > 1000,
    "High",
    IF(
        sale_order[amount_total] > 500,
        "Medium",
        "Low"
    )
)
```

## Publishing to Power BI Service

### Step 1: Save Report

1. In Power BI Desktop, click **File** → **Save**
2. Save as `.pbix` file

### Step 2: Publish

1. Click **Publish** in the Home ribbon
2. Select your workspace
3. Click **Select**
4. Wait for upload to complete

### Step 3: Configure Refresh

1. Go to https://app.powerbi.com
2. Open your workspace
3. Click the dataset → Settings
4. Configure refresh schedule
5. For CSV/SQLite: Upload new files manually
6. For PostgreSQL: Configure gateway for automatic refresh

## Troubleshooting

### Issue: Relationships Not Detected

**Solution**: Manually create relationships in Model View:
1. Click Model View
2. Drag from foreign key to primary key
3. Set cardinality (usually 1:many)
4. Set cross filter direction (single or both)

### Issue: Slow Performance

**Solutions**:
1. Use Star Schema instead of snowflake
2. Reduce number of loaded columns
3. Use calculated measures instead of calculated columns
4. Enable incremental refresh for large datasets
5. Use Composite Models for very large datasets

### Issue: Date Format Issues

**Solution**:
1. In Power Query, change column type to Date
2. Use Locale settings if needed
3. For European dates (DD/MM/YYYY), set locale to appropriate region

### Issue: Memory Issues

**Solutions**:
1. Load only necessary tables
2. Filter data at source (Power Query)
3. Use DirectQuery instead of Import for large datasets
4. Enable Data Reduction settings

## Sample Dashboard Layout

```
┌─────────────────────────────────────────────────┐
│  Summit Electronics - Sales Dashboard          │
├─────────────────────────────────────────────────┤
│  [Total Revenue]  [Total Orders]  [Avg Order]  │
├──────────────────┬──────────────────────────────┤
│  Date Slicer     │  Revenue Trend (Line Chart)  │
│  (Top)           │                              │
│                  │                              │
│  Customer Slicer│  Top Customers (Bar Chart)   │
│  (Left)          │                              │
│                  │                              │
│  Category Slicer│  Product Performance (Table) │
│  (Left)          │                              │
└──────────────────┴──────────────────────────────┘
```

## Next Steps

1. **Import the data** using your preferred method
2. **Create relationships** in the data model
3. **Build measures** for key metrics
4. **Create visualizations** for your analysis
5. **Publish** to Power BI Service for sharing
6. **Set up refresh** for ongoing updates

## Additional Resources

- [Power BI Documentation](https://docs.microsoft.com/power-bi/)
- [DAX Reference](https://docs.microsoft.com/dax/)
- [Power Query M Reference](https://docs.microsoft.com/powerquery-m/)
- [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) - General technical guide
- [COMPANY_STORY.md](COMPANY_STORY.md) - Company context for analysis
