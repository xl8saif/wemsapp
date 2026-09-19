# Waraq Enterprise Management System (WEMS)

WEMS is a business management system for Waraq Enterprises, Gilgit. The same codebase now supports both the existing offline Windows/SQLite mode and an online multi-user deployment backed by PostgreSQL.

## Deployment modes

- **Offline desktop:** no DATABASE_URL; WEMS uses local SQLite at database/waraq.db.
- **Online web:** set DATABASE_URL to a PostgreSQL connection URL; WEMS uses PostgreSQL and supports concurrent web users.
- The Windows build remains SQLite-based unless DATABASE_URL is deliberately configured.
- Do not expose the SQLite database directly to the internet.

## Online architecture

Browser → Flask/WSGI → PostgreSQL

Generated files such as invoices, exports, profile uploads and CVs remain on the application server. Database backups should be handled by the PostgreSQL provider rather than copying a live PostgreSQL data file.

## Migrating existing office data

Do not upload waraq.db to a public repository or replace the production database blindly. First create a verified backup, provision PostgreSQL, then run:

```bash
python scripts/migrate_sqlite_to_postgres.py --sqlite database/waraq.db --database-url "postgresql://USER:PASSWORD@HOST:5432/DBNAME"
```

The migration refuses a non-empty destination unless `--replace` is explicitly supplied. Verify row counts and sample invoices/users after migration before switching the live site to the database URL.



## Current capabilities

- Client management
- Job and service tracking
- Professional invoice creation
- Invoice PDF generation and print views
- Payment recording with server-side balance protection
- Revenue and outstanding-balance reports
- Excel export for clients, invoices, and jobs
- SQLite database backup and download
- Urdu RTL interface with English/Urdu switching
- Bundled local assets for offline runtime use
- Waraq and CloudTrans branding, signature and stamp support

## Offline architecture

WEMS does not require an internet connection during normal operation. Runtime CSS, icons, JavaScript charting, and the Urdu font are stored locally in the repository. External links shown in the profile area are ordinary navigation links and are not required for application operation.

The Urdu interface uses the locally bundled Noto Nastaliq Urdu font. The application also includes a lightweight local chart engine, so dashboard analytics do not depend on a CDN.

## Tech stack

- Python / Flask
- SQLite
- HTML5 / CSS3 / JavaScript
- Local Canvas-based chart engine
- xhtml2pdf for PDF generation
- openpyxl for Excel export
- Pillow for image handling

## Run from source

1. Install Python 3.8 or newer.
2. Open Command Prompt or PowerShell in the WEMS folder.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start WEMS:

```bash
python app.py
```

5. Open:

```text
http://127.0.0.1:5000
```

The application binds to localhost only and runs with Flask debug mode disabled by default.

## Data and generated files

The SQLite database is created automatically at `database/waraq.db` when WEMS starts. Generated invoices, Excel exports, and database backups are kept in the `invoices/`, `exports/`, and `backups/` directories respectively.

For a future Windows installer, these writable data directories should be moved to a per-user application-data directory rather than Program Files.

## Folder structure

```text
Waraq-Enterprise-Management-System/
├── app.py
├── config.py
├── requirements.txt
├── database/
│   ├── db.py
│   └── waraq.db                 # auto-created locally
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── clients/
│   ├── jobs/
│   ├── invoices/
│   └── payments/
├── static/
│   ├── css/
│   │   ├── style.css
│   │   ├── branding.css
│   │   ├── fonts.css
│   │   └── offline-icons.css
│   ├── fonts/
│   │   └── NotoNastaliqUrdu-Regular.ttf
│   ├── images/
│   │   ├── waraq-logo.png
│   │   ├── cloudtrans-logo.png
│   │   ├── saif-ullah.jpg
│   │   ├── Waraq-Stamp.jpg
│   │   └── Waraq-Signature.jpg
│   └── js/
│       ├── app.js
│       ├── chart.min.js
│       ├── i18n.js
│       └── invoice-language.js
├── invoices/
├── exports/
└── backups/
```

## Branding and configuration

Company details and canonical local asset paths are defined in `config.py`. Current WEMS assets are stored under `static/images/` and should not be renamed without updating configuration and templates.

The application is branded as:

**ورق انٹرپرائز مینجمنٹ سسٹم (WEMS)**

A project of Waraq Enterprises, Gilgit.

Developed by **سید سیف اللہ جیلانی**.

## License

Proprietary - Waraq Enterprises, Gilgit
