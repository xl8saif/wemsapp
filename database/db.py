"""Database compatibility layer for WEMS.

The desktop build uses SQLite. When DATABASE_URL is set, WEMS uses PostgreSQL.
Application SQL can continue using SQLite-style ? placeholders.
"""
import os
import sqlite3
from config import Config
from werkzeug.security import generate_password_hash

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    dict_row = None

DBIntegrityError = sqlite3.IntegrityError
if psycopg is not None:
    DBIntegrityError = (sqlite3.IntegrityError, psycopg.IntegrityError)

_DEFAULT_SERVICES = [
    ("Legal Drafting - Agreement", "Legal Drafting", "General legal agreement drafting", 5000),
    ("Legal Drafting - Affidavit", "Legal Drafting", "Affidavit preparation", 2000),
    ("Legal Drafting - Power of Attorney", "Legal Drafting", "Power of attorney document", 3000),
    ("Legal Drafting - Contract", "Legal Drafting", "Business contract drafting", 8000),
    ("Court File Preparation", "Court Services", "Complete court file preparation", 10000),
    ("Court Case Filing", "Court Services", "Filing court cases", 5000),
    ("Printing - Black & White", "Printing", "B&W printing per page", 10),
    ("Printing - Color", "Printing", "Color printing per page", 50),
    ("Printing - Large Format", "Printing", "Large format printing", 200),
    ("Online Registration - Business", "Online Registration", "Business registration service", 15000),
    ("Online Registration - Trademark", "Online Registration", "Trademark registration", 20000),
    ("Online Registration - Domain", "Online Registration", "Domain registration assistance", 5000),
    ("Document Attestation", "Documentation", "Document attestation service", 3000),
    ("Translation Service", "Documentation", "Document translation", 2000),
    ("Consultation", "Other", "General consultation", 2000),
]

class DBRow(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)

class CompatCursor:
    def __init__(self, cursor, backend):
        self._cursor = cursor
        self._backend = backend
    def execute(self, sql, params=()):
        self._cursor.execute(_adapt_sql(sql, self._backend), params)
        return self
    def executemany(self, sql, seq):
        self._cursor.executemany(_adapt_sql(sql, self._backend), seq)
        return self
    def fetchone(self):
        return _wrap_row(self._cursor.fetchone())
    def fetchall(self):
        return [_wrap_row(row) for row in self._cursor.fetchall()]
    @property
    def rowcount(self):
        return self._cursor.rowcount
    @property
    def description(self):
        return self._cursor.description
    def close(self):
        return self._cursor.close()

class CompatConnection:
    def __init__(self, connection, backend):
        self._connection = connection
        self.backend = backend
    def execute(self, sql, params=()):
        return CompatCursor(self._connection.cursor(), self.backend).execute(sql, params)
    def executemany(self, sql, seq):
        return CompatCursor(self._connection.cursor(), self.backend).executemany(sql, seq)
    def cursor(self):
        return CompatCursor(self._connection.cursor(), self.backend)
    def commit(self):
        return self._connection.commit()
    def rollback(self):
        return self._connection.rollback()
    def close(self):
        return self._connection.close()

def _wrap_row(row):
    if row is None:
        return None
    if isinstance(row, DBRow):
        return row
    if isinstance(row, sqlite3.Row):
        return DBRow({key: row[key] for key in row.keys()})
    if isinstance(row, dict):
        return DBRow(row)
    return row

def _adapt_sql(sql, backend):
    if backend != "postgres":
        return sql
    sql = sql.replace("strftime('%Y-%m', created_at)", "to_char(created_at, 'YYYY-MM')")
    return sql.replace("?", "%s")

def _postgres_schema(sql):
    return sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")

def get_db_backend():
    return "postgres" if Config.DATABASE_URL else "sqlite"

