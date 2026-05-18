-- ─────────────────────────────────────────
--  B2B Voucher Platform — SQLite Schema
-- ─────────────────────────────────────────

-- ROLES
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- PERMISSIONS per role per module
CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    module TEXT NOT NULL,
    can_view INTEGER DEFAULT 0,
    can_add INTEGER DEFAULT 0,
    can_edit INTEGER DEFAULT 0,
    can_delete INTEGER DEFAULT 0,
    can_import INTEGER DEFAULT 0,
    can_export INTEGER DEFAULT 0,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- USERS
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    user_type TEXT NOT NULL CHECK(user_type IN ('superadmin','internal','client','supplier')),
    role_id INTEGER,
    client_id INTEGER,
    supplier_id INTEGER,
    totp_secret TEXT,
    totp_enabled INTEGER DEFAULT 0,
    must_change_password INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,
    last_login DATETIME,
    last_login_ip TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- COUNTRIES
CREATE TABLE IF NOT EXISTS countries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- CURRENCIES
CREATE TABLE IF NOT EXISTS currencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    symbol TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- DENOMINATIONS
CREATE TABLE IF NOT EXISTS denominations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK(type IN ('fixed','variable')),
    value REAL,
    range_from REAL,
    range_to REAL,
    label TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- BRANDS
CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    logo_path TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- BRAND ↔ COUNTRY mapping
CREATE TABLE IF NOT EXISTS brand_countries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL,
    country_id INTEGER NOT NULL,
    FOREIGN KEY (brand_id) REFERENCES brands(id),
    FOREIGN KEY (country_id) REFERENCES countries(id),
    UNIQUE(brand_id, country_id)
);

-- PRODUCTS
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    product_code TEXT NOT NULL UNIQUE,
    brand_id INTEGER NOT NULL,
    country_id INTEGER NOT NULL,
    currency_id INTEGER NOT NULL,
    denomination_id INTEGER NOT NULL,
    validity_days INTEGER,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id),
    FOREIGN KEY (country_id) REFERENCES countries(id),
    FOREIGN KEY (currency_id) REFERENCES currencies(id),
    FOREIGN KEY (denomination_id) REFERENCES denominations(id)
);

-- SUPPLIERS
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    supplier_code TEXT NOT NULL UNIQUE,
    country_id INTEGER,
    address TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    api_endpoint TEXT,
    api_key TEXT,
    api_enabled INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (country_id) REFERENCES countries(id)
);

-- SUPPLIER BANK ACCOUNTS (per currency)
CREATE TABLE IF NOT EXISTS supplier_bank_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    currency_id INTEGER NOT NULL,
    bank_name TEXT,
    account_number TEXT,
    account_name TEXT,
    swift_code TEXT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (currency_id) REFERENCES currencies(id)
);

-- SUPPLIER CURRENCIES enabled
CREATE TABLE IF NOT EXISTS supplier_currencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    currency_id INTEGER NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (currency_id) REFERENCES currencies(id),
    UNIQUE(supplier_id, currency_id)
);

-- SUPPLIER FUND BALANCES
CREATE TABLE IF NOT EXISTS supplier_fund_balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    currency_id INTEGER NOT NULL,
    balance REAL DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (currency_id) REFERENCES currencies(id),
    UNIQUE(supplier_id, currency_id)
);

-- SUPPLIER RATE LIST
CREATE TABLE IF NOT EXISTS supplier_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    brand_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    country_id INTEGER NOT NULL,
    denomination_id INTEGER NOT NULL,
    rate_type TEXT NOT NULL CHECK(rate_type IN ('discount_pct','markup_pct','discount_amt','markup_amt','fixed')),
    rate_value REAL NOT NULL,
    cost_price REAL,
    effective_date DATE,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (brand_id) REFERENCES brands(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- CLIENTS
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    client_code TEXT NOT NULL UNIQUE,
    country_id INTEGER,
    address TEXT,
    email TEXT,
    phone TEXT,
    default_currency_id INTEGER,
    fx_buffer_pct REAL DEFAULT 1.0,
    credit_limit REAL DEFAULT 0,
    credit_enabled INTEGER DEFAULT 0,
    login_enabled INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (country_id) REFERENCES countries(id),
    FOREIGN KEY (default_currency_id) REFERENCES currencies(id)
);

-- CLIENT CURRENCIES enabled
CREATE TABLE IF NOT EXISTS client_currencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    currency_id INTEGER NOT NULL,
    is_default INTEGER DEFAULT 0,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (currency_id) REFERENCES currencies(id),
    UNIQUE(client_id, currency_id)
);

-- CLIENT FUND BALANCES
CREATE TABLE IF NOT EXISTS client_fund_balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    currency_id INTEGER NOT NULL,
    balance REAL DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (currency_id) REFERENCES currencies(id),
    UNIQUE(client_id, currency_id)
);

