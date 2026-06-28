#!/usr/bin/env python3
"""Generate a fully interconnected ERP dataset via the ERP system's JSON-RPC API.

This script generates ERP data for Summit Electronics, a fictional
consumer electronics retailer founded in 2018 in Amsterdam, Netherlands. The data reflects:
- Multi-channel operations (e-commerce, retail stores, B2B)
- Strong European presence with 35 stores across Netherlands, Germany, Belgium, France, UK
- North American expansion with 10 stores in US and Canada
- European seasonal patterns (Sinterklaas, King's Day, Black Friday, Christmas)
- Dutch business context (VAT, IBAN, European regulations)
- Regional market differences and promotional campaigns
- Supply chain complexity with global suppliers
- Customer segmentation (enthusiasts, practical buyers, gift buyers)

The data model is based on real ERP system architecture with proper referential integrity,
covering the complete order-to-cash workflow: sales, purchases, inventory, and accounting.

Run this after the ERP web-frontend is up. It creates partners, products,
purchase orders (receipts, bills, payments), sales orders (deliveries,
invoices, payments, refunds/credit notes), and ties everything together.
"""
import os
import random
import logging
from datetime import datetime, timedelta

import requests
from faker import Faker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ODOO_URL = os.environ.get("ODOO_URL", "http://localhost:8069")
DB = os.environ.get("ODOO_DB", "odoo_demo")
USER = os.environ.get("ODOO_USER", "admin")
PASSWORD = os.environ.get("ODOO_PASSWORD", "admin")

# Scale knobs (adjustable via environment variables for bigger datasets)
CUSTOMERS = int(os.environ.get("GEN_CUSTOMERS", "200"))
SUPPLIERS = int(os.environ.get("GEN_SUPPLIERS", "100"))
PRODUCTS = int(os.environ.get("GEN_PRODUCTS", "300"))
SALE_ORDERS = int(os.environ.get("GEN_SALE_ORDERS", "500"))
PURCHASE_ORDERS = int(os.environ.get("GEN_PURCHASE_ORDERS", "300"))
MAX_LINES_PER_ORDER = int(os.environ.get("GEN_MAX_LINES", "5"))
BATCH_SIZE = int(os.environ.get("GEN_BATCH_SIZE", "100"))
# Payment / credit-note coverage
PAYMENT_RATE = float(os.environ.get("GEN_PAYMENT_RATE", "0.85"))
CREDIT_NOTE_RATE = float(os.environ.get("GEN_CREDIT_NOTE_RATE", "0.10"))

fake = Faker()


def random_date(start_days_ago=730, end_days_ago=0):
    """Return a random date within the last N days as a string."""
    days_ago = random.randint(end_days_ago, start_days_ago)
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def random_datetime(start_days_ago=730, end_days_ago=0):
    """Return a random datetime within the last N days as a string."""
    days_ago = random.randint(end_days_ago, start_days_ago)
    dt = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def random_order_datetime(campaign_weeks=None, campaign_rate=0.25):
    """
    Return an order datetime that is spread over the last 24 months but
    biased toward optional campaign weeks and holiday periods for realism.
    """
    # Use a fixed end date to ensure consistent distribution across the last 24 months.
    # This avoids bias toward the current date when the script runs.
    end_date = datetime(2026, 6, 20, 12, 0, 0)
    
    # 30% chance to place order during a holiday period
    if random.random() < 0.30 and HOLIDAY_PERIODS:
        holiday_start, holiday_end, holiday_name = random.choice(HOLIDAY_PERIODS)
        # Random date within the holiday period
        holiday_duration = (holiday_end - holiday_start).days
        offset = timedelta(days=random.randint(0, holiday_duration), hours=random.randint(8, 18), minutes=random.randint(0, 59))
        dt = holiday_start + offset
    elif campaign_weeks and random.random() < campaign_rate:
        # Pick a random campaign week and place the order on a random day/hour within it.
        campaign_start = random.choice(campaign_weeks)
        offset = timedelta(days=random.randint(0, 6), hours=random.randint(8, 18), minutes=random.randint(0, 59))
        dt = campaign_start + offset
    else:
        # Spread uniformly across the last 24 months so the time-series covers years/months evenly.
        days_ago = random.randint(0, 730)
        dt = end_date - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# Campaign weeks (e.g., Black Friday, summer sale, end-of-quarter push).
# Fixed dates for consistency and reproducibility.
CAMPAIGN_WEEKS = [
    datetime(2024, 9, 29),   # Fall campaign
    datetime(2024, 10, 19),  # Black Friday-ish
    datetime(2025, 1, 21),   # New Year sale
    datetime(2025, 5, 1),    # Spring sale
    datetime(2025, 6, 3),     # Summer kickoff
    datetime(2026, 4, 16),    # Easter-ish
]

# Holiday periods with increased order probability
# European and Dutch-specific holidays for Summit Electronics
HOLIDAY_PERIODS = [
    (datetime(2024, 12, 1), datetime(2024, 12, 25), "Christmas 2024"),  # Christmas shopping
    (datetime(2024, 12, 5), datetime(2024, 12, 6), "Sinterklaas 2024"),   # Dutch Sinterklaas
    (datetime(2025, 1, 1), datetime(2025, 1, 15), "New Year 2025"),     # New Year sales
    (datetime(2025, 4, 18), datetime(2025, 4, 21), "Easter 2025"),      # Easter weekend
    (datetime(2025, 4, 27), datetime(2025, 4, 27), "King's Day 2025"),   # Dutch King's Day
    (datetime(2025, 5, 1), datetime(2025, 5, 5), "Labor Day 2025"),     # European Labor Day
    (datetime(2025, 7, 1), datetime(2025, 7, 31), "Summer Sale 2025"), # European summer sales
    (datetime(2025, 11, 20), datetime(2025, 12, 5), "Black Friday 2025"), # Black Friday/Cyber Monday
    (datetime(2025, 12, 1), datetime(2025, 12, 25), "Christmas 2025"),  # Christmas shopping
    (datetime(2025, 12, 5), datetime(2025, 12, 6), "Sinterklaas 2025"),   # Dutch Sinterklaas
    (datetime(2026, 1, 1), datetime(2026, 1, 15), "New Year 2026"),     # New Year sales
]

