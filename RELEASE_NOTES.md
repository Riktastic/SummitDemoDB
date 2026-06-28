# Release Notes

## v1.0.0 - June 28, 2026

### Initial Release

First release of Summit Demo DB - an ERP dataset based on real system architecture.

### What's Included

**Dataset**
- 21 interconnected tables covering the complete order-to-cash workflow
- 200 customers, 100 suppliers, 300 products
- 500 sales orders, 300 purchase orders
- Data spanning January 2023 - December 2024
- European and North American business context (Summit Electronics)

**Export Formats**
- CSV files (all tables)
- SQLite database
- PostgreSQL SQL file
- Microsoft SQL Server SQL file
- MariaDB/MySQL SQL file

**Documentation**
- COMPANY_STORY.md - Complete company profile and business context
- TECHNICAL_GUIDE.md - Technical setup and usage guide
- Interactive ERD visualization (GitHub Pages)
- Database schema documentation

### Key Features

- **Business Data**: Seasonal patterns, regional differences, promotional campaigns
- **Proper Referential Integrity**: All foreign keys validated
- **Multi-Format Support**: Works with CSV, SQLite, PostgreSQL, MSSQL, MariaDB
- **Docker-Based Generation**: Easy to regenerate with custom parameters
- **BI Tool Ready**: Compatible with Power BI, Tableau, Excel, and more

### Company Context

The dataset represents Summit Electronics, a fictional consumer electronics retailer:
- Founded 2018 in Amsterdam, Netherlands
- 35 stores across Europe (Netherlands, Germany, Belgium, France, UK)
- 10 stores in North America (US, Canada)
- €50M annual revenue (2024)
- Multi-channel operations: E-commerce (65%), Retail (25%), B2B (10%)

### Data Model

The dataset follows standard ERP patterns:
- Sales orders and order lines
- Purchase orders and order lines
- Inventory management (stock pickings, moves, warehouses)
- Accounting (journal entries, payments, taxes)
- Master data (customers, suppliers, products, categories)

### Installation

**Quick Start**
```bash
./run-all.sh
```

**Download Release**
Get the latest release from: https://github.com/Riktastic/SummitDemoDB/releases

### Technical Details

- Based on real ERP system architecture
- PostgreSQL 16 backend
- Generated via Python with Faker library
- European seasonal patterns (Sinterklaas, King's Day, Black Friday)
- Dutch business context (VAT, IBAN, European regulations)

### Known Limitations

- First release - may have edge cases in data generation
- Default scale: 200 customers, 100 suppliers, 300 products (configurable)
- Data generation requires Docker (10-15 minutes initial setup)

### Future Enhancements

- Larger default dataset options
- Additional industry templates
- More geographic regions
- Extended time periods

### Credits

Created by Rik - https://rik.blue

### License

MIT License - See LICENSE file for details
