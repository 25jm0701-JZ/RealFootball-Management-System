-- =====================================================================
-- RealFootball 足球管理系统 —— 数据库 Schema
-- 数据库：SQLite（soccer.db）
-- 说明：
--   1) 以下结构与 soccer.db 实际 schema 一致（.schema 导出）。
--   2) 表分为两类：
--        [数据表] 由 Kaggle 欧洲足球数据集导入，只读，Django 端 managed=False
--        [业务表] 系统运行所需的用户 / 关注 / 执教等关系表
--   3) 结尾附「建议改进」，是理想化的完整约束版本，供文档 / 答辩参考。
-- =====================================================================


-- ---------------------------------------------------------------------
-- 第一部分：数据表（来自数据集）
-- ---------------------------------------------------------------------

-- 国家表（11 行）
CREATE TABLE country (
    id   INTEGER PRIMARY KEY,
    name TEXT
);

-- 联赛表（11 行）：国家 1 —— N 联赛
CREATE TABLE league (
    id         INTEGER PRIMARY KEY,
    country_id INTEGER,          -- 外键 → country.id
    name       TEXT
);

-- 球队表（299 行）
CREATE TABLE team (
    id               INTEGER,
    team_api_id      INTEGER PRIMARY KEY,   -- 系统内唯一队标
    team_fifa_api_id INTEGER,
    team_long_name   TEXT,                  -- 全名，如 "Manchester United"
    team_short_name  TEXT,                  -- 简称，如 "MUN"
    league_id        INTEGER                -- 外键 → league.id
);

-- 球员表（11,060 行）：球队 1 —— N 球员
CREATE TABLE player (
    id                 INTEGER,
    player_api_id      INTEGER,
    player_name        TEXT,
    player_fifa_api_id INTEGER PRIMARY KEY, -- 系统内唯一球员标
    birthday           TEXT,
    height             INTEGER,             -- 单位：厘米
    weight             INTEGER,             -- 单位：磅
    team_api_id        INTEGER,             -- 外键 → team.team_api_id
    league_id          INTEGER              -- 冗余自球队
);

-- 球员能力快照表（183,978 行，最大的表）
-- 同一球员在不同日期有多条快照，构成时间序列；取 date 最新一条即当前能力。
CREATE TABLE player_attributes (
    id                  INTEGER,
    player_fifa_api_id  INTEGER,   -- 外键 → player.player_fifa_api_id
    player_api_id       INTEGER,
    date                TEXT,      -- 快照日期（YYYY-MM-DD）
    overall_rating      INTEGER,   -- 总评
    potential           INTEGER,   -- 潜力
    preferred_foot      TEXT,      -- 惯用脚
    attacking_work_rate TEXT,
    defensive_work_rate TEXT,
    -- 技术属性（0~100）
    crossing INTEGER, finishing INTEGER, heading_accuracy INTEGER,
    short_passing INTEGER, volleys INTEGER, dribbling INTEGER, curve INTEGER,
    free_kick_accuracy INTEGER, long_passing INTEGER, ball_control INTEGER,
    acceleration INTEGER, sprint_speed INTEGER, agility INTEGER, reactions INTEGER,
    balance INTEGER, shot_power INTEGER, jumping INTEGER, stamina INTEGER,
    strength INTEGER, long_shots INTEGER, aggression INTEGER, interceptions INTEGER,
    positioning INTEGER, vision INTEGER, penalties INTEGER, marking INTEGER,
    standing_tackle INTEGER, sliding_tackle INTEGER,
    -- 门将属性
    gk_diving INTEGER, gk_handling INTEGER, gk_kicking INTEGER,
    gk_positioning INTEGER, gk_reflexes INTEGER
);

-- 球队战术快照表（1,458 行）：同一球队多日期快照
CREATE TABLE team_attributes (
    id                INTEGER,
    team_fifa_api_id  INTEGER,
    team_api_id       INTEGER,    -- 外键 → team.team_api_id
    date              TEXT,       -- 快照日期
    -- 进攻组织（build up play）
    buildUpPlaySpeed INTEGER, buildUpPlaySpeedClass TEXT,
    buildUpPlayDribbling INTEGER, buildUpPlayDribblingClass TEXT,
    buildUpPlayPassing INTEGER, buildUpPlayPassingClass TEXT,
    buildUpPlayPositioningClass TEXT,
    -- 机会创造（chance creation）
    chanceCreationPassing INTEGER, chanceCreationPassingClass TEXT,
    chanceCreationCrossing INTEGER, chanceCreationCrossingClass TEXT,
    chanceCreationShooting INTEGER, chanceCreationShootingClass TEXT,
    chanceCreationPositioningClass TEXT,
    -- 防守（defence）
    defencePressure INTEGER, defencePressureClass TEXT,
    defenceAggression INTEGER, defenceAggressionClass TEXT,
    defenceTeamWidth INTEGER, defenceTeamWidthClass TEXT,
    defenceDefenderLineClass TEXT
);