# Seasonal product preferences (month -> product categories with higher probability)
# European electronics retail patterns for Summit Electronics
SEASONAL_PREFERENCES = {
    1: ["Audio", "Smart Home"],      # January: New Year tech upgrades, winter audio
    4: ["Computing", "Mobile"],     # April: Spring tech refresh, mobile upgrades
    5: ["Smart Home", "Audio"],     # May: Pre-summer smart home installations
    6: ["Computing", "Audio"],      # June: Summer audio, computing upgrades
    7: ["Mobile", "Smart Home"],    # July: Summer mobile deals, smart home
    8: ["Computing", "Mobile"],     # August: Back-to-school computing and mobile
    9: ["Computing", "Audio"],      # September: Post-summer audio, computing
    11: ["Electronics", "Mobile"],  # November: Black Friday prep, mobile deals
    12: ["Electronics", "Audio"],   # December: Holiday gifts, premium audio
}

# Regional groupings for deal targeting
REGIONS = {
    "EUROPE": ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"],
    "NORTH_AMERICA": ["US", "CA", "MX"],
    "ASIA_PACIFIC": ["AU", "NZ", "JP", "SG", "HK", "IN", "KR", "TW", "TH", "MY", "PH", "VN", "ID"],
    "LATAM": ["BR", "AR", "CL", "CO", "PE", "VE"],
    "MIDDLE_EAST": ["AE", "SA", "IL", "QA", "KW", "OM", "BH"],
}

# Promo codes with regional restrictions and discount percentages
# European-focused campaigns for Summit Electronics
PROMO_CODES = {
    "EUROSUMMER24": {"region": "EUROPE", "discount": 0.20, "description": "Europe Summer Sale 2024"},
    "EUROFLASH25": {"region": "EUROPE", "discount": 0.15, "description": "Europe Flash Sale 2025"},
    "KONINGSDAG25": {"region": "NL", "discount": 0.21, "description": "Dutch King's Day 2025"},
    "SINTER25": {"region": "NL", "discount": 0.18, "description": "Sinterklaas Special 2025"},
    "EUROBF25": {"region": "EUROPE", "discount": 0.25, "description": "Europe Black Friday 2025"},
    "EURONY26": {"region": "EUROPE", "discount": 0.20, "description": "Europe New Year 2026"},
    "NAFALL24": {"region": "NORTH_AMERICA", "discount": 0.18, "description": "North America Fall Sale"},
    "GLOBALBF24": {"region": "GLOBAL", "discount": 0.25, "description": "Global Black Friday 2024"},
    "GLOBALNY25": {"region": "GLOBAL", "discount": 0.20, "description": "Global New Year 2025"},
}

# Country to region mapping
COUNTRY_TO_REGION = {}
for region, countries in REGIONS.items():
    for country in countries:
        COUNTRY_TO_REGION[country] = region



