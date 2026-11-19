from flask import Flask, request, render_template, redirect, session, jsonify
import sqlite3, os, hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "غير_هذا_السر_قبل_النشر_12345"

DB = "users.db"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact TEXT NOT NULL,
            password TEXT NOT NULL,
            lat REAL,
            lng REAL,
            location_allowed INTEGER DEFAULT 0,
            ip TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    contact = (data.get("contact") or "").strip()
    password = (data.get("password") or "").strip()
    lat = data.get("lat")
    lng = data.get("lng")
    location_allowed = 1 if (lat is not None and lng is not None) else 0
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    if not contact or not password:
        return jsonify({"ok": False, "error": "الايميل/الرقم والباسورد مطلوبين"}), 400

    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO users (contact, password, lat, lng, location_allowed, ip, created_at) VALUES (?,?,?,?,?,?,?)",
        (contact, hash_pw(password), lat, lng, location_allowed, ip, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect("/admin")
        error = "بيانات الدخول غلط"
    return render_template("admin_login.html", error=error)


@app.route("/admin")
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect("/admin/login")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", users=rows)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
