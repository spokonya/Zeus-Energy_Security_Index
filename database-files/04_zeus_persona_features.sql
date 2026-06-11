-- =============================================================
-- OPTIONAL PERSONA FEATURES — schema only (no UI wired yet)
-- Household: saved EU energy news articles
-- Journalist: frozen snapshot payloads + private journalist notes
-- =============================================================

USE Zeus;

-- Household Owner — bookmark articles from GET /news/eu-energy
CREATE TABLE IF NOT EXISTS saved_articles (
    article_id  INT           NOT NULL AUTO_INCREMENT,
    user_id     INT           NOT NULL,
    title       VARCHAR(300)  NOT NULL,
    link        VARCHAR(500)  NOT NULL,
    source_name VARCHAR(150),
    description TEXT,
    pub_date    DATETIME,
    saved_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_saved_articles PRIMARY KEY (article_id),
    CONSTRAINT fk_saved_articles_user
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    INDEX idx_saved_articles_user (user_id)
);

-- Journalist — save a frozen indicator + ML output bundle for citation
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id  INT          NOT NULL AUTO_INCREMENT,
    user_id      INT          NOT NULL,
    country_code CHAR(2)      NOT NULL,
    label        VARCHAR(150),
    payload      JSON         NOT NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_snapshots PRIMARY KEY (snapshot_id),
    CONSTRAINT fk_snapshots_user
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    INDEX idx_snapshots_user (user_id)
);

-- Journalist — private notes tied to a country (optional) or general notes
CREATE TABLE IF NOT EXISTS notes (
    note_id      INT           NOT NULL AUTO_INCREMENT,
    user_id      INT           NOT NULL,
    country_code CHAR(2),
    content      VARCHAR(2000) NOT NULL,
    context      JSON,
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT pk_notes PRIMARY KEY (note_id),
    CONSTRAINT fk_notes_user
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    INDEX idx_notes_user (user_id)
);