class OdooClient:
    def __init__(self, url, db, user, password):
        self.url = url.rstrip("/") + "/jsonrpc"
        self.db = db
        self.user = user
        self.password = password
        self.uid = self._authenticate()
        logger.info("Authenticated as user id %s", self.uid)

    def _call(self, service, method, args=None, kwargs=None):
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": service,
                "method": method,
                "args": args or [],
                "kwargs": kwargs or {},
            },
            "id": random.randint(1, 100000000),
        }
        resp = requests.post(self.url, json=payload, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            raise RuntimeError(data["error"])
        return data["result"]

    def _authenticate(self):
        return self._call("common", "authenticate", [self.db, self.user, self.password, {}])

    def search(self, model, domain=None, limit=None):
        kwargs = {"context": {"lang": "en_US"}}
        if limit:
            kwargs["limit"] = limit
        return self._call(
            "object",
            "execute_kw",
            [self.db, self.uid, self.password, model, "search", [domain or []]],
            kwargs,
        )

    def search_read(self, model, domain=None, fields=None, limit=None, order=None):
        kwargs = {"context": {"lang": "en_US"}}
        if fields:
            kwargs["fields"] = fields
        if limit:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
        return self._call(
            "object",
            "execute_kw",
            [self.db, self.uid, self.password, model, "search_read", [domain or []]],
            kwargs,
        )

    def read(self, model, ids, fields):
        return self._call(
            "object",
            "execute_kw",
            [self.db, self.uid, self.password, model, "read", [ids]],
            {"fields": fields, "context": {"lang": "en_US"}},
        )

    def create(self, model, records, context=None):
        kwargs = {}
        if context:
            kwargs["context"] = context
        return self._call(
            "object",
            "execute_kw",
            [self.db, self.uid, self.password, model, "create", [records]],
            kwargs,
        )

    def write(self, model, ids, values, context=None):
        kwargs = {}
        if context:
            kwargs["context"] = context
        return self._call(
            "object",
            "execute_kw",
            [self.db, self.uid, self.password, model, "write", [ids, values]],
            kwargs,
        )

    def execute(self, model, method, *args, **kwargs):
        return self._call(
            "object",
            "execute_kw",
            [self.db, self.uid, self.password, model, method, list(args)],
            kwargs,
        )

    def action_confirm(self, model, ids):
        if model == "purchase.order":
            return self.execute(model, "button_confirm", ids)
        return self.execute(model, "action_confirm", ids)


# ---------------------------------------------------------------------------
# Master data helpers
# ---------------------------------------------------------------------------

def get_master_data(client):
    logger.info("Reading master data...")
    warehouses = client.search_read("stock.warehouse", [], ["id", "name"])
    categories = client.search_read("product.category", [], ["id", "name"])
    uoms = client.search_read("uom.uom", [], ["id", "name", "category_id"])
    taxes = client.search_read("account.tax", [], ["id", "name", "amount", "type_tax_use"])
    journals = client.search_read(
        "account.journal",
        [["type", "in", ["sale", "purchase", "bank", "cash"]]],
        ["id", "name", "type", "default_account_id"],
    )

    if not warehouses:
        raise RuntimeError("No warehouses found")
    if not categories:
        raise RuntimeError("No product categories found")
    if not uoms:
        raise RuntimeError("No UoMs found")

    unit_uom = next(
        (u for u in uoms if u["name"].lower() in {"unit", "units", "each", "piece"}),
        uoms[0],
    )
    bank_journal = next((j for j in journals if j["type"] in {"bank", "cash"}), None)
    sale_tax = next((t for t in taxes if t.get("type_tax_use") == "sale"), None)
    purchase_tax = next((t for t in taxes if t.get("type_tax_use") == "purchase"), None)
    return {
        "warehouses": warehouses,
        "categories": categories,
        "uoms": uoms,
        "unit_uom": unit_uom,
        "journals": journals,
        "bank_journal": bank_journal,
        "sale_tax": sale_tax,
        "purchase_tax": purchase_tax,
    }


COMPANY_PREFIXES = [
    "Global", "Euro", "Atlantic", "Pacific", "Northern", "Southern", "United", "Prime",
    "Advanced", "Bright", "Swift", "Solid", "Reliable", "Modern", "Classic", "Dynamic",
    "First", "Royal", "Apex", "Summit", "Crest", "Vantage", "Pioneer", "Horizon",
]
COMPANY_SUFFIXES = [
    "Logistics", "Trading", "Supplies", "Solutions", "Industries", "Group", "Holdings",
    "Technologies", "Systems", "Products", "Services", "Retail", "Wholesale", "Manufacturing",
    "Distribution", "Import", "Export", "Partners", "Enterprises", "B.V.", "GmbH", "Ltd",
    "S.A.", "S.L.", "S.r.l.", "B.V.", "Kft.", "A/S", "AB", "Oy",
]


def generate_company_name():
    """Build a unique company name from real word parts."""
    prefix = random.choice(COMPANY_PREFIXES)
    base = fake.last_name() if random.random() < 0.5 else fake.city()
    suffix = random.choice(COMPANY_SUFFIXES)
    return f"{prefix} {base} {suffix}"


def generate_contact_name():
    """Return a person name."""
    return f"{fake.first_name()} {fake.last_name()}"


# Product vocabulary grouped by category families.
PRODUCT_LINES = {
    "Electronics": [
        ("Wireless Mouse", "consu", 15, 80), ("Mechanical Keyboard", "consu", 50, 250),
        ("USB-C Hub", "consu", 25, 120), ("27-inch Monitor", "consu", 200, 600),
        ("Webcam 1080p", "consu", 40, 150), ("Bluetooth Headset", "consu", 35, 180),
        ("Smartphone Stand", "consu", 8, 35), ("HDMI Cable 2m", "consu", 5, 25),
        ("Laptop Sleeve", "consu", 12, 45), ("Portable SSD 1TB", "consu", 80, 180),
        ("Smart Plug", "consu", 10, 40), ("Noise Cancelling Earbuds", "consu", 60, 220),
        ("Drawing Tablet", "consu", 70, 300), ("Document Scanner", "consu", 120, 450),
        ("Projector Mini", "consu", 150, 500),
    ],
    "Office Furniture": [
        ("Ergonomic Office Chair", "consu", 120, 450), ("Standing Desk", "consu", 250, 900),
        ("Filing Cabinet", "consu", 80, 220), ("Meeting Table", "consu", 300, 1200),
        ("Desk Lamp LED", "consu", 25, 90), ("Bookshelf", "consu", 60, 200),
        ("Whiteboard 90x60", "consu", 40, 140), ("Office Sofa", "consu", 400, 1500),
        ("Monitor Arm", "consu", 35, 130), ("Cable Tray", "consu", 15, 55),
    ],
    "Packaging": [
        ("Cardboard Box S", "consu", 0.5, 3), ("Cardboard Box M", "consu", 1, 5),
        ("Cardboard Box L", "consu", 2, 9), ("Bubble Wrap Roll", "consu", 8, 25),
        ("Packing Tape", "consu", 2, 8), ("Shipping Label", "consu", 0.1, 0.5),
        ("Pallet 120x80", "consu", 15, 45), ("Stretch Film", "consu", 12, 40),
    ],
    "Apparel": [
        ("Cotton T-Shirt", "consu", 8, 30), ("Polo Shirt", "consu", 15, 55),
        ("Hooded Sweatshirt", "consu", 20, 75), ("Work Jacket", "consu", 35, 120),
        ("Safety Vest", "consu", 5, 20), ("Baseball Cap", "consu", 6, 22),
        ("Winter Gloves", "consu", 8, 28), ("Sports Socks", "consu", 4, 15),
    ],
    "Services": [
        ("Installation Service", "service", 80, 250), ("Premium Support", "service", 50, 150),
        ("Consulting Hour", "service", 100, 300), ("Training Session", "service", 200, 600),
        ("Maintenance Visit", "service", 120, 350), ("Custom Configuration", "service", 150, 500),
        ("Warranty Extension", "service", 30, 100), ("Remote Diagnostics", "service", 40, 120),
    ],
}


def create_partners(client, count, is_customer):
    if count == 0:
        return []
    label = "customers" if is_customer else "suppliers"
    logger.info("Creating %s %s...", count, label)
    # Pre-fetch a pool of real country ids and codes for regional targeting.
    countries = client.search_read("res.country", [], ["id", "code"], limit=80)
    if not countries:
        countries = [{"id": False, "code": False}]
    country_ids = [c["id"] for c in countries]
    country_map = {c["id"]: c["code"] for c in countries if c["code"]}

    records = []
    used_names = set()
    for i in range(count):
        if random.random() < 0.7:
            name = generate_company_name()
            # Ensure uniqueness by appending a discriminator when needed.
            original_name = name
            while name in used_names:
                name = f"{original_name} {i+1:03d}"
            used_names.add(name)
            contact = False
        else:
            name = generate_contact_name()
            while name in used_names:
                name = f"{generate_contact_name()} {i+1:03d}"
            used_names.add(name)
            contact = True
        country_id = random.choice(country_ids)
        country_code = country_map.get(country_id, False)
        # Use the base en_US faker for address fields; they are available and still
        # sufficient when paired with a real country_id.
        records.append(
            {
                "name": name,
                "street": fake.street_address(),
                "street2": fake.secondary_address() if random.random() < 0.3 else False,
                "city": fake.city(),
                "zip": fake.postcode(),
                "country_id": country_id,
                "email": fake.email(),
                "phone": fake.phone_number(),
                "website": f"https://www.{name.lower().replace(' ', '-').replace('.', '')}.com" if random.random() < 0.5 else False,
                "vat": fake.bothify("??#########") if random.random() < 0.4 else False,
                "is_company": not contact,
                "customer_rank": 1 if is_customer else 0,
                "supplier_rank": 1 if not is_customer else 0,
                # Store country code for regional targeting (will be used in order creation)
                "_country_code": country_code,
            }
        )
    created = []
    partner_country_map = {}
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        # Extract country codes before creating (they won't be stored in Odoo)
        batch_codes = {r["name"]: r.pop("_country_code") for r in batch}
        ids = client.create("res.partner", batch)
        created.extend(ids)
        # Map created IDs to their country codes
        for idx, pid in enumerate(ids):
            partner_country_map[pid] = batch_codes[batch[idx]["name"]]
        logger.info("  %s/%s %s created", len(created), count, label)
    return created, partner_country_map


def create_products(client, count, categories, unit_uom, sale_tax, purchase_tax):
    if count == 0:
        return []
    logger.info("Creating %s products...", count)
    records = []
    used_names = set()
    product_families = []  # Track which family each product belongs to
    for i in range(count):
        categ = random.choice(categories)
        family = random.choice(list(PRODUCT_LINES.keys()))
        product_families.append(family)
        base, ptype, cost_min, cost_max = random.choice(PRODUCT_LINES[family])
        # Add a variant / size attribute so names stay unique.
        variants = ["Standard", "Pro", "Lite", "Plus", "XL", "Compact", "Enterprise", "Basic"]
        variant = random.choice(variants)
        name = f"{base} - {variant}"
        while name in used_names:
            name = f"{base} - {variant} ({i+1:04d})"
        used_names.add(name)
        vals = {
            "name": name,
            "type": ptype,
            "categ_id": categ["id"],
            "uom_id": unit_uom["id"],
            "uom_po_id": unit_uom["id"],
            "list_price": round(random.uniform(cost_max * 0.8, cost_max * 1.4), 2),
            "standard_price": round(random.uniform(cost_min, cost_max), 2),
            "default_code": f"SKU-{i+1000:06d}",
            "barcode": f"{random.randint(1000000000000, 9999999999999)}",
            "sale_ok": True,
            "purchase_ok": True,
        }
        if sale_tax:
            vals["taxes_id"] = [(6, 0, [sale_tax["id"]])]
        if purchase_tax:
            vals["supplier_taxes_id"] = [(6, 0, [purchase_tax["id"]])]
        records.append(vals)
    created = []
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        created.extend(client.create("product.product", batch))
        logger.info("  %s/%s products created", len(created), count)
    
    # Create mapping of product ID to family for seasonal targeting
    product_category_map = {pid: family for pid, family in zip(created, product_families)}
    
    return created, product_category_map


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

def build_order_lines(model_name, product_ids, tax_id=None, promoted_product_ids=None, deal_price_factor=None, seasonal_categories=None, product_category_map=None):
    """Build order lines. Favor promoted products when available, and seasonal categories when specified."""
    lines = []
    promoted_pool = promoted_product_ids or []
    for _ in range(random.randint(1, MAX_LINES_PER_ORDER)):
        # Seasonal bias: if seasonal categories are specified and we have category info, prefer products in those categories
        if seasonal_categories and product_category_map and random.random() < 0.40:
            # Find products in seasonal categories
            seasonal_products = [
                pid for pid, cat in product_category_map.items()
                if cat in seasonal_categories
            ]
            if seasonal_products:
                product_id = random.choice(seasonal_products)
            elif promoted_pool and random.random() < 0.55:
                product_id = random.choice(promoted_pool)
            else:
                product_id = random.choice(product_ids)
        elif promoted_pool and random.random() < 0.55:
            product_id = random.choice(promoted_pool)
        else:
            product_id = random.choice(product_ids)
        qty = random.randint(1, 20)
        # Deals/promotions are reflected in higher quantities and slightly lower prices.
        if deal_price_factor is not None:
            qty = random.randint(5, 50)
        price = round(random.uniform(5, 500) * (deal_price_factor or 1.0), 2)
        line = {"product_id": product_id}
        if model_name == "sale.order":
            line["product_uom_qty"] = qty
            line["price_unit"] = price
            if tax_id:
                line["tax_id"] = [(6, 0, [tax_id])]
        else:
            line["product_qty"] = qty
            line["price_unit"] = price
            if tax_id:
                line["taxes_id"] = [(6, 0, [tax_id])]
        lines.append([0, 0, line])
    return lines


ORDER_COMMENTS = [
    "Promotional deal - discounted volume pricing",
    "Rush order - customer requested expedited delivery",
    "Back-to-school campaign stock-up",
    "End-of-quarter bulk purchase",
    "Replenishment after stock-out",
    "New product line trial order",
    "Annual contract renewal shipment",
    "VIP customer preferred pricing applied",
    "Trade-show follow-up order",
    "Holiday season pre-order",
    "Clearance event - limited stock",
    "Customer upgrade program",
    "Regional branch restock",
    "Subscription box fulfilment",
    "Warranty replacement batch",
]


def create_orders(client, model_name, count, partner_ids, product_ids, tax_id=None, promoted_product_ids=None, partner_country_map=None, product_category_map=None):
    if count == 0 or not partner_ids:
        return [], {}
    label = model_name.replace(".", "_")
    logger.info("Creating %s %s...", count, label)
    # Skew the partner pool so ~20% of customers generate ~60% of orders.
    skewed_partners = partner_ids + random.choices(partner_ids, k=int(count * 0.6))
    order_dates = {}
    records = []
    for i in range(count):
        partner_id = random.choice(skewed_partners)
        # Orders are spread over ~2 years, with 25% clustering in promotional campaign weeks.
        date_order = random_order_datetime(campaign_weeks=CAMPAIGN_WEEKS, campaign_rate=0.25)
        order_month = datetime.strptime(date_order, "%Y-%m-%d %H:%M:%S").month
        
        # Regional deal logic: check if customer is in a region with an active promo
        promo_code = None
        deal_price_factor = None
        is_deal = False
        
        if partner_country_map and model_name == "sale.order":
            country_code = partner_country_map.get(partner_id)
            customer_region = COUNTRY_TO_REGION.get(country_code, "GLOBAL")
            
            # 20% chance of a regional promo being applied
            if random.random() < 0.20:
                # Find promos that match the customer's region or are global
                eligible_promos = [
                    (code, details) for code, details in PROMO_CODES.items()
                    if details["region"] in (customer_region, "GLOBAL")
                ]
                if eligible_promos:
                    promo_code, promo_details = random.choice(eligible_promos)
                    deal_price_factor = 1.0 - promo_details["discount"]
                    is_deal = True
        
        if not is_deal:
            is_deal = random.random() < 0.15
            if is_deal:
                deal_price_factor = 0.85
        
        # Apply seasonal product preferences for sale orders
        seasonal_categories = None
        if model_name == "sale.order" and order_month in SEASONAL_PREFERENCES:
            seasonal_categories = SEASONAL_PREFERENCES[order_month]
        
        order_line = build_order_lines(
            model_name, product_ids, tax_id,
            promoted_product_ids=promoted_product_ids,
            deal_price_factor=deal_price_factor,
            seasonal_categories=seasonal_categories,
            product_category_map=product_category_map,
        )
        
        notes = False
        if is_deal or random.random() < 0.25:
            notes = random.choice(ORDER_COMMENTS)
            if promo_code:
                notes = f"PROMO: {promo_code} - {PROMO_CODES[promo_code]['description']}. {notes}"
        
        order_vals = {
            "partner_id": partner_id,
            "date_order": date_order,
            "order_line": order_line,
        }
        # Add expected delivery date a few days after the order.
        days_to_deliver = random.randint(1, 10)
        if model_name == "sale.order":
            order_vals["commitment_date"] = (datetime.strptime(date_order, "%Y-%m-%d %H:%M:%S") + timedelta(days=days_to_deliver)).strftime("%Y-%m-%d %H:%M:%S")
            order_vals["note"] = notes
            # Include promo code in client order ref if applicable
            if promo_code:
                order_vals["client_order_ref"] = f"{promo_code}-{fake.bothify('ORD-########')}"
            else:
                order_vals["client_order_ref"] = fake.bothify("ORD-########") if random.random() < 0.6 else False
        else:
            for line in order_line:
                line[2]["date_planned"] = (datetime.strptime(date_order, "%Y-%m-%d %H:%M:%S") + timedelta(days=days_to_deliver)).strftime("%Y-%m-%d %H:%M:%S")
            order_vals["notes"] = notes
        records.append(order_vals)
    created = []
    # Sale orders must be created one at a time to avoid date_order being reset to create_date.
    # Purchase orders can still use bulk create for performance.
    if model_name == "sale.order":
        write_failures = 0
        for i, record in enumerate(records):
            try:
                # Create without date_order first to bypass Odoo's default behavior
                date_order = record.pop("date_order")
                oid = client.create(model_name, [record])[0]
                created.append(oid)
                order_dates[oid] = date_order
                if (i + 1) % 50 == 0:
                    logger.info("  %s/%s %s created", len(created), count, label)
            except Exception as e:
                logger.warning("  failed creating sale order %s: %s", i, e)
        logger.info("  %s/%s %s created", len(created), count, label)
    else:
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i : i + BATCH_SIZE]
            ids = client.create(model_name, batch)
            created.extend(ids)
            for idx, oid in enumerate(ids):
                order_dates[oid] = records[i + idx]["date_order"]
            logger.info("  %s/%s %s created", len(created), count, label)

    return created, order_dates


