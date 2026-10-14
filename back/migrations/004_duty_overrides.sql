-- PostgreSQL: keep duty swap history and the revert link for accepted exchanges.
ALTER TABLE exchange_posts ADD COLUMN IF NOT EXISTS revert_of VARCHAR(36);
CREATE INDEX IF NOT EXISTS ix_exchange_posts_revert_of ON exchange_posts(revert_of);

CREATE TABLE IF NOT EXISTS duty_overrides (
    id VARCHAR(36) PRIMARY KEY,
    driver_name VARCHAR(100) NOT NULL,
    date VARCHAR(10) NOT NULL,
    code VARCHAR(32) NOT NULL,
    original_code VARCHAR(32) NOT NULL,
    post_id VARCHAR(36) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_duty_overrides_driver_name ON duty_overrides(driver_name);
CREATE INDEX IF NOT EXISTS ix_duty_overrides_date ON duty_overrides(date);
CREATE INDEX IF NOT EXISTS ix_duty_overrides_post_id ON duty_overrides(post_id);
CREATE INDEX IF NOT EXISTS ix_duty_overrides_active ON duty_overrides(active);
CREATE UNIQUE INDEX IF NOT EXISTS uq_duty_overrides_active_driver_date
    ON duty_overrides(driver_name, date) WHERE active = TRUE;
