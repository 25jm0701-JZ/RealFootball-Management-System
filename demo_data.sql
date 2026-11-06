-- RealFootball 业务表与演示数据（Kaggle 静态表可重新下载，业务数据仅存于此）
-- 生成: 从 soccer.db 导出 2026-11-07
BEGIN TRANSACTION;

CREATE TABLE "user" ("user_id" INTEGER, "name" TEXT, "age" INTEGER, "id" INTEGER);
INSERT INTO "user" VALUES('1','测试粉丝','20','1');

CREATE TABLE "user_account" ("user_id" INTEGER, "username" TEXT, "password" TEXT, "id" INTEGER, "last_login" DATETIME);
INSERT INTO "user_account" VALUES('1','fantest','pbkdf2_sha256$1000000$OOJIbaACQHJUo6Iwm46vjM$1Q46wHPBvWLtEBWyII2ypMEyS9/43TJXS1QDspP3qeI=','1','2026-08-06 06:48:27.261944');

CREATE TABLE "football_manager" ("licence_id" INTEGER, "name" TEXT, "age" INTEGER, "id" INTEGER);
INSERT INTO "football_manager" VALUES('1','教练甲','40','1');
INSERT INTO "football_manager" VALUES('2','JJ','30','2');
INSERT INTO "football_manager" VALUES('3','JoseM','56','3');

CREATE TABLE "manager_account" ("licence_id" INTEGER, "username" TEXT, "password" TEXT, "id" INTEGER, "last_login" DATETIME);
INSERT INTO "manager_account" VALUES('1','coach01','pbkdf2_sha256$1000000$6ulhwWDWN83Ds7B3CcsYzS$Mp974g9oxruqBd0oYkPO9dMuqRvTi+oViw13WWKMuDU=','1','2026-08-06 08:15:31.297847');
INSERT INTO "manager_account" VALUES('2','Coach1','pbkdf2_sha256$1000000$C3JgJcVuk6O9MRdtLn2cEq$VipecETW1PmaBjwdPI0XJtNfogwdbMCuY/mVpV+2mqY=','2',NULL);
INSERT INTO "manager_account" VALUES('3','JoseM','pbkdf2_sha256$1000000$GLtovPjLqmDIXgs2fdsCi2$J+09/w2MNOkoC3yiVKemo/tH9IO3fQNWbLeEPECBIFo=','3','2026-09-13 14:34:34.645684');

CREATE TABLE "interested" ("licence_id" INTEGER, "player_fifa_api_id" INTEGER, "id" INTEGER);
INSERT INTO "interested" VALUES('2','179811',NULL);
INSERT INTO "interested" VALUES('1','30110',NULL);
INSERT INTO "interested" VALUES('1','184344',NULL);
INSERT INTO "interested" VALUES('1','192505',NULL);
INSERT INTO "interested" VALUES('1','189615',NULL);
INSERT INTO "interested" VALUES('3','204549',NULL);

CREATE TABLE "employ" ("licence_id" INTEGER, "team_api_id" INTEGER, "id" INTEGER);
INSERT INTO "employ" VALUES('2','10260',NULL);
INSERT INTO "employ" VALUES('1','8633',NULL);

CREATE TABLE "follow" ("player_fifa_api_id" INTEGER, "user_id" INTEGER, "id" INTEGER);
INSERT INTO "follow" VALUES('244','1','1');
INSERT INTO "follow" VALUES('225685','1','2');
INSERT INTO "follow" VALUES('13732','1','3');

CREATE TABLE "subscribe" ("team_api_id" INTEGER, "user_id" INTEGER, "id" INTEGER);
INSERT INTO "subscribe" VALUES('8456','1','1');

COMMIT;