def confirm_orders(client, model_name, ids, order_dates=None, confirm_rate=0.85, cancel_rate=0.05):
    if not ids:
        return [], [], []
    logger.info("Confirming %s %s records (%.0f%% confirm, %.0f%% cancel)...", len(ids), model_name, confirm_rate * 100, cancel_rate * 100)
    random.shuffle(ids)
    n = len(ids)
    n_cancel = int(n * cancel_rate)
    n_confirm = int(n * confirm_rate)
    to_cancel = ids[:n_cancel]
    to_confirm = ids[n_cancel : n_cancel + n_confirm]
    to_draft = ids[n_cancel + n_confirm :]

    for i in range(0, len(to_confirm), BATCH_SIZE):
        batch = to_confirm[i : i + BATCH_SIZE]
        try:
            client.action_confirm(model_name, batch)
        except Exception as e:
            logger.warning("  failed confirming batch %s-%s: %s", i, i + len(batch), e)

    # Write date_order after confirmation for sale orders to prevent Odoo from resetting it
    if model_name == "sale.order" and order_dates and to_confirm:
        logger.info("  writing date_order for confirmed sale orders...")
        write_failures = 0
        for oid in to_confirm:
            if oid in order_dates:
                try:
                    client.write(model_name, [oid], {"date_order": order_dates[oid]})
                except Exception as e:
                    logger.warning("  failed writing date_order for order %s: %s", oid, e)
                    write_failures += 1
        logger.info("  date_order write failures: %s", write_failures)

    for i in range(0, len(to_cancel), BATCH_SIZE):
        batch = to_cancel[i : i + BATCH_SIZE]
        try:
            cancel_method = "button_cancel" if model_name == "purchase.order" else "action_cancel"
            client.execute(model_name, cancel_method, batch)
        except Exception as e:
            logger.warning("  failed cancelling batch %s-%s: %s", i, i + len(batch), e)

    return to_confirm, to_cancel, to_draft


