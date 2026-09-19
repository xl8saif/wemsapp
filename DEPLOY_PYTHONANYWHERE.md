# Deploying WEMS online on PythonAnywhere

WEMS supports a normal Flask/WSGI deployment with PostgreSQL. PythonAnywhere documents manual Flask deployments through a WSGI entry point; do not run Flask's development server on the hosted site.

## 1. Provision PostgreSQL

PythonAnywhere-hosted PostgreSQL requires a paid account. A paid PythonAnywhere account can also connect to an external PostgreSQL service.

Create a dedicated PostgreSQL database and application user. Keep the database credentials private.

## 2. Clone WEMS

```bash
git clone -b online-migration https://github.com/xl8saif/wemsapp.git ~/wemsapp
cd ~/wemsapp
```

## 3. Create the virtual environment

Use the Python version supported by your PythonAnywhere account and keep it consistent with the web app configuration.

```bash
mkvirtualenv wems-env --python=$(which python3.12)
pip install -r ~/wemsapp/requirements.txt
```

Psycopg 3 currently supports Python 3.10–3.15 and provides binary wheels, so it is suitable for the project's current Python range.

## 4. Migrate the office SQLite database

First copy the office database to a safe location and verify the backup.

Then, from a machine that can reach the PostgreSQL server:

```bash
python scripts/migrate_sqlite_to_postgres.py \
  --sqlite database/waraq.db \
  --database-url "postgresql://USER:PASSWORD@HOST:5432/DBNAME"
```

The migration tool refuses to write into a non-empty target unless `--replace` is explicitly supplied.

## 5. Configure the web application

Set these environment variables in the hosting environment:

```text
WEMS_ENV=production
SECRET_KEY=<long-random-secret>
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME
```

Generate a secret with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Do not commit DATABASE_URL or SECRET_KEY to GitHub.

## 6. Configure WSGI

Use the repository's `wsgi.py` as the application entry point:

```python
import sys
path = '/home/USERNAME/wemsapp'
if path not in sys.path:
    sys.path.insert(0, path)

from wsgi import application
```

PythonAnywhere's standard Flask deployment uses the WSGI configuration and does not require `app.run()`; WEMS keeps `app.run()` behind the normal Python main guard for local Windows use.

## 7. Static files

If using the standard PythonAnywhere web configuration, map:

```text
URL: /static/
Directory: /home/USERNAME/wemsapp/static/
```

Keep private uploads outside the public static directory where possible.

## 8. First login

Open the site once. If the migrated database contains users, the setup page is already locked. Log in with an existing account.

If this is a new database, visit `/setup` immediately and create the first admin account before sharing the URL.

## 9. Updating the application

```bash
cd ~/wemsapp
git pull origin online-migration
source ~/.virtualenvs/wems-env/bin/activate
pip install -r requirements.txt
```

Then reload the web app from the PythonAnywhere Web tab.

## 10. Important operational rules

- PostgreSQL is the source of truth for the online instance.
- Keep the existing office SQLite database as a separate offline copy during the transition.
- Do not use the old SQLite `/backup` mechanism for PostgreSQL.
- Use PostgreSQL provider backups/snapshots and test restoration periodically.
- Do not expose database credentials, exported dumps, CVs, or uploaded documents through GitHub.
- The online instance should use HTTPS and production SECRET_KEY settings.

## Architecture

```
Users' browsers
      |
      v
PythonAnywhere HTTPS / WSGI
      |
      v
WEMS Flask application
      |
      v
PostgreSQL
```

The Windows build continues to use:

```
Windows WEMS -> local SQLite -> offline operation
```

This lets the online and offline editions share application code without forcing the office desktop to depend on an internet connection.
