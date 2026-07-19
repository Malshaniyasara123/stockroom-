# Stockroom — Inventory Management System

A simple, self-hosted inventory system for small businesses. Runs as a local website (Flask + SQLite) — no external services, no monthly fees.

## Features
- **Products** — add/edit/delete items with SKU, category, price, and reorder level
- **Stock Movement** — record stock in (received) and stock out (sold/used), with full history
- **Overview dashboard** — total products, total stock value, low-stock alerts, recent activity
- **Reports** — value by category, reorder list

## Requirements
- Python 3.9+
- pip

## Setup

```bash
# 1. Go into the project folder
cd inventory_app

# 2. (Recommended) create a virtual environment
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate

# 3. Install Flask
pip install flask

# 4. Run the app (this also creates inventory.db on first run)
python3 app.py
```

Then open **http://localhost:5000** in your browser.

## Notes
- All data is stored in `inventory.db` (a single SQLite file) in the project folder. Back it up by simply copying that file.
- To reset all data, stop the app and delete `inventory.db` — it will be recreated empty next time you run `python3 app.py`.
- `app.secret_key` in `app.py` should be changed to a random string before using this beyond your own machine.
- To make this reachable from other devices on your network (e.g. a phone at the counter), it already binds to `0.0.0.0:5000` — just visit `http://<your-computer's-local-ip>:5000` from another device on the same Wi-Fi.

## Next steps you might want
- Add user login if more than one person will use it
- Deploy to a small host (Render, Railway, PythonAnywhere) if you want it accessible outside your local network
- Add barcode scanning support (most USB barcode scanners just "type" into the SKU search field already)
