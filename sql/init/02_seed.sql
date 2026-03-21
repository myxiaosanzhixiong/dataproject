-- =============================================================
-- Seed Data
-- =============================================================

USE portfolio_mgmt;

-- Traders
INSERT INTO Traders (name, email, phone, role) VALUES
('Alice Chen',   'alice.chen@firm.com',   '+1-212-555-0101', 'fund_manager'),
('Bob Zhang',    'bob.zhang@firm.com',    '+1-212-555-0102', 'prop_trader'),
('Carol Liu',    'carol.liu@firm.com',    '+1-212-555-0103', 'risk_officer'),
('David Wang',   'david.wang@firm.com',   '+1-212-555-0104', 'prop_trader'),
('Eva Nguyen',   'eva.nguyen@firm.com',   '+1-212-555-0105', 'fund_manager');

-- Counterparties
INSERT INTO Counterparties (name, type, country, credit_rating) VALUES
('Goldman Sachs',       'broker',        'US', 'AA'),
('JP Morgan',           'broker',        'US', 'AA'),
('NYSE',                'exchange',      'US', 'AAA'),
('HKEX',                'exchange',      'HK', 'AA+'),
('Citibank',            'bank',          'US', 'A+'),
('LCH Clearnet',        'clearing_house','UK', 'AAA');

-- Assets
INSERT INTO Assets (ticker, name, asset_class, market, currency, last_price, price_updated_at) VALUES
('AAPL',  'Apple Inc.',                     'equity',     'NASDAQ', 'USD', 189.50, NOW()),
('MSFT',  'Microsoft Corp.',                'equity',     'NASDAQ', 'USD', 415.20, NOW()),
('TSLA',  'Tesla Inc.',                     'equity',     'NASDAQ', 'USD', 245.00, NOW()),
('SPY',   'SPDR S&P 500 ETF',               'etf',        'NYSE',   'USD', 520.30, NOW()),
('QQQ',   'Invesco QQQ Trust',              'etf',        'NASDAQ', 'USD', 448.10, NOW()),
('US10Y', 'US 10-Year Treasury Bond',       'bond',       'OTC',    'USD',  98.75, NOW()),
('EURUSD','EUR/USD FX Spot',                'fx',         'OTC',    'USD',   1.085, NOW()),
('GC1',   'Gold Futures (front month)',     'commodity',  'COMEX',  'USD',2340.00, NOW()),
('ES1',   'E-mini S&P 500 Futures',         'derivative', 'CME',    'USD',5210.00, NOW()),
('700.HK','Tencent Holdings',               'equity',     'HKEX',   'HKD', 385.00, NOW());

-- Accounts
INSERT INTO Accounts (account_name, account_type, base_currency, trader_id) VALUES
('Global Equity Fund',        'fund',          'USD', 1),
('Asia Opportunities Fund',   'fund',          'USD', 5),
('Prop Desk Alpha',           'proprietary',   'USD', 2),
('Prop Desk Beta',            'proprietary',   'USD', 4),
('Fixed Income Custody',      'custody',       'USD', 1);

-- Transactions
INSERT INTO Transactions (account_id, asset_id, counterparty_id, trade_type, direction, quantity, execution_price, currency, traded_at) VALUES
(1, 1,  1, 'spot', 'buy',  5000,  185.20, 'USD', '2026-03-01 09:35:00'),
(1, 2,  1, 'spot', 'buy',  3000,  410.50, 'USD', '2026-03-01 09:40:00'),
(1, 4,  3, 'spot', 'buy',  2000,  515.00, 'USD', '2026-03-02 10:00:00'),
(2,10,  4, 'spot', 'buy',  8000,  375.00, 'HKD', '2026-03-02 10:30:00'),
(3, 9,  3, 'futures','buy', 50,  5150.00, 'USD', '2026-03-03 14:00:00'),
(3, 8,  3, 'futures','buy', 20,  2310.00, 'USD', '2026-03-03 14:15:00'),
(4, 3,  2, 'spot', 'buy',  4000,  238.00, 'USD', '2026-03-04 11:00:00'),
(4, 5,  3, 'spot', 'buy',  1500,  440.00, 'USD', '2026-03-04 11:10:00'),
(5, 6,  5, 'bond', 'buy', 50000,   98.50, 'USD', '2026-03-05 09:00:00'),
(1, 1,  1, 'spot', 'sell', 1000,  191.00, 'USD', '2026-03-10 15:00:00'),
(3, 9,  3, 'futures','sell',20,  5250.00, 'USD', '2026-03-15 13:30:00'),
(4, 3,  2, 'spot', 'sell', 500,   252.00, 'USD', '2026-03-18 10:45:00');

-- Holdings  (net positions derived from transactions above)
INSERT INTO Holdings (account_id, asset_id, net_quantity, avg_cost_price) VALUES
(1, 1,  4000, 185.20),   -- AAPL  (5000 bought - 1000 sold)
(1, 2,  3000, 410.50),   -- MSFT
(1, 4,  2000, 515.00),   -- SPY
(2,10,  8000, 375.00),   -- Tencent
(3, 9,    30, 5150.00),  -- ES1 futures (50 - 20 sold)
(3, 8,    20, 2310.00),  -- Gold futures
(4, 3,  3500, 238.00),   -- TSLA (4000 - 500 sold)
(4, 5,  1500, 440.00),   -- QQQ
(5, 6, 50000,  98.50);   -- US10Y bond

-- Risk Limits
INSERT INTO Risk_Limits (account_id, asset_id, asset_class, max_position, max_concentration, alert_threshold) VALUES
-- Account-level equity concentration limit
(1, NULL, 'equity',     20000000, 60.00, 80.00),
-- Per-asset limits
(1,    1,  NULL,        10000,    NULL,  80.00),   -- AAPL max 10k shares
(1,    2,  NULL,         8000,    NULL,  80.00),   -- MSFT max 8k shares
(3,    9,  NULL,          100,    NULL,  75.00),   -- ES1 futures max 100 contracts
(3, NULL, 'commodity',   5000000, 20.00, 80.00),   -- Commodity notional limit
(4,    3,  NULL,        10000,    NULL,  80.00),   -- TSLA max 10k shares
(5, NULL, 'bond',      100000000, 80.00, 85.00);   -- Fixed income limit