-- 比赛表（25,979 行）：一场比赛一行，主客队各一套统计
CREATE TABLE match (
    id               INTEGER,
    league_id        INTEGER,     -- 外键 → league.id
    season           TEXT,        -- 赛季，如 "2010/2011"
    stage            INTEGER,     -- 轮次
    date             TEXT,
    match_api_id     INTEGER,
    home_team_api_id INTEGER,     -- 外键 → team.team_api_id（主队）
    away_team_api_id INTEGER,     -- 外键 → team.team_api_id（客队）
    home_team_goal   INTEGER,
    away_team_goal   INTEGER,
    -- 主队 / 客队技术统计
    shoton1    INTEGER, shoton2    INTEGER,   -- 射正
    shotoff1   INTEGER, shotoff2   INTEGER,   -- 射偏
    foulcommit1 INTEGER, foulcommit2 INTEGER,  -- 犯规
    card1      INTEGER, card2      INTEGER,    -- 黄牌
    cross1     INTEGER, cross2     INTEGER,    -- 传中
    corner1    INTEGER, corner2    INTEGER,    -- 角球
    possession1 INTEGER, possession2 INTEGER    -- 控球率（%）
);

-- 数据表查询索引（性能命脉）
CREATE INDEX idx_player_player_name ON player(player_name);
CREATE INDEX idx_player_team_api_id ON player(team_api_id);
CREATE INDEX idx_player_league_id   ON player(league_id);
CREATE INDEX idx_player_attributes_player ON player_attributes(player_fifa_api_id);


-- ---------------------------------------------------------------------
-- 第二部分：业务表（系统运行时数据）
-- ---------------------------------------------------------------------

-- 普通球迷资料表
CREATE TABLE user (
    user_id INTEGER,
    name    TEXT,
    age     INTEGER,
    id      INTEGER
);

-- 球迷登录账号表（与 user 一一对应）
CREATE TABLE user_account (
    user_id    INTEGER,
    username   TEXT,
    password   TEXT,
    id         INTEGER,
    last_login DATETIME
);

-- 球迷关注球队（user 与 team 的多对多关系表）
CREATE TABLE subscribe (
    team_api_id INTEGER,   -- 外键 → team.team_api_id
    user_id     INTEGER,   -- 外键 → user.user_id
    id          INTEGER
);

-- 球迷关注球员（user 与 player 的多对多关系表）
CREATE TABLE follow (
    player_fifa_api_id INTEGER,  -- 外键 → player.player_fifa_api_id
    user_id            INTEGER,  -- 外键 → user.user_id
    id                 INTEGER
);

-- 足球经理资料表
CREATE TABLE football_manager (
    licence_id INTEGER,   -- 执教执照号，业务主键
    name       TEXT,
    age        INTEGER,
    id         INTEGER
);

-- 经理登录账号表（与 football_manager 一一对应）
CREATE TABLE manager_account (
    licence_id INTEGER,
    username   TEXT,
    password   TEXT,
    id         INTEGER,
    last_login DATETIME
);

-- 经理执教球队（licence_id 是主键 → 一个经理只能带一支队）
CREATE TABLE employ (
    licence_id  INTEGER,   -- 外键 → football_manager.licence_id
    team_api_id INTEGER,   -- 外键 → team.team_api_id
    id          INTEGER
);

-- 经理感兴趣的球员（football_manager 与 player 的多对多关系表）
CREATE TABLE interested (
    licence_id         INTEGER,   -- 外键 → football_manager.licence_id
    player_fifa_api_id INTEGER,   -- 外键 → player.player_fifa_api_id
    id                 INTEGER
);


-- ---------------------------------------------------------------------
-- 建议改进（理想化完整约束版本，Django 端 managed=False 未生效）
-- ---------------------------------------------------------------------
-- 1) 业务表的 id 列未声明 PRIMARY KEY，也无 AUTOINCREMENT，
--    代码里用 SELECT MAX(id)+1 手工造主键，并发写入会撞键。
--    建议：
--        id INTEGER PRIMARY KEY AUTOINCREMENT,
-- 2) 全库未建 FOREIGN KEY 约束（关系靠应用层维护）。
--    建议对 employ / interested / follow / subscribe 等表补上
--    REFERENCES team(team_api_id) / REFERENCES player(player_fifa_api_id) 等。
-- 3) player_attributes / team_attributes / match 可补主键与
--    (player_fifa_api_id, date) 复合索引，加速「取最新快照」类查询。
