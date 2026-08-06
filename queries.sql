-- =====================================================================
-- RealFootball 足球管理系统 —— 核心业务查询 SQL
-- 说明：项目代码用 Django ORM 实现，以下是对应 ORM 翻译出的等效 SQL。
-- 占位符 ? 表示参数（会话中的 user_id / manager_id、表单提交的 id 等）。
-- =====================================================================


-- ---------------------------------------------------------------------
-- 一、认证：注册
-- ---------------------------------------------------------------------

-- 1.1 判断用户名是否已存在
SELECT 1 FROM user_account WHERE username = 'zhang' LIMIT 1;

-- 1.2 计算新用户 id（取当前最大值 + 1）
SELECT MAX(user_id) FROM user;

-- 1.3 插入用户资料 + 账号（两张表配合，业务主键一致）
INSERT INTO user (user_id, id, name, age) VALUES (2, 2, '张三', 20);
INSERT INTO user_account (user_id, id, username, password) VALUES (2, 2, 'zhang', 'pbkdf2_sha256$...');

-- 经理注册逻辑同上，对象换为 football_manager / manager_account。


-- ---------------------------------------------------------------------
-- 二、普通球迷：关注
-- ---------------------------------------------------------------------

-- 2.1 关注球队（INSERT，主键用 MAX+1 手工生成）
SELECT MAX(id) FROM subscribe;
INSERT INTO subscribe (id, user_id, team_api_id) VALUES (4, 1, 50);

-- 2.2 关注球员
SELECT MAX(id) FROM follow;
INSERT INTO follow (id, user_id, player_fifa_api_id) VALUES (4, 1, 192);


-- ---------------------------------------------------------------------
-- 三、普通球迷：查看我关注的
-- ---------------------------------------------------------------------

-- 3.1 查看关注的球队（子查询 → 主查询 → 每队取最新战术快照）
SELECT team_api_id FROM subscribe WHERE user_id = 1;

SELECT * FROM team WHERE team_api_id IN (50, 87, 100) ORDER BY team_long_name;

SELECT * FROM team_attributes
WHERE team_api_id = 50
ORDER BY date DESC
LIMIT 1;                              -- date 最新 = 当前战术

-- 3.2 查看关注的球员
SELECT player_fifa_api_id FROM follow WHERE user_id = 1;

SELECT * FROM player
WHERE player_fifa_api_id IN (192, 377, 1508)
ORDER BY player_name;

SELECT * FROM player_attributes
WHERE player_fifa_api_id = 192
ORDER BY date DESC
LIMIT 1;                              -- 最新能力快照

-- 3.3 查看关注的比赛（OR 条件：主队或客队是我关注的球队）
SELECT * FROM match
WHERE home_team_api_id IN (50, 87, 100)
   OR away_team_api_id IN (50, 87, 100)
ORDER BY date DESC;

-- 3.4 给比赛行补充对手队名（单独一次查询做映射，避免 N+1）
SELECT team_api_id, team_long_name FROM team
WHERE team_api_id IN (50, 87, 100, 78, 34);   -- 从比赛行收集的所有队


-- ---------------------------------------------------------------------
-- 四、普通球迷：取消关注（DELETE，带复合条件只删自己的记录）
-- ---------------------------------------------------------------------

DELETE FROM subscribe WHERE user_id = 1 AND team_api_id = 50;
DELETE FROM follow WHERE user_id = 1 AND player_fifa_api_id = 192;


-- ---------------------------------------------------------------------
-- 五、普通球迷：球队推荐（按关注球队某战术属性的均值 ± 5 找相似队）
-- ---------------------------------------------------------------------

-- 5.1 先看我关注球队的平均风格（AVG 聚合，忽略空值）
SELECT AVG(buildUpPlaySpeed) AS avg_speed
FROM team_attributes
WHERE team_api_id IN (50, 87, 100)
  AND buildUpPlaySpeed IS NOT NULL;

-- 5.2 找均值 ±5 范围内的其他球队（区间查找 + 排除已关注的队）
SELECT * FROM team_attributes
WHERE team_api_id NOT IN (50, 87, 100)
  AND buildUpPlaySpeed BETWEEN 65 AND 75;


