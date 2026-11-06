-- =====================================================================
-- RealFootball —— 从 Kaggle 原始数据集重建本项目的数据表
--
-- 用法（在项目根目录）：
--   cp <kaggle 解压目录>/database.sqlite soccer.db
--   sqlite3 soccer.db < rebuild_data.sql     -- 本文件：派生列 + 索引
--   sqlite3 soccer.db < demo_data.sql        -- 业务表 + 演示账号
--
-- 前提：soccer.db 中已有 Kaggle 的 7 张原表：
--       country / league / team / player / player_attributes /
--       team_attributes / match
--
-- 作用：补齐数据集里没有、但本项目代码依赖的派生列，并建查询索引。
-- =====================================================================

BEGIN TRANSACTION;

-- ---------------------------------------------------------------------
-- 1) team.league_id —— 该队出场次数最多的联赛
--    数据集里球队表没有所属联赛，需要从比赛表反推。
-- ---------------------------------------------------------------------
ALTER TABLE team ADD COLUMN league_id INTEGER;

UPDATE team SET league_id = (
    SELECT m.league_id FROM match m
    WHERE m.home_team_api_id = team.team_api_id
       OR m.away_team_api_id = team.team_api_id
    GROUP BY m.league_id
    ORDER BY COUNT(*) DESC
    LIMIT 1
);

-- ---------------------------------------------------------------------
-- 2) player.team_api_id / player.league_id
--    数据集里球员表也没有球队字段，从每场比赛的首发名单反推：
--    取该球员最后一次出场时所在的球队，联赛再由球队带出。
-- ---------------------------------------------------------------------
ALTER TABLE player ADD COLUMN team_api_id INTEGER;
ALTER TABLE player ADD COLUMN league_id  INTEGER;

CREATE TEMP TABLE _appearance AS
    SELECT home_player_1  AS pid, home_team_api_id AS tid, date FROM match WHERE home_player_1  IS NOT NULL
    UNION ALL SELECT away_player_1  AS pid, away_team_api_id AS tid, date FROM match WHERE away_player_1  IS NOT NULL
    UNION ALL SELECT home_player_2  AS pid, home_team_api_id AS tid, date FROM match WHERE home_player_2  IS NOT NULL
    UNION ALL SELECT away_player_2  AS pid, away_team_api_id AS tid, date FROM match WHERE away_player_2  IS NOT NULL
    UNION ALL SELECT home_player_3  AS pid, home_team_api_id AS tid, date FROM match WHERE home_player_3  IS NOT NULL
    UNION ALL SELECT away_player_3  AS pid, away_team_api_id AS tid, date FROM match WHERE away_player_3  IS NOT NULL
    UNION ALL SELECT home_player_4  AS pid, home_team_api_id AS tid, date FROM match WHERE home_player_4  IS NOT NULL
    UNION ALL SELECT away_player_4  AS pid, away_team_api_id AS tid, date FROM match WHERE away_player_4  IS NOT NULL
    UNION ALL SELECT home_player_5  AS pid, home_team_api_id AS tid, date FROM match WHERE home_player_5  IS NOT NULL
    UNION ALL SELECT away_player_5  AS pid, away_team_api_id AS tid, date FROM match WHERE away_player_5  IS NOT NULL
    UNION ALL SELECT home_player_6  AS pid, home_team_api_id AS tid, date FROM match WHERE home_player_6  IS NOT NULL
    UNION ALL SELECT away_player_6  AS pid, away_team_api_id AS tid, date FROM match WHERE away_player_6  IS NOT NULL
    UNION ALL SELECT home_player_7  AS pid, home_team_api_id AS tid, date FROM match WHERE home_player_7  IS NOT NULL
    UNION ALL SELECT away_player_7  AS pid, away_team_api_id AS tid, date FROM match WHERE away_player_7  IS NOT NULL
    UNION ALL SELECT home_player_8  AS pid, home_team_api_id AS tid, date FROM match WHERE home_player_8  IS NOT NULL
    UNION ALL SELECT away_player_8  AS pid, away_team_api_id AS tid, date FROM match WHERE away_player_8  IS NOT NULL
    UNION ALL SELECT home_player_9  AS pid, home_team_api_id AS tid, date FROM match WHERE home_player_9  IS NOT NULL
    UNION ALL SELECT away_player_9  AS pid, away_team_api_id AS tid, date FROM match WHERE away_player_9  IS NOT NULL
    UNION ALL SELECT home_player_10 AS pid, home_team_api_id AS tid, date FROM match WHERE home_player_10 IS NOT NULL
    UNION ALL SELECT away_player_10 AS pid, away_team_api_id AS tid, date FROM match WHERE away_player_10 IS NOT NULL
    UNION ALL SELECT home_player_11 AS pid, home_team_api_id AS tid, date FROM match WHERE home_player_11 IS NOT NULL
    UNION ALL SELECT away_player_11 AS pid, away_team_api_id AS tid, date FROM match WHERE away_player_11 IS NOT NULL;

UPDATE player SET team_api_id = (
    SELECT a.tid FROM _appearance a
    WHERE a.pid = player.player_api_id
    ORDER BY a.date DESC
    LIMIT 1
);

UPDATE player SET league_id = (
    SELECT t.league_id FROM team t
    WHERE t.team_api_id = player.team_api_id
);

DROP TABLE _appearance;

-- ---------------------------------------------------------------------
-- 3) match 的主客队技术统计列
--    数据集原始比赛表每场只有一套球队统计（主队口径），本项目把它拆成
--    shoton1/shoton2 这类主客两列。重建时把原值写进 *1，*2 留空。
--    （原 soccer.db 中 *2 的数据源不在 Kaggle 数据集里，无法恢复。）
-- ---------------------------------------------------------------------
ALTER TABLE match ADD COLUMN shoton1     INTEGER;
ALTER TABLE match ADD COLUMN shotoff1    INTEGER;
ALTER TABLE match ADD COLUMN foulcommit1 INTEGER;
ALTER TABLE match ADD COLUMN card1       INTEGER;
ALTER TABLE match ADD COLUMN cross1      INTEGER;
ALTER TABLE match ADD COLUMN corner1     INTEGER;
ALTER TABLE match ADD COLUMN possession1 INTEGER;
ALTER TABLE match ADD COLUMN shoton2     INTEGER;
ALTER TABLE match ADD COLUMN shotoff2    INTEGER;
ALTER TABLE match ADD COLUMN foulcommit2 INTEGER;
ALTER TABLE match ADD COLUMN card2       INTEGER;
ALTER TABLE match ADD COLUMN cross2      INTEGER;
ALTER TABLE match ADD COLUMN corner2     INTEGER;
ALTER TABLE match ADD COLUMN possession2 INTEGER;

UPDATE match SET
    shoton1     = shoton,
    shotoff1    = shotoff,
    foulcommit1 = foulcommit,
    card1       = card,
    cross1      = cross,
    corner1     = corner,
    possession1 = possession;

-- ---------------------------------------------------------------------
-- 4) 查询索引（球员名模糊搜索、按球队/联赛筛选都靠它）
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_player_player_name          ON player(player_name);
CREATE INDEX IF NOT EXISTS idx_player_team_api_id         ON player(team_api_id);
CREATE INDEX IF NOT EXISTS idx_player_league_id           ON player(league_id);
CREATE INDEX IF NOT EXISTS idx_player_attributes_player   ON player_attributes(player_fifa_api_id);

COMMIT;
