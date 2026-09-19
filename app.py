import os
import io
import re
import shutil
import glob as globmod
import hmac
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from xhtml2pdf import pisa
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

from config import Config
from database.db import (
    get_db_connection,
    init_db,
    get_stats,
    get_recent_jobs,
    get_recent_invoices,
    get_monthly_revenue,
    get_outstanding_clients,
    get_setting,
    set_setting,
    DBIntegrityError,
    get_db_backend,
)

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# ==================== DOCUMENT LANGUAGE ====================
# Printable documents (invoice print view / PDF) follow the UI language.
# i18n.js mirrors the toggle choice into the `wems-lang` cookie; the server
# reads it here so server-rendered PDFs come out in the same language.

def get_doc_lang():
    return 'en' if request.cookies.get('wems-lang') == 'en' else 'ur'

def get_static_image_path(filename):
    """Absolute filesystem path to a bundled static image (for xhtml2pdf)."""
    return os.path.join(app.root_path, 'static', 'images', filename)

def _pdf_link_callback(uri, rel):
    """Map relative font/image URLs in the PDF template to real files.
    Without this, xhtml2pdf resolves them against the process CWD and fails
    on Windows (empty temp copy that reportlab cannot open)."""
    if uri.startswith(('static/', '/static/')):
        return os.path.join(app.root_path, uri.lstrip('/').replace('/', os.sep))
    return uri

_urdu_pdf_font_ready = False

def _ensure_urdu_pdf_font():
    """Register the Nastaliq font with reportlab directly, bypassing
    xhtml2pdf's @font-face loader which breaks on Windows (it copies the TTF
    to a locked temp file that reportlab cannot re-open). The PDF template's
    CSS then just references the pre-registered family name."""
    global _urdu_pdf_font_ready
    if _urdu_pdf_font_ready:
        return
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont as RLTTFont
        from xhtml2pdf import default as pisa_default
        font_path = os.path.join(app.root_path, 'static', 'fonts', 'NotoNastaliqUrdu-Regular.ttf')
        pdfmetrics.registerFont(RLTTFont('NotoNastaliqUrdu', font_path))
        pisa_default.DEFAULT_FONT['notonastaliqurdu'] = 'NotoNastaliqUrdu'
        _urdu_pdf_font_ready = True
    except Exception:
        pass  # PDF still generates with the fallback font

# Ensure directories exist
for directory in [Config.INVOICE_DIR, Config.EXPORT_DIR, Config.BACKUP_DIR, Config.STATIC_IMAGE_DIR]:
    os.makedirs(directory, exist_ok=True)

# ==================== AUTHENTICATION ====================

def safe_prune_backups(keep=30):
    """Delete old automatic backups, keeping the newest `keep` files."""
    try:
        backups = sorted(
            globmod.glob(os.path.join(Config.BACKUP_DIR, '*.db')),
            key=lambda p: (os.path.getmtime(p), os.path.basename(p)),
            reverse=True
        )
        for old in backups[keep:]:
            try:
                os.remove(old)
            except OSError:
                pass
    except OSError:
        pass

def auto_backup():
    """Back up SQLite locally; PostgreSQL is backed up by the database provider."""
    if get_db_backend() != "sqlite":
        return
    try:
        stamp = datetime.now().strftime('%Y%m%d')
        marker = os.path.join(Config.BACKUP_DIR, f'.autobackup_{stamp}')
        if os.path.exists(marker):
            return
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(Config.BACKUP_DIR, f'waraq_auto_{timestamp}.db')
        shutil.copy2(Config.DATABASE, backup_path)
        with open(marker, 'w') as f:
            f.write(timestamp)
        safe_prune_backups(keep=30)
    except Exception:
        # Backup problems must never stop the office from working.
        pass

# Initialize database on startup
init_db()
auto_backup()

# ==================== LOGIN GATE ====================

@app.before_request
def require_login():
    allowed = ('login', 'setup', 'static', 'healthz')
    if request.endpoint in allowed:
        return None
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return None

# ==================== USER ACCOUNTS / AUTH ====================

def _users_count():
    conn = get_db_connection()
    n = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return n

def _current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    conn = get_db_connection()
    row = conn.execute(
        """SELECT u.*, p.photo FROM users u
           LEFT JOIN user_profile p ON p.user_id = u.id
           WHERE u.id = ? AND u.is_active = 1""", (uid,)
    ).fetchone()
    conn.close()
    return row

def _require_admin():
    user = _current_user()
    if not user or user['role'] != 'admin':
        return None
    return user

@app.route('/healthz')
def healthz():
    """Lightweight deployment health check; verifies database connectivity."""
    conn = get_db_connection()
    try:
        conn.execute("SELECT 1").fetchone()
        return jsonify({"status": "ok", "database": get_db_backend()})
    finally:
        conn.close()

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """First-run registration: creates the first admin account.
    Blocked once any user exists."""
    if _users_count() > 0:
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        if not username or not full_name:
            flash('Client name is required.', 'error')
            return redirect(url_for('setup'))
        if len(password) < 6:
            flash('پاس ورڈ کم از کم 6 حروف کا ہونا چاہیے۔ Password must be at least 6 characters.', 'error')
            return redirect(url_for('setup'))
        if password != confirm:
            flash('پاس ورڈز مشابہ نہیں ہیں۔ Passwords do not match.', 'error')
            return redirect(url_for('setup'))
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, 'admin')",
                (username, generate_password_hash(password), full_name),
            )
            conn.commit()
        except DBIntegrityError:
            conn.close()
            flash('یہ صارف نام پہلے سے موجود ہے۔ Username already exists.', 'error')
            return redirect(url_for('setup'))
        conn.close()
        flash('ایڈمین اکاؤنٹ بنا دیا گیا۔ اب داخل ہوں۔ Admin account created. Please sign in.', 'success')
        return redirect(url_for('login'))
    return render_template('setup.html')

# --- Login brute-force protection (per-username lockout) ---
# Keyed by username rather than IP: hosts like PythonAnywhere sit behind a
# shared proxy, so an IP-based ban would lock out every legitimate user.
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCK_SECONDS = 600  # 10 minutes
_failed_logins = {}  # username -> {'count': int, 'locked_until': datetime|None}

def _login_locked_until(username):
    """Return the datetime until which `username` is locked out, or None."""
    rec = _failed_logins.get(username)
    if rec and rec.get('locked_until'):
        if datetime.now() < rec['locked_until']:
            return rec['locked_until']
    return None

