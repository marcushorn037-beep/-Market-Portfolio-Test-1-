import pytest

import app as app_module


@pytest.fixture
def client(monkeypatch, tmp_path):
    db_path = tmp_path / "portfolio.db"
    monkeypatch.setattr(app_module, "DB_NAME", str(db_path))
    app_module.init_db()
    monkeypatch.setattr(app_module, "fetch_market_price", lambda ticker, exchange: 100.0)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


def test_normalize_ticker_for_canadian_exchanges():
    assert app_module.normalize_ticker("ry", "TSX") == "RY.TO"
    assert app_module.normalize_ticker("ry", "NASDAQ") == "RY"
    assert app_module.normalize_ticker("", "TSX") == ""


def test_add_holding_and_portfolio_summary(client):
    response = client.post(
        "/add",
        data={
            "ticker": "RY",
            "company": "Royal Bank",
            "sector": "Financials",
            "shares": "10",
            "avg_cost": "90",
            "annual_dividend": "4.5",
            "currency": "CAD",
            "exchange": "TSX",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Royal Bank" in response.data

    conn = app_module.get_db()
    row = conn.execute("SELECT ticker, company, shares, avg_cost FROM holdings").fetchone()
    conn.close()

    assert row["ticker"] == "RY"
    assert row["company"] == "Royal Bank"
    assert row["shares"] == 10.0
    assert row["avg_cost"] == 90.0

    holdings = app_module.build_enriched_holdings()
    summary = app_module.portfolio_summary(holdings)

    assert len(holdings) == 1
    assert holdings[0]["market_value"] == 1000.0
    assert summary["total_value"] == 1000.0
    assert summary["holdings_count"] == 1


def test_export_csv_download(client):
    client.post(
        "/add",
        data={
            "ticker": "CNQ",
            "company": "Canadian Natural Resources",
            "sector": "Energy",
            "shares": "5",
            "avg_cost": "30",
            "annual_dividend": "2",
            "currency": "CAD",
            "exchange": "TSX",
        },
    )

    response = client.get("/export")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv")
    assert b"ticker,company,sector" in response.data
    assert b"CNQ" in response.data