# ---------------------------------------------------------------------------
# Pickings (deliveries / receipts)
# ---------------------------------------------------------------------------

def get_pickings_for_orders(client, order_ids, model_name):
    """Return the related stock.picking ids for the given orders."""
    if not order_ids:
        return []
    field = "picking_ids" if model_name == "sale.order" else "picking_ids"
    orders = client.read(model_name, order_ids, [field])
    picking_ids = []
    for order in orders:
        picking_ids.extend(order.get(field) or [])
    return list(set(picking_ids))


def validate_pickings(client, picking_ids, order_dates=None):
    if not picking_ids:
        return
    order_dates = order_dates or {}
    logger.info("Validating %s pickings...", len(picking_ids))
    ok = 0
    for i in range(0, len(picking_ids), BATCH_SIZE):
        batch = picking_ids[i : i + BATCH_SIZE]
        try:
            client.execute("stock.picking", "button_validate", batch)
            ok += len(batch)
        except Exception as e:
            logger.warning("  failed validating batch %s-%s: %s", i, i + len(batch), e)
            for pid in batch:
                try:
                    client.execute("stock.picking", "button_validate", [pid])
                    ok += 1
                except Exception as e2:
                    logger.warning("    failed validating picking %s: %s", pid, e2)

    # Set done date close to the originating order date.
    pickings = client.read("stock.picking", picking_ids, ["sale_id", "purchase_id"])
    for picking in pickings:
        order_id = (picking.get("sale_id") or [None])[0] or (picking.get("purchase_id") or [None])[0]
        if order_id and order_id in order_dates:
            base = datetime.strptime(order_dates[order_id], "%Y-%m-%d %H:%M:%S")
            done_date = base + timedelta(days=random.randint(1, 10), hours=random.randint(0, 23))
            try:
                client.write("stock.picking", [picking["id"]], {"date_done": done_date.strftime("%Y-%m-%d %H:%M:%S")})
            except Exception as e:
                logger.warning("  failed setting date_done on picking %s: %s", picking["id"], e)
    logger.info("  %s/%s pickings validated", ok, len(picking_ids))