def _record_failed_login(username):
    rec = _failed_logins.setdefault(username, {'count': 0, 'locked_until': None})
    rec['count'] += 1
    if rec['count'] >= LOGIN_MAX_ATTEMPTS:
        rec['locked_until'] = datetime.now() + timedelta(seconds=LOGIN_LOCK_SECONDS)
        rec['count'] = 0

def _clear_failed_logins(username):
    _failed_logins.pop(username, None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if _users_count() == 0:
        return redirect(url_for('setup'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        locked_until = _login_locked_until(username)
        if locked_until:
            minutes = max(1, int((locked_until - datetime.now()).total_seconds() // 60) + 1)
            flash(
                f'بہت زیادہ غلط کوششیں۔ تقریباً {minutes} منٹ بعد دوبارہ کوشش کریں۔ '
                f'Too many failed attempts. Please try again in about {minutes} minutes.',
                'error',
            )
        else:
            conn = get_db_connection()
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)
            ).fetchone()
            conn.close()
            if user and check_password_hash(user['password_hash'], password):
                _clear_failed_logins(username)
                session.permanent = True
                session['user_id'] = user['id']
                return redirect(url_for('dashboard'))
            _record_failed_login(username)
            flash('غلط صارف نام یا پاس ورڈ۔ Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ==================== HELPERS ====================


def parse_nonnegative_decimal(value, field_name, allow_zero=True):
    """Parse a monetary/quantity value safely and reject invalid input."""
    raw = str(value if value is not None else "").strip()
    if raw == "":
        return Decimal("0") if allow_zero else None
    try:
        number = Decimal(raw)
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid {field_name}.")
    if not number.is_finite():
        raise ValueError(f"Invalid {field_name}.")
    if number < 0 or (not allow_zero and number <= 0):
        raise ValueError(f"{field_name} must be {'zero or greater' if allow_zero else 'greater than zero'}.")
    return number


def valid_date(value, field_name, required=False):
    value = (value or "").strip()
    if not value:
        if required:
            raise ValueError(f"{field_name} is required.")
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid {field_name}.")
    return value


def get_invoice_or_404(conn, invoice_id):
    invoice = conn.execute(
        "SELECT * FROM invoices WHERE id = ?", (invoice_id,)
    ).fetchone()
    return invoice


@app.context_processor
def inject_globals():
    return {
        'company_name': Config.COMPANY_NAME,
        'company_address': Config.COMPANY_ADDRESS,
        'company_phone': Config.COMPANY_PHONE,
        'company_email': Config.COMPANY_EMAIL,
        'currency': Config.CURRENCY,
        'current_year': datetime.now().year,
        'current_user': _current_user(),
    }

# ==================== VALIDATION HELPERS ====================

def parse_float(value, field_label, default=None):
    """Parse a money/quantity field. On bad input, flash a friendly message
    and return `default` so the caller can re-render the form."""
    if value is None or str(value).strip() == '':
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        flash(f'Invalid number entered in "{field_label}". Please enter digits only.', 'error')
        return None

# ==================== DASHBOARD ====================

def _parse_linkedin_activity(url):
    """Extract the numeric activity ID from a LinkedIn post URL.
    Accepts every common form: /feed/update/urn:li:activity:ID,
    /embed/feed/update/urn:li:activity:ID, /posts/slug-activity-ID,
    /activity:ID and /share/... ; returns the digits or None."""
    m = re.search(r'(?:activity|share)[:\-/]+(\d{15,25})', url or '')
    return m.group(1) if m else None

@app.route("/")
def dashboard():
    stats = get_stats()
    recent_jobs = get_recent_jobs()
    recent_invoices = get_recent_invoices()
    outstanding = get_outstanding_clients()
    monthly_data = get_monthly_revenue()
    months = [row["month"] for row in reversed(monthly_data)]
    revenues = [float(row["revenue"]) for row in reversed(monthly_data)]
    collected = [float(row["collected"]) for row in reversed(monthly_data)]
    # Pinned LinkedIn posts shown in the developer card (admin-managed).
    li_raw = get_setting('linkedin_posts', '')
    li_posts = [a for a in li_raw.split(',') if a.strip()][:4]
    return render_template(
        "dashboard.html",
        stats=stats,
        recent_jobs=recent_jobs,
        recent_invoices=recent_invoices,
        outstanding=outstanding,
        months=months,
        revenues=revenues,
        collected=collected,
        li_posts=li_posts,
    )


# ==================== CLIENTS ====================

@app.route("/clients")
def clients_list():
    conn = get_db_connection()
    search = request.args.get("search", "")
    client_type = request.args.get("type", "")
    query = "SELECT * FROM clients WHERE 1=1"
    params = []
    if search:
        query += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ? OR cnic LIKE ?)"
        params.extend([f"%{search}%"] * 4)
    if client_type:
        query += " AND client_type = ?"
        params.append(client_type)
    query += " ORDER BY name"
    clients = conn.execute(query, params).fetchall()
    conn.close()
    return render_template("clients/list.html", clients=clients, search=search, client_type=client_type)


@app.route("/clients/add", methods=["GET", "POST"])
def client_add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Client name is required.', 'error')
            return render_template('clients/form.html', client=None)
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO clients (name, contact_person, phone, email, address, cnic, client_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            request.form.get('contact_person', ''),
            request.form.get('phone', ''),
            request.form.get('email', ''),
            request.form.get('address', ''),
            request.form.get('cnic', ''),
            request.form.get('client_type', 'Individual')
        ))
        conn.commit()
        conn.close()
        flash("Client added successfully!", "success")
        return redirect(url_for("clients_list"))
    return render_template("clients/form.html", client=None)


@app.route("/clients/<int:id>")
def client_detail(id):
    conn = get_db_connection()
    client = conn.execute("SELECT * FROM clients WHERE id = ?", (id,)).fetchone()
    if not client:
        conn.close()
        return "Client not found", 404
    jobs = conn.execute("SELECT * FROM jobs WHERE client_id = ? ORDER BY created_at DESC", (id,)).fetchall()
    invoices = conn.execute("SELECT * FROM invoices WHERE client_id = ? ORDER BY created_at DESC", (id,)).fetchall()
    total_billed = conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE client_id = ?", (id,)).fetchone()[0]
    total_paid = conn.execute("SELECT COALESCE(SUM(paid_amount), 0) FROM invoices WHERE client_id = ?", (id,)).fetchone()[0]
    balance = total_billed - total_paid
    conn.close()
    return render_template("clients/detail.html", client=client, jobs=jobs, invoices=invoices,
                           total_billed=total_billed, total_paid=total_paid, balance=balance)


@app.route("/clients/<int:id>/edit", methods=["GET", "POST"])
def client_edit(id):
    conn = get_db_connection()
    client = conn.execute("SELECT * FROM clients WHERE id = ?", (id,)).fetchone()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            conn.close()
            flash('Client name is required.', 'error')
            return render_template('clients/form.html', client=client)
        conn.execute("""
            UPDATE clients SET name=?, contact_person=?, phone=?, email=?, address=?, cnic=?, client_type=?
            WHERE id=?
        """, (
            name, request.form.get('contact_person', ''),
            request.form.get('phone', ''), request.form.get('email', ''),
            request.form.get('address', ''), request.form.get('cnic', ''),
            request.form.get('client_type', 'Individual'), id
        ))
        conn.commit()
        conn.close()
        flash("Client updated successfully!", "success")
        return redirect(url_for("client_detail", id=id))
    conn.close()
    return render_template("clients/form.html", client=client)


@app.route("/clients/<int:id>/delete", methods=["POST"])
def client_delete(id):
    conn = get_db_connection()
    invoice_count = conn.execute("SELECT COUNT(*) FROM invoices WHERE client_id = ?", (id,)).fetchone()[0]
    if invoice_count > 0:
        conn.close()
        flash('This client has invoices on record and cannot be deleted. Delete or reassign their invoices first.', 'error')
        return redirect(url_for('clients_list'))
    job_count = conn.execute("SELECT COUNT(*) FROM jobs WHERE client_id = ?", (id,)).fetchone()[0]
    if job_count > 0:
        conn.close()
        flash('This client has jobs on record and cannot be deleted. Delete their jobs first.', 'error')
        return redirect(url_for('clients_list'))
    cursor = conn.execute("DELETE FROM clients WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        flash("Client not found.", "error")
    else:
        flash("Client deleted successfully!", "success")
    return redirect(url_for("clients_list"))


# ==================== SERVICES ====================

@app.route("/services")
def services_list():
    conn = get_db_connection()
    services = conn.execute("SELECT * FROM services WHERE is_active = 1 ORDER BY category, service_name").fetchall()
    conn.close()
    return render_template("services/list.html", services=services)


@app.route("/services/add", methods=["POST"])
def service_add():
    service_name = request.form.get('service_name', '').strip()
    category = request.form.get('category', '').strip()
    if not service_name or not category:
        flash('Service name and category are required.', 'error')
        return redirect(url_for('services_list'))
    base_price = parse_float(request.form.get('base_price'), 'Base Price', 0)
    if base_price is None:
        return redirect(url_for('services_list'))
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO services (service_name, category, description, base_price)
        VALUES (?, ?, ?, ?)
    """, (
        service_name, category,
        request.form.get('description', ''), base_price
    ))
    conn.commit()
    conn.close()
    flash("Service added successfully!", "success")
    return redirect(url_for("services_list"))


@app.route("/services/<int:id>/edit", methods=["POST"])
def service_edit(id):
    service_name = request.form.get('service_name', '').strip()
    category = request.form.get('category', '').strip()
    if not service_name or not category:
        flash('Service name and category are required.', 'error')
        return redirect(url_for('services_list'))
    base_price = parse_float(request.form.get('base_price'), 'Base Price', 0)
    if base_price is None:
        return redirect(url_for('services_list'))
    conn = get_db_connection()
    conn.execute("""
        UPDATE services SET service_name=?, category=?, description=?, base_price=?
        WHERE id=?
    """, (
        service_name, category,
        request.form.get('description', ''), base_price, id
    ))
    conn.commit()
    conn.close()
    flash("Service updated!", "success")
    return redirect(url_for("services_list"))


@app.route("/services/<int:id>/delete", methods=["POST"])
def service_delete(id):
    conn = get_db_connection()
    cursor = conn.execute("UPDATE services SET is_active = 0 WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Service deleted!" if cursor.rowcount else "Service not found.", "success" if cursor.rowcount else "error")
    return redirect(url_for("services_list"))


# ==================== JOBS ====================

@app.route("/jobs")
def jobs_list():
    conn = get_db_connection()
    status = request.args.get("status", "")
    category = request.args.get("category", "")
    search = request.args.get("search", "")
    query = """SELECT j.*, c.name as client_name, s.service_name
               FROM jobs j JOIN clients c ON j.client_id = c.id
               LEFT JOIN services s ON j.service_id = s.id WHERE 1=1"""
    params = []
    if status:
        query += " AND j.status = ?"
        params.append(status)
    if category:
        query += " AND j.category = ?"
        params.append(category)
    if search:
        query += " AND (j.job_title LIKE ? OR c.name LIKE ? OR j.description LIKE ?)"
        params.extend([f"%{search}%"] * 3)
    query += " ORDER BY j.created_at DESC"
    jobs = conn.execute(query, params).fetchall()
    categories = conn.execute("SELECT DISTINCT category FROM jobs ORDER BY category").fetchall()
    conn.close()
    return render_template("jobs/list.html", jobs=jobs, categories=categories, status=status, category=category, search=search)


@app.route("/jobs/add", methods=["GET", "POST"])
def job_add():
    conn = get_db_connection()
    clients = conn.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
    services = conn.execute("SELECT * FROM services WHERE is_active=1 ORDER BY service_name").fetchall()

    if request.method == 'POST':
        if not request.form.get('client_id') or not request.form.get('job_title', '').strip():
            conn.close()
            flash('Client and job title are required.', 'error')
            return render_template('jobs/form.html', job=None, clients=clients, services=services)
        cost = parse_float(request.form.get('cost'), 'Cost', 0)
        if cost is None:
            conn.close()
            return render_template('jobs/form.html', job=None, clients=clients, services=services)
        conn.execute("""
            INSERT INTO jobs (client_id, service_id, job_title, category, description, 
                            priority, assigned_to, start_date, due_date, cost, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form['client_id'], request.form.get('service_id') or None,
            request.form['job_title'].strip(), request.form['category'],
            request.form.get('description', ''), request.form.get('priority', 'Normal'),
            request.form.get('assigned_to', ''), request.form.get('start_date'),
            request.form.get('due_date'), cost,
            request.form.get('notes', '')
        ))
        conn.commit()
        conn.close()
        flash("Job created successfully!", "success")
        return redirect(url_for("jobs_list"))
    conn.close()
    return render_template("jobs/form.html", job=None, clients=clients, services=services)


@app.route("/jobs/<int:id>")
def job_detail(id):
    conn = get_db_connection()
    job = conn.execute("""SELECT j.*, c.name as client_name, c.phone as client_phone, c.address as client_address,
                         s.service_name, s.base_price FROM jobs j JOIN clients c ON j.client_id=c.id
                         LEFT JOIN services s ON j.service_id=s.id WHERE j.id=?""", (id,)).fetchone()
    conn.close()
    if not job:
        return "Job not found", 404
    return render_template("jobs/detail.html", job=job)


@app.route("/jobs/<int:id>/edit", methods=["GET", "POST"])
def job_edit(id):
    conn = get_db_connection()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (id,)).fetchone()
    if not job:
        conn.close()
        return "Job not found", 404
    clients = conn.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
    services = conn.execute("SELECT * FROM services WHERE is_active=1 ORDER BY service_name").fetchall()

    if request.method == 'POST':
        if not request.form.get('client_id') or not request.form.get('job_title', '').strip():
            conn.close()
            flash('Client and job title are required.', 'error')
            return render_template('jobs/form.html', job=job, clients=clients, services=services)
        cost = parse_float(request.form.get('cost'), 'Cost', 0)
        if cost is None:
            conn.close()
            return render_template('jobs/form.html', job=job, clients=clients, services=services)

        status = request.form.get('status', job['status'])
        completed_date = None
        if status == 'Completed' and job['status'] != 'Completed':
            completed_date = datetime.now().strftime('%Y-%m-%d')
        elif status != 'Completed':
            completed_date = None
        else:
            completed_date = job['completed_date']

        conn.execute("""
            UPDATE jobs SET client_id=?, service_id=?, job_title=?, category=?, description=?,
                          status=?, priority=?, assigned_to=?, start_date=?, due_date=?,
                          completed_date=?, cost=?, notes=?
            WHERE id=?
        """, (
            request.form['client_id'], request.form.get('service_id') or None,
            request.form['job_title'].strip(), request.form['category'],
            request.form.get('description', ''), status,
            request.form.get('priority', 'Normal'), request.form.get('assigned_to', ''),
            request.form.get('start_date'), request.form.get('due_date'),
            completed_date, cost, request.form.get('notes', ''), id
        ))
        conn.commit()
        conn.close()
        flash("Job updated successfully!", "success")
        return redirect(url_for("job_detail", id=id))
    conn.close()
    return render_template("jobs/form.html", job=job, clients=clients, services=services)


@app.route("/jobs/<int:id>/delete", methods=["POST"])
def job_delete(id):
    conn = get_db_connection()
    invoice_count = conn.execute("SELECT COUNT(*) FROM invoices WHERE job_id = ?", (id,)).fetchone()[0]
    if invoice_count > 0:
        conn.close()
        flash('This job has invoices linked to it and cannot be deleted.', 'error')
        return redirect(url_for('jobs_list'))
    cursor = conn.execute("DELETE FROM jobs WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Job deleted!" if cursor.rowcount else "Job not found.", "success" if cursor.rowcount else "error")
    return redirect(url_for("jobs_list"))


# ==================== INVOICES ====================

@app.route("/invoices")
def invoices_list():
    conn = get_db_connection()
    status = request.args.get("status", "")
    search = request.args.get("search", "")
    query = """SELECT i.*, c.name as client_name, c.phone as client_phone
               FROM invoices i JOIN clients c ON i.client_id=c.id WHERE 1=1"""
    params = []
    if status:
        query += " AND i.status=?"
        params.append(status)
    if search:
        query += " AND (i.invoice_number LIKE ? OR c.name LIKE ?)"
        params.extend([f"%{search}%"] * 2)
    query += " ORDER BY i.created_at DESC"
    invoices = conn.execute(query, params).fetchall()
    conn.close()
    return render_template("invoices/list.html", invoices=invoices, status=status, search=search)


@app.route("/invoices/create", methods=["GET", "POST"])
def invoice_create():
    conn = get_db_connection()
    clients = conn.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
    services = conn.execute("SELECT * FROM services WHERE is_active=1 ORDER BY service_name").fetchall()

    if request.method == 'POST':
        client_id = request.form.get('client_id')
        if not client_id:
            conn.close()
            flash('Please select a client.', 'error')
            return render_template('invoices/create.html', clients=clients, services=services)
        client_id = int(client_id)
        job_id = request.form.get('job_id') or None
        issue_date = request.form.get('issue_date', datetime.now().strftime('%Y-%m-%d'))
        due_date = request.form.get('due_date', (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))

        # Generate invoice number: continue from the highest existing number
        # for this month, so deleting an invoice never causes a collision.
        prefix = f"WARQ-{datetime.now().strftime('%Y%m')}-"
        row = conn.execute(
            "SELECT MAX(invoice_number) FROM invoices WHERE invoice_number LIKE ? || '%'",
            (prefix,)
        ).fetchone()
        last_seq = 0
        if row and row[0]:
            try:
                last_seq = int(row[0].rsplit('-', 1)[1])
            except (IndexError, ValueError):
                last_seq = 0
        invoice_number = f"{prefix}{last_seq + 1:04d}"

        # Calculate totals from items
        descriptions = request.form.getlist('item_description[]')
        quantities = request.form.getlist('item_quantity[]')
        unit_prices = request.form.getlist('item_unit_price[]')

        subtotal = 0
        items = []
        valid = True
        for desc, qty, price in zip(descriptions, quantities, unit_prices):
            if desc.strip():
                qty = parse_float(qty, 'Quantity', 1)
                price = parse_float(price, 'Unit Price', 0)
                if qty is None or price is None:
                    valid = False
                    break
                total = qty * price
                subtotal += total
                items.append((desc, qty, price, total))

        discount = parse_float(request.form.get('discount'), 'Discount', 0) if valid else None
        if not valid or discount is None:
            conn.close()
            return render_template('invoices/create.html', clients=clients, services=services)

        tax_amount = subtotal * Config.TAX_RATE
        total_amount = subtotal + tax_amount - discount

        conn.execute("""
            INSERT INTO invoices (invoice_number, client_id, job_id, issue_date, due_date,
                                subtotal, tax_amount, discount, total_amount, balance_due, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (invoice_number, client_id, job_id, issue_date, due_date,
              subtotal, tax_amount, discount, total_amount, total_amount, request.form.get('notes', '')))

        invoice_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        for item in items:
            conn.execute("""
                INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            """, (invoice_id, item[0], item[1], item[2], item[3]))

        conn.commit()
        conn.close()
        flash(f"Invoice {invoice_number} created successfully!", "success")
        return redirect(url_for("invoice_detail", id=invoice_id))
    conn.close()
    return render_template("invoices/create.html", clients=clients, services=services)


@app.route("/invoices/<int:id>")
def invoice_detail(id):
    conn = get_db_connection()
    invoice = conn.execute("""SELECT i.*, c.name as client_name, c.phone as client_phone,
                              c.email as client_email, c.address as client_address, c.cnic as client_cnic
                              FROM invoices i JOIN clients c ON i.client_id=c.id WHERE i.id=?""", (id,)).fetchone()
    if not invoice:
        conn.close()
        return "Invoice not found", 404
    items = conn.execute("SELECT * FROM invoice_items WHERE invoice_id=?", (id,)).fetchall()
    payments = conn.execute("SELECT * FROM payments WHERE invoice_id=? ORDER BY payment_date", (id,)).fetchall()
    conn.close()
    return render_template("invoices/detail.html", invoice=invoice, items=items, payments=payments)


@app.route("/invoices/<int:id>/pdf")
def invoice_pdf(id):
    conn = get_db_connection()
    invoice = conn.execute("""SELECT i.*, c.name as client_name, c.phone as client_phone,
                              c.email as client_email, c.address as client_address, c.cnic as client_cnic
                              FROM invoices i JOIN clients c ON i.client_id=c.id WHERE i.id=?""", (id,)).fetchone()
    if not invoice:
        conn.close()
        return "Invoice not found", 404
    items = conn.execute("SELECT * FROM invoice_items WHERE invoice_id=?", (id,)).fetchall()
    conn.close()

    # Render HTML template for PDF (language follows the UI toggle via cookie)
    _ensure_urdu_pdf_font()
    html = render_template('invoices/invoice_pdf.html', invoice=invoice, items=items,
                           lang=get_doc_lang(),
                           signature_path=get_static_image_path('Waraq-Signature.jpg'),
                           stamp_path=get_static_image_path('Waraq-Stamp.jpg'),
                           waraq_logo_path=get_static_image_path('waraq-logo-transparent.png'),
                           cloudtrans_logo_path=get_static_image_path('cloudtrans-logo-transparent.png'))

    # Generate PDF
    result = io.BytesIO()
    pdf = pisa.CreatePDF(io.StringIO(html), result, link_callback=_pdf_link_callback)

    if not pdf.err:
        response = make_response(result.getvalue())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f'inline; filename=Invoice_{invoice["invoice_number"]}.pdf'
        return response
    flash("Error generating PDF", "error")
    return redirect(url_for("invoice_detail", id=id))


@app.route("/invoices/<int:id>/print")
def invoice_print(id):
    conn = get_db_connection()
    invoice = conn.execute("""SELECT i.*, c.name as client_name, c.phone as client_phone,
                              c.email as client_email, c.address as client_address, c.cnic as client_cnic
                              FROM invoices i JOIN clients c ON i.client_id=c.id WHERE i.id=?""", (id,)).fetchone()
    if not invoice:
        conn.close()
        return "Invoice not found", 404
    items = conn.execute("SELECT * FROM invoice_items WHERE invoice_id=?", (id,)).fetchall()
    conn.close()
    return render_template('invoices/print.html', invoice=invoice, items=items,
                           lang=get_doc_lang(),
                           signature_url=url_for('static', filename='images/Waraq-Signature.jpg'),
                           stamp_url=url_for('static', filename='images/Waraq-Stamp.jpg'),
                           waraq_logo_url=url_for('static', filename='images/waraq-logo-transparent.png'),
                           cloudtrans_logo_url=url_for('static', filename='images/cloudtrans-logo-transparent.png'))


@app.route("/invoices/<int:id>/delete", methods=["POST"])
def invoice_delete(id):
    conn = get_db_connection()
    payment_count = conn.execute("SELECT COUNT(*) FROM payments WHERE invoice_id = ?", (id,)).fetchone()[0]
    if payment_count > 0:
        conn.close()
        flash('This invoice has payments recorded against it and cannot be deleted. Delete its payments first.', 'error')
        return redirect(url_for('invoices_list'))
    conn.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (id,))
    conn.execute("DELETE FROM invoices WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Invoice deleted!", "success")
    return redirect(url_for("invoices_list"))


# ==================== PAYMENTS ====================

@app.route("/payments")
def payments_list():
    conn = get_db_connection()
    payments = conn.execute("""SELECT p.*, c.name as client_name, i.invoice_number
                               FROM payments p JOIN clients c ON p.client_id=c.id
                               JOIN invoices i ON p.invoice_id=i.id ORDER BY p.payment_date DESC""").fetchall()
    conn.close()
    return render_template("payments/list.html", payments=payments)


@app.route("/payments/add", methods=["POST"])
def payment_add():
    invoice_id = request.form.get('invoice_id')
    client_id = request.form.get('client_id')
    payment_date = request.form.get('payment_date') or datetime.now().strftime('%Y-%m-%d')
    payment_method = request.form.get('payment_method', 'Cash')
    reference_no = request.form.get('reference_no', '')
    notes = request.form.get('notes', '')

    amount = parse_float(request.form.get('amount'), 'Amount')
    if amount is None or amount <= 0:
        flash('Payment amount must be a positive number.', 'error')
        return redirect(url_for('invoice_detail', id=invoice_id) if invoice_id else url_for('payments_list'))

    conn = get_db_connection()
    invoice = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    if not invoice:
        conn.close()
        flash('Invoice not found.', 'error')
        return redirect(url_for('payments_list'))
    if amount > invoice['balance_due']:
        conn.close()
        flash(f'Amount exceeds the remaining balance ({invoice["balance_due"]:,.2f}). Please record a smaller payment.', 'error')
        return redirect(url_for('invoice_detail', id=invoice_id))

    conn.execute("""
        INSERT INTO payments (invoice_id, client_id, amount, payment_date, payment_method, reference_no, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (invoice_id, client_id, amount, payment_date, payment_method, reference_no, notes))

    # Update invoice
    conn.execute("""
        UPDATE invoices 
        SET paid_amount = paid_amount + ?, 
            balance_due = balance_due - ?,
            status = CASE 
                WHEN balance_due - ? <= 0 THEN 'Paid'
                WHEN paid_amount + ? > 0 THEN 'Partial'
                ELSE status
            END
        WHERE id = ?
    """, (amount, amount, amount, amount, invoice_id))

    conn.commit()
    conn.close()
    flash("Payment recorded successfully!", "success")
    return redirect(url_for("invoice_detail", id=invoice_id))


# ==================== EXPENSES ====================

@app.route('/expenses')
def expenses_list():
    conn = get_db_connection()

    month = request.args.get('month', '')
    category = request.args.get('category', '')

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if month:
        query += " AND strftime('%Y-%m', expense_date) = ?"
        params.append(month)
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY expense_date DESC, id DESC"
    expenses = conn.execute(query, params).fetchall()

    total = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses").fetchone()[0]
    month_total = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE strftime('%Y-%m', expense_date) = ?",
        (datetime.now().strftime('%Y-%m'),)
    ).fetchone()[0]
    categories = conn.execute("SELECT DISTINCT category FROM expenses ORDER BY category").fetchall()

    conn.close()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('expenses/list.html', expenses=expenses, total=total,
                         month_total=month_total, categories=categories,
                         month=month, category=category, today=today)

@app.route('/expenses/add', methods=['POST'])
def expense_add():
    category = request.form.get('category', '').strip()
    expense_date = request.form.get('expense_date') or datetime.now().strftime('%Y-%m-%d')
    if not category:
        flash('Expense category is required.', 'error')
        return redirect(url_for('expenses_list'))
    amount = parse_float(request.form.get('amount'), 'Amount')
    if amount is None or amount <= 0:
        flash('Expense amount must be a positive number.', 'error')
        return redirect(url_for('expenses_list'))

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO expenses (category, description, amount, expense_date, paid_by, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        category,
        request.form.get('description', ''),
        amount,
        expense_date,
        request.form.get('paid_by', ''),
        request.form.get('notes', '')
    ))
    conn.commit()
    conn.close()
    flash('Expense added successfully!', 'success')
    return redirect(url_for('expenses_list'))