-- ---------------------------------------------------------------------
-- 六、普通球迷：猜球员小游戏（随机抽一名球员显示属性）
-- ---------------------------------------------------------------------

-- 6.1 加载全部有效属性（ORM 端 random.choice 随机，18 万行全量读入）
SELECT * FROM player_attributes WHERE player_fifa_api_id IS NOT NULL;

-- 6.2 取候选球员资料
SELECT * FROM player WHERE player_fifa_api_id = 192 LIMIT 1;

-- 6.3 取其它球员名做干扰选项
SELECT DISTINCT player_name FROM player
WHERE player_name <> 'Lionel Messi';


-- ---------------------------------------------------------------------
-- 七、足球经理：感兴趣球员
-- ---------------------------------------------------------------------

-- 7.1 加入感兴趣名单（先去重判断）
SELECT 1 FROM interested
WHERE licence_id = 2 AND player_fifa_api_id = 192 LIMIT 1;

INSERT INTO interested (id, licence_id, player_fifa_api_id) VALUES (6, 2, 192);

-- 7.2 查看感兴趣球员（列表）
SELECT player_fifa_api_id FROM interested WHERE licence_id = 2;

SELECT * FROM player
WHERE player_fifa_api_id IN (192, 377)
ORDER BY player_name;

-- 7.3 删除感兴趣球员
DELETE FROM interested WHERE licence_id = 2 AND player_fifa_api_id = 192;


-- ---------------------------------------------------------------------
-- 八、足球经理：申请执教
-- ---------------------------------------------------------------------

-- 8.1 检查是否已执教（Employ 主键是 licence_id → 一个经理最多一支队）
SELECT 1 FROM employ WHERE licence_id = 2 LIMIT 1;

-- 8.2 提交执教申请
INSERT INTO employ (licence_id, team_api_id) VALUES (2, 50);

-- 8.3 查看我的球队
SELECT * FROM employ WHERE licence_id = 2;
SELECT * FROM team WHERE team_api_id = 50;
SELECT * FROM league WHERE id = 1;

-- 8.4 我球队的所有球员（每个球员再取最新能力快照）
SELECT * FROM player WHERE team_api_id = 50 ORDER BY player_name;

SELECT * FROM player_attributes
WHERE player_fifa_api_id = 192
ORDER BY date DESC
LIMIT 1;


-- ---------------------------------------------------------------------
-- 九、足球经理：浏览全部球员（条件筛选 + 模糊搜索 + 分页）
-- ---------------------------------------------------------------------

-- 按联赛筛选（子查询：联赛 → 球队 → 球员）
SELECT team_api_id FROM team WHERE league_id = 1;

SELECT * FROM player
WHERE team_api_id IN (50, 87, 100)
ORDER BY player_name
LIMIT 50 OFFSET 0;                    -- 分页：每页 50 条

-- 模糊搜索（大小写不敏感的 LIKE）
SELECT * FROM player
WHERE player_name LIKE '%messi%' COLLATE NOCASE
ORDER BY player_name;

-- 联赛 + 球队 + 关键字组合
SELECT * FROM player
WHERE team_api_id = 50
  AND player_name LIKE '%mess%' COLLATE NOCASE
ORDER BY player_name
LIMIT 50 OFFSET 0;


-- ---------------------------------------------------------------------
-- 十、足球经理：球员推荐（按感兴趣球员某属性均值 ± 5 推荐）
-- ---------------------------------------------------------------------

-- 10.1 算均值（Python 端逐条 int() 转换，忽略非法值）
SELECT AVG(finishing) AS avg_finishing
FROM player_attributes
WHERE player_fifa_api_id IN (192, 377)
  AND finishing IS NOT NULL;

-- 10.2 找均值 ±5 范围、排除已感兴趣球员
SELECT * FROM player_attributes
WHERE finishing >= 70 AND finishing <= 80
  AND player_fifa_api_id NOT IN (192, 377);

-- 10.3 取推荐球员资料做展示
SELECT * FROM player
WHERE player_fifa_api_id IN (1508, 3315, 17499);
