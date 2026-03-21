-- =============================================================
-- Business Queries — Portfolio Management System
-- =============================================================

USE portfolio_mgmt;

-- -------------------------------------------------------------
-- 1. Per-account holdings with unrealized P&L
-- -------------------------------------------------------------
SELECT
    a.account_name,
    ast.ticker,
    ast.name          AS asset_name,
    ast.asset_class,
    h.net_quantity,
    h.avg_cost_price,
    ast.last_price    AS current_price,
    ast.currency,
    ROUND((ast.last_price - h.avg_cost_price) * h.net_quantity, 2)  AS unrealized_pnl,
    ROUND((ast.last_price - h.avg_cost_price) / h.avg_cost_price * 100, 2) AS pnl_pct
FROM Holdings h
JOIN Accounts a  ON a.account_id  = h.account_id
JOIN Assets   ast ON ast.asset_id  = h.asset_id
WHERE h.net_quantity <> 0
ORDER BY a.account_name, unrealized_pnl DESC;

-- -------------------------------------------------------------
-- 2. Portfolio summary — total cost, market value, P&L per account
-- -------------------------------------------------------------
SELECT
    a.account_id,
    a.account_name,
    a.account_type,
    ROUND(SUM(h.avg_cost_price * h.net_quantity), 2)  AS total_cost,
    ROUND(SUM(ast.last_price   * h.net_quantity), 2)  AS market_value,
    ROUND(SUM((ast.last_price - h.avg_cost_price) * h.net_quantity), 2) AS unrealized_pnl,
    ROUND(SUM((ast.last_price - h.avg_cost_price) * h.net_quantity)
          / NULLIF(SUM(h.avg_cost_price * h.net_quantity), 0) * 100, 2) AS pnl_pct
FROM Holdings h
JOIN Accounts a   ON a.account_id  = h.account_id
JOIN Assets   ast ON ast.asset_id  = h.asset_id
GROUP BY a.account_id, a.account_name, a.account_type
ORDER BY market_value DESC;

-- -------------------------------------------------------------
-- 3. Asset-class exposure across all accounts
-- -------------------------------------------------------------
SELECT
    ast.asset_class,
    COUNT(DISTINCT h.asset_id)                                    AS num_assets,
    ROUND(SUM(ast.last_price * h.net_quantity), 2)                AS total_market_value,
    ROUND(SUM(ast.last_price * h.net_quantity)
          / (SELECT SUM(a2.last_price * h2.net_quantity)
             FROM Holdings h2 JOIN Assets a2 ON a2.asset_id = h2.asset_id) * 100, 2) AS concentration_pct
FROM Holdings h
JOIN Assets ast ON ast.asset_id = h.asset_id
GROUP BY ast.asset_class
ORDER BY total_market_value DESC;

-- -------------------------------------------------------------
-- 4. Risk limit breach / alert detection
-- -------------------------------------------------------------
SELECT
    a.account_name,
    COALESCE(ast.ticker, '— ALL —')      AS ticker,
    COALESCE(rl.asset_class, '— ALL —')  AS asset_class,
    rl.max_position,
    rl.alert_threshold,
    COALESCE(h.net_quantity, 0)           AS current_position,
    ROUND(COALESCE(h.net_quantity, 0) / rl.max_position * 100, 2) AS utilization_pct,
    CASE
        WHEN COALESCE(h.net_quantity, 0) >= rl.max_position
            THEN 'BREACH'
        WHEN COALESCE(h.net_quantity, 0) >= rl.max_position * rl.alert_threshold / 100
            THEN 'ALERT'
        ELSE 'OK'
    END AS status
FROM Risk_Limits rl
JOIN Accounts a ON a.account_id = rl.account_id
LEFT JOIN Assets  ast ON ast.asset_id = rl.asset_id
LEFT JOIN Holdings h  ON h.account_id = rl.account_id
                      AND (rl.asset_id IS NULL OR h.asset_id = rl.asset_id)
WHERE rl.is_active = TRUE
ORDER BY utilization_pct DESC;

-- -------------------------------------------------------------
-- 5. Realized P&L from completed round-trips (FIFO simplified)
-- -------------------------------------------------------------
SELECT
    a.account_name,
    ast.ticker,
    SUM(CASE WHEN t.direction = 'buy'  THEN  t.quantity * t.execution_price ELSE 0 END) AS total_buy_cost,
    SUM(CASE WHEN t.direction = 'sell' THEN  t.quantity * t.execution_price ELSE 0 END) AS total_sell_proceeds,
    SUM(CASE WHEN t.direction = 'sell' THEN  t.quantity ELSE 0 END)                     AS sold_qty,
    ROUND(
        SUM(CASE WHEN t.direction = 'sell' THEN t.quantity * t.execution_price ELSE 0 END)
      - SUM(CASE WHEN t.direction = 'buy'  THEN t.quantity * t.execution_price ELSE 0 END)
          * SUM(CASE WHEN t.direction = 'sell' THEN t.quantity ELSE 0 END)
          / NULLIF(SUM(CASE WHEN t.direction = 'buy' THEN t.quantity ELSE 0 END), 0)
    , 2) AS realized_pnl
FROM Transactions t
JOIN Accounts a  ON a.account_id  = t.account_id
JOIN Assets  ast ON ast.asset_id  = t.asset_id
WHERE t.status <> 'cancelled'
GROUP BY a.account_name, ast.ticker
HAVING sold_qty > 0
ORDER BY realized_pnl DESC;

-- -------------------------------------------------------------
-- 6. Recent transactions (last 30 days)
-- -------------------------------------------------------------
SELECT
    t.transaction_id,
    a.account_name,
    ast.ticker,
    t.direction,
    t.trade_type,
    t.quantity,
    t.execution_price,
    ROUND(t.quantity * t.execution_price, 2) AS notional,
    t.currency,
    cp.name  AS counterparty,
    t.status,
    t.traded_at
FROM Transactions t
JOIN Accounts      a   ON a.account_id      = t.account_id
JOIN Assets        ast ON ast.asset_id       = t.asset_id
JOIN Counterparties cp ON cp.counterparty_id = t.counterparty_id
WHERE t.traded_at >= NOW() - INTERVAL 30 DAY
ORDER BY t.traded_at DESC;