@app.route('/expenses/<int:id>/delete', methods=['POST'])
def expense_delete(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM expenses WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Expense deleted!', 'success')
    return redirect(url_for('expenses_list'))

# ==================== REPORTS ====================

@app.route("/reports")
def reports():
    conn = get_db_connection()
    revenue_by_category = conn.execute("""SELECT j.category, COUNT(*) as job_count,
        COALESCE(SUM(i.total_amount), 0) as revenue FROM jobs j LEFT JOIN invoices i ON j.id=i.job_id
        GROUP BY j.category""").fetchall()
    monthly_summary = conn.execute("""SELECT strftime('%Y-%m', created_at) as month,
        COUNT(*) as invoice_count, COALESCE(SUM(total_amount),0) as total,
        COALESCE(SUM(paid_amount),0) as collected, COALESCE(SUM(balance_due),0) as pending
        FROM invoices GROUP BY month ORDER BY month DESC LIMIT 12""").fetchall()
    expense_summary = conn.execute("""SELECT category, COALESCE(SUM(amount),0) as total
        FROM expenses GROUP BY category""").fetchall()
    conn.close()
    return render_template("reports.html", revenue_by_category=revenue_by_category,
                           monthly_summary=monthly_summary, expense_summary=expense_summary)


# ==================== EXPORTS ====================


def _style_export_header(ws):
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="2c3e50", end_color="2c3e50", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")


def _send_workbook(wb, filename):
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name=filename)


