-- =============================================================
-- ENERGY TRADER (persona 3) — watchlist, price alerts, trade journal
-- Matches: 52_My_Markets.py, 53_Trade_Journal.py
-- Price forecast ML1 data lives in 05_price_prediction.sql
-- =============================================================

USE Zeus;

-- Bidding zones the trader is actively watching (My Markets watchlist)
CREATE TABLE IF NOT EXISTS trader_watchlist (
    watchlist_id INT      NOT NULL AUTO_INCREMENT,
    user_id      INT      NOT NULL,
    country_code CHAR(2)  NOT NULL,
    added_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_trader_watchlist PRIMARY KEY (watchlist_id),
    CONSTRAINT uq_trader_watchlist_user_country UNIQUE (user_id, country_code),
    CONSTRAINT fk_trader_watchlist_user
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    INDEX idx_trader_watchlist_user (user_id)
);

-- Per-zone forecast threshold alerts (My Markets price alerts)
CREATE TABLE IF NOT EXISTS trader_price_alerts (
    alert_id     INT                              NOT NULL AUTO_INCREMENT,
    user_id      INT                              NOT NULL,
    country_code CHAR(2)                          NOT NULL,
    threshold    DECIMAL(10, 2)                   NOT NULL,
    direction    ENUM('above', 'below')           NOT NULL,
    created_at   DATETIME                         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME                         NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT pk_trader_price_alerts PRIMARY KEY (alert_id),
    CONSTRAINT uq_trader_price_alerts_user_country UNIQUE (user_id, country_code),
    CONSTRAINT fk_trader_price_alerts_user
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    INDEX idx_trader_price_alerts_user (user_id)
);

-- Trade journal entries — forecast calls, rationale, and outcome annotation
CREATE TABLE IF NOT EXISTS trader_trade_notes (
    note_id        INT                                           NOT NULL AUTO_INCREMENT,
    user_id        INT                                           NOT NULL,
    trade_date     DATE                                          NOT NULL,
    country_code   CHAR(2)                                       NOT NULL,
    direction      ENUM('Long', 'Short', 'Hedge')                NOT NULL,
    forecast_call  VARCHAR(300),
    note           TEXT,
    outcome        ENUM('Pending', 'Forecast correct', 'Forecast wrong')
                   NOT NULL DEFAULT 'Pending',
    outcome_note   VARCHAR(500),
    created_at     DATETIME                                      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME                                      NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT pk_trader_trade_notes PRIMARY KEY (note_id),
    CONSTRAINT fk_trader_trade_notes_user
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    INDEX idx_trader_trade_notes_user_date (user_id, trade_date)
);

-- Trade journal seed data is loaded from 08_mockaroo_data.sql.
