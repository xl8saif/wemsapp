"""One-time SQLite -> PostgreSQL migration for WEMS.

Usage:
  python scripts/migrate_sqlite_to_postgres.py --sqlite database/waraq.db --database-url "postgresql://..."

The destination must be empty unless --replace is supplied.
"""
import argparse
import os
import sqlite3

TABLES = [
    "clients", "services", "jobs", "invoices", "invoice_items",
    "payments", "expenses", "users", "user_profile", "app_settings",
]

def sqlite_columns(conn, table):
    return [row[1] for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", required=True)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.sqlite):
        raise SystemExit(f"SQLite database not found: {args.sqlite}")

    os.environ["DATABASE_URL"] = args.database_url
    from database.db import get_db_connection, init_db

    src = sqlite3.connect(args.sqlite)
    src.row_factory = sqlite3.Row
    dst = None
    try:
        init_db()
        dst = get_db_connection()
        counts = {table: dst.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in TABLES}
        if any(counts.values()) and not args.replace:
            raise SystemExit("Destination is not empty. Use --replace only after verifying the target database.")

        if args.replace:
            dst.execute(
                "TRUNCATE TABLE app_settings, user_profile, users, expenses, payments, "
                "invoice_items, invoices, jobs, services, clients RESTART IDENTITY CASCADE"
            )
            dst.commit()

        for table in TABLES:
            source_columns = sqlite_columns(src, table)
            target_columns = list(source_columns)
            if table == "user_profile" and "user_id" not in source_columns:
                target_columns.append("user_id")

            select_sql = ", ".join(source_columns)
            rows = src.execute(f'SELECT {select_sql} FROM "{table}"').fetchall()
            if not rows:
                continue

            values = []
            for row in rows:
                item = [row[col] for col in source_columns]
                if "user_id" not in source_columns and table == "user_profile":
                    item.append(None)
                values.append(tuple(item))

            columns_sql = ", ".join(target_columns)
            placeholders = ", ".join(["?"] * len(target_columns))
            dst.executemany(
                f"INSERT INTO {table} ({columns_sql}) VALUES ({placeholders})",
                values,
            )
            dst.commit()
            print(f"{table}: {len(rows)} rows")

        for table in TABLES:
            if table == "app_settings":
                continue
            try:
                dst.execute(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                    f"COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM {table}"
                )
            except Exception:
                dst.rollback()
        dst.commit()
        print("Migration completed successfully.")
    finally:
        src.close()
        if dst:
            dst.close()

if __name__ == "__main__":
    main()