@app.route("/export/clients")
def export_clients():
    conn = get_db_connection()
    clients = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    conn.close()
    wb = Workbook()
    ws = wb.active
    ws.title = "Clients"
    ws.append(["ID", "Name", "Contact Person", "Phone", "Email", "Address", "CNIC", "Type", "Created"])
    for c in clients:
        ws.append([c["id"], c["name"], c["contact_person"], c["phone"], c["email"], c["address"], c["cnic"], c["client_type"], c["created_at"]])
    _style_export_header(ws)
    return _send_workbook(wb, f'Waraq_Clients_{datetime.now().strftime("%Y%m%d")}.xlsx')


@app.route("/export/invoices")
def export_invoices():
    conn = get_db_connection()
    invoices = conn.execute("""SELECT i.*, c.name as client_name FROM invoices i
                               JOIN clients c ON i.client_id=c.id ORDER BY i.created_at DESC""").fetchall()
    conn.close()
    wb = Workbook()
    ws = wb.active
    ws.title = "Invoices"
    ws.append(["Invoice #", "Client", "Issue Date", "Due Date", "Subtotal", "Tax", "Discount", "Total", "Paid", "Balance", "Status"])
    for i in invoices:
        ws.append([i["invoice_number"], i["client_name"], i["issue_date"], i["due_date"], i["subtotal"], i["tax_amount"], i["discount"], i["total_amount"], i["paid_amount"], i["balance_due"], i["status"]])
    _style_export_header(ws)
    return _send_workbook(wb, f'Waraq_Invoices_{datetime.now().strftime("%Y%m%d")}.xlsx')