-- CLIENT FUND TRANSACTIONS
CREATE TABLE IF NOT EXISTS client_fund_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    currency_id INTEGER NOT NULL,
    txn_type TEXT NOT NULL CHECK(txn_type IN ('topup','topdown','order_debit','reversal','swap_out','swap_in')),
    amount REAL NOT NULL,
    balance_before REAL NOT NULL,
    balance_after REAL NOT NULL,
    remarks TEXT,
    reference TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (currency_id) REFERENCES currencies(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- CATALOGUES
CREATE TABLE IF NOT EXISTS catalogues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    supplier_id INTEGER NOT NULL,
    catalogue_type TEXT NOT NULL CHECK(catalogue_type IN ('standard','offer')),
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- CATALOGUE PRODUCTS (with pricing rules)
CREATE TABLE IF NOT EXISTS catalogue_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalogue_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    denomination_id INTEGER NOT NULL,
    supplier_rate_type TEXT CHECK(supplier_rate_type IN ('discount_pct','markup_pct','discount_amt','markup_amt','fixed')),
    supplier_rate_value REAL,
    client_rate_type TEXT CHECK(client_rate_type IN ('discount_pct','markup_pct','discount_amt','markup_amt','fixed')),
    client_rate_value REAL,
    min_markup_pct REAL DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (catalogue_id) REFERENCES catalogues(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (denomination_id) REFERENCES denominations(id),
    UNIQUE(catalogue_id, product_id, denomination_id)
);

-- CLIENT ↔ CATALOGUE mapping
CREATE TABLE IF NOT EXISTS client_catalogues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    catalogue_id INTEGER NOT NULL,
    mapped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (catalogue_id) REFERENCES catalogues(id),
    UNIQUE(client_id, catalogue_id)
);

-- FX RATES CACHE
CREATE TABLE IF NOT EXISTS fx_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_currency TEXT NOT NULL,
    to_currency TEXT NOT NULL,
    rate REAL NOT NULL,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_currency, to_currency)
);

-- ORDERS
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL UNIQUE,
    client_id INTEGER NOT NULL,
    currency_id INTEGER NOT NULL,
    order_type TEXT NOT NULL CHECK(order_type IN ('api','manual','preorder')),
    status TEXT NOT NULL DEFAULT 'ordered' CHECK(status IN ('ordered','pending_delivery','delivered','failed','cancelled')),
    total_amount REAL NOT NULL,
    total_usd REAL,
    fx_rate_used REAL,
    fx_buffer_pct REAL,
    invoice_number TEXT,
    remarks TEXT,
    cancelled_by INTEGER,
    cancelled_at DATETIME,
    cancellation_reason TEXT,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (currency_id) REFERENCES currencies(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- ORDER ITEMS
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    denomination_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    supplier_rate_id INTEGER,
    qty INTEGER NOT NULL,
    cost_price REAL NOT NULL,
    selling_price REAL NOT NULL,
    total_cost REAL NOT NULL,
    total_selling REAL NOT NULL,
    profit REAL,
    status TEXT DEFAULT 'ordered' CHECK(status IN ('ordered','pending_delivery','delivered','failed')),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- VOUCHER CODES
CREATE TABLE IF NOT EXISTS voucher_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    denomination_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    code TEXT NOT NULL UNIQUE,
    pin TEXT,
    status TEXT NOT NULL DEFAULT 'available' CHECK(status IN ('available','reserved','sold','expired')),
    cost_price REAL,
    expiry_date DATE,
    order_item_id INTEGER,
    reserved_at DATETIME,
    sold_at DATETIME,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (order_item_id) REFERENCES order_items(id)
);

-- INVENTORY PURCHASE ORDERS
CREATE TABLE IF NOT EXISTS inventory_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    denomination_id INTEGER NOT NULL,
    qty_ordered INTEGER NOT NULL,
    qty_delivered INTEGER DEFAULT 0,
    cost_price REAL NOT NULL,
    rate_type TEXT,
    rate_value REAL,
    total_cost REAL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending','partial','delivered','cancelled')),
    lpo_number TEXT,
    remarks TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- NOTIFICATIONS
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- AUDIT LOGS
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_email TEXT,
    action TEXT NOT NULL,
    module TEXT NOT NULL,
    record_id INTEGER,
    old_value TEXT,
    new_value TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_orders_client ON orders(client_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_vouchers_status ON voucher_codes(status);
CREATE INDEX IF NOT EXISTS idx_vouchers_product ON voucher_codes(product_id);
CREATE INDEX IF NOT EXISTS idx_audit_module ON audit_logs(module);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_fund_txn_client ON client_fund_transactions(client_id);
