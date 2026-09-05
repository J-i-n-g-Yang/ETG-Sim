-- ============================================================
-- Townhall ETG Schema  (SQL Server)
-- Apply once before running the app.
-- ============================================================

CREATE TABLE townhall_players (
    user_id       VARCHAR(36)   NOT NULL PRIMARY KEY,
    display_name  VARCHAR(50)   NOT NULL UNIQUE,
    credits       DECIMAL(18,2) NOT NULL DEFAULT 1000,
    created_at    DATETIME      NOT NULL DEFAULT GETDATE()
);

-- One row per live/settled round.  The server restores state from here on restart.
CREATE TABLE townhall_rounds (
    round_id        INT IDENTITY(1,1) PRIMARY KEY,
    game            VARCHAR(20)   NOT NULL,  -- baccarat | sicbo | roulette
    game_index      INT           NOT NULL,  -- 0..2
    round_number    INT           NOT NULL,  -- 1..8
    phase           VARCHAR(16)   NOT NULL,  -- IDLE|BETTING_OPEN|BETTING_LOCKED|REVEALING|SETTLED|VOIDED
    betting_ends_at DATETIME      NULL,
    outcome_json    NVARCHAR(MAX) NULL,      -- set exactly once at REVEALING
    settled_at      DATETIME      NULL,
    created_at      DATETIME      NOT NULL DEFAULT GETDATE()
);

CREATE TABLE townhall_bets (
    bet_id         INT IDENTITY(1,1) PRIMARY KEY,
    round_id       INT           NOT NULL,
    user_id        VARCHAR(36)   NOT NULL,
    game           VARCHAR(20)   NOT NULL,
    wager_type     VARCHAR(30)   NOT NULL,
    amount         DECIMAL(18,2) NOT NULL,
    payout         DECIMAL(18,2) NULL,       -- filled at settlement
    balance_after  DECIMAL(18,2) NULL,       -- filled at settlement
    bet_uid        VARCHAR(64)   NULL,       -- optional client idempotency key
    ts             DATETIME      NOT NULL DEFAULT GETDATE()
);

CREATE INDEX IX_bets_round ON townhall_bets(round_id);
CREATE INDEX IX_bets_user  ON townhall_bets(user_id);
CREATE UNIQUE INDEX UX_bets_uid ON townhall_bets(bet_uid) WHERE bet_uid IS NOT NULL;

-- ============================================================
-- Admin helpers (run manually)
-- ============================================================

-- Reset event (keep players, restore credits, wipe rounds/bets):
--   DELETE FROM townhall_bets;
--   DELETE FROM townhall_rounds;
--   UPDATE townhall_players SET credits = 1000;
--
-- Full wipe:
--   DELETE FROM townhall_bets;
--   DELETE FROM townhall_rounds;
--   DELETE FROM townhall_players;
--
-- See winner:
--   SELECT TOP 5 display_name, credits
--   FROM townhall_players
--   ORDER BY credits DESC, created_at ASC;

select lightning_json from gamingoptimizationsfo.dbo.townhall_rounds