def get_db_connection():
    if Config.DATABASE_URL:
        if psycopg is None:
            raise RuntimeError('PostgreSQL support is not installed. Run: pip install "psycopg[binary]"')
        return CompatConnection(psycopg.connect(Config.DATABASE_URL, row_factory=dict_row), "postgres")
    os.makedirs(os.path.dirname(Config.DATABASE), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return CompatConnection(conn, "sqlite")

_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, contact_person TEXT,
        phone TEXT, email TEXT, address TEXT, cnic TEXT, client_type TEXT DEFAULT 'Individual',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT, service_name TEXT NOT NULL, category TEXT NOT NULL,
        description TEXT, base_price REAL DEFAULT 0, is_active INTEGER DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER NOT NULL, service_id INTEGER,
        job_title TEXT NOT NULL, category TEXT NOT NULL, description TEXT,
        status TEXT DEFAULT 'Pending', priority TEXT DEFAULT 'Normal', assigned_to TEXT,
        start_date DATE, due_date DATE, completed_date DATE, cost REAL DEFAULT 0, notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
        FOREIGN KEY (service_id) REFERENCES services(id)
    )""",
    """CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_number TEXT UNIQUE NOT NULL,
        client_id INTEGER NOT NULL, job_id INTEGER, issue_date DATE NOT NULL, due_date DATE,
        subtotal REAL DEFAULT 0, tax_amount REAL DEFAULT 0, discount REAL DEFAULT 0,
        total_amount REAL DEFAULT 0, paid_amount REAL DEFAULT 0, balance_due REAL DEFAULT 0,
        status TEXT DEFAULT 'Unpaid', payment_method TEXT, notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id), FOREIGN KEY (job_id) REFERENCES jobs(id)
    )""",
    """CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER NOT NULL, description TEXT NOT NULL,
        quantity REAL DEFAULT 1, unit_price REAL DEFAULT 0, total_price REAL DEFAULT 0,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER NOT NULL, client_id INTEGER NOT NULL,
        amount REAL NOT NULL, payment_date DATE NOT NULL, payment_method TEXT DEFAULT 'Cash',
        reference_no TEXT, notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id), FOREIGN KEY (client_id) REFERENCES clients(id)
    )""",
    """CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, description TEXT,
        amount REAL NOT NULL, expense_date DATE NOT NULL, paid_by TEXT, notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'staff', is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE, full_name TEXT DEFAULT '',
        email TEXT, date_of_birth TEXT, mobile TEXT, photo TEXT, socials TEXT, skills TEXT,
        cv_file TEXT, cv_name TEXT, summary TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)""",
]

def init_db():
    conn = get_db_connection()
    try:
        for schema in _SCHEMA:
            conn.execute(_postgres_schema(schema) if conn.backend == "postgres" else schema)
        if conn.backend == "sqlite":
            columns = [col[1] for col in conn.execute("PRAGMA table_info(user_profile)").fetchall()]
            if "user_id" not in columns:
                conn.execute("ALTER TABLE user_profile ADD COLUMN user_id INTEGER")
                conn.execute("DELETE FROM user_profile WHERE user_id IS NULL")
        else:
            conn.execute("ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS user_id INTEGER")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_user_profile_user_id ON user_profile(user_id)")
        if conn.execute("SELECT COUNT(*) FROM services").fetchone()[0] == 0:
            conn.executemany("INSERT INTO services (service_name, category, description, base_price) VALUES (?, ?, ?, ?)", _DEFAULT_SERVICES)

        # Online WEMS is a single-admin system. The first admin is
        # provisioned from deployment secrets; public registration is disabled.
        admin_username = os.environ.get("WEMS_ADMIN_USERNAME", "").strip().lower()
        admin_password = os.environ.get("WEMS_ADMIN_PASSWORD", "")
        admin_name = os.environ.get("WEMS_ADMIN_FULL_NAME", "Waraq Enterprises Administrator").strip()
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]

        if user_count == 0:
            if not admin_username or len(admin_password) < 12:
                if os.environ.get("WEMS_ENV", "").lower() == "production":
                    raise RuntimeError("WEMS_ADMIN_USERNAME and WEMS_ADMIN_PASSWORD (minimum 12 characters) are required in production.")
            else:
                conn.execute(
                    "INSERT INTO users (username, password_hash, full_name, role, is_active) VALUES (?, ?, ?, 'admin', 1)",
                    (admin_username, generate_password_hash(admin_password), admin_name),
                )
        elif os.environ.get("WEMS_ENV", "").lower() == "production":
            if admin_count != 1:
                raise RuntimeError("Production WEMS requires exactly one administrator account.")
            if not admin_username or len(admin_password) < 12:
                raise RuntimeError("WEMS_ADMIN_USERNAME and WEMS_ADMIN_PASSWORD (minimum 12 characters) are required in production.")
            conn.execute(
                "UPDATE users SET username = ?, password_hash = ?, full_name = ?, is_active = 1 WHERE role = 'admin'",
                (admin_username, generate_password_hash(admin_password), admin_name),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_stats():
    conn = get_db_connection()
    try:
        queries = {
            "total_clients": "SELECT COUNT(*) FROM clients", "total_jobs": "SELECT COUNT(*) FROM jobs",
            "pending_jobs": "SELECT COUNT(*) FROM jobs WHERE status = 'Pending'",
            "completed_jobs": "SELECT COUNT(*) FROM jobs WHERE status = 'Completed'",
            "total_invoices": "SELECT COUNT(*) FROM invoices", "unpaid_invoices": "SELECT COUNT(*) FROM invoices WHERE status = 'Unpaid'",
            "total_revenue": "SELECT COALESCE(SUM(total_amount), 0) FROM invoices",
            "outstanding_balance": "SELECT COALESCE(SUM(balance_due), 0) FROM invoices WHERE status != 'Paid'",
            "total_payments": "SELECT COALESCE(SUM(amount), 0) FROM payments", "total_expenses": "SELECT COALESCE(SUM(amount), 0) FROM expenses",
        }
        return {key: conn.execute(sql).fetchone()[0] for key, sql in queries.items()}
    finally:
        conn.close()

def get_recent_jobs(limit=5):
    conn = get_db_connection()
    try:
        return conn.execute("""SELECT j.*, c.name as client_name FROM jobs j JOIN clients c ON j.client_id = c.id ORDER BY j.created_at DESC LIMIT ?""", (limit,)).fetchall()
    finally:
        conn.close()

def get_recent_invoices(limit=5):
    conn = get_db_connection()
    try:
        return conn.execute("""SELECT i.*, c.name as client_name FROM invoices i JOIN clients c ON i.client_id = c.id ORDER BY i.created_at DESC LIMIT ?""", (limit,)).fetchall()
    finally:
        conn.close()

def get_monthly_revenue():
    conn = get_db_connection()
    try:
        return conn.execute("""SELECT strftime('%Y-%m', created_at) as month, COALESCE(SUM(total_amount), 0) as revenue,
            COALESCE(SUM(paid_amount), 0) as collected FROM invoices GROUP BY month ORDER BY month DESC LIMIT 12""").fetchall()
    finally:
        conn.close()

def get_outstanding_clients():
    conn = get_db_connection()
    try:
        return conn.execute("""SELECT c.id, c.name, c.phone, COALESCE(SUM(i.balance_due), 0) as total_due,
            COUNT(i.id) as invoice_count FROM clients c JOIN invoices i ON c.id = i.client_id
            WHERE i.balance_due > 0 GROUP BY c.id ORDER BY total_due DESC LIMIT 10""").fetchall()

    finally:
        conn.close()

def get_setting(key, default=''):
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        return row['value'] if row and row['value'] is not None else default
    finally:
        conn.close()

def set_setting(key, value):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO app_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
        conn.commit()
    finally:
        conn.close()
