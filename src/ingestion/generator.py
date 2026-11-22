"""Deterministic Canonical Retail Data Generator.

Generates realistic, reproducible synthetic retail records across 10 entities
for the Walmart Retail Intelligence platform.
"""

from datetime import date, datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import json
import hashlib
from src.utils.logger import logger
from src.utils.config import app_config


class RetailDataGenerator:
    """Generates synthetic canonical retail data adhering to the warehouse model."""

    def __init__(self, mode: str = "small", random_seed: int = 42):
        self.mode = mode
        self.seed = random_seed
        self.np_random = np.random.default_rng(random_seed)

        mode_cfg = app_config.settings.get("modes", {}).get(mode, {})
        if not mode_cfg:
            raise ValueError(f"Unknown dataset mode: {mode}")
        self.target_transactions = mode_cfg.get("transactions", 25000)
        self.num_stores = mode_cfg.get("stores", 10)
        self.num_products = mode_cfg.get("products", 150)
        self.num_customers = mode_cfg.get("customers", 500)
        self.num_suppliers = mode_cfg.get("suppliers", 20)
        self.num_shipments = mode_cfg.get("shipments", 800)
        self.id_prefix = mode_cfg.get("id_prefix", "")
        self.annual_growth_rate = float(mode_cfg.get("annual_growth_rate", 0.0))
        self.anomaly_rate = float(mode_cfg.get("anomaly_rate", 0.0))
        self.anomaly_truth: list[dict] = []
        self.start_date = datetime.strptime(mode_cfg.get("date_start", "2023-01-01"), "%Y-%m-%d").date()
        self.end_date = datetime.strptime(mode_cfg.get("date_end", "2024-12-31"), "%Y-%m-%d").date()

    def generate_calendar(self) -> pd.DataFrame:
        """Generate contiguous calendar dates with holiday and seasonal attributes."""
        logger.info(f"Generating calendar from {self.start_date} to {self.end_date}...")
        cur_date = self.start_date
        records = []

        fixed_holidays = {
            (1, 1): "New Year's Day",
            (7, 4): "Independence Day",
            (12, 24): "Christmas Eve",
            (12, 25): "Christmas Day",
            (12, 31): "New Year's Eve",
        }
        holidays = {}
        for year in range(self.start_date.year, self.end_date.year + 1):
            for (month, day), name in fixed_holidays.items():
                holidays[date(year, month, day)] = name
            may_end = date(year, 5, 31)
            memorial = may_end - timedelta(days=may_end.weekday())
            september = date(year, 9, 1)
            labor = september + timedelta(days=(-september.weekday()) % 7)
            november = date(year, 11, 1)
            thanksgiving = november + timedelta(days=(3 - november.weekday()) % 7 + 21)
            holidays.update({memorial: "Memorial Day", labor: "Labor Day",
                             thanksgiving: "Thanksgiving Day",
                             thanksgiving + timedelta(days=1): "Black Friday"})

        while cur_date <= self.end_date:
            day_of_week = cur_date.weekday() + 1 # 1=Mon, 7=Sun
            day_name = cur_date.strftime("%A")
            is_weekend = 1 if day_of_week in [6, 7] else 0
            month = cur_date.month
            month_name = cur_date.strftime("%B")
            quarter = (month - 1) // 3 + 1
            year = cur_date.year

            h_key = cur_date
            is_holiday = 1 if h_key in holidays else 0
            holiday_name = holidays.get(h_key, None)

            if month in [12, 1, 2]:
                season = "Winter"
            elif month in [3, 4, 5]:
                season = "Spring"
            elif month in [6, 7, 8]:
                season = "Summer"
            else:
                season = "Fall"

            records.append({
                "CalendarDate": cur_date,
                "DayOfWeek": day_of_week,
                "DayName": day_name,
                "DayOfMonth": cur_date.day,
                "DayOfYear": cur_date.timetuple().tm_yday,
                "WeekNumber": int(cur_date.strftime("%U")),
                "MonthNumber": month,
                "MonthName": month_name,
                "QuarterNumber": quarter,
                "YearNumber": year,
                "IsWeekend": is_weekend,
                "IsHoliday": is_holiday,
                "HolidayName": holiday_name,
                "Season": season,
            })
            cur_date += timedelta(days=1)

        return pd.DataFrame(records)

    def generate_suppliers(self) -> pd.DataFrame:
        """Generate national merchandise suppliers."""
        logger.info(f"Generating {self.num_suppliers} suppliers...")
        categories = ["Grocery", "Electronics", "Apparel", "Home & Kitchen", "Health & Beauty", "General Merchandise"]
        regions = ["Midwest", "South", "Northeast", "West"]
        records = []

        for i in range(1, self.num_suppliers + 1):
            records.append({
                "SourceSupplierID": f"SUPP-{i:03d}",
                "SupplierName": f"Pinnacle Supply Partner {i}",
                "SupplierCategory": categories[i % len(categories)],
                "Country": "USA",
                "Region": regions[i % len(regions)],
                "LeadTimeDays": int(self.np_random.integers(3, 14)),
                "QualityRating": round(float(self.np_random.uniform(3.8, 5.0)), 2),
            })
        return pd.DataFrame(records)

    def generate_products(self, suppliers_df: pd.DataFrame) -> pd.DataFrame:
        """Generate product catalog with embedded association pairs."""
        logger.info(f"Generating {self.num_products} products...")
        supp_ids = suppliers_df["SourceSupplierID"].tolist()

        catalog_templates = [
            # Grocery & Essentials
            ("Great Value Whole Milk 1Gal", "Grocery", "Dairy", "Great Value", 1.95, 3.28),
            ("Wonder Classic White Bread", "Grocery", "Bakery", "Wonder", 1.20, 2.48),
            ("Jif Creamy Peanut Butter 16oz", "Grocery", "Pantry", "Jif", 1.80, 2.98),
            ("Smucker's Strawberry Jam 18oz", "Grocery", "Pantry", "Smucker's", 2.10, 3.48),
            ("Barilla Spaghetti Pasta 16oz", "Grocery", "Pantry", "Barilla", 0.95, 1.78),
            ("Prego Traditional Pasta Sauce 24oz", "Grocery", "Pantry", "Prego", 1.30, 2.38),
            ("Folgers Classic Roast Coffee 30oz", "Grocery", "Beverages", "Folgers", 5.20, 8.48),
            ("Bounty Select-a-Size Paper Towels", "Grocery", "Paper Goods", "Bounty", 10.50, 16.98),
            ("Oscar Mayer Hot Dogs 16oz", "Grocery", "Meat", "Oscar Mayer", 1.85, 3.12),
            ("Ball Park Hot Dog Buns 8ct", "Grocery", "Bakery", "Ball Park", 1.40, 2.58),
            # Electronics
            ("HP 15.6 Laptop Intel Core i5", "Electronics", "Computers", "HP", 380.00, 499.00),
            ("Logitech M185 Wireless Mouse", "Electronics", "Accessories", "Logitech", 9.20, 16.99),
            ("Targus 15.6 Laptop Sleeve", "Electronics", "Accessories", "Targus", 11.50, 21.99),
            ("Onn 50-inch 4K UHD Smart Roku TV", "Electronics", "Video", "Onn", 160.00, 238.00),
            ("Philips 6ft 4K HDMI Cable", "Electronics", "Accessories", "Philips", 4.10, 9.88),
            ("Apple AirPods 2nd Generation", "Electronics", "Audio", "Apple", 85.00, 119.00),
            ("Anker USB-C Fast Charger 20W", "Electronics", "Accessories", "Anker", 7.50, 14.98),
            # Health & Beauty
            ("Head & Shoulders Shampoo 28oz", "Health & Beauty", "Hair Care", "Head & Shoulders", 5.50, 9.48),
            ("Pantene Moisture Conditioner 25oz", "Health & Beauty", "Hair Care", "Pantene", 5.20, 8.98),
            ("Colgate Total Whitening Toothpaste", "Health & Beauty", "Oral Care", "Colgate", 2.40, 4.48),
            # Apparel
            ("George Men's Regular Fit Jeans", "Apparel", "Men's", "George", 9.80, 16.98),
            ("Time and Tru Women's Crew T-Shirt", "Apparel", "Women's", "Time and Tru", 4.10, 7.98),
            ("Hanes Men's Cushion Crew Socks 10pk", "Apparel", "Men's", "Hanes", 7.20, 12.48),
            # Home & Kitchen
            ("Mainstays 20-Piece Cookware Set", "Home & Kitchen", "Cookware", "Mainstays", 26.00, 44.97),
            ("Ninja Professional Plus Blender", "Home & Kitchen", "Appliances", "Ninja", 58.00, 89.00),
            ("Brita Standard Water Filter 3pk", "Home & Kitchen", "Appliances", "Brita", 10.20, 17.88),
        ]

        records = []
        for i in range(self.num_products):
            pid = f"PROD-{i+1:03d}"
            if i < len(catalog_templates):
                name, cat, subcat, brand, cost, price = catalog_templates[i]
            else:
                cat_choice = catalog_templates[i % len(catalog_templates)]
                cat = cat_choice[1]
                subcat = cat_choice[2]
                brand = f"Brand-{i%15}"
                name = f"{brand} Retail Item {i+1}"
                cost = round(float(self.np_random.uniform(2.5, 120.0)), 2)
                price = round(cost * float(self.np_random.uniform(1.25, 1.65)), 2)

            records.append({
                "SourceProductID": pid,
                "ProductName": name,
                "Category": cat,
                "Subcategory": subcat,
                "Brand": brand,
                "UnitCost": cost,
                "BasePrice": price,
                "UnitOfMeasure": "EACH",
                "SourceSupplierID": supp_ids[i % len(supp_ids)],
                "CreatedDate": datetime(2023, 1, 1),
                "ModifiedDate": datetime(2023, 1, 1),
            })

        return pd.DataFrame(records)

    def generate_stores(self) -> pd.DataFrame:
        """Generate retail store branches."""
        logger.info(f"Generating {self.num_stores} stores...")
        store_configs = [
            ("STORE-001", "Bentonville Supercenter #100", "Supercenter", "Bentonville", "South", "AR", 185000, "2015-04-10"),
            ("STORE-002", "Dallas North Supercenter #220", "Supercenter", "Dallas", "South", "TX", 195000, "2016-08-15"),
            ("STORE-003", "Orlando East Neighborhood #305", "Neighborhood Market", "Orlando", "South", "FL", 42000, "2018-02-20"),
            ("STORE-004", "Chicago West Supercenter #410", "Supercenter", "Chicago", "Midwest", "IL", 178000, "2017-06-01"),
            ("STORE-005", "Columbus Central Discount #515", "Discount Store", "Columbus", "Midwest", "OH", 110000, "2019-11-12"),
            ("STORE-006", "Atlanta Metro Supercenter #620", "Supercenter", "Atlanta", "South", "GA", 190000, "2016-03-25"),
            ("STORE-007", "Phoenix Desert Supercenter #725", "Supercenter", "Phoenix", "West", "AZ", 182000, "2017-09-18"),
            ("STORE-008", "Denver Foothills Neighborhood #830", "Neighborhood Market", "Denver", "West", "CO", 44000, "2020-01-15"),
            ("STORE-009", "Charlotte Express Hub #935", "Express", "Charlotte", "South", "NC", 25000, "2021-05-10"),
            ("STORE-010", "Philadelphia Suburban #1040", "Supercenter", "Philadelphia", "Northeast", "PA", 175000, "2018-10-05"),
        ]

        records = []
        for i in range(self.num_stores):
            if i < len(store_configs):
                sid, name, stype, city, reg, state, sqft, odate = store_configs[i]
            else:
                sid = f"STORE-{i+1:03d}"
                name = f"Regional Store #{i+1}"
                stype = "Supercenter" if i % 2 == 0 else "Neighborhood Market"
                city = f"City-{i}"
                reg = "Midwest" if i % 2 == 0 else "West"
                state = "MO"
                sqft = 120000
                odate = "2019-01-01"

            records.append({
                "SourceStoreID": sid,
                "StoreName": name,
                "StoreType": stype,
                "AddressLine": f"{100 + i*15} Retail Blvd",
                "City": city,
                "StateOrRegion": reg,
                "PostalCode": f"727{i:02d}",
                "Country": "USA",
                "SquareFootage": sqft,
                "OpenDate": datetime.strptime(odate, "%Y-%m-%d").date(),
            })

        return pd.DataFrame(records)

    def generate_customers(self) -> pd.DataFrame:
        """Generate loyalty customer base."""
        logger.info(f"Generating {self.num_customers} customers...")
        segments = ["Premium", "Regular", "Value", "Occasional"]
        cities = ["Bentonville", "Dallas", "Orlando", "Chicago", "Atlanta", "Phoenix", "Denver"]
        states = ["AR", "TX", "FL", "IL", "GA", "AZ", "CO"]

        records = []
        for i in range(1, self.num_customers + 1):
            city_idx = i % len(cities)
            join_offset = int(self.np_random.integers(10, 700))
            join_date = self.start_date - timedelta(days=join_offset)

            records.append({
                "SourceCustomerID": f"CUST-{i:04d}",
                "CustomerName": f"Customer {i}",
                "Email": f"customer_{i}@example.invalid",
                "CustomerSegment": segments[i % len(segments)],
                "City": cities[city_idx],
                "StateOrRegion": states[city_idx],
                "JoinDate": join_date,
            })
        return pd.DataFrame(records)

    def generate_promotions(self) -> pd.DataFrame:
        """Generate marketing promotions and seasonal discount campaigns."""
        logger.info("Generating promotional campaigns...")
        if self.start_date == date(2023, 1, 1) and self.end_date == date(2024, 12, 31):
            promotions = [
            ("PROMO-001", "New Year Rollback Fest", "Rollback", 10.00, "2023-01-01", "2023-01-15"),
            ("PROMO-002", "Spring Savings Bonanza", "Holiday Special", 15.00, "2023-04-10", "2023-04-24"),
            ("PROMO-003", "Summer July 4th Clearance", "Clearance", 20.00, "2023-07-01", "2023-07-08"),
            ("PROMO-004", "Labor Day Value Kickoff", "Rollback", 12.50, "2023-08-28", "2023-09-06"),
            ("PROMO-005", "Black Friday Mega Deals 2023", "Flash Sale", 25.00, "2023-11-20", "2023-11-27"),
            ("PROMO-006", "Holiday Wonder Savings 2023", "Holiday Special", 15.00, "2023-12-10", "2023-12-26"),
            ("PROMO-007", "Spring Clearance 2024", "Clearance", 18.00, "2024-03-15", "2024-03-25"),
            ("PROMO-008", "Black Friday Mega Deals 2024", "Flash Sale", 25.00, "2024-11-25", "2024-12-02"),
            ("PROMO-009", "Holiday Countdown 2024", "Holiday Special", 15.00, "2024-12-12", "2024-12-26"),
            ]
        else:
            promotions = []
            for year in range(self.start_date.year, self.end_date.year + 1):
                promotions.extend([
                    (
                        f"{self.id_prefix}PROMO-{year}-NY",
                        f"New Year Rollback {year}",
                        "Rollback",
                        10.00,
                        f"{year}-01-01",
                        f"{year}-01-15",
                    ),
                    (
                        f"{self.id_prefix}PROMO-{year}-SUMMER",
                        f"Summer Clearance {year}",
                        "Clearance",
                        15.00,
                        f"{year}-07-01",
                        f"{year}-07-10",
                    ),
                    (
                        f"{self.id_prefix}PROMO-{year}-HOLIDAY",
                        f"Holiday Value Event {year}",
                        "Holiday Special",
                        20.00,
                        f"{year}-11-20",
                        f"{year}-11-30",
                    ),
                ])

        records = []
        for pid, name, ptype, pct, sdate, edate in promotions:
            records.append({
                "PromotionID": pid,
                "PromotionName": name,
                "PromotionType": ptype,
                "DiscountPercent": pct,
                "StartDate": datetime.strptime(sdate, "%Y-%m-%d").date(),
                "EndDate": datetime.strptime(edate, "%Y-%m-%d").date(),
            })
        return pd.DataFrame(records)

    def generate_transactions(
        self,
        products_df: pd.DataFrame,
        stores_df: pd.DataFrame,
        customers_df: pd.DataFrame,
        promotions_df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Generate transactions and line items with market basket co-occurrences."""
        logger.info(f"Generating approximately {self.target_transactions} transaction lines...")

        store_ids = stores_df["SourceStoreID"].tolist()
        cust_ids = customers_df["SourceCustomerID"].tolist()
        prod_dict = {row["SourceProductID"]: row for _, row in products_df.iterrows()}
        all_pids = list(prod_dict.keys())

        # Association patterns for Market Basket Analysis
        associations = {
            "PROD-002": ("PROD-001", 0.45), # Bread -> Milk
            "PROD-003": ("PROD-004", 0.40), # Peanut Butter -> Jam
            "PROD-005": ("PROD-006", 0.50), # Pasta -> Pasta Sauce
            "PROD-011": ("PROD-012", 0.35), # Laptop -> Mouse
            "PROD-014": ("PROD-015", 0.40), # Smart TV -> HDMI Cable
            "PROD-018": ("PROD-019", 0.45), # Shampoo -> Conditioner
            "PROD-009": ("PROD-010", 0.55), # Hot Dogs -> Buns
        }

        channels = ["In-Store", "Online", "Mobile", "Curbside"]
        channel_probs = [0.65, 0.20, 0.10, 0.05]
        pay_methods = ["Credit Card", "Debit Card", "Mobile Wallet", "Cash"]

        tx_records = []
        line_records = []

        total_days = (self.end_date - self.start_date).days
        current_tx_id = 1
        lines_count = 0

        # Estimated transactions needed to hit target lines (avg ~2.8 lines per tx)
        num_tx = int(self.target_transactions / 2.8)

        day_values = np.arange(total_days + 1)
        if self.annual_growth_rate:
            dates = pd.to_datetime(self.start_date) + pd.to_timedelta(day_values, unit="D")
            years = dates.year.to_numpy() - self.start_date.year
            weights = np.power(1.0 + self.annual_growth_rate, years)
            weights = weights / weights.sum()
            sampled_offsets = self.np_random.choice(
                day_values, size=num_tx, replace=True, p=weights
            )
        else:
            sampled_offsets = self.np_random.integers(0, total_days + 1, size=num_tx)

        for day_offset in sampled_offsets:
            tx_id = f"{self.id_prefix}TX-{current_tx_id:07d}"
            day_offset = int(day_offset)
            tx_date = self.start_date + timedelta(days=day_offset)

            # Hour simulation (store peak hours 11am-2pm, 5pm-8pm)
            hour = int(self.np_random.choice([9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]))
            minute = int(self.np_random.integers(0, 60))
            tx_time = f"{hour:02d}:{minute:02d}:00"

            store_id = self.np_random.choice(store_ids)
            # 75% registered customer, 25% anonymous guest
            cust_id = self.np_random.choice(cust_ids) if self.np_random.uniform() < 0.75 else None
            channel = self.np_random.choice(channels, p=channel_probs)
            payment = self.np_random.choice(pay_methods)

            # Check if any promotion is active on this date
            active_promos = promotions_df[
                (promotions_df["StartDate"] <= tx_date) & (promotions_df["EndDate"] >= tx_date)
            ]
            active_promo_id = active_promos.iloc[0]["PromotionID"] if not active_promos.empty else None
            active_promo_disc = (
                float(active_promos.iloc[0]["DiscountPercent"]) / 100.0 if active_promo_id else 0.0
            )

            # Basket size between 1 and 6
            basket_size = int(self.np_random.choice([1, 2, 3, 4, 5, 6], p=[0.25, 0.35, 0.20, 0.10, 0.07, 0.03]))
            chosen_pids = set()

            # First primary product
            first_pid = self.np_random.choice(all_pids)
            chosen_pids.add(first_pid)

            # Check for association rule addition
            if first_pid in associations and len(chosen_pids) < basket_size:
                partner_pid, prob = associations[first_pid]
                if self.np_random.uniform() < prob:
                    if partner_pid in prod_dict:
                        chosen_pids.add(partner_pid)

            # Fill remaining basket
            while len(chosen_pids) < basket_size:
                rand_p = self.np_random.choice(all_pids)
                chosen_pids.add(rand_p)

            tx_total = 0.0
            for line_no, pid in enumerate(sorted(chosen_pids), start=1):
                p_info = prod_dict[pid]
                base_price = float(p_info["BasePrice"])
                anomaly_type = None
                if self.anomaly_rate and self.np_random.uniform() < self.anomaly_rate:
                    qty = int(self.np_random.integers(8, 21))
                    anomaly_type = "INJECTED_HIGH_QUANTITY"
                else:
                    qty = int(self.np_random.choice([1, 2, 3], p=[0.85, 0.12, 0.03]))

                # Apply discount if promotional
                disc_amt = round(qty * base_price * active_promo_disc, 2) if active_promo_id else 0.0
                line_total = round((qty * base_price) - disc_amt, 2)
                tx_total += line_total

                line_records.append({
                    "TransactionID": tx_id,
                    "LineNumber": line_no,
                    "SourceProductID": pid,
                    "Quantity": qty,
                    "UnitPrice": base_price,
                    "DiscountAmount": disc_amt,
                    "LineTotalAmount": line_total,
                    "PromotionID": active_promo_id,
                })
                if anomaly_type:
                    self.anomaly_truth.append({
                        "TransactionID": tx_id,
                        "LineNumber": line_no,
                        "AnomalyType": anomaly_type,
                    })
                lines_count += 1

            tx_records.append({
                "TransactionID": tx_id,
                "SourceStoreID": store_id,
                "SourceCustomerID": cust_id,
                "TransactionDate": tx_date,
                "TransactionTime": tx_time,
                "Channel": channel,
                "TotalAmount": round(tx_total, 2),
                "PaymentMethod": payment,
            })
            current_tx_id += 1

        logger.info(f"Generated {len(tx_records)} transactions and {len(line_records)} line items.")
        return pd.DataFrame(tx_records), pd.DataFrame(line_records)

    def generate_inventory(
        self, products_df: pd.DataFrame, stores_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Generate daily inventory snapshots across stores and top products."""
        logger.info("Generating inventory snapshots...")
        records = []
        pids = products_df["SourceProductID"].head(30).tolist() # Track 30 key SKUs daily
        sids = stores_df["SourceStoreID"].head(5).tolist()

        # Generate snapshots for the last 60 days
        snapshot_start = max(self.start_date, self.end_date - timedelta(days=59))
        cur_date = snapshot_start

        while cur_date <= self.end_date:
            for sid in sids:
                for pid in pids:
                    reorder_pt = int(self.np_random.integers(15, 45))
                    safety_stk = int(reorder_pt * 0.4)
                    # 94% in-stock, 6% stockout scenario
                    is_stockout = self.np_random.uniform() < 0.06
                    qoh = 0 if is_stockout else int(self.np_random.integers(safety_stk, reorder_pt * 3))
                    qoo = int(self.np_random.integers(20, 80)) if qoh <= reorder_pt else 0

                    records.append({
                        "SnapshotDate": cur_date,
                        "SourceStoreID": sid,
                        "SourceProductID": pid,
                        "QuantityOnHand": qoh,
                        "QuantityOnOrder": qoo,
                        "ReorderPoint": reorder_pt,
                        "SafetyStock": safety_stk,
                    })
            cur_date += timedelta(days=1)

        return pd.DataFrame(records)

    def generate_shipments(
        self, products_df: pd.DataFrame, stores_df: pd.DataFrame, suppliers_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Generate supplier purchase order delivery records."""
        logger.info("Generating supplier shipment telemetry...")
        records = []
        sids = stores_df["SourceStoreID"].tolist()
        supplier_by_product = products_df.set_index("SourceProductID")["SourceSupplierID"].to_dict()
        pids = products_df["SourceProductID"].tolist()

        num_orders = self.num_shipments
        total_days = (self.end_date - self.start_date).days

        for i in range(1, num_orders + 1):
            day_offset = int(self.np_random.integers(0, max(1, total_days - 20)))
            order_date = self.start_date + timedelta(days=day_offset)
            store_id = self.np_random.choice(sids)
            pid = self.np_random.choice(pids)
            supp_id = supplier_by_product[pid]

            lead_days = int(self.np_random.integers(3, 12))
            promised_date = order_date + timedelta(days=lead_days)

            # 85% on-time, 15% delayed
            delayed = self.np_random.uniform() < 0.15
            delay_days = int(self.np_random.integers(1, 6)) if delayed else 0
            actual_date = promised_date + timedelta(days=delay_days)

            qty_ordered = int(self.np_random.integers(50, 400))
            # 92% full fill, 8% partial fill
            fill_pct = 1.0 if self.np_random.uniform() < 0.92 else float(self.np_random.uniform(0.70, 0.95))
            qty_received = int(qty_ordered * fill_pct)

            records.append({
                "ShipmentID": f"{self.id_prefix}SHIP-{i:06d}",
                "PurchaseOrderID": f"{self.id_prefix}PO-{i:06d}",
                "SourceSupplierID": supp_id,
                "SourceStoreID": store_id,
                "SourceProductID": pid,
                "OrderDate": order_date,
                "PromisedDeliveryDate": promised_date,
                "ActualDeliveryDate": actual_date,
                "QuantityOrdered": qty_ordered,
                "QuantityReceived": qty_received,
                "ShipmentStatus": "Delayed" if delayed else "Delivered",
            })

        return pd.DataFrame(records)

    def generate_all(self, output_dir: str = "data/synthetic") -> dict[str, pd.DataFrame]:
        """Generate all canonical datasets and persist to disk."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        if any(out_path.glob("*.csv")):
            raise FileExistsError(f"Preserving existing CSV files in {out_path}; choose a new output directory.")

        logger.info(f"Starting deterministic canonical data generation (Mode: {self.mode})...")

        cal_df = self.generate_calendar()
        supp_df = self.generate_suppliers()
        prod_df = self.generate_products(supp_df)
        stores_df = self.generate_stores()
        cust_df = self.generate_customers()
        promo_df = self.generate_promotions()
        tx_df, lines_df = self.generate_transactions(prod_df, stores_df, cust_df, promo_df)
        inv_df = self.generate_inventory(prod_df, stores_df)
        ship_df = self.generate_shipments(prod_df, stores_df, supp_df)

        datasets = {
            "SourceCalendar": cal_df,
            "SourceSupplier": supp_df,
            "SourceProduct": prod_df,
            "SourceStore": stores_df,
            "SourceCustomer": cust_df,
            "SourcePromotion": promo_df,
            "SourceSalesTransaction": tx_df,
            "SourceSalesTransactionLine": lines_df,
            "SourceInventory": inv_df,
            "SourceShipment": ship_df,
        }

        for name, df in datasets.items():
            csv_path = out_path / f"{name}.csv"
            df.to_csv(csv_path, index=False)
            logger.info(f"Saved {name}: {len(df):,} rows -> {csv_path}")

        ground_truth_files = {}
        if self.anomaly_truth:
            truth_path = out_path / "ground_truth_sales_anomalies.csv"
            pd.DataFrame(self.anomaly_truth).to_csv(truth_path, index=False)
            ground_truth_files["sales_anomalies"] = {
                "file": truth_path.name,
                "rows": len(self.anomaly_truth),
                "sha256": hashlib.sha256(truth_path.read_bytes()).hexdigest(),
                "label_source": "deterministic generator injection",
            }

        manifest = {"source_system": "SYNTHETIC_CANONICAL", "synthetic": True,
                    "seed": self.seed, "mode": self.mode,
                    "date_start": str(self.start_date), "date_end": str(self.end_date),
                    "id_prefix": self.id_prefix,
                    "requested_transaction_lines": self.target_transactions,
                    "annual_growth_rate": self.annual_growth_rate,
                    "injected_anomaly_rate": self.anomaly_rate,
                    "limitations": ["Educational generated records; not Walmart internal data.",
                                     "Inventory is independent simulation for 30 SKUs/5 stores over 60 days.",
                                     "Basket associations are deliberately embedded; not discovered retail evidence.",
                                     "Approximate transaction line count; transaction dates are weighted by the configured annual growth rate."],
                    "files": {name: {"rows": len(df), "sha256": hashlib.sha256(
                        (out_path / f"{name}.csv").read_bytes()).hexdigest()} for name, df in datasets.items()},
                    "ground_truth_files": ground_truth_files}
        (out_path / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        logger.info("Deterministic canonical generation complete.")
        return datasets
