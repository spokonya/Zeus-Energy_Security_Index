-- =============================================================
-- ZEUS CORE — users + household profiles (Household Owner persona)
-- Matches: Home.py, user_routes.py, household_routes.py,
--          41_Household_Persona_Info.py
-- =============================================================

USE Zeus;

-- Mock demo users (no passwords). One row per dropdown option on Home.
-- email, country, and language are seeded and edited on the Persona Info page.
-- Seed data is loaded from 08_mockaroo_data.sql (runs after all schemas).
CREATE TABLE IF NOT EXISTS users (
    user_id      INT          NOT NULL AUTO_INCREMENT,
    display_name VARCHAR(100) NOT NULL,
    persona      ENUM('household_owner', 'journalist', 'energy_trader') NOT NULL,
    first_name   VARCHAR(50),
    email        VARCHAR(255),
    country      VARCHAR(100),
    language     VARCHAR(50),
    CONSTRAINT pk_users PRIMARY KEY (user_id)
);

-- Billing preferences per household_owner user (Persona Info billing form)
CREATE TABLE IF NOT EXISTS household_profiles (
    profile_id          INT           NOT NULL AUTO_INCREMENT,
    user_id             INT           NOT NULL,
    utility_provider    VARCHAR(100)  NOT NULL,
    monthly_bill_amount DECIMAL(10, 2) NOT NULL,
    bill_due_date       DATE          NOT NULL,
    billing_frequency   ENUM('Weekly', 'Monthly', 'Quarterly', 'Annually') NOT NULL,
    avg_monthly_kwh     DECIMAL(10, 2) NOT NULL,
    tariff_type         ENUM('Fixed rate', 'Variable rate', 'Time-of-use') NOT NULL,
    notes               TEXT,
    CONSTRAINT pk_household_profiles PRIMARY KEY (profile_id),
    CONSTRAINT uq_household_profiles_user UNIQUE (user_id),
    CONSTRAINT fk_household_profiles_user
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);
