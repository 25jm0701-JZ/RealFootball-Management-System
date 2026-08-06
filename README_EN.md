# RealFootball Football Management System

> Sophomore-year *Database* course assignment · Django + SQLite

A Django-based football information management system serving two types of users — **football fans** and **football managers**. Fans can follow teams/players, view matches, play a "Guess the Player" mini-game, and get team recommendations; managers can manage a shortlist of players they are interested in, apply to coach a club, browse and search all players, and receive player recommendations. The system is database-centric, built on the public Kaggle European Soccer dataset (≈220,000 records; the core table holds 180,000+ player attribute rows).

---

## Project Origin & Contribution

This project is a sophomore-year *Database* course assignment, released open-source after being refined from an existing initial version.

- **Initial version**: completed by the course group together.
- **Modifications & refinements**: done by [@25jm0701-JZ](https://github.com/25jm0701-JZ) on top of the initial version, including feature enhancements, UI/interaction improvements, database structure reorganization, and this documentation.

> Contact the author for a more detailed breakdown of individual contributions.

---

## Features

### 👤 Regular Fan (User)

| Feature | Description |
|---|---|
| Register / Login / Logout | Dedicated fan identity system |
| Follow a team | Two-level cascade selection: "League → Team" |
| Follow a player | Three-level cascade selection: "League → Team → Player" |
| View followed teams / players | Shows the follow list with each item's **latest attribute/tactic snapshot** |
| View followed matches | Shows matches involving followed teams, filterable by team |
| Unfollow | One-click unfollow for teams / players |
| Team recommendation | Recommends stylistically similar teams based on the average value of a tactic attribute of the teams you follow |
| Guess-the-Player mini-game | Guess a player's name from their attributes (3 choices) |

### 🧑‍💼 Football Manager

| Feature | Description |
|---|---|
| Register / Login / Logout | Dedicated manager identity system |
| Shortlist interested players | Add / view / remove players from an interest list (auto-dedup) |
| Apply to coach a club | A manager can only coach one club at a time (1:1 constraint) |
| View my club | Shows club info, tactic attributes, and full player roster |
| Browse all players | Filter by league/team + fuzzy keyword search, paginated (50 per page) |
| View player details | Shows the player's latest attribute snapshot and all technical / goalkeeper attributes |
| Player recommendation | Recommends players of similar level based on the average attribute value of your shortlisted players (one-click add to shortlist) |

### 🌐 General

- Bilingual UI (Django i18n, `zh-Hans` / `en`, switchable on the fly)
- Responsive pages built with Bootstrap 5 + FontAwesome
- Unified success / error pages and form validation messages
- **15 tables**, ≈**220,000** data records

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python · Django 5.2 |
| Database | SQLite (Django ORM, `managed=False` — connects to an existing database) |
| Frontend | Bootstrap 5.3 · FontAwesome 6 (CDN) · Django templates |
| i18n | Django i18n (`locale/zh_Hans`) |

---

## Database Design

The database contains **15 tables** in two groups:

- **Data tables** (from the Kaggle dataset, read-only): `country`, `league`, `team`, `player`, `match`, `team_attributes`, `player_attributes`
- **Business tables** (maintained by the system): `user`, `user_account`, `football_manager`, `manager_account`, `follow`, `subscribe`, `employ`, `interested`

Key design points:

- `player_attributes` / `team_attributes` are **time-series snapshot tables** (multiple dated records per entity); the record with the latest `date` represents the current attributes / tactics;
- `follow` / `subscribe` / `interested` are **many-to-many relationship tables** linking users (fans / managers) to data entities;
- `employ` uses `licence_id` as its primary key, enforcing **one manager coaches one club**;
- `match` links to `team` through two foreign keys (home and away).

| Table | Rows |
|---|---|
| player_attributes | 183,978 |
| match | 25,979 |
| player | 11,060 |
| team_attributes | 1,458 |
| team | 299 |
| league / country | 11 |

Supporting documents (all in this repository):

- [schema.sql](schema.sql) — full DDL (all tables & indexes), with suggested improvements
- [queries.sql](queries.sql) — the equivalent SQL for the core business queries (commented)
- [ER图.html](ER图.html) — entity-relationship diagram, open directly in a browser

---

## Database: Source & How to Get It (Important)

The project uses a SQLite database `soccer.db` (≈**300 MB**). Because it exceeds GitHub's single-file limit (100 MB), **it is not included in this repository**. You must obtain the database before running the app.

### Data source

The raw player / team / match data comes from the public Kaggle dataset
[European Soccer Database (hugomathien/soccer)](https://www.kaggle.com/datasets/hugomathien/soccer/data).

> Note: this project does not use the dataset as-is; it was modified:
> - `team` gained a `league_id` column;
> - `player` gained `team_api_id` and `league_id` columns;
> - `match` statistic columns were split into home / away pairs (e.g. `shoton1` / `shoton2`);
> - 8 business tables were added (`user`, `follow`, `subscribe`, `employ`, etc.).
>
> Full schema: [schema.sql](schema.sql).

### Getting soccer.db (Option 1 or 2)

**Option 1 (recommended): use the ready-made soccer.db**

The business tables and demo data are not in the Kaggle dataset, so **contact the author for the ready-made `soccer.db`** (it already contains the business tables and demo accounts). Place the file in the **project root** (next to `manage.py`).

**Option 2: rebuild it yourself from the Kaggle data**

1. Download and extract the dataset from the [Kaggle page](https://www.kaggle.com/datasets/hugomathien/soccer/data);
2. Use a SQLite tool (e.g. `sqlite3`, DB Browser for SQLite) to import `Country`, `League`, `Team`, `Player`, `Match`, `Team_Attributes`, `Player_Attributes`;
3. Apply the schema changes described above following [schema.sql](schema.sql);
4. Run the "Business tables" DDL in [schema.sql](schema.sql) to create `user` / `follow` / `subscribe` / `employ` / `interested`, etc.

---

## Running Locally

### Requirements

- Python 3.10+
- A copy of `soccer.db` (see "Database: Source & How to Get It" above)

### Steps

```bash
# 1. Clone
git clone https://github.com/25jm0701-JZ/RealFootball-Management-System.git
cd RealFootball-Management-System

# 2. Install dependencies
pip install -r requirements.txt

# 3. Put soccer.db in the project root (next to manage.py)

# 4. Run
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser. Register or log in on first visit.

> Note: the app reports database errors if `soccer.db` is missing — complete the database step first.

---

## Demo Accounts

Pre-seeded demo accounts in the database (ask the author for passwords, or register a new account at `/register/`):

| Identity | Username |
|---|---|
| Regular fan | `fantest` |
| Football manager | `coach01` |

---

## Project Structure

```
RealFootball-Management-System/
├── manage.py                 # Django entry point
├── soccer_project/           # Project settings (settings / urls)
├── soccer_app/               # Main application
│   ├── models.py             # Data models (15 tables)
│   ├── views.py              # All view logic
│   ├── urls.py               # URL routing
│   ├── templates/            # Page templates (base.html + feature pages)
│   ├── templatetags/         # Template filters
│   └── migrations/           # Django migrations (managed=False)
├── locale/                   # Translation files
├── schema.sql                # DDL + indexes
├── queries.sql               # Core business query SQL
└── ER图.html                 # Entity-relationship diagram
```

---

## Credits

- Data source: [Kaggle · European Soccer Database](https://www.kaggle.com/datasets/hugomathien/soccer/data) by [hugomathien](https://www.kaggle.com/hugomathien)