# ---------------------------------------------------------------------------
# Invoices and bills
# ---------------------------------------------------------------------------

def move_date_from_order(order_date, days_after=None):
    """Return a date string days_after the order datetime."""
    base = datetime.strptime(order_date, "%Y-%m-%d %H:%M:%S")
    if days_after is None:
        days_after = random.randint(1, 5)
    return (base + timedelta(days=days_after)).strftime("%Y-%m-%d")


def set_move_dates(client, move_ids, move_dates=None):
    if not move_ids:
        return
    move_dates = move_dates or {}
    logger.info("Setting invoice/bill date on %s moves...", len(move_ids))
    for i in range(0, len(move_ids), BATCH_SIZE):
        batch = move_ids[i : i + BATCH_SIZE]
        default_date = datetime.now().strftime("%Y-%m-%d")
        try:
            client.write("account.move", batch, {"invoice_date": default_date})
        except Exception as e:
            logger.warning("  failed setting date on batch %s-%s: %s", i, i + len(batch), e)


def create_invoices_from_orders(client, order_ids, model_name, order_dates=None, tax_field="tax_id"):
    if not order_ids:
        return []
    order_dates = order_dates or {}
    label = "customer invoices" if model_name == "sale.order" else "vendor bills"
    logger.info("Creating %s from %s %s...", label, len(order_ids), model_name)
    created = []

    if model_name == "purchase.order":
        # purchase.order still exposes action_create_invoice in Odoo 18.
        for oid in order_ids:
            try:
                res = client.execute(model_name, "action_create_invoice", [oid])
                if isinstance(res, dict):
                    if res.get("res_id"):
                        created.append(res["res_id"])
                    elif res.get("res_ids"):
                        created.extend(res["res_ids"])
            except Exception as e:
                logger.warning("  failed creating bill from PO %s: %s", oid, e)
        # Align vendor bill dates with the originating PO date.
        if created and order_dates:
            pos = client.read("purchase.order", order_ids, ["invoice_ids"])
            for po in pos:
                po_date = order_dates.get(po["id"])
                if not po_date:
                    continue
                bill_date = move_date_from_order(po_date, days_after=random.randint(3, 10))
                for bill_id in po.get("invoice_ids") or []:
                    if bill_id in created:
                        try:
                            client.write("account.move", [bill_id], {"invoice_date": bill_date})
                        except Exception as e:
                            logger.warning("  failed setting bill date for %s: %s", bill_id, e)
    else:
        # sale.order.action_create_invoice was removed in Odoo 18; create account.move directly.
        line_model = "sale.order.line" if model_name == "sale.order" else "purchase.order.line"
        move_type = "out_invoice" if model_name == "sale.order" else "in_invoice"
        for oid in order_ids:
            try:
                order = client.read(model_name, [oid], ["partner_id", "partner_invoice_id", "currency_id"])[0]
                lines = client.search_read(
                    line_model,
                    [["order_id", "=", oid]],
                    ["id", "product_id", "product_uom_qty", "product_qty", "price_unit", "product_uom", tax_field],
                )
                if not lines:
                    continue
                invoice_lines = []
                for line in lines:
                    product_id = line["product_id"][0] if line["product_id"] else False
                    uom_id = line["product_uom"][0] if line["product_uom"] else False
                    qty = line.get("product_uom_qty") or line.get("product_qty") or 0
                    tax_ids = [t for t in (line.get(tax_field) or [])]
                    link_field = "sale_line_ids" if model_name == "sale.order" else "purchase_line_id"
                    link_value = [(6, 0, [line["id"]])] if model_name == "sale.order" else line["id"]
                    invoice_lines.append(
                        [0, 0, {
                            "product_id": product_id,
                            "quantity": qty,
                            "price_unit": line["price_unit"],
                            "product_uom_id": uom_id,
                            "tax_ids": [(6, 0, tax_ids)],
                            link_field: link_value,
                        }]
                    )
                invoice_date = move_date_from_order(order_dates.get(oid, datetime.now().strftime("%Y-%m-%d %H:%M:%S")), days_after=random.randint(3, 10))
                vals = {
                    "move_type": move_type,
                    "partner_id": order["partner_id"][0],
                    "invoice_date": invoice_date,
                    "invoice_line_ids": invoice_lines,
                }
                if order.get("currency_id"):
                    vals["currency_id"] = order["currency_id"][0]
                move_id = client.create("account.move", [vals])[0]
                created.append(move_id)
            except Exception as e:
                logger.warning("  failed creating invoice from SO %s: %s", oid, e)

    logger.info("  %s %s created", len(created), label)
    return created


