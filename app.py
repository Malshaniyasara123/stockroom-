import sqlite3
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, g

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")

DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(__file__))
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "inventory.db")


# ---------- Database helpers ----------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT DEFAULT '',
            quantity INTEGER NOT NULL DEFAULT 0,
            price REAL NOT NULL DEFAULT 0,
            reorder_level INTEGER NOT NULL DEFAULT 5,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('in','out')),
            quantity INTEGER NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        """
    )
    db.commit()
    db.close()


# ---------- Routes: Dashboard ----------

@app.route("/")
def dashboard():
    db = get_db()
    products = db.execute("SELECT * FROM products").fetchall()

    total_products = len(products)
    total_value = sum(p["quantity"] * p["price"] for p in products)
    low_stock = [p for p in products if p["quantity"] <= p["reorder_level"]]

    recent_tx = db.execute(
        """
        SELECT t.*, p.name as product_name, p.sku as product_sku
        FROM transactions t
        JOIN products p ON p.id = t.product_id
        ORDER BY t.id DESC LIMIT 8
        """
    ).fetchall()

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_value=total_value,
        low_stock=low_stock,
        recent_tx=recent_tx,
    )


# ---------- Routes: Products ----------

@app.route("/products")
def products():
    db = get_db()
    q = request.args.get("q", "").strip()
    if q:
        rows = db.execute(
            "SELECT * FROM products WHERE name LIKE ? OR sku LIKE ? OR category LIKE ? ORDER BY name",
            (f"%{q}%", f"%{q}%", f"%{q}%"),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM products ORDER BY name").fetchall()
    return render_template("products.html", products=rows, q=q)


@app.route("/products/new", methods=["GET", "POST"])
def new_product():
    if request.method == "POST":
        db = get_db()
        try:
            db.execute(
                """INSERT INTO products (sku, name, category, quantity, price, reorder_level, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    request.form["sku"].strip(),
                    request.form["name"].strip(),
                    request.form.get("category", "").strip(),
                    int(request.form.get("quantity", 0) or 0),
                    float(request.form.get("price", 0) or 0),
                    int(request.form.get("reorder_level", 5) or 5),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            db.commit()
            flash(f"Product '{request.form['name']}' added.", "success")
            return redirect(url_for("products"))
        except sqlite3.IntegrityError:
            flash("SKU eka already exists. Try a different SKU.", "error")
    return render_template("product_form.html", product=None)


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    if request.method == "POST":
        try:
            db.execute(
                """UPDATE products SET sku=?, name=?, category=?, price=?, reorder_level=?
                   WHERE id=?""",
                (
                    request.form["sku"].strip(),
                    request.form["name"].strip(),
                    request.form.get("category", "").strip(),
                    float(request.form.get("price", 0) or 0),
                    int(request.form.get("reorder_level", 5) or 5),
                    product_id,
                ),
            )
            db.commit()
            flash("Product updated.", "success")
            return redirect(url_for("products"))
        except sqlite3.IntegrityError:
            flash("SKU eka already exists. Try a different SKU.", "error")

    return render_template("product_form.html", product=product)


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    flash("Product deleted.", "success")
    return redirect(url_for("products"))


# ---------- Routes: Stock transactions ----------

@app.route("/stock", methods=["GET", "POST"])
def stock():
    db = get_db()
    if request.method == "POST":
        product_id = int(request.form["product_id"])
        tx_type = request.form["type"]
        qty = int(request.form["quantity"])
        note = request.form.get("note", "").strip()

        product = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if product is None:
            flash("Product not found.", "error")
            return redirect(url_for("stock"))

        if tx_type == "out" and qty > product["quantity"]:
            flash(
                f"Cannot remove {qty} units — only {product['quantity']} in stock.",
                "error",
            )
            return redirect(url_for("stock"))

        new_qty = product["quantity"] + qty if tx_type == "in" else product["quantity"] - qty
        db.execute("UPDATE products SET quantity=? WHERE id=?", (new_qty, product_id))
        db.execute(
            "INSERT INTO transactions (product_id, type, quantity, note, created_at) VALUES (?,?,?,?,?)",
            (product_id, tx_type, qty, note, datetime.now().isoformat(timespec="seconds")),
        )
        db.commit()
        flash("Stock updated.", "success")
        return redirect(url_for("stock"))

    products_list = db.execute("SELECT * FROM products ORDER BY name").fetchall()
    history = db.execute(
        """
        SELECT t.*, p.name as product_name, p.sku as product_sku
        FROM transactions t JOIN products p ON p.id = t.product_id
        ORDER BY t.id DESC LIMIT 50
        """
    ).fetchall()
    return render_template("stock.html", products=products_list, history=history)


# ---------- Routes: Reports ----------

@app.route("/reports")
def reports():
    db = get_db()
    products_list = db.execute("SELECT * FROM products").fetchall()
    low_stock = [p for p in products_list if p["quantity"] <= p["reorder_level"]]
    by_category = {}
    for p in products_list:
        cat = p["category"] or "Uncategorized"
        by_category.setdefault(cat, {"count": 0, "value": 0.0})
        by_category[cat]["count"] += 1
        by_category[cat]["value"] += p["quantity"] * p["price"]

    total_value = sum(p["quantity"] * p["price"] for p in products_list)
    total_units = sum(p["quantity"] for p in products_list)

    return render_template(
        "reports.html",
        low_stock=low_stock,
        by_category=by_category,
        total_value=total_value,
        total_units=total_units,
    )


# Initialize the database on import so it also works under gunicorn,
# not just when run directly with `python3 app.py`.
init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
