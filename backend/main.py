from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from typing import Optional
import pymysql, os

# ── DB config ──────────────────────────────────────────────────
DB = dict(
    host=os.getenv("DB_HOST", "mysql"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER", "trader"),
    password=os.getenv("DB_PASSWORD", "traderpass123"),
    database=os.getenv("DB_NAME", "portfolio_mgmt"),
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True,
)

def get_conn():
    return pymysql.connect(**DB)

# ── App ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="Portfolio Management API", lifespan=lifespan)

# ── Helpers ────────────────────────────────────────────────────
def query(sql: str, args=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args or ())
            return cur.fetchall()
    finally:
        conn.close()

def execute(sql: str, args=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args or ())
            return cur.lastrowid
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════
# PORTFOLIO SUMMARY
# ══════════════════════════════════════════════════════════════
@app.get("/api/portfolio/summary")
def portfolio_summary():
    """Overall portfolio: total cost, market value, P&L per account."""
    rows = query("""
        SELECT a.account_id, a.account_name, a.account_type,
               ROUND(SUM(h.avg_cost_price * h.net_quantity), 2)  AS total_cost,
               ROUND(SUM(ast.last_price   * h.net_quantity), 2)  AS market_value,
               ROUND(SUM((ast.last_price - h.avg_cost_price) * h.net_quantity), 2) AS unrealized_pnl,
               ROUND(SUM((ast.last_price - h.avg_cost_price) * h.net_quantity)
                     / NULLIF(SUM(h.avg_cost_price * h.net_quantity),0) * 100, 2) AS pnl_pct
        FROM Holdings h
        JOIN Accounts a   ON a.account_id  = h.account_id
        JOIN Assets   ast ON ast.asset_id  = h.asset_id
        GROUP BY a.account_id, a.account_name, a.account_type
        ORDER BY market_value DESC
    """)
    total_mv  = sum(float(r["market_value"]  or 0) for r in rows)
    total_pnl = sum(float(r["unrealized_pnl"] or 0) for r in rows)
    total_cost= sum(float(r["total_cost"]    or 0) for r in rows)
    return {
        "accounts": rows,
        "totals": {
            "total_cost":      round(total_cost, 2),
            "market_value":    round(total_mv, 2),
            "unrealized_pnl":  round(total_pnl, 2),
            "pnl_pct": round(total_pnl / total_cost * 100, 2) if total_cost else 0,
        }
    }

# ══════════════════════════════════════════════════════════════
# HOLDINGS
# ══════════════════════════════════════════════════════════════
@app.get("/api/holdings")
def get_holdings(account_id: Optional[int] = None):
    sql = """
        SELECT a.account_id, a.account_name,
               ast.ticker, ast.name AS asset_name, ast.asset_class, ast.currency,
               h.net_quantity, h.avg_cost_price,
               ast.last_price AS current_price,
               ROUND((ast.last_price - h.avg_cost_price) * h.net_quantity, 2) AS unrealized_pnl,
               ROUND((ast.last_price - h.avg_cost_price) / h.avg_cost_price * 100, 2) AS pnl_pct
        FROM Holdings h
        JOIN Accounts a   ON a.account_id  = h.account_id
        JOIN Assets   ast ON ast.asset_id  = h.asset_id
        WHERE h.net_quantity <> 0
    """
    args = ()
    if account_id:
        sql += " AND a.account_id = %s"
        args = (account_id,)
    sql += " ORDER BY unrealized_pnl DESC"
    return query(sql, args)

# ══════════════════════════════════════════════════════════════
# RISK ALERTS
# ══════════════════════════════════════════════════════════════
@app.get("/api/risk/alerts")
def risk_alerts():
    rows = query("""
        SELECT a.account_name,
               COALESCE(ast.ticker, '— ALL —')     AS ticker,
               COALESCE(rl.asset_class,'— ALL —')  AS asset_class,
               rl.max_position, rl.alert_threshold,
               COALESCE(h.net_quantity, 0)          AS current_position,
               ROUND(COALESCE(h.net_quantity,0) / rl.max_position * 100, 2) AS utilization_pct,
               CASE
                 WHEN COALESCE(h.net_quantity,0) >= rl.max_position
                      THEN 'BREACH'
                 WHEN COALESCE(h.net_quantity,0) >= rl.max_position * rl.alert_threshold / 100
                      THEN 'ALERT'
                 ELSE 'OK'
               END AS status
        FROM Risk_Limits rl
        JOIN Accounts a   ON a.account_id = rl.account_id
        LEFT JOIN Assets   ast ON ast.asset_id = rl.asset_id
        LEFT JOIN Holdings h   ON h.account_id = rl.account_id
                               AND (rl.asset_id IS NULL OR h.asset_id = rl.asset_id)
        WHERE rl.is_active = TRUE
        ORDER BY utilization_pct DESC
    """)
    return rows

# ══════════════════════════════════════════════════════════════
# EXPOSURE BY ASSET CLASS
# ══════════════════════════════════════════════════════════════
@app.get("/api/exposure")
def exposure():
    return query("""
        SELECT ast.asset_class,
               COUNT(DISTINCT h.asset_id) AS num_assets,
               ROUND(SUM(ast.last_price * h.net_quantity), 2) AS market_value
        FROM Holdings h JOIN Assets ast ON ast.asset_id = h.asset_id
        GROUP BY ast.asset_class ORDER BY market_value DESC
    """)

# ══════════════════════════════════════════════════════════════
# TRANSACTIONS  (CRUD)
# ══════════════════════════════════════════════════════════════
@app.get("/api/transactions")
def get_transactions(account_id: Optional[int] = None, limit: int = Query(50, le=500)):
    sql = """
        SELECT t.transaction_id, a.account_name,
               ast.ticker, t.direction, t.trade_type,
               t.quantity, t.execution_price,
               ROUND(t.quantity * t.execution_price, 2) AS notional,
               t.currency, cp.name AS counterparty,
               t.status, t.traded_at
        FROM Transactions t
        JOIN Accounts      a   ON a.account_id      = t.account_id
        JOIN Assets        ast ON ast.asset_id       = t.asset_id
        JOIN Counterparties cp ON cp.counterparty_id = t.counterparty_id
    """
    args = []
    if account_id:
        sql += " WHERE t.account_id = %s"
        args.append(account_id)
    sql += " ORDER BY t.traded_at DESC LIMIT %s"
    args.append(limit)
    return query(sql, tuple(args))

@app.post("/api/transactions")
def create_transaction(body: dict):
    required = ["account_id","asset_id","counterparty_id","trade_type",
                "direction","quantity","execution_price","currency","traded_at"]
    for f in required:
        if f not in body:
            raise HTTPException(400, f"Missing field: {f}")
    lid = execute("""
        INSERT INTO Transactions
          (account_id,asset_id,counterparty_id,trade_type,direction,quantity,
           execution_price,currency,traded_at,notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (body["account_id"], body["asset_id"], body["counterparty_id"],
          body["trade_type"], body["direction"], body["quantity"],
          body["execution_price"], body["currency"], body["traded_at"],
          body.get("notes","")))
    # update holdings
    _refresh_holding(body["account_id"], body["asset_id"])
    return {"transaction_id": lid}

@app.patch("/api/transactions/{txn_id}")
def amend_transaction(txn_id: int, body: dict):
    rows = query("SELECT * FROM Transactions WHERE transaction_id=%s", (txn_id,))
    if not rows:
        raise HTTPException(404, "Transaction not found")
    allowed = {"execution_price","quantity","notes","status"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        raise HTTPException(400, "No amendable fields provided")
    set_clause = ", ".join(f"{k}=%s" for k in updates)
    execute(f"UPDATE Transactions SET {set_clause}, status='amended' WHERE transaction_id=%s",
            (*updates.values(), txn_id))
    _refresh_holding(rows[0]["account_id"], rows[0]["asset_id"])
    return {"updated": txn_id}

@app.delete("/api/transactions/{txn_id}")
def cancel_transaction(txn_id: int):
    rows = query("SELECT * FROM Transactions WHERE transaction_id=%s", (txn_id,))
    if not rows:
        raise HTTPException(404, "Transaction not found")
    execute("UPDATE Transactions SET status='cancelled' WHERE transaction_id=%s", (txn_id,))
    _refresh_holding(rows[0]["account_id"], rows[0]["asset_id"])
    return {"cancelled": txn_id}

def _refresh_holding(account_id: int, asset_id: int):
    """Recalculate net_quantity and avg_cost from non-cancelled transactions."""
    rows = query("""
        SELECT direction, SUM(quantity) AS qty, AVG(execution_price) AS avg_px
        FROM Transactions
        WHERE account_id=%s AND asset_id=%s AND status<>'cancelled'
        GROUP BY direction
    """, (account_id, asset_id))
    buy_qty  = next((float(r["qty"]) for r in rows if r["direction"]=="buy"),  0)
    sell_qty = next((float(r["qty"]) for r in rows if r["direction"]=="sell"), 0)
    avg_px   = next((float(r["avg_px"]) for r in rows if r["direction"]=="buy"), 0)
    net = buy_qty - sell_qty
    if net > 0:
        execute("""
            INSERT INTO Holdings (account_id, asset_id, net_quantity, avg_cost_price)
            VALUES (%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE net_quantity=%s, avg_cost_price=%s
        """, (account_id, asset_id, net, avg_px, net, avg_px))
    else:
        execute("DELETE FROM Holdings WHERE account_id=%s AND asset_id=%s",
                (account_id, asset_id))

# ══════════════════════════════════════════════════════════════
# MASTER DATA
# ══════════════════════════════════════════════════════════════
@app.get("/api/accounts")
def get_accounts():
    return query("SELECT account_id, account_name, account_type, base_currency, status FROM Accounts WHERE status='active'")

@app.post("/api/accounts")
def create_account(body: dict):
    required = ["account_name", "account_type", "base_currency", "trader_id"]
    for f in required:
        if f not in body:
            raise HTTPException(400, f"Missing field: {f}")
    lid = execute("""
        INSERT INTO Accounts (account_name, account_type, base_currency, trader_id)
        VALUES (%s, %s, %s, %s)
    """, (body["account_name"], body["account_type"], body["base_currency"], body["trader_id"]))
    return {"account_id": lid}

@app.delete("/api/accounts/{account_id}")
def deactivate_account(account_id: int):
    rows = query("SELECT * FROM Accounts WHERE account_id=%s", (account_id,))
    if not rows:
        raise HTTPException(404, "Account not found")
    execute("UPDATE Accounts SET status='closed' WHERE account_id=%s", (account_id,))
    return {"closed": account_id}

@app.get("/api/assets")
def get_assets():
    return query("SELECT asset_id, ticker, name, asset_class, market, currency, last_price, status FROM Assets WHERE status='active' ORDER BY ticker")

@app.post("/api/assets")
def create_asset(body: dict):
    required = ["ticker", "name", "asset_class", "market", "currency"]
    for f in required:
        if f not in body:
            raise HTTPException(400, f"Missing field: {f}")
    lid = execute("""
        INSERT INTO Assets (ticker, name, asset_class, market, currency, last_price, price_updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
    """, (body["ticker"], body["name"], body["asset_class"], body["market"],
          body["currency"], body.get("last_price", 0)))
    return {"asset_id": lid}

@app.patch("/api/assets/{asset_id}/price")
def update_price(asset_id: int, body: dict):
    if "last_price" not in body:
        raise HTTPException(400, "last_price required")
    execute("UPDATE Assets SET last_price=%s, price_updated_at=NOW() WHERE asset_id=%s",
            (body["last_price"], asset_id))
    return {"updated": asset_id}

@app.delete("/api/assets/{asset_id}")
def delist_asset(asset_id: int):
    rows = query("SELECT * FROM Assets WHERE asset_id=%s", (asset_id,))
    if not rows:
        raise HTTPException(404, "Asset not found")
    execute("UPDATE Assets SET status='delisted' WHERE asset_id=%s", (asset_id,))
    return {"delisted": asset_id}

@app.get("/api/counterparties")
def get_counterparties():
    return query("SELECT * FROM Counterparties WHERE status='active' ORDER BY name")

@app.post("/api/counterparties")
def create_counterparty(body: dict):
    required = ["name", "type"]
    for f in required:
        if f not in body:
            raise HTTPException(400, f"Missing field: {f}")
    lid = execute("""
        INSERT INTO Counterparties (name, type, country, credit_rating)
        VALUES (%s, %s, %s, %s)
    """, (body["name"], body["type"], body.get("country", ""), body.get("credit_rating", "")))
    return {"counterparty_id": lid}

@app.delete("/api/counterparties/{cp_id}")
def deactivate_counterparty(cp_id: int):
    rows = query("SELECT * FROM Counterparties WHERE counterparty_id=%s", (cp_id,))
    if not rows:
        raise HTTPException(404, "Counterparty not found")
    execute("UPDATE Counterparties SET status='inactive' WHERE counterparty_id=%s", (cp_id,))
    return {"deactivated": cp_id}

@app.get("/api/traders")
def get_traders():
    return query("SELECT trader_id, name, email, role, status FROM Traders ORDER BY name")

# ══════════════════════════════════════════════════════════════
# RISK LIMITS CRUD
# ══════════════════════════════════════════════════════════════
@app.get("/api/risk-limits")
def get_risk_limits():
    return query("""
        SELECT rl.limit_id, a.account_name, COALESCE(ast.ticker,'— ALL —') AS ticker,
               COALESCE(rl.asset_class,'— ALL —') AS asset_class,
               rl.max_position, rl.max_concentration, rl.alert_threshold, rl.is_active
        FROM Risk_Limits rl
        JOIN Accounts a ON a.account_id = rl.account_id
        LEFT JOIN Assets ast ON ast.asset_id = rl.asset_id
        ORDER BY a.account_name, ticker
    """)

@app.post("/api/risk-limits")
def create_risk_limit(body: dict):
    if "account_id" not in body or "max_position" not in body:
        raise HTTPException(400, "account_id and max_position required")
    lid = execute("""
        INSERT INTO Risk_Limits (account_id, asset_id, asset_class, max_position, max_concentration, alert_threshold)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (body["account_id"], body.get("asset_id"), body.get("asset_class"),
          body["max_position"], body.get("max_concentration"), body.get("alert_threshold", 80)))
    return {"limit_id": lid}

@app.patch("/api/risk-limits/{limit_id}")
def update_risk_limit(limit_id: int, body: dict):
    rows = query("SELECT * FROM Risk_Limits WHERE limit_id=%s", (limit_id,))
    if not rows:
        raise HTTPException(404, "Risk limit not found")
    allowed = {"max_position", "max_concentration", "alert_threshold", "is_active"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        raise HTTPException(400, "No updatable fields provided")
    set_clause = ", ".join(f"{k}=%s" for k in updates)
    execute(f"UPDATE Risk_Limits SET {set_clause} WHERE limit_id=%s", (*updates.values(), limit_id))
    return {"updated": limit_id}

@app.delete("/api/risk-limits/{limit_id}")
def delete_risk_limit(limit_id: int):
    rows = query("SELECT * FROM Risk_Limits WHERE limit_id=%s", (limit_id,))
    if not rows:
        raise HTTPException(404, "Risk limit not found")
    execute("UPDATE Risk_Limits SET is_active=FALSE WHERE limit_id=%s", (limit_id,))
    return {"deactivated": limit_id}

# ══════════════════════════════════════════════════════════════
# REALIZED P&L
# ══════════════════════════════════════════════════════════════
@app.get("/api/pnl/realized")
def realized_pnl():
    return query("""
        SELECT a.account_name, ast.ticker,
               SUM(CASE WHEN t.direction='buy'  THEN t.quantity*t.execution_price ELSE 0 END) AS buy_cost,
               SUM(CASE WHEN t.direction='sell' THEN t.quantity*t.execution_price ELSE 0 END) AS sell_proceeds,
               SUM(CASE WHEN t.direction='sell' THEN t.quantity ELSE 0 END) AS sold_qty,
               ROUND(
                 SUM(CASE WHEN t.direction='sell' THEN t.quantity*t.execution_price ELSE 0 END)
               - SUM(CASE WHEN t.direction='buy'  THEN t.quantity*t.execution_price ELSE 0 END)
                 * SUM(CASE WHEN t.direction='sell' THEN t.quantity ELSE 0 END)
                 / NULLIF(SUM(CASE WHEN t.direction='buy' THEN t.quantity ELSE 0 END),0)
               , 2) AS realized_pnl
        FROM Transactions t
        JOIN Accounts a  ON a.account_id = t.account_id
        JOIN Assets  ast ON ast.asset_id  = t.asset_id
        WHERE t.status <> 'cancelled'
        GROUP BY a.account_name, ast.ticker
        HAVING sold_qty > 0
        ORDER BY realized_pnl DESC
    """)

# ══════════════════════════════════════════════════════════════
# STATIC FRONTEND
# ══════════════════════════════════════════════════════════════
app.mount("/static", StaticFiles(directory="/app/frontend/static"), name="static")

@app.get("/")
def root():
    return FileResponse("/app/frontend/index.html")
