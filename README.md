# RealFootball 足球管理系统

> 大学二年级《数据库》课程作业项目 · Django + SQLite

一个基于 Django 的足球信息管理系统，面向**普通球迷**与**足球经理**两类用户提供不同的功能：球迷可以关注球队 / 球员、查看比赛、玩"猜球员"小游戏并获得球队推荐；足球经理可以管理感兴趣的球员、申请执教球队、浏览与搜索全部球员并获得球员推荐。系统以数据库为核心，底层使用 Kaggle 公开的欧洲足球数据集（约 22 万条记录，核心表 18 万+ 行球员能力数据）。

---

## 项目来源与分工说明

本项目为大学二年级《数据库》课程作业项目，基于一个已有的初版进行修改完善后开源。

- **初版**：由课程小组共同完成。
- **修改与完善**：由 [@25jm0701-JZ](https://github.com/25jm0701-JZ) 在初版基础上完成，包括功能增强、页面与交互优化、数据库结构整理以及本项目文档编写。

> 如需更详细的个人分工说明，请联系作者。

---

## 功能一览

### 👤 普通球迷（User）

| 功能 | 说明 |
|---|---|
| 注册 / 登录 / 登出 | 独立的球迷身份体系 |
| 关注球队 | 按「联赛 → 球队」两级下拉选择并关注 |
| 关注球员 | 按「联赛 → 球队 → 球员」三级级联选择并关注 |
| 查看关注的球队 / 球员 | 展示关注列表及其**最新能力 / 战术快照** |
| 查看关注的比赛 | 展示关注球队参与的比赛，可按球队筛选 |
| 取消关注 | 一键取消对球队 / 球员的关注 |
| 球队推荐 | 以关注球队某战术属性的平均值为基准，推荐风格相近的其他球队 |
| 猜球员小游戏 | 根据给出的球员属性猜出球员姓名（3 选 1） |

### 🧑‍💼 足球经理（Manager）

| 功能 | 说明 |
|---|---|
| 注册 / 登录 / 登出 | 独立的经理身份体系 |
| 关注感兴趣的球员 | 加入 / 查看 / 删除兴趣名单（自动去重） |
| 申请执教球队 | 一个经理同一时间只能执教一支球队（1:1 约束） |
| 查看我的球队 | 展示球队信息、战术属性与全部球员名单 |
| 浏览全部球员 | 按联赛 / 球队筛选 + 关键字模糊搜索，分页展示（每页 50 条） |
| 查看球员详情 | 展示球员最新能力快照与全部技术 / 门将属性 |
| 球员推荐 | 以感兴趣球员某属性平均值为基准，推荐水平相近的球员（可一键加入兴趣名单） |

### 🌐 通用功能

- 中英双语界面（Django i18n，`zh-Hans` / `en` 即时切换）
- 基于 Bootstrap 5 + FontAwesome 的响应式页面
- 统一成功 / 错误提示页，表单错误提示
- 数据库共 **15 张表**，约 **22 万条**数据记录

---

## 技术栈

| 层次 | 技术 |
|---|---|
| 后端 | Python · Django 5.2 |
| 数据库 | SQLite（ORM 为 Django ORM，`managed=False` 直连既有数据库） |
| 前端 | Bootstrap 5.3 · FontAwesome 6（CDN）· Django 模板 |
| 国际化 | Django i18n（`locale/zh_Hans`） |

---

## 数据库设计

系统数据库共 **15 张表**，分为两组：

- **数据表**（来自 Kaggle 数据集，只读）：`country`、`league`、`team`、`player`、`match`、`team_attributes`、`player_attributes`
- **业务表**（系统自行维护）：`user`、`user_account`、`football_manager`、`manager_account`、`follow`、`subscribe`、`employ`、`interested`

关键设计：

- `player_attributes` / `team_attributes` 为**时间序列快照表**（同一实体多个日期记录），取 `date` 最新一条即当前能力 / 战术；
- `follow` / `subscribe` / `interested` 为**多对多关系表**，连接用户（球迷 / 经理）与数据实体；
- `employ` 以 `licence_id` 为主键，保证**一个经理只能执教一支球队**；
- `match` 以主队 / 客队两个外键关联 `team`。

| 表 | 行数 |
|---|---|
| player_attributes | 183,978 |
| match | 25,979 |
| player | 11,060 |
| team_attributes | 1,458 |
| team | 299 |
| league / country | 11 |

配套文档（均在本仓库中）：

- [schema.sql](schema.sql) —— 全部建表语句（DDL）与索引，含建议改进
- [queries.sql](queries.sql) —— 核心业务查询对应的等效 SQL（含注释）
- [ER图.html](ER图.html) —— 浏览器直接打开即可查看的实体关系图

---

## 数据库说明与获取（重要）

项目使用 SQLite 数据库 `soccer.db`（约 **300MB**），因超出 GitHub 单文件限制（100MB），**该文件不包含在本仓库中**。克隆后需要先获取数据库才能运行。

### 数据来源

原始球员 / 球队 / 比赛数据来自 Kaggle 公开数据集
[European Soccer Database（hugomathien/soccer）](https://www.kaggle.com/datasets/hugomathien/soccer/data)。

> 本项目并非直接使用该数据集，而是在其基础上进行了改造：
> - `team` 表新增 `league_id` 字段；
> - `player` 表新增 `team_api_id`、`league_id` 字段；
> - `match` 表的统计字段拆分为主队 / 客队两套（如 `shoton1` / `shoton2`）；
> - 新增 8 张业务表（`user`、`follow`、`subscribe`、`employ` 等）。
>
> 完整结构见 [schema.sql](schema.sql)。

### 获取 soccer.db（二选一）

**方式一（推荐）：直接使用现成的 soccer.db**

由于业务表与演示数据不在 Kaggle 数据集中，推荐**联系作者获取现成的 `soccer.db`**（已包含完整业务表与演示账号）。拿到后将文件放入**项目根目录**（与 `manage.py` 同级）即可。

**方式二：自行从 Kaggle 数据重建**

1. 在 [Kaggle 页面](https://www.kaggle.com/datasets/hugomathien/soccer/data) 下载数据集压缩包并解压；
2. 使用 SQLite 工具（如 `sqlite3`、DB Browser for SQLite）导入 `Country`、`League`、`Team`、`Player`、`Match`、`Team_Attributes`、`Player_Attributes` 数据；
3. 按 [schema.sql](schema.sql) 完成结构改造（见上文"数据来源"中的 4 点差异）；
4. 执行 [schema.sql](schema.sql) 中「第二部分：业务表」的建表语句，创建 `user` / `follow` / `subscribe` / `employ` / `interested` 等业务表。

---

## 本地运行

### 环境要求

- Python 3.10+
- 已获取 `soccer.db`（见上文「数据库说明与获取」）

### 启动步骤

```bash
# 1. 克隆仓库
git clone https://github.com/25jm0701-JZ/RealFootball-Management-System.git
cd RealFootball-Management-System

# 2. 安装依赖
pip install -r requirements.txt

# 3. 将获取到的 soccer.db 放到项目根目录（与 manage.py 同级）
#    Windows 示例：
#    copy /y 下载目录\soccer.db .

# 4. 启动服务
python manage.py runserver
```

浏览器访问 http://127.0.0.1:8000/ 即可打开首页。首次访问请先注册或登录。

> 提示：`soccer.db` 缺失时页面会报数据库错误，请先完成数据库获取步骤。

---

## 演示账号

数据库中预置的演示账号（密码请联系作者，或直接在 `/register/` 注册新账号）：

| 身份 | 用户名 |
|---|---|
| 普通球迷 | `fantest` |
| 足球经理 | `coach01` |

---

## 项目结构

```
RealFootball-Management-System/
├── manage.py                 # Django 入口
├── soccer_project/           # 项目配置（settings / urls）
├── soccer_app/               # 应用主代码
│   ├── models.py             # 数据模型（15 张表）
│   ├── views.py              # 全部视图逻辑
│   ├── urls.py               # 路由
│   ├── templates/            # 页面模板（base.html + 各功能页）
│   ├── templatetags/         # 模板过滤器
│   └── migrations/           # Django 迁移（managed=False）
├── locale/                   # 中英文翻译文件
├── schema.sql                # 建表 DDL + 索引
├── queries.sql               # 核心业务查询 SQL
└── ER图.html                 # 实体关系图
```

---

## 致谢

- 数据来源：[Kaggle · European Soccer Database](https://www.kaggle.com/datasets/hugomathien/soccer/data)（[hugomathien](https://www.kaggle.com/hugomathien)）