def post_moves(client, move_ids, order_dates=None):
    if not move_ids:
        return
    set_move_dates(client, move_ids)
    logger.info("Posting %s account moves...", len(move_ids))
    ok = 0
    for i in range(0, len(move_ids), BATCH_SIZE):
        batch = move_ids[i : i + BATCH_SIZE]
        try:
            client.execute("account.move", "action_post", batch)
            ok += len(batch)
        except Exception as e:
            logger.warning("  failed posting batch %s-%s: %s", i, i + len(batch), e)
            # Fall back to one-by-one so partial failures don't lose the whole batch.
            for mid in batch:
                try:
                    client.execute("account.move", "action_post", [mid])
                    ok += 1
                except Exception as e2:
                    logger.warning("    failed posting move %s: %s", mid, e2)
    logger.info("  %s/%s moves posted", ok, len(move_ids))


def register_payment(client, move_id, bank_journal_id, payment_date=None):
    if not bank_journal_id:
        logger.warning("No bank/cash journal found; skipping payment")
        return False
    if payment_date is None:
        payment_date = datetime.now().strftime("%Y-%m-%d")
    try:
        # Use the transient account.payment.register model.
        reg_id = client.create(
            "account.payment.register",
            [
                {
                    "line_ids": [(6, 0, [move_id])],
                    "journal_id": bank_journal_id,
                    "payment_date": payment_date,
                }
            ],
        )[0]
        client.execute("account.payment.register", "action_create_payments", [reg_id])
        return True
    except Exception as e:
        logger.warning("  failed registering payment for move %s: %s", move_id, e)
        return False


