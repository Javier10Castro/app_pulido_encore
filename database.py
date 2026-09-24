"""Capa de datos (SQLite). Si ya tienes tu propia BD, solo reemplaza las funciones de este archivo
manteniendo los mismos nombres y la UI seguirá funcionando igual."""
import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "encore.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE COLLATE NOCASE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS empleados(
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    turno TEXT NOT NULL CHECK(turno IN ('A','B','C')));
CREATE TABLE IF NOT EXISTS materiales(
    nombre TEXT PRIMARY KEY COLLATE NOCASE);
CREATE TABLE IF NOT EXISTS reporte(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empleado INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    turno TEXT NOT NULL,
    material TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    fecha TEXT NOT NULL);
"""


def _c():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _c() as c:
        c.executescript(SCHEMA)


def _hash(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex()
    return f"{salt}${h}"


def _check(pw, stored):
    salt = stored.split("$")[0]
    return hmac.compare_digest(_hash(pw, salt), stored)


# ---------------- usuarios ----------------
def user_count():
    with _c() as c:
        return c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]


def create_user(username, password, is_admin=False):
    with _c() as c:
        c.execute("INSERT INTO usuarios(username,password,is_admin) VALUES(?,?,?)",
                  (username, _hash(password), int(is_admin)))


def verify_user(username, password):
    with _c() as c:
        r = c.execute("SELECT * FROM usuarios WHERE username=?", (username,)).fetchone()
    return r if r and _check(password, r["password"]) else None


def list_users():
    with _c() as c:
        return c.execute("SELECT id,username,is_admin FROM usuarios ORDER BY username").fetchall()


def delete_user(uid):
    with _c() as c:
        c.execute("DELETE FROM usuarios WHERE id=?", (uid,))


# ---------------- empleados ----------------
def get_employee(emp_id):
    with _c() as c:
        return c.execute("SELECT * FROM empleados WHERE id=?", (emp_id,)).fetchone()


def employee_exists(emp_id):
    return get_employee(emp_id) is not None


def add_employee(emp_id, nombre, turno):
    with _c() as c:
        c.execute("INSERT INTO empleados(id,nombre,turno) VALUES(?,?,?)", (emp_id, nombre, turno))


def update_employee(emp_id, nombre, turno):
    with _c() as c:
        c.execute("UPDATE empleados SET nombre=?, turno=? WHERE id=?", (nombre, turno, emp_id))


def delete_employee(emp_id):
    with _c() as c:
        c.execute("DELETE FROM empleados WHERE id=?", (emp_id,))


def list_employees():
    with _c() as c:
        return c.execute("SELECT * FROM empleados ORDER BY id").fetchall()


# ---------------- materiales ----------------
def material_exists(nombre):
    with _c() as c:
        return c.execute("SELECT 1 FROM materiales WHERE nombre=?", (nombre,)).fetchone() is not None


def add_material(nombre):
    with _c() as c:
        c.execute("INSERT INTO materiales(nombre) VALUES(?)", (nombre,))


def rename_material(old, new):
    with _c() as c:
        c.execute("UPDATE materiales SET nombre=? WHERE nombre=?", (new, old))
        c.execute("UPDATE reporte SET material=? WHERE material=?", (new, old))


def delete_material(nombre):
    with _c() as c:
        c.execute("DELETE FROM materiales WHERE nombre=?", (nombre,))


def list_materials():
    with _c() as c:
        return [r[0] for r in c.execute("SELECT nombre FROM materiales ORDER BY nombre")]


# ---------------- reporte ----------------
def add_report(emp_id, material, cantidad):
    """Guarda el registro con la fecha y hora actuales."""
    emp = get_employee(emp_id)
    with _c() as c:
        c.execute("INSERT INTO reporte(empleado,nombre,turno,material,cantidad,fecha) VALUES(?,?,?,?,?,?)",
                  (emp["id"], emp["nombre"], emp["turno"], material, int(cantidad),
                   datetime.now().strftime("%Y-%m-%d %H:%M:%S")))


def delete_report(rid):
    with _c() as c:
        c.execute("DELETE FROM reporte WHERE id=?", (rid,))


def report_rows(turno=None, material=None, days=None):
    q, p = "SELECT * FROM reporte WHERE 1=1", []
    if turno:
        q += " AND turno=?"; p.append(turno)
    if material:
        q += " AND material=?"; p.append(material)
    if days:
        q += " AND fecha>=?"
        p.append((datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d 00:00:00"))
    with _c() as c:
        return c.execute(q + " ORDER BY fecha DESC", p).fetchall()