@app.route("/export/jobs")
def export_jobs():
    conn = get_db_connection()
    jobs = conn.execute("""SELECT j.*, c.name as client_name, s.service_name FROM jobs j
                           JOIN clients c ON j.client_id=c.id LEFT JOIN services s ON j.service_id=s.id
                           ORDER BY j.created_at DESC""").fetchall()
    conn.close()
    wb = Workbook()
    ws = wb.active
    ws.title = "Jobs"
    ws.append(["ID", "Client", "Service", "Title", "Category", "Status", "Priority", "Assigned To", "Start", "Due", "Cost"])
    for j in jobs:
        ws.append([j["id"], j["client_name"], j["service_name"], j["job_title"], j["category"], j["status"], j["priority"], j["assigned_to"], j["start_date"], j["due_date"], j["cost"]])
    _style_export_header(ws)
    return _send_workbook(wb, f'Waraq_Jobs_{datetime.now().strftime("%Y%m%d")}.xlsx')


# ==================== BACKUP ====================

# ==================== USERS ADMIN (admin only) ====================

@app.route('/users')
def users_list():
    if not _require_admin():
        flash('Invoice not found.', 'error')
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    users = conn.execute(
        """SELECT u.*, (SELECT COUNT(*) FROM user_profile p WHERE p.user_id = u.id AND p.full_name != '') AS has_profile
           FROM users u ORDER BY u.id"""
    ).fetchall()
    conn.close()
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['POST'])
def users_add():
    if not _require_admin():
        flash('Invoice not found.', 'error')
        return redirect(url_for('dashboard'))
    username = request.form.get('username', '').strip().lower()
    full_name = request.form.get('full_name', '').strip()
    role = request.form.get('role', 'staff').strip()
    password = request.form.get('password', '')
    if not username or not full_name or len(password) < 6:
        flash('پاس ورڈ کم از کم 6 حروف کا ہونا چاہیے۔ Password must be at least 6 characters.', 'error')
        return redirect(url_for('users_list'))
    if role not in ('admin', 'staff'):
        role = 'staff'
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            (username, generate_password_hash(password), full_name, role),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        flash('یہ صارف نام پہلے سے موجود ہے۔ Username already exists.', 'error')
        return redirect(url_for('users_list'))
    conn.close()
    flash('Service added successfully!', 'success')
    return redirect(url_for('users_list'))

@app.route('/users/<int:uid>/toggle', methods=['POST'])
def users_toggle(uid):
    admin = _require_admin()
    if not admin or admin['id'] == uid:
        flash('Invoice not found.', 'error')
        return redirect(url_for('users_list'))
    conn = get_db_connection()
    conn.execute("UPDATE users SET is_active = 1 - is_active WHERE id = ?", (uid,))
    conn.commit()
    conn.close()
    flash('Service updated!', 'success')
    return redirect(url_for('users_list'))

@app.route('/users/<int:uid>/reset-password', methods=['POST'])
def users_reset_password(uid):
    admin = _require_admin()
    if not admin:
        flash('Invoice not found.', 'error')
        return redirect(url_for('dashboard'))
    password = request.form.get('password', '')
    if len(password) < 6:
        flash('پاس ورڈ کم از کم 6 حروف کا ہونا چاہیے۔ Password must be at least 6 characters.', 'error')
        return redirect(url_for('users_list'))
    conn = get_db_connection()
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(password), uid))
    conn.commit()
    conn.close()
    flash('Service updated!', 'success')
    return redirect(url_for('users_list'))

@app.route('/users/<int:uid>/delete', methods=['POST'])
def users_delete(uid):
    admin = _require_admin()
    if not admin or admin['id'] == uid:
        flash('Invoice not found.', 'error')
        return redirect(url_for('users_list'))
    conn = get_db_connection()
    admins_left = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND is_active=1 AND id != ?", (uid,)).fetchone()[0]
    if admins_left == 0:
        conn.close()
        flash('Invoice not found.', 'error')
        return redirect(url_for('users_list'))
    conn.execute("DELETE FROM user_profile WHERE user_id = ?", (uid,))
    conn.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()
    flash('Service deleted!', 'success')
    return redirect(url_for('users_list'))

# ==================== LINKEDIN POSTS (developer card) ====================

@app.route('/linkedin/posts/add', methods=['POST'])
def linkedin_add():
    if not _require_admin():
        flash('صرف ایڈمن کے لیے۔ Admins only.', 'error')
        return redirect(url_for('dashboard'))
    url = (request.form.get('url') or '').strip()
    aid = _parse_linkedin_activity(url)
    if not aid:
        flash(
            'یہ لنکڈ ان پوسٹ کا لنک نہیں۔ LinkedIn post link required.',
            'error',
        )
        return redirect(url_for('dashboard'))
    current = [a for a in get_setting('linkedin_posts', '').split(',') if a.strip()]
    if aid not in current:
        current.insert(0, aid)
    set_setting('linkedin_posts', ','.join(current[:4]))
    flash('لنکڈ ان پوسٹ شامل ہو گئی۔ LinkedIn post added.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/linkedin/posts/remove/<aid>', methods=['POST'])
def linkedin_remove(aid):
    if not _require_admin():
        flash('صرف ایڈمن کے لیے۔ Admins only.', 'error')
        return redirect(url_for('dashboard'))
    current = [a for a in get_setting('linkedin_posts', '').split(',') if a.strip()]
    current = [a for a in current if a != aid]
    set_setting('linkedin_posts', ','.join(current))
    flash('لنکڈ ان پوسٹ ہٹا دی گئی۔ LinkedIn post removed.', 'success')
    return redirect(url_for('dashboard'))

# ==================== CHANGE OWN PASSWORD ====================

@app.route('/account/password', methods=['GET', 'POST'])
def change_password():
    user = _current_user()
    if not user:
        return redirect(url_for('login'))
    if request.method == 'POST':
        old = request.form.get('old', '')
        new = request.form.get('new', '')
        confirm = request.form.get('confirm', '')
        if not check_password_hash(user['password_hash'], old):
            flash('غلط صارف نام یا پاس ورڈ۔ Invalid username or password.', 'error')
            return redirect(url_for('change_password'))
        if len(new) < 6:
            flash('پاس ورڈ کم از کم 6 حروف کا ہونا چاہیے۔ Password must be at least 6 characters.', 'error')
            return redirect(url_for('change_password'))
        if new != confirm:
            flash('پاس ورڈز مشابہ نہیں ہیں۔ Passwords do not match.', 'error')
            return redirect(url_for('change_password'))
        conn = get_db_connection()
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(new), user['id']))
        conn.commit()
        conn.close()
        flash('Service updated!', 'success')
        return redirect(url_for('profile_view'))
    return render_template('change_password.html')

# ==================== USER PROFILE (per user) ====================

PROFILE_UPLOAD_DIR = Config.STATIC_IMAGE_DIR  # profile photos live with brand images
PROFILE_CV_DIR = os.path.join(os.path.dirname(Config.STATIC_IMAGE_DIR), os.pardir, 'uploads')  # <app>/uploads

SKILL_OPTIONS = {
    'Languages': [
        'Urdu (Native)', 'English', 'Arabic', 'Persian', 'Pashto', 'Shina',
        'Balti', 'Indus Kohistani', 'Burushaski', 'Turkish', 'Chinese',
    ],
    'Language Services': [
        'Translation', 'MTPE (Machine Translation Post-Editing)', 'Localization',
        'LQA (Language Quality Assurance)', 'Linguistic Testing', 'Interpreting',
        'Subtitling', 'Transcription', 'Proofreading', 'Copywriting', 'Terminology Management',
    ],
    'Domains': [
        'Legal', 'Religious Texts', 'Corporate', 'Technical', 'Educational',
        'Medical', 'Government', 'Game Localization', 'Marketing', 'Literary',
    ],
    'Digital & Office': [
        'MS Office', 'Google Workspace', 'CAT Tools (Trados/memoQ)', 'Data Entry',
        'Web Research', 'Email Handling', 'Customer Support', 'Bookkeeping',
    ],
    'Design & Media': [
        'Graphic Design', 'Photoshop', 'Illustrator', 'Video Editing', 'Typing',
    ],
    'Web & Tech': [
        'HTML/CSS', 'Python', 'WordPress', 'SEO', 'Social Media Management',
    ],
}