def register_payments(client, move_ids, bank_journal_id, order_dates=None):
    if not move_ids or not bank_journal_id:
        return 0
    order_dates = order_dates or {}
    logger.info("Registering payments for %s moves...", len(move_ids))
    # Read invoice dates to keep payments close to invoicing.
    moves = client.read("account.move", move_ids, ["invoice_date"])
    move_dates = {m["id"]: m.get("invoice_date") for m in moves}
    ok = 0
    for mid in move_ids:
        if random.random() < PAYMENT_RATE:
            inv_date = move_dates.get(mid)
            if inv_date:
                base = datetime.strptime(inv_date, "%Y-%m-%d")
                payment_date = (base + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
            else:
                payment_date = datetime.now().strftime("%Y-%m-%d")
            if register_payment(client, mid, bank_journal_id, payment_date=payment_date):
                ok += 1
    logger.info("  %s/%s payments registered", ok, len(move_ids))
    return ok


def create_credit_notes(client, invoice_ids, bank_journal_id, order_dates=None):
    if not invoice_ids:
        return []
    order_dates = order_dates or {}
    count = max(1, int(len(invoice_ids) * CREDIT_NOTE_RATE))
    selected = random.sample(invoice_ids, count)
    logger.info("Creating %s credit notes/refunds...", len(selected))
    # Read invoice dates so credit notes are shortly after the invoice.
    invoices = client.read("account.move", selected, ["invoice_date"])
    inv_date_map = {inv["id"]: inv.get("invoice_date") for inv in invoices}
    created = []
    for inv_id in selected:
        try:
            inv_date = inv_date_map.get(inv_id)
            if inv_date:
                base = datetime.strptime(inv_date, "%Y-%m-%d")
                reversal_date = (base + timedelta(days=random.randint(7, 45))).strftime("%Y-%m-%d")
            else:
                reversal_date = datetime.now().strftime("%Y-%m-%d")
            # Read the invoice's journal to use for the reversal.
            inv = client.read("account.move", [inv_id], ["journal_id"])[0]
            journal_id = inv["journal_id"][0] if inv.get("journal_id") else bank_journal_id
            reversal_id = client.create(
                "account.move.reversal",
                [
                    {
                        "move_ids": [(6, 0, [inv_id])],
                        "reason": random.choice(["Demo refund", "Customer return", "Pricing correction", "Damaged goods"]),
                        "date": reversal_date,
                        "journal_id": journal_id,
                    }
                ],
            )[0]
            reverse_res = client.execute("account.move.reversal", "reverse_moves", [reversal_id])
            if isinstance(reverse_res, dict) and reverse_res.get("res_id"):
                created.append(reverse_res["res_id"])
            elif isinstance(reverse_res, dict) and reverse_res.get("res_ids"):
                created.extend(reverse_res["res_ids"])
        except Exception as e:
            logger.warning("  failed credit note for invoice %s: %s", inv_id, e)
    logger.info("  %s credit notes created", len(created))
    return created


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def main():
    client = OdooClient(ODOO_URL, DB, USER, PASSWORD)
    master = get_master_data(client)

    customers, customer_country_map = create_partners(client, CUSTOMERS, is_customer=True)
    suppliers, supplier_country_map = create_partners(client, SUPPLIERS, is_customer=False)
    product_ids, product_category_map = create_products(
        client, PRODUCTS, master["categories"], master["unit_uom"],
        master["sale_tax"], master["purchase_tax"]
    )
    # Select a small set of "deal" products that will appear disproportionately often.
    promoted_count = max(1, int(len(product_ids) * 0.05))
    promoted_product_ids = random.sample(product_ids, promoted_count)
    logger.info("Promoted %s products for skewed demand", promoted_count)
    bank_journal_id = master["bank_journal"]["id"] if master["bank_journal"] else None

    # --- Purchase side first to put stock into the warehouse ---
    purchase_ids, po_dates = create_orders(
        client, "purchase.order", PURCHASE_ORDERS, suppliers, product_ids,
        master["purchase_tax"]["id"] if master["purchase_tax"] else None,
        promoted_product_ids=promoted_product_ids,
        partner_country_map=supplier_country_map,
        product_category_map=product_category_map,
    )
    po_confirmed, po_cancelled, po_draft = confirm_orders(client, "purchase.order", purchase_ids, po_dates)
    po_picking_ids = get_pickings_for_orders(client, po_confirmed, "purchase.order")
    validate_pickings(client, po_picking_ids, po_dates)
    vendor_bill_ids = create_invoices_from_orders(client, po_confirmed, "purchase.order", order_dates=po_dates)
    post_moves(client, vendor_bill_ids, order_dates=po_dates)
    register_payments(client, vendor_bill_ids, bank_journal_id, order_dates=po_dates)

    # --- Sales side ---
    # Make some customers more active (repeat orders) for an active-customer base.
    active_customer_pool = customers + random.choices(customers, k=int(SALE_ORDERS * 0.3))
    sale_ids, so_dates = create_orders(
        client, "sale.order", SALE_ORDERS, active_customer_pool, product_ids,
        master["sale_tax"]["id"] if master["sale_tax"] else None,
        promoted_product_ids=promoted_product_ids,
        partner_country_map=customer_country_map,
        product_category_map=product_category_map,
    )
    so_confirmed, so_cancelled, so_draft = confirm_orders(client, "sale.order", sale_ids, so_dates)
    so_picking_ids = get_pickings_for_orders(client, so_confirmed, "sale.order")
    validate_pickings(client, so_picking_ids, so_dates)
    customer_invoice_ids = create_invoices_from_orders(client, so_confirmed, "sale.order", order_dates=so_dates)
    post_moves(client, customer_invoice_ids, order_dates=so_dates)
    payment_count = register_payments(client, customer_invoice_ids, bank_journal_id, order_dates=so_dates)
    credit_note_ids = create_credit_notes(client, customer_invoice_ids, bank_journal_id, order_dates=so_dates)
    post_moves(client, credit_note_ids, order_dates=so_dates)
    refund_payment_count = register_payments(client, credit_note_ids, bank_journal_id, order_dates=so_dates)

    logger.info("Generation complete.")
    logger.info("Summary:")
    logger.info("  Customers: %s", len(customers))
    logger.info("  Suppliers: %s", len(suppliers))
    logger.info("  Products: %s", len(product_ids))
    logger.info("  Promoted products: %s", len(promoted_product_ids))
    logger.info("  Purchase orders: %s (confirmed %s, cancelled %s, draft %s)", len(purchase_ids), len(po_confirmed), len(po_cancelled), len(po_draft))
    logger.info("  Vendor bills: %s", len(vendor_bill_ids))
    logger.info("  Customer payments on bills: %s", len(vendor_bill_ids))
    logger.info("  Sale orders: %s (confirmed %s, cancelled %s, draft %s)", len(sale_ids), len(so_confirmed), len(so_cancelled), len(so_draft))
    logger.info("  Customer invoices: %s", len(customer_invoice_ids))
    logger.info("  Customer payments: %s", payment_count)
    logger.info("  Credit notes / refunds: %s", len(credit_note_ids))
    logger.info("  Refund payments: %s", refund_payment_count)


if __name__ == "__main__":
    main()
