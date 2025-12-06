import os
import sqlite3
from io import BytesIO
from functools import wraps
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "event_portal.db")

app = Flask(__name__)
app.secret_key = "replace_this_with_a_secure_random_value"  # change in production


# ----------------- DB helpers -----------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # enforce foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Create DB and seed admin & sample events if missing."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'user'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      date TEXT,
      venue TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS registrations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_id INTEGER NOT NULL,
      username TEXT NOT NULL,
      email TEXT NOT NULL,
      year TEXT,
      branch TEXT,
      created_at TEXT,
      FOREIGN KEY (event_id) REFERENCES events(id)
    )
    """)

    # Seed admin if missing (username: admin, password: admin123)
    cur.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    if not cur.fetchone():
        hashed = generate_password_hash("admin123")
        cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    ("admin", hashed, "admin"))

    # Seed sample events if none exist
    cur.execute("SELECT COUNT(*) as cnt FROM events")
    if cur.fetchone()["cnt"] == 0:
        sample_events = [
            ("Tech Innovation Summit 2025", "Jan 10, 2025", "ECE Dept"),
            ("AI & Robotics Expo", "Jan 13, 2026", "AI & ML Dept"),
            ("Startup Launchpad", "Mar 5, 2026", "Data Science Dept"),
            ("Cloud Computing Workshop", "Apr 12, 2026", "CSE Dept"),
            ("Open Mic Night", "Feb 20, 2026", "Mech Dept"),
            ("Film Festival", "Apr 29, 2026", "Mech Dept"),
        ]
        cur.executemany("INSERT INTO events (name, date, venue) VALUES (?, ?, ?)", sample_events)

    conn.commit()
    conn.close()


init_db()


# ----------------- Helpers & decorators -----------------
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin area only.", "danger")
            return redirect(url_for("dashboard"))
        return fn(*args, **kwargs)
    return wrapper


# ----------------- Routes -----------------
@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = user["username"]
            session["role"] = user["role"]
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            flash("Fill all fields.", "warning")
            return redirect(url_for("register"))

        conn = get_db_connection()
        try:
            hashed = generate_password_hash(password)
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            conn.commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))
        finally:
            conn.close()
    return render_template("register.html")


# Dashboard / Welcome (list events)
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()
    events = conn.execute("SELECT * FROM events ORDER BY id").fetchall()
    conn.close()
    return render_template("dashboard.html", events=events)


# Event registration form
@app.route("/register_event/<int:event_id>", methods=["GET", "POST"])
@login_required
def register_event(event_id):
    conn = get_db_connection()
    event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if not event:
        conn.close()
        flash("Event not found.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = session["user"]
        email = request.form["email"].strip()
        year = request.form["year"]
        branch = request.form["branch"].strip()
        created_at = datetime.utcnow().isoformat()

        conn.execute(
            "INSERT INTO registrations (event_id, username, email, year, branch, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (event_id, username, email, year, branch, created_at)
        )
        conn.commit()
        conn.close()
        flash(f"Registered for {event['name']}.", "success")
        return redirect(url_for("my_registrations"))

    conn.close()
    return render_template("event_form.html", event=event)


# User's registration history
@app.route("/my_registrations")
@login_required
def my_registrations():
    username = session["user"]
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT r.id, e.name as event, r.email, r.year, r.branch, r.created_at
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE r.username = ?
        ORDER BY r.id DESC
    """, (username,)).fetchall()
    conn.close()
    return render_template("registrations.html", registrations=rows)


# Sample certificate (just preview - redirects to download if admin or owner)
@app.route("/certificate/<int:registration_id>")
@login_required
def certificate(registration_id):
    conn = get_db_connection()
    row = conn.execute("""
        SELECT r.id, e.name as event_name, r.username, r.email, r.year, r.branch, r.created_at
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE r.id = ?
    """, (registration_id,)).fetchone()
    conn.close()

    if not row:
        flash("Registration not found.", "danger")
        return redirect(url_for("dashboard"))

    # allow admin or the user who registered to download the certificate
    if session.get("role") != "admin" and session.get("user") != row["username"]:
        flash("Not authorized to view this certificate.", "danger")
        return redirect(url_for("dashboard"))

    # generate PDF in memory using reportlab
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 120, "Certificate of Participation")

    # Body
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 180, f"This is to certify that")
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 210, f"{row['username']}")
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 240, f"has participated in \"{row['event_name']}\".")

    # details
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 280, f"Year: {row['year']}    Branch: {row['branch']}")
    c.drawCentredString(width / 2, height - 300, f"Date: {row['created_at'][:10]}")

    # signature lines
    c.drawString(60, 80, "Organizer")
    c.line(50, 75, 200, 75)
    c.drawString(width - 220, 80, "Signature")
    c.line(width - 240, 75, width - 60, 75)

    c.showPage()
    c.save()
    buffer.seek(0)

    filename = f"certificate_{row['id']}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")


# Admin dashboard
@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    users = conn.execute("SELECT id, username, role FROM users ORDER BY id").fetchall()
    events = conn.execute("SELECT * FROM events ORDER BY id").fetchall()
    registrations = conn.execute("""
        SELECT r.id, e.name as event, r.username, r.email, r.year, r.branch, r.created_at
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        ORDER BY r.id DESC
    """).fetchall()
    conn.close()
    return render_template("admin.html", users=users, events=events, registrations=registrations)


# Admin: add event
@app.route("/admin/add_event", methods=["POST"])
@admin_required
def admin_add_event():
    name = request.form["name"].strip()
    date = request.form["date"].strip()
    venue = request.form["venue"].strip()
    if not name:
        flash("Event name required.", "warning")
        return redirect(url_for("admin_dashboard"))
    conn = get_db_connection()
    conn.execute("INSERT INTO events (name, date, venue) VALUES (?, ?, ?)", (name, date, venue))
    conn.commit()
    conn.close()
    flash("Event added.", "success")
    return redirect(url_for("admin_dashboard"))


# Admin: delete event
@app.route("/admin/delete_event/<int:event_id>", methods=["POST"])
@admin_required
def admin_delete_event(event_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    flash("Event deleted.", "info")
    return redirect(url_for("admin_dashboard"))


# Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