def _get_or_create_profile(user_id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM user_profile WHERE user_id = ?", (user_id,)).fetchone()
    if not row:
        conn.execute("INSERT INTO user_profile (user_id) VALUES (?)", (user_id,))
        conn.commit()
        row = conn.execute("SELECT * FROM user_profile WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row


@app.route('/profile')
def profile_view():
    user = _current_user()
    if not user:
        return redirect(url_for('login'))
    profile = _get_or_create_profile(user['id'])
    skills = [s for s in (profile['skills'] or '').split('|') if s]
    socials = [s for s in (profile['socials'] or '').split('|') if s]
    return render_template('profile.html', profile=profile, user=user, skills=skills, socials=socials, skill_options=SKILL_OPTIONS)


@app.route('/users/<int:uid>/profile')
def user_profile_by_id(uid):
    """Admin shortcut: view any user's profile showcase."""
    admin = _require_admin()
    if not admin:
        flash('Invoice not found.', 'error')
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    target = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    if not target:
        flash('Invoice not found.', 'error')
        return redirect(url_for('users_list'))
    profile = _get_or_create_profile(uid)
    skills = [s for s in (profile['skills'] or '').split('|') if s]
    socials = [s for s in (profile['socials'] or '').split('|') if s]
    return render_template('profile.html', profile=profile, user=target, skills=skills, socials=socials, skill_options=SKILL_OPTIONS)


@app.route('/profile/edit', methods=['GET', 'POST'])
def profile_edit():
    user = _current_user()
    if not user:
        return redirect(url_for('login'))
    profile = _get_or_create_profile(user['id'])
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        if not full_name:
            flash('Client name is required.', 'error')
            return redirect(url_for('profile_edit'))

        email = request.form.get('email', '').strip()
        date_of_birth = request.form.get('date_of_birth', '').strip()
        mobile = request.form.get('mobile', '').strip()
        summary = request.form.get('summary', '').strip()
        socials = '|'.join(s.strip() for s in request.form.getlist('socials') if s.strip())
        skills = '|'.join(request.form.getlist('skills'))

        photo = request.files.get('photo')
        cv = request.files.get('cv')

        photo_name = None
        if photo and photo.filename:
            ext = os.path.splitext(photo.filename)[1].lower()
            if ext not in ('.png', '.jpg', '.jpeg', '.webp'):
                flash('Only image files (PNG, JPG, WEBP) are allowed for the photo.', 'error')
                return redirect(url_for('profile_edit'))
            photo_name = f'profile-photo{ext}'
            photo.save(os.path.join(PROFILE_UPLOAD_DIR, photo_name))

        cv_name = None
        if cv and cv.filename:
            ext = os.path.splitext(cv.filename)[1].lower()
            if ext not in ('.pdf', '.doc', '.docx'):
                flash('Only PDF or Word documents are allowed for the CV.', 'error')
                return redirect(url_for('profile_edit'))
            os.makedirs(PROFILE_CV_DIR, exist_ok=True)
            cv_name = secure_filename(cv.filename)
            cv.save(os.path.join(PROFILE_CV_DIR, cv_name))

        conn = get_db_connection()
        conn.execute(
            """UPDATE user_profile SET full_name=?, email=?, date_of_birth=?, mobile=?,
               socials=?, skills=?, summary=?, updated_at=CURRENT_TIMESTAMP,
               photo=COALESCE(?, photo), cv_file=COALESCE(?, cv_file),
               cv_name=COALESCE(?, cv_name) WHERE user_id=?""",
            (full_name, email, date_of_birth, mobile, socials, skills, summary,
             photo_name, cv_name, cv_name, user['id']),
        )
        conn.execute("UPDATE users SET full_name = ? WHERE id = ?", (full_name, user['id']))
        conn.commit()
        conn.close()
        flash('Client updated successfully!', 'success')
        return redirect(url_for('profile_view'))

    return render_template('profile_edit.html', profile=profile, skill_options=SKILL_OPTIONS,
                           skills=[s for s in (profile['skills'] or '').split('|') if s],
                           socials=[s for s in (profile['socials'] or '').split('|') if s])


@app.route('/profile/cv')
def profile_cv():
    user = _current_user()
    if not user:
        return redirect(url_for('login'))
    profile = _get_or_create_profile(user['id'])
    if not profile or not profile['cv_file']:
        flash('Invoice not found.', 'error')
        return redirect(url_for('profile_view'))
    path = os.path.join(PROFILE_CV_DIR, profile['cv_file'])
    if not os.path.exists(path):
        flash('Invoice not found.', 'error')
        return redirect(url_for('profile_view'))
    return send_file(path, as_attachment=True, download_name=profile['cv_name'] or profile['cv_file'])

@app.route('/backup')
def backup():
    if get_db_backend() != 'sqlite':
        flash('PostgreSQL backups are managed outside the web application. Use the database provider backup/export process.', 'error')
        return redirect(url_for('dashboard'))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(Config.BACKUP_DIR, f'waraq_backup_{timestamp}.db')
    shutil.copy2(Config.DATABASE, backup_path)
    safe_prune_backups(keep=30)
    flash(f'Database backed up to {backup_path}', 'success')
    return redirect(url_for('dashboard'))

# ==================== API ENDPOINTS ====================

@app.route("/api/client/<int:id>/jobs")
def api_client_jobs(id):
    conn = get_db_connection()
    if not conn.execute("SELECT id FROM clients WHERE id=?", (id,)).fetchone():
        conn.close()
        return jsonify({"error": "Client not found"}), 404
    jobs = conn.execute("SELECT id, job_title, cost FROM jobs WHERE client_id=? AND status!='Completed' ORDER BY created_at DESC", (id,)).fetchall()
    conn.close()
    return jsonify([dict(job) for job in jobs])


@app.route("/api/service/<int:id>")
def api_service(id):
    conn = get_db_connection()
    service = conn.execute("SELECT * FROM services WHERE id=?", (id,)).fetchone()
    conn.close()
    if not service:
        return jsonify({"error": "Service not found"}), 404
    return jsonify(dict(service))


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return render_template("base.html", error_message="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("base.html", error_message="An internal server error occurred."), 500


# ==================== MAIN ====================

if __name__ == "__main__":
    print("Starting Waraq Enterprise Management System...")
    print(f"Database: {Config.DATABASE}")
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(debug=False, host="127.0.0.1", port=5000)
