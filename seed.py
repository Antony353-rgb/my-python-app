

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import execute_db, query_db, init_db
from werkzeug.security import generate_password_hash
from datetime import datetime, date

def seed():
    print("Seeding sample data...")

    # ── ROLES ──────────────────────────────────────────────────────────────────
    roles = [("superadmin",), ("internal_staff",), ("client_user",), ("supplier_user",)]
    for r in roles:
        try: execute_db("INSERT INTO roles (name) VALUES (?)", r)
        except: pass

    # ── COUNTRIES ──────────────────────────────────────────────────────────────
    countries = [
        ("United States", "US"), ("United Kingdom", "GB"), ("India", "IN"),
        ("United Arab Emirates", "AE"), ("Saudi Arabia", "SA"), ("Germany", "DE"),
        ("France", "FR"), ("Australia", "AU"), ("Canada", "CA"), ("Singapore", "SG"),
    ]
    for c in countries:
        try: execute_db("INSERT INTO countries (name, code) VALUES (?,?)", c)
        except: pass

    # ── CURRENCIES ─────────────────────────────────────────────────────────────
    currencies = [
        ("US Dollar", "USD", "$"), ("Euro", "EUR", "€"),
        ("British Pound", "GBP", "£"), ("Indian Rupee", "INR", "₹"),
        ("UAE Dirham", "AED", "د.إ"), ("Saudi Riyal", "SAR", "﷼"),
        ("Australian Dollar", "AUD", "A$"), ("Canadian Dollar", "CAD", "C$"),
        ("Singapore Dollar", "SGD", "S$"),
    ]
    for c in currencies:
        try: execute_db("INSERT INTO currencies (name, code, symbol) VALUES (?,?,?)", c)
        except: pass

    # ── DENOMINATIONS ──────────────────────────────────────────────────────────
    denoms = [
        ("fixed", "₹100",   100,    None,  None),
        ("fixed", "₹250",   250,    None,  None),
        ("fixed", "₹500",   500,    None,  None),
        ("fixed", "₹1000",  1000,   None,  None),
        ("fixed", "₹2000",  2000,   None,  None),
        ("fixed", "₹5000",  5000,   None,  None),
        ("fixed", "$10",    10,     None,  None),
        ("fixed", "$25",    25,     None,  None),
        ("fixed", "$50",    50,     None,  None),
        ("fixed", "$100",   100,    None,  None),
        ("fixed", "$200",   200,    None,  None),
        ("fixed", "£10",    10,     None,  None),
        ("fixed", "£25",    25,     None,  None),
        ("fixed", "£50",    50,     None,  None),
        ("fixed", "€10",    10,     None,  None),
        ("fixed", "€25",    25,     None,  None),
        ("fixed", "€50",    50,     None,  None),
        ("fixed", "€100",   100,    None,  None),
        ("variable", "$10–$500", None, 10, 500),
        ("variable", "₹100–₹10000", None, 100, 10000),
    ]
    for d in denoms:
        try: execute_db("INSERT INTO denominations (type,label,value,range_from,range_to) VALUES (?,?,?,?,?)", d)
        except: pass

    # ── BRANDS ─────────────────────────────────────────────────────────────────
    brands = [
        "Amazon", "Apple", "Google Play", "Steam", "Netflix",
        "Spotify", "Flipkart", "Noon", "Carrefour", "IKEA",
    ]
    for b in brands:
        try: execute_db("INSERT INTO brands (name) VALUES (?)", (b,))
        except: pass

    # ── BRAND ↔ COUNTRY ─────────────────────────────────────────────────────
    us = query_db("SELECT id FROM countries WHERE code='US'", one=True)
    gb = query_db("SELECT id FROM countries WHERE code='GB'", one=True)
    in_ = query_db("SELECT id FROM countries WHERE code='IN'", one=True)
    ae = query_db("SELECT id FROM countries WHERE code='AE'", one=True)
    sa = query_db("SELECT id FROM countries WHERE code='SA'", one=True)

    amazon = query_db("SELECT id FROM brands WHERE name='Amazon'", one=True)
    apple  = query_db("SELECT id FROM brands WHERE name='Apple'", one=True)
    google = query_db("SELECT id FROM brands WHERE name='Google Play'", one=True)
    steam  = query_db("SELECT id FROM brands WHERE name='Steam'", one=True)
    netflix = query_db("SELECT id FROM brands WHERE name='Netflix'", one=True)
    spotify = query_db("SELECT id FROM brands WHERE name='Spotify'", one=True)
    flipkart = query_db("SELECT id FROM brands WHERE name='Flipkart'", one=True)
    noon = query_db("SELECT id FROM brands WHERE name='Noon'", one=True)

    mappings = []
    if amazon:
        for cid in [us["id"], gb["id"], in_["id"], ae["id"]]:
            mappings.append((amazon["id"], cid))
    if apple:
        for cid in [us["id"], gb["id"], ae["id"]]:
            mappings.append((apple["id"], cid))
    if google:
        for cid in [us["id"], in_["id"], ae["id"]]:
            mappings.append((google["id"], cid))
    if steam and us: mappings.append((steam["id"], us["id"]))
    if netflix and us: mappings.append((netflix["id"], us["id"]))
    if spotify and us: mappings.append((spotify["id"], us["id"]))
    if flipkart and in_: mappings.append((flipkart["id"], in_["id"]))
    if noon and ae: mappings.append((noon["id"], ae["id"]))
    if noon and sa: mappings.append((noon["id"], sa["id"]))

    for m in mappings:
        try: execute_db("INSERT INTO brand_countries (brand_id, country_id) VALUES (?,?)", m)
        except: pass

    # ── CURRENCIES by code ──────────────────────────────────────────────────
    def cur(code): return query_db("SELECT id FROM currencies WHERE code=?", (code,), one=True)
    def den(label): return query_db("SELECT id FROM denominations WHERE label=?", (label,), one=True)
    def cty(code): return query_db("SELECT id FROM countries WHERE code=?", (code,), one=True)

    usd = cur("USD"); gbp = cur("GBP"); inr = cur("INR"); eur = cur("EUR")

    # ── PRODUCTS ───────────────────────────────────────────────────────────────
    products = []
    if amazon and inr and in_:
        for lbl in ["₹100","₹250","₹500","₹1000","₹2000","₹5000"]:
            d = den(lbl)
            if d: products.append(("Amazon India "+lbl, "AMZ-IN-"+lbl.replace("₹",""), amazon["id"], in_["id"], inr["id"], d["id"], 365))
    if amazon and usd and us:
        for lbl in ["$10","$25","$50","$100","$200"]:
            d = den(lbl)
            if d: products.append(("Amazon US "+lbl, "AMZ-US-"+lbl.replace("$",""), amazon["id"], us["id"], usd["id"], d["id"], 365))
    if amazon and gbp and gb:
        for lbl in ["£10","£25","£50"]:
            d = den(lbl)
            if d: products.append(("Amazon UK "+lbl, "AMZ-UK-"+lbl.replace("£",""), amazon["id"], gb["id"], gbp["id"], d["id"], 365))
    if apple and usd and us:
        for lbl in ["$10","$25","$50","$100"]:
            d = den(lbl)
            if d: products.append(("Apple US "+lbl, "APL-US-"+lbl.replace("$",""), apple["id"], us["id"], usd["id"], d["id"], 365))
    if google and inr and in_:
        for lbl in ["₹100","₹500","₹1000"]:
            d = den(lbl)
            if d: products.append(("Google Play India "+lbl, "GPY-IN-"+lbl.replace("₹",""), google["id"], in_["id"], inr["id"], d["id"], 365))
    if google and usd and us:
        for lbl in ["$10","$25","$50"]:
            d = den(lbl)
            if d: products.append(("Google Play US "+lbl, "GPY-US-"+lbl.replace("$",""), google["id"], us["id"], usd["id"], d["id"], 365))
    if steam and usd and us:
        for lbl in ["$10","$25","$50","$100"]:
            d = den(lbl)
            if d: products.append(("Steam US "+lbl, "STM-US-"+lbl.replace("$",""), steam["id"], us["id"], usd["id"], d["id"], 730))
    if netflix and usd and us:
        d = den("$25"); d2 = den("$50")
        if d:  products.append(("Netflix US $25",  "NFX-US-25",  netflix["id"], us["id"], usd["id"], d["id"],  30))
        if d2: products.append(("Netflix US $50",  "NFX-US-50",  netflix["id"], us["id"], usd["id"], d2["id"], 30))
    if spotify and usd and us:
        d = den("$10")
        if d: products.append(("Spotify US $10", "SPT-US-10", spotify["id"], us["id"], usd["id"], d["id"], 30))
    if flipkart and inr and in_:
        for lbl in ["₹500","₹1000","₹2000"]:
            d = den(lbl)
            if d: products.append(("Flipkart "+lbl, "FLK-IN-"+lbl.replace("₹",""), flipkart["id"], in_["id"], inr["id"], d["id"], 365))

    prod_ids = {}
    for p in products:
        try:
            pid = execute_db("INSERT INTO products (name,product_code,brand_id,country_id,currency_id,denomination_id,validity_days) VALUES (?,?,?,?,?,?,?)", p)
            prod_ids[p[1]] = pid
        except: pass

    # ── SUPPLIERS ──────────────────────────────────────────────────────────────
    suppliers_data = [
        ("VoucherGuru Inc", "SUP001", us["id"] if us else None, "123 Market St, New York", "ops@voucherguru.com",   "https://api.voucherguru.com/v1", "vg_live_key_abc123", 0),
        ("GiftCodePro Ltd", "SUP002", gb["id"] if gb else None, "45 Oxford St, London",   "api@giftcodepro.co.uk", "https://api.giftcodepro.co.uk/v2", "gcp_key_xyz789",  0),
        ("DigitalDen FZCO", "SUP003", ae["id"] if ae else None, "Dubai Media City, Dubai",  "supply@digitaldenfz.ae", None, None, 0),
    ]
    sup_ids = {}
    for s in suppliers_data:
        try:
            sid = execute_db("""INSERT INTO suppliers (name,supplier_code,country_id,address,contact_email,api_endpoint,api_key,api_enabled)
                                VALUES (?,?,?,?,?,?,?,?)""", s)
            sup_ids[s[1]] = sid
            currencies_all = query_db("SELECT id FROM currencies WHERE is_active=1")
            for c in currencies_all:
                try: execute_db("INSERT INTO supplier_fund_balances (supplier_id, currency_id, balance) VALUES (?,?,?)",
                                (sid, c["id"], round(5000 + hash(str(sid)+str(c["id"])) % 10000, 2)))
                except: pass
            try: execute_db("INSERT INTO supplier_currencies (supplier_id, currency_id) VALUES (?,?)",
                            (sid, usd["id"] if usd else 1))
            except: pass
        except: pass

    # ── SUPPLIER RATES ─────────────────────────────────────────────────────────
    sup1 = sup_ids.get("SUP001")
    sup2 = sup_ids.get("SUP002")
    sup3 = sup_ids.get("SUP003")

    def add_rate(sup_id, brand_name, country_code, denom_label, rate_type, rate_value, cost_price=None):
        b = query_db("SELECT id FROM brands WHERE name=?", (brand_name,), one=True)
        c = query_db("SELECT id FROM countries WHERE code=?", (country_code,), one=True)
        d = query_db("SELECT id FROM denominations WHERE label=?", (denom_label,), one=True)
        p = query_db("SELECT id FROM products WHERE brand_id=? AND country_id=? AND denomination_id=?",
                     (b["id"] if b else 0, c["id"] if c else 0, d["id"] if d else 0), one=True)
        if not all([sup_id, b, c, d, p]): return
        try:
            execute_db("""INSERT INTO supplier_rates (supplier_id,brand_id,product_id,country_id,denomination_id,rate_type,rate_value,cost_price,effective_date)
                          VALUES (?,?,?,?,?,?,?,?,?)""",
                       (sup_id, b["id"], p["id"], c["id"], d["id"], rate_type, rate_value, cost_price, "2025-01-01"))
        except: pass

    if sup1:
        add_rate(sup1, "Amazon", "IN", "₹500",  "discount_pct", 8,  460)
        add_rate(sup1, "Amazon", "IN", "₹1000", "discount_pct", 9,  910)
        add_rate(sup1, "Amazon", "IN", "₹2000", "discount_pct", 10, 1800)
        add_rate(sup1, "Amazon", "IN", "₹5000", "discount_pct", 10, 4500)
        add_rate(sup1, "Amazon", "US", "$25",   "discount_pct", 7,  23.25)
        add_rate(sup1, "Amazon", "US", "$50",   "discount_pct", 7,  46.50)
        add_rate(sup1, "Amazon", "US", "$100",  "discount_pct", 8,  92)
        add_rate(sup1, "Google Play", "IN", "₹100", "discount_pct", 8, 92)
        add_rate(sup1, "Google Play", "IN", "₹500", "discount_pct", 9, 455)
        add_rate(sup1, "Steam", "US", "$10", "discount_pct", 10, 9)
        add_rate(sup1, "Steam", "US", "$50", "discount_pct", 10, 45)
        add_rate(sup1, "Netflix", "US", "$25", "discount_pct", 8, 23)
        add_rate(sup1, "Spotify", "US", "$10", "discount_pct", 5, 9.50)
    if sup2:
        add_rate(sup2, "Apple",  "US", "$25",  "discount_pct", 9, 22.75)
        add_rate(sup2, "Apple",  "US", "$50",  "discount_pct", 9, 45.50)
        add_rate(sup2, "Apple",  "US", "$100", "discount_pct", 9, 91)
        add_rate(sup2, "Amazon", "GB", "£25",  "discount_pct", 8, 23)
        add_rate(sup2, "Amazon", "GB", "£50",  "discount_pct", 8, 46)
        add_rate(sup2, "Steam",  "US", "$25",  "discount_pct", 11, 22.25)
        add_rate(sup2, "Steam",  "US", "$100", "discount_pct", 10, 90)
    if sup3:
        add_rate(sup3, "Amazon", "IN", "₹100",  "discount_pct", 7, 93)
        add_rate(sup3, "Amazon", "IN", "₹250",  "discount_pct", 7, 232.50)
        add_rate(sup3, "Flipkart","IN","₹500",  "discount_pct", 8, 460)
        add_rate(sup3, "Flipkart","IN","₹1000", "discount_pct", 9, 910)

    # ── CLIENTS ────────────────────────────────────────────────────────────────
    clients_data = [
        ("Resellix Technologies", "CLT001", in_["id"] if in_ else None, "42 MG Road, Bangalore, KA", "ops@resellix.in",   "+91-9876543210", inr["id"] if inr else None, 1.0, 1, 0, 0),
        ("VoucherHub DMCC",      "CLT002", ae["id"] if ae else None, "JLT Cluster G, Dubai UAE", "orders@voucherhub.ae", "+971-501234567",  usd["id"] if usd else None, 1.0, 1, 0, 0),
        ("GiftDeals UK Ltd",     "CLT003", gb["id"] if gb else None, "22 Baker St, London, UK",  "api@giftdeals.co.uk",  "+44-2012345678",  gbp["id"] if gbp else None, 1.5, 1, 0, 0),
        ("CardMart Pvt Ltd",     "CLT004", in_["id"] if in_ else None, "101 Hitech City, Hyd",  "buy@cardmart.in",      "+91-9988776655",  inr["id"] if inr else None, 1.0, 1, 500, 1),
    ]
    cli_ids = {}
    for cl in clients_data:
        try:
            cid = execute_db("""INSERT INTO clients
                (name,client_code,country_id,address,email,phone,default_currency_id,fx_buffer_pct,login_enabled,credit_enabled,credit_limit)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""", cl)
            cli_ids[cl[1]] = cid
            # Enable currencies per client
            curs = [(inr, cid, 1), (usd, cid, 0)] if cl[1] in ("CLT001","CLT004") else \
                   [(usd, cid, 1), (eur, cid, 0)] if cl[1] == "CLT002" else \
                   [(gbp, cid, 1), (usd, cid, 0)]
            for cur_obj, client_id, is_def in curs:
                if cur_obj:
                    try: execute_db("INSERT INTO client_currencies (client_id,currency_id,is_default) VALUES (?,?,?)",
                                    (client_id, cur_obj["id"], is_def))
                    except: pass
                    try: execute_db("INSERT INTO client_fund_balances (client_id,currency_id,balance) VALUES (?,?,?)",
                                    (client_id, cur_obj["id"], 50000.00 if is_def else 5000.00))
                    except: pass
        except Exception as e:
            print(f"  Client insert error: {e}")

    # ── CATALOGUES ─────────────────────────────────────────────────────────────
    cat_ids = {}
    if sup_ids.get("SUP001"):
        cat_ids["CAT001"] = execute_db("INSERT INTO catalogues (name,supplier_id,catalogue_type) VALUES (?,?,?)",
                                       ("VoucherGuru Standard", sup_ids["SUP001"], "standard"))
    if sup_ids.get("SUP002"):
        cat_ids["CAT002"] = execute_db("INSERT INTO catalogues (name,supplier_id,catalogue_type) VALUES (?,?,?)",
                                       ("GiftCodePro Premium", sup_ids["SUP002"], "standard"))
    if sup_ids.get("SUP001"):
        cat_ids["CAT003"] = execute_db("INSERT INTO catalogues (name,supplier_id,catalogue_type) VALUES (?,?,?)",
                                       ("VoucherGuru Offer Deals", sup_ids["SUP001"], "offer"))

    # ── CATALOGUE PRODUCTS ─────────────────────────────────────────────────────
    def add_cat_product(cat_id, brand_name, country_code, denom_label, client_rate_type="markup_pct", client_rate_value=5, min_markup=2):
        b = query_db("SELECT id FROM brands WHERE name=?", (brand_name,), one=True)
        c = query_db("SELECT id FROM countries WHERE code=?", (country_code,), one=True)
        d = query_db("SELECT id FROM denominations WHERE label=?", (denom_label,), one=True)
        if not all([b, c, d]): return
        p = query_db("SELECT id FROM products WHERE brand_id=? AND country_id=? AND denomination_id=?",
                     (b["id"], c["id"], d["id"]), one=True)
        if not p: return
        try:
            execute_db("""INSERT INTO catalogue_products
                (catalogue_id,product_id,denomination_id,client_rate_type,client_rate_value,min_markup_pct)
                VALUES (?,?,?,?,?,?)""",
                       (cat_id, p["id"], d["id"], client_rate_type, client_rate_value, min_markup))
        except: pass

    if cat_ids.get("CAT001"):
        cat1 = cat_ids["CAT001"]
        for lbl in ["₹500","₹1000","₹2000","₹5000"]:
            add_cat_product(cat1, "Amazon", "IN", lbl, "markup_pct", 5, 3)
        for lbl in ["₹100","₹500","₹1000"]:
            add_cat_product(cat1, "Google Play", "IN", lbl, "markup_pct", 4, 2)
        for lbl in ["$10","$25","$50","$100"]:
            add_cat_product(cat1, "Amazon", "US", lbl, "markup_pct", 5, 3)
        for lbl in ["$10","$25","$50"]:
            add_cat_product(cat1, "Steam", "US", lbl, "markup_pct", 6, 4)
        add_cat_product(cat1, "Netflix", "US", "$25", "markup_pct", 7, 4)
        add_cat_product(cat1, "Spotify", "US", "$10", "markup_pct", 8, 5)

    if cat_ids.get("CAT002"):
        cat2 = cat_ids["CAT002"]
        for lbl in ["$25","$50","$100"]:
            add_cat_product(cat2, "Apple", "US", lbl, "markup_pct", 6, 4)
        for lbl in ["£25","£50"]:
            add_cat_product(cat2, "Amazon", "GB", lbl, "markup_pct", 5, 3)
        for lbl in ["$25","$100"]:
            add_cat_product(cat2, "Steam", "US", lbl, "markup_pct", 7, 4)

    # ── MAP CATALOGUES TO CLIENTS ───────────────────────────────────────────
    maps = [
        (cli_ids.get("CLT001"), cat_ids.get("CAT001")),
        (cli_ids.get("CLT002"), cat_ids.get("CAT001")),
        (cli_ids.get("CLT002"), cat_ids.get("CAT002")),
        (cli_ids.get("CLT003"), cat_ids.get("CAT002")),
        (cli_ids.get("CLT004"), cat_ids.get("CAT001")),
        (cli_ids.get("CLT004"), cat_ids.get("CAT003")),
    ]
    for cl_id, ca_id in maps:
        if cl_id and ca_id:
            try: execute_db("INSERT INTO client_catalogues (client_id,catalogue_id) VALUES (?,?)", (cl_id, ca_id))
            except: pass

    # ── USERS ──────────────────────────────────────────────────────────────────
    sadmin_role = query_db("SELECT id FROM roles WHERE name='superadmin'", one=True)
    staff_role  = query_db("SELECT id FROM roles WHERE name='internal_staff'", one=True)
    client_role = query_db("SELECT id FROM roles WHERE name='client_user'", one=True)
    sup_role    = query_db("SELECT id FROM roles WHERE name='supplier_user'", one=True)

    users = [
        ("Super Admin",    "admin@platform.com",       "Admin@1234",   "superadmin", sadmin_role["id"] if sadmin_role else None, None, None),
        ("Ravi Kumar",     "ravi@platform.com",         "Staff@1234",   "internal",   staff_role["id"]  if staff_role  else None, None, None),
        ("Priya Sharma",   "priya@platform.com",        "Staff@1234",   "internal",   staff_role["id"]  if staff_role  else None, None, None),
        ("Resellix User",  "user@resellix.in",          "Client@1234",  "client",     client_role["id"] if client_role else None, cli_ids.get("CLT001"), None),
        ("VoucherHub User","user@voucherhub.ae",        "Client@1234",  "client",     client_role["id"] if client_role else None, cli_ids.get("CLT002"), None),
        ("GiftDeals User", "user@giftdeals.co.uk",      "Client@1234",  "client",     client_role["id"] if client_role else None, cli_ids.get("CLT003"), None),
        ("CardMart User",  "user@cardmart.in",          "Client@1234",  "client",     client_role["id"] if client_role else None, cli_ids.get("CLT004"), None),
        ("VG Supplier",    "ops@voucherguru.com",       "Supplier@1234","supplier",   sup_role["id"]    if sup_role    else None, None, sup_ids.get("SUP001")),
        ("GCP Supplier",   "api@giftcodepro.co.uk",     "Supplier@1234","supplier",   sup_role["id"]    if sup_role    else None, None, sup_ids.get("SUP002")),
    ]
    for u in users:
        try:
            execute_db("""INSERT INTO users (name,email,password_hash,user_type,role_id,client_id,supplier_id,must_change_password)
                          VALUES (?,?,?,?,?,?,?,?)""",
                       (u[0], u[1], generate_password_hash(u[2]), u[3], u[4], u[5], u[6], 0))
        except: pass

    # ── VOUCHER CODES ──────────────────────────────────────────────────────────
    import random, string
    def gen_code(prefix, n=12):
        return prefix + "-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=n))

    products_all = query_db("SELECT p.*, d.value as denom_value FROM products p JOIN denominations d ON d.id=p.denomination_id WHERE p.is_active=1")
    added_codes = 0
    for prod in products_all[:20]:  # First 20 products
        sup_id = sup_ids.get("SUP001") or sup_ids.get("SUP002")
        if not sup_id: continue
        for _ in range(20):  # 20 codes each
            code = gen_code(prod["product_code"][:6])
            try:
                execute_db("""INSERT INTO voucher_codes (product_id,denomination_id,supplier_id,code,status,cost_price)
                              VALUES (?,?,?,?,?,?)""",
                           (prod["id"], prod["denomination_id"], sup_id, code, "available",
                            round((prod["denom_value"] or 100) * 0.9, 2)))
                added_codes += 1
            except: pass

    # ── INVENTORY ORDERS ───────────────────────────────────────────────────────
    if sup_ids.get("SUP001"):
        amz_prods = query_db("SELECT p.id, p.denomination_id FROM products p JOIN brands b ON b.id=p.brand_id WHERE b.name='Amazon' AND p.is_active=1 LIMIT 3")
        for p in amz_prods:
            try:
                execute_db("""INSERT INTO inventory_orders (supplier_id,product_id,denomination_id,qty_ordered,qty_delivered,cost_price,total_cost,status,lpo_number)
                              VALUES (?,?,?,?,?,?,?,?,?)""",
                           (sup_ids["SUP001"], p["id"], p["denomination_id"], 100, 80, 450.0, 45000.0, "partial", "LPO-2025-001"))
            except: pass

    # ── SAMPLE ORDERS ──────────────────────────────────────────────────────────
    import uuid
    def make_order_num():
        return "ORD-" + datetime.utcnow().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:8].upper()

    admin_user = query_db("SELECT id FROM users WHERE email='admin@platform.com'", one=True)
    admin_id = admin_user["id"] if admin_user else 1

    order_samples = [
        (cli_ids.get("CLT001"), inr["id"] if inr else 1, "api",      "delivered", 4500.0),
        (cli_ids.get("CLT001"), inr["id"] if inr else 1, "api",      "delivered", 9000.0),
        (cli_ids.get("CLT001"), inr["id"] if inr else 1, "api",      "ordered",   2000.0),
        (cli_ids.get("CLT002"), usd["id"] if usd else 1, "api",      "delivered", 250.0),
        (cli_ids.get("CLT002"), usd["id"] if usd else 1, "manual",   "delivered", 150.0),
        (cli_ids.get("CLT003"), gbp["id"] if gbp else 1, "api",      "pending_delivery", 75.0),
        (cli_ids.get("CLT004"), inr["id"] if inr else 1, "preorder", "ordered",   5000.0),
    ]
    for (cl_id, cur_id, otype, status, total) in order_samples:
        if not cl_id: continue
        try:
            ord_num  = make_order_num()
            inv_num  = "INV-" + uuid.uuid4().hex[:8].upper()
            ord_id = execute_db("""INSERT INTO orders (order_number,client_id,currency_id,order_type,status,total_amount,invoice_number,fx_rate_used,fx_buffer_pct,created_by)
                                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                                (ord_num, cl_id, cur_id, otype, status, total, inv_num, 1.0, 1.0, admin_id))
            # Add a sample order item
            prod = query_db("SELECT p.id, p.denomination_id FROM products p WHERE p.is_active=1 LIMIT 1", one=True)
            sup_id = sup_ids.get("SUP001") or 1
            if prod:
                execute_db("""INSERT INTO order_items (order_id,product_id,denomination_id,supplier_id,qty,cost_price,selling_price,total_cost,total_selling,profit,status)
                              VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                           (ord_id, prod["id"], prod["denomination_id"], sup_id, 1, total*0.9, total, total*0.9, total, total*0.1, status if status=="delivered" else "ordered"))
        except Exception as e:
            print(f"  Order insert error: {e}")

    # ── CLIENT FUND TRANSACTIONS ───────────────────────────────────────────────
    for code, cid in cli_ids.items():
        cur_id = inr["id"] if code in ("CLT001","CLT004") else usd["id"]
        if not cur_id: continue
        try:
            execute_db("""INSERT INTO client_fund_transactions (client_id,currency_id,txn_type,amount,balance_before,balance_after,remarks,created_by)
                          VALUES (?,?,?,?,?,?,?,?)""",
                       (cid, cur_id, "topup", 50000, 0, 50000, "Initial fund deposit", admin_id))
        except: pass

    # ── FX RATES ───────────────────────────────────────────────────────────────
    rates = [
        ("USD","INR",83.50), ("USD","GBP",0.79), ("USD","EUR",0.92),
        ("USD","AED",3.67),  ("USD","SAR",3.75),  ("EUR","INR",90.75),
        ("GBP","INR",105.20),("EUR","USD",1.09),  ("GBP","USD",1.27),
        ("INR","USD",0.012), ("AED","USD",0.27),
    ]
    for (fc, tc, rate) in rates:
        try:
            execute_db("INSERT INTO fx_rates (from_currency,to_currency,rate) VALUES (?,?,?)", (fc, tc, rate))
        except: pass

    # ── NOTIFICATIONS ─────────────────────────────────────────────────────────
    resellix_user = query_db("SELECT id FROM users WHERE email='user@resellix.in'", one=True)
    if resellix_user:
        notifs = [
            (resellix_user["id"], "funds_updated", "Funds Topped Up", "₹50,000 has been added to your INR wallet."),
            (resellix_user["id"], "order_delivered", "Order Delivered", "Your order ORD-20250501-XXXX has been delivered. Download your codes."),
            (resellix_user["id"], "low_balance", "Low Balance Warning", "Your INR balance is below ₹1,000. Please topup to continue ordering."),
        ]
        for n in notifs:
            try: execute_db("INSERT INTO notifications (user_id,type,title,message) VALUES (?,?,?,?)", n)
            except: pass

    print(f"\n✅ Seed complete!")
    print(f"   Countries:    {len(countries)}")
    print(f"   Currencies:   {len(currencies)}")
    print(f"   Brands:       {len(brands)}")
    print(f"   Denominations:{len(denoms)}")
    print(f"   Products:     {len(products)}")
    print(f"   Suppliers:    {len(suppliers_data)}")
    print(f"   Clients:      {len(clients_data)}")
    print(f"   Users:        {len(users)}")
    print(f"   Voucher codes:{added_codes}")
    print(f"   FX Rates:     {len(rates)}")
    print(f"\n📋 Login Credentials:")
    print(f"   admin@platform.com     → Admin@1234   (Super Admin)")
    print(f"   ravi@platform.com      → Staff@1234   (Internal Staff)")
    print(f"   user@resellix.in       → Client@1234  (Client — Resellix)")
    print(f"   user@voucherhub.ae     → Client@1234  (Client — VoucherHub)")
    print(f"   ops@voucherguru.com    → Supplier@1234 (Supplier — VoucherGuru)")

if __name__ == "__main__":
    init_db()
    seed()