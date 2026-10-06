from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import csv
import io
import os
from decimal import Decimal, ROUND_HALF_UP
import yfinance as yf

app = Flask(__name__)
app.config["DEMO_MODE"] = os.environ.get("DEMO_MODE", "").lower() in {"1", "true", "yes", "on"}
DB_NAME = "portfolio.db"

DEMO_PRICES = {
    "RY": 118.42,
    "TD": 87.25,
    "BNS": 67.10,
    "CNQ": 49.85,
    "XIU": 34.60,
    "MSFT": 423.15,
    "AAPL": 214.77,
}


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def seed_demo_data():
    demo_holdings = [
        ("RY", "Royal Bank of Canada", "Financials", 12, 102.40, 4.10, "CAD", "TSX"),
        ("TD", "Toronto-Dominion Bank", "Financials", 9, 81.75, 3.65, "CAD", "TSX"),
        ("CNQ", "Canadian Natural Resources", "Energy", 18, 38.90, 2.70, "CAD", "TSX"),
        ("XIU", "iShares S&P/TSX 60 Index ETF", "ETF", 22, 31.25, 1.90, "CAD", "TSX"),
    ]

    conn = get_db()
    conn.executemany(
        """
        INSERT INTO holdings (ticker, company, sector, shares, avg_cost, annual_dividend, currency, exchange)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        demo_holdings,
    )
    conn.commit()
    conn.close()


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            company TEXT NOT NULL,
            sector TEXT NOT NULL DEFAULT 'Unknown',
            shares REAL NOT NULL,
            avg_cost REAL NOT NULL,
            annual_dividend REAL NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'CAD',
            exchange TEXT NOT NULL DEFAULT 'TSX',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    if app.config.get("DEMO_MODE"):
        row = conn.execute("SELECT COUNT(*) as count FROM holdings").fetchone()
        if row["count"] == 0:
            seed_demo_data()

    conn.commit()
    conn.close()


def normalize_ticker(ticker, exchange):
    symbol = (ticker or "").strip().upper().replace(" ", "")
    if not symbol:
        return symbol

    if any(symbol.endswith(suffix) for suffix in [".TO", ".TSE", ".V", ".N", ".NYSE", ".NASDAQ"]):
        return symbol

    normalized_exchange = (exchange or "").upper().replace("-", "").replace(" ", "")
    if normalized_exchange in {"TSX", "TSE", "TSXH"}:
        return f"{symbol}.TO"
    if normalized_exchange in {"TSXV", "TSXVENTURE"}:
        return f"{symbol}.V"
    return symbol


def fetch_market_price(ticker, exchange):
    symbol = normalize_ticker(ticker, exchange)
    base_symbol = symbol.split(".")[0].upper()
    if base_symbol in DEMO_PRICES:
        return float(DEMO_PRICES[base_symbol])

    try:
        stock = yf.Ticker(symbol)

        info = getattr(stock, "fast_info", None)
        if info is not None:
            last_price = info.get("last_price") or info.get("lastPrice")
            if last_price is not None:
                return float(last_price)

        info = stock.info
        if info and info.get("regularMarketPrice") is not None:
            return float(info["regularMarketPrice"])

        hist = stock.history(period="5d", auto_adjust=True)
        if not hist.empty:
            return float(hist["Close"].iloc[-1])

        return 0.0
    except Exception:
        return 0.0


def money(value):
    if value is None:
        value = 0
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def build_enriched_holdings():
    conn = get_db()
    rows = conn.execute("SELECT * FROM holdings ORDER BY created_at DESC").fetchall()
    conn.close()

    enriched = []
    for row in rows:
        current_price = fetch_market_price(row["ticker"], row["exchange"])
        shares = float(row["shares"])
        avg_cost = float(row["avg_cost"])
        dividend = float(row["annual_dividend"])
        market_value = current_price * shares
        total_cost = avg_cost * shares
        gain_loss = market_value - total_cost
        gain_pct = (gain_loss / total_cost * 100) if total_cost else 0.0
        dividend_income = dividend * shares

        enriched.append(
            {
                "id": row["id"],
                "ticker": row["ticker"].upper(),
                "company": row["company"],
                "sector": row["sector"],
                "shares": shares,
                "avg_cost": avg_cost,
                "annual_dividend": dividend,
                "currency": row["currency"],
                "exchange": row["exchange"],
                "current_price": current_price,
                "market_value": market_value,
                "total_cost": total_cost,
                "gain_loss": gain_loss,
                "gain_pct": gain_pct,
                "dividend_income": dividend_income,
            }
        )

    return enriched


def portfolio_summary(holdings):
    total_value = sum(h["market_value"] for h in holdings)
    total_cost = sum(h["total_cost"] for h in holdings)
    total_gain = total_value - total_cost
    gain_pct = (total_gain / total_cost * 100) if total_cost else 0.0
    dividend_income = sum(h["dividend_income"] for h in holdings)

    return {
        "total_value": total_value,
        "total_cost": total_cost,
        "total_gain": total_gain,
        "gain_pct": gain_pct,
        "dividend_income": dividend_income,
        "holdings_count": len(holdings),
    }


@app.route("/")
def index():
    holdings = build_enriched_holdings()
    summary = portfolio_summary(holdings)
    return render_template("index.html", holdings=holdings, summary=summary)


@app.route("/add", methods=["POST"])
def add_holding():
    ticker = (request.form.get("ticker") or "").strip()
    company = (request.form.get("company") or "").strip()
    sector = (request.form.get("sector") or "Unknown").strip()
    shares = request.form.get("shares")
    avg_cost = request.form.get("avg_cost")
    annual_dividend = request.form.get("annual_dividend") or "0"
    currency = (request.form.get("currency") or "CAD").strip().upper()
    exchange = (request.form.get("exchange") or "TSX").strip().upper()

    if not ticker or not company or not shares or not avg_cost:
        return redirect(url_for("index"))

    conn = get_db()
    conn.execute(
        """
        INSERT INTO holdings (ticker, company, sector, shares, avg_cost, annual_dividend, currency, exchange)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticker.upper(),
            company,
            sector or "Unknown",
            float(shares),
            float(avg_cost),
            float(annual_dividend),
            currency,
            exchange,
        ),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:holding_id>", methods=["POST"])
def delete_holding(holding_id):
    conn = get_db()
    conn.execute("DELETE FROM holdings WHERE id = ?", (holding_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/export")
def export_csv():
    holdings = build_enriched_holdings()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ticker",
        "company",
        "sector",
        "shares",
        "avg_cost",
        "currency",
        "exchange",
        "current_price",
        "market_value",
        "gain_loss",
        "dividend_income",
    ])

    for holding in holdings:
        writer.writerow([
            holding["ticker"],
            holding["company"],
            holding["sector"],
            money(holding["shares"]),
            money(holding["avg_cost"]),
            holding["currency"],
            holding["exchange"],
            money(holding["current_price"]),
            money(holding["market_value"]),
            money(holding["gain_loss"]),
            money(holding["dividend_income"]),
        ])

    data = output.getvalue().encode("utf-8")
    return send_file(
        io.BytesIO(data),
        mimetype="text/csv",
        as_attachment=True,
        download_name="canadian_portfolio.csv",
    )


if __name__ == "__main__":
    app.config["DEMO_MODE"] = True
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
