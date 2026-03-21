-- =============================================================
-- Institutional Trader Portfolio Management System
-- Schema: portfolio_mgmt
-- =============================================================

USE portfolio_mgmt;

-- -------------------------------------------------------------
-- Traders
-- -------------------------------------------------------------
CREATE TABLE Traders (
    trader_id     INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100)        NOT NULL,
    email         VARCHAR(150)        NOT NULL UNIQUE,
    phone         VARCHAR(30),
    role          ENUM('fund_manager','prop_trader','risk_officer','admin') NOT NULL,
    status        ENUM('active','inactive') NOT NULL DEFAULT 'active',
    created_at    DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- Counterparties
-- -------------------------------------------------------------
CREATE TABLE Counterparties (
    counterparty_id   INT AUTO_INCREMENT PRIMARY KEY,
    name              VARCHAR(150)  NOT NULL,
    type              ENUM('broker','exchange','bank','clearing_house') NOT NULL,
    country           VARCHAR(60),
    credit_rating     VARCHAR(10),
    status            ENUM('active','inactive') NOT NULL DEFAULT 'active',
    created_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- Assets
-- -------------------------------------------------------------
CREATE TABLE Assets (
    asset_id      INT AUTO_INCREMENT PRIMARY KEY,
    ticker        VARCHAR(20)     NOT NULL UNIQUE,
    name          VARCHAR(200)    NOT NULL,
    asset_class   ENUM('equity','bond','fx','commodity','derivative','etf') NOT NULL,
    market        VARCHAR(50)     NOT NULL,   -- e.g. NYSE, NASDAQ, HKEX
    currency      CHAR(3)         NOT NULL,   -- ISO 4217
    last_price    DECIMAL(18,6),
    price_updated_at DATETIME,
    status        ENUM('active','delisted') NOT NULL DEFAULT 'active',
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- Accounts
-- -------------------------------------------------------------
CREATE TABLE Accounts (
    account_id    INT AUTO_INCREMENT PRIMARY KEY,
    account_name  VARCHAR(150)    NOT NULL,
    account_type  ENUM('proprietary','fund','hedge','custody') NOT NULL,
    base_currency CHAR(3)         NOT NULL DEFAULT 'USD',
    trader_id     INT             NOT NULL,
    status        ENUM('active','suspended','closed') NOT NULL DEFAULT 'active',
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_account_trader FOREIGN KEY (trader_id) REFERENCES Traders(trader_id)
);

-- -------------------------------------------------------------
-- Transactions
-- -------------------------------------------------------------
CREATE TABLE Transactions (
    transaction_id    INT AUTO_INCREMENT PRIMARY KEY,
    account_id        INT             NOT NULL,
    asset_id          INT             NOT NULL,
    counterparty_id   INT             NOT NULL,
    trade_type        ENUM('spot','futures','options','swap','bond') NOT NULL,
    direction         ENUM('buy','sell') NOT NULL,
    quantity          DECIMAL(18,6)   NOT NULL,
    execution_price   DECIMAL(18,6)   NOT NULL,
    currency          CHAR(3)         NOT NULL,
    status            ENUM('executed','amended','cancelled') NOT NULL DEFAULT 'executed',
    traded_at         DATETIME        NOT NULL,
    created_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes             TEXT,
    CONSTRAINT fk_txn_account       FOREIGN KEY (account_id)      REFERENCES Accounts(account_id),
    CONSTRAINT fk_txn_asset         FOREIGN KEY (asset_id)         REFERENCES Assets(asset_id),
    CONSTRAINT fk_txn_counterparty  FOREIGN KEY (counterparty_id)  REFERENCES Counterparties(counterparty_id),
    INDEX idx_txn_account  (account_id),
    INDEX idx_txn_asset    (asset_id),
    INDEX idx_txn_traded   (traded_at)
);

-- -------------------------------------------------------------
-- Holdings  (snapshot refreshed by trigger / batch)
-- -------------------------------------------------------------
CREATE TABLE Holdings (
    holding_id        INT AUTO_INCREMENT PRIMARY KEY,
    account_id        INT             NOT NULL,
    asset_id          INT             NOT NULL,
    net_quantity      DECIMAL(18,6)   NOT NULL DEFAULT 0,
    avg_cost_price    DECIMAL(18,6)   NOT NULL DEFAULT 0,
    last_updated      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_holding_account FOREIGN KEY (account_id) REFERENCES Accounts(account_id),
    CONSTRAINT fk_holding_asset   FOREIGN KEY (asset_id)   REFERENCES Assets(asset_id),
    UNIQUE KEY uq_holding (account_id, asset_id),
    INDEX idx_holding_asset (asset_id)
);

-- -------------------------------------------------------------
-- Risk_Limits
-- -------------------------------------------------------------
CREATE TABLE Risk_Limits (
    limit_id          INT AUTO_INCREMENT PRIMARY KEY,
    account_id        INT             NOT NULL,
    asset_id          INT,                     -- NULL = applies to whole account
    asset_class       ENUM('equity','bond','fx','commodity','derivative','etf'),  -- NULL = any
    max_position      DECIMAL(18,6)   NOT NULL,
    max_concentration DECIMAL(5,2),            -- % of portfolio (0-100)
    alert_threshold   DECIMAL(5,2)    NOT NULL DEFAULT 80.00,  -- % of limit that triggers alert
    is_active         BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_limit_account FOREIGN KEY (account_id) REFERENCES Accounts(account_id),
    CONSTRAINT fk_limit_asset   FOREIGN KEY (asset_id)   REFERENCES Assets(asset_id),
    INDEX idx_limit_account (account_id)
);
