# Waraq Enterprise Management System (WEMS)

WEMS is a business management system for Waraq Enterprises, Gilgit. The same codebase supports offline Windows/SQLite operation and online multi-user deployment backed by PostgreSQL.

## Deployment modes

- **Offline desktop:** no DATABASE_URL; WEMS uses local SQLite at database/waraq.db.
- **Online web:** set DATABASE_URL to PostgreSQL; WEMS supports concurrent web users.
- The Windows build remains SQLite-based unless DATABASE_URL is deliberately configured.
- Do not expose the SQLite database directly to the internet.

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

## Tech stack

- Python / Flask
- SQLite / PostgreSQL
- HTML5 / CSS3 / JavaScript
- xhtml2pdf for PDF generation
- openpyxl for Excel export
- Pillow for image handling

## Developer portfolio

WEMS is part of Saif Ullah's multilingual technology and localization work.

Portfolio: https://xl8saif.github.io/site/

Professional focus: Arabic ↔ Urdu translation, localization, LQA, MTPE, AI data and language technology.

## Run from source

1. Install Python 3.8 or newer.
2. Open Command Prompt or PowerShell in the WEMS folder.
3. Install dependencies: `pip install -r requirements.txt`
4. Start WEMS: `python app.py`
5. Open `http://127.0.0.1:5000`

The application binds to localhost only and runs with Flask debug mode disabled by default.

## Data and generated files

The SQLite database is created automatically at `database/waraq.db` when WEMS starts. Generated invoices, Excel exports, and database backups are kept in the `invoices/`, `exports/`, and `backups/` directories respectively.

For production PostgreSQL deployments, verify backups, row counts and sample invoices before switching the live site to a database URL.

## Branding

Company details and canonical local asset paths are defined in `config.py`.

**ورق انٹرپرائز مینجمنٹ سسٹم (WEMS)**  
A project of Waraq Enterprises, Gilgit.  
Developed by **سید سیف اللہ جیلانی**.

## License

Proprietary - Waraq Enterprises, Gilgit
