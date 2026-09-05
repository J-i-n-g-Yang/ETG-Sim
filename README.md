# 🎰 ETG Sim

**ETG Sim** is a web-based Electronic Table Game simulator built with Python, Flask, JavaScript, and SQLite.

The project provides both:

- a **solo simulation environment** for testing and playing individual casino table games; and
- a **multiplayer event/table environment** with player balances, betting rounds, operator controls, projector views, persistent state, and settlement.

The simulator currently includes Baccarat, Blackjack, Poker, Roulette, Dice games, Dueling 8's 21+, Royal Three Pictures, and several game-specific variants.

Game logic is separated from the web interface and is covered by an automated unit and integration test suite.

---

# Features

## Solo Play

ETG Sim provides standalone interactive tables for supported games.

Depending on the game, the solo interfaces support features such as:

- multi-seat play;
- chip-based wagering;
- side wagers;
- player decisions;
- splitting;
- doubling;
- surrender;
- insurance;
- dealer / house play;
- shared community cards;
- settlement;
- payout breakdowns;
- round history;
- persistent local credit balances;
- game-specific betting layouts;
- casino-style card and table presentation.

Solo gameplay runs through Flask API endpoints, while the browser handles table presentation and player interaction.

## Multiplayer

The multiplayer portion of ETG Sim provides:

- player registration;
- persistent player credits;
- betting rounds;
- wager placement;
- operator controls;
- projector / display views;
- round settlement;
- leaderboard data;
- event multipliers;
- round history;
- server-sent event updates;
- SQLite persistence.

## Operator and Display Interfaces

The application includes dedicated routes for:

- the main portal;
- multiplayer lobby;
- player table;
- operator controls;
- projector display;
- individual solo games.

---

# Supported Games

## Baccarat

Implemented Baccarat variants include:

- Dragon Tiger No Commission Baccarat
- Immortal Dragon Tiger No Commission Baccarat
- Rising Dragon Tiger No Commission Baccarat

The Baccarat frontend includes casino-style result tracking / road presentation in addition to the normal betting and settlement interface.

---

## Blackjack

Implemented Blackjack variants include:

- Blackjack Lucky 8
- Free Bet Blackjack
- King's Bounty Blackjack
- Pontoon

The Blackjack implementation supports variant-specific functionality including:

- Hit
- Stand
- Double
- Split
- Surrender
- Insurance
- Even Money
- Free Double
- Free Split
- Pontoon Double Rescue
- variant-specific side bets
- multi-seat play

The exact actions available depend on the selected variant and current hand state.

---

## Dueling 8's 21+

Dueling 8's 21+ is implemented as a dedicated three-seat interactive game.

Features include:

- permanent Player and Dealer 8♠;
- up to three active seats;
- Hit;
- Stand;
- partial Double;
- Split 8s;
- Surrender;
- 6-7-8 bonus;
- Superb 8s;
- Tie on 18;
- 21+;
- per-seat side wager settlement.

---

## Royal Three Pictures

Royal Three Pictures includes:

- three active player seats;
- one shared dealer hand;
- Main wagers;
- Tie wagers;
- Royal Pictures wagers;
- picture-hand evaluation;
- game-specific point comparison and settlement.

---

## Poker

Implemented Poker variants include:

- Three Card Poker Xtreme
- Singapore Stud Poker
- Texas Hold'em Bonus
- Ultimate Texas Hold'em
- Mississippi Stud Poker
- Fortune Pai Gow Poker

Depending on the game, the Poker system supports:

- Ante wagers;
- Blind wagers;
- Play wagers;
- side wagers;
- multi-stage betting;
- community cards;
- viewed and blind seats;
- dealer qualification;
- fold/check/play decisions;
- Mississippi Stud street betting;
- Ultimate Texas Hold'em staged Play wagers;
- Fortune Pai Gow manual hand setting;
- Fortune Pai Gow House Way;
- Pai Gow Joker handling;
- variant-specific settlement and bonuses.

Some progressive jackpot functionality is intentionally unavailable where the corresponding progressive system is not implemented.

---

## Dice Games

Implemented dice games include:

- Sic Bo
- Craps
- Great Fortune Dice

These games use dedicated game engines and casino-style betting boards.

Craps additionally maintains persistent round/table state where required by its wager lifecycle.

---

## Roulette

Implemented Roulette variants include:

- Single Zero Roulette
- Double Zero Roulette
- Sands Roulette

The Roulette system supports standard inside and outside wagers along with variant-specific rules.

---

# Architecture

ETG Sim is organized into several major layers:

```text
ETG_Sim/
├── api/
│   ├── control.py
│   ├── routes.py
│   └── solo.py
│
├── db/
│   ├── pool.py
│   └── queries.py
│
├── engine/
│   ├── session.py
│   └── settlement.py
│
├── game/
│   ├── baccarat_*.py
│   ├── blackjack_*.py
│   ├── craps*.py
│   ├── dice_*.py
│   ├── dueling_8s_21.py
│   ├── poker_*.py
│   ├── pontoon.py
│   ├── roulette_*.py
│   ├── royal_three_pictures.py
│   ├── sicbo.py
│   └── registry.py
│
├── static/
│   ├── css/
│   └── js/
│
├── templates/
│
├── tests/
│
├── data/
│
├── app.py
├── config.py
├── schema.sql
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
└── .env.example
```

---

# Application Layers

## `game/`

Contains game-specific rules, hand evaluation, wager validation, payout logic, dealer logic, and game engines.

Game logic is kept separate from the frontend wherever practical so it can be tested independently.

## `api/`

Contains Flask API endpoints.

Important modules include:

- `api/routes.py` — multiplayer API and event state;
- `api/control.py` — operator/control endpoints;
- `api/solo.py` — solo-game endpoints and interactive game flows.

## `engine/`

Contains higher-level multiplayer session and settlement functionality.

## `db/`

Contains SQLite connection and query logic.

`db/pool.py` provides thread-local SQLite connections.

`db/queries.py` contains schema bootstrap and persistence operations for:

- players;
- rounds;
- bets;
- balances;
- leaderboards;
- history.

## `templates/`

Contains Flask/Jinja HTML templates for the portal, game tables, operator controls, projector, and solo interfaces.

## `static/js/`

Contains browser-side controllers and shared board/rendering functionality.

## `tests/`

Contains unit and integration tests covering game rules, payout logic, API flows, settlement, and interactive game behaviour.

---

# Technology Stack

## Backend

- Python
- Flask
- Waitress
- SQLite
- python-dotenv

## Frontend

- HTML
- CSS
- JavaScript
- Jinja templates

## Deployment

- Docker
- Docker Compose
- Waitress WSGI server

## Continuous Integration

- GitHub Actions

---

# Requirements

For local Python development:

- Python 3.12 or later
- `pip`
- virtual environment support

The current Docker production environment uses:

```text
Python 3.12
```

The project is also actively developed/tested locally with newer Python versions.

For containerized execution:

- Docker
- Docker Compose

---

# Python Dependencies

The project uses pinned direct dependencies:

```text
Flask==3.1.3
waitress==3.0.2
python-dotenv==1.2.3
```

Install them with:

```bash
python -m pip install -r requirements.txt
```

---

# Local Development Setup

## 1. Clone the repository

```bash
git clone <repository-url>
cd ETG_Sim
```

## 2. Create a virtual environment

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Create your environment file

Copy the example:

```bash
cp .env.example .env
```

Then edit `.env` for the local environment.

Do **not** commit `.env`.

---

# Environment Variables

ETG Sim supports the following configuration values:

| Variable | Purpose | Development default |
|---|---|---:|
| `DB_PATH` | SQLite database location | `data/etg_sim.db` |
| `EVENT_CODE` | Multiplayer event code | `TOWNHALL2026` |
| `CONTROL_PIN` | Operator/control PIN | `1234` |
| `STARTING_CREDITS` | Initial player/solo credits | `100000` |
| `BETTING_SECONDS` | Multiplayer betting period | `35` |
| `MAX_BET` | Maximum wager/stake configuration | `20000` |
| `SECRET_KEY` | Flask secret key | Development-only fallback |

A development `.env.example` may look like:

```dotenv
DB_PATH=data/etg_sim.db

EVENT_CODE=TOWNHALL2026
CONTROL_PIN=change_me

STARTING_CREDITS=100000
BETTING_SECONDS=35
MAX_BET=20000

SECRET_KEY=change_me_to_a_long_random_secret
```

For production deployments, replace `CONTROL_PIN` and `SECRET_KEY` with secure values.

Generate a suitable random secret with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Never commit production secrets to Git.

---

# Database

ETG Sim uses SQLite.

The default local database path is:

```text
data/etg_sim.db
```

The database file is **runtime data** and is not intended to be committed to Git.

## Automatic Bootstrap

The application automatically initializes its required schema when it starts.

`create_app()` invokes the database bootstrap logic, which creates the required tables and indexes when they do not already exist.

A completely empty installation therefore does not require a pre-existing `.db` file.

Current tables include:

```text
townhall_players
townhall_rounds
townhall_bets
```

Current application indexes include:

```text
IX_bets_round
IX_bets_user
UX_bets_uid
```

The database directory and SQLite file are created automatically when necessary.

---

# Running Locally

With the virtual environment activated and configuration prepared, the application can be started using Waitress:

```bash
waitress-serve --listen=0.0.0.0:8060 app:app
```

Then open:

```text
http://localhost:8060
```

---

# Main Routes

Common browser routes include:

| Route | Purpose |
|---|---|
| `/` | ETG Sim portal |
| `/multiplayer` | Multiplayer lobby |
| `/play` | Multiplayer player table |
| `/projector` | Projector/display interface |
| `/control` | Operator controls |
| `/games/<game>` | Supported solo game pages |
| `/games/blackjack/<variant>` | Blackjack variants |

Additional variant-specific pages and API routes are registered through the Flask blueprints.

---

# API Structure

The application registers three major API blueprints:

```text
/api
/api/control
/api/solo
```

These separate multiplayer state, operator functionality, and solo-game functionality.

For example, the application health/state endpoint is available at:

```text
GET /api/state
```

Solo interactive games use endpoints under:

```text
/api/solo/
```

---

# Running Tests

Run the complete test suite from the project root:

```bash
python -m unittest discover -s tests
```

For verbose output:

```bash
python -m unittest discover -s tests -v
```

At the current deployment baseline:

```text
Ran 418 tests

OK
```

The suite includes both unit and integration coverage.

Examples include:

- Baccarat rules and settlement;
- Blackjack API flow;
- Blackjack Lucky 8;
- Free Bet Blackjack;
- King's Bounty Blackjack;
- Pontoon;
- Sic Bo;
- Craps;
- Great Fortune Dice;
- Roulette variants;
- Dueling 8's 21+;
- Royal Three Pictures;
- Three Card Poker Xtreme;
- Singapore Stud Poker;
- Texas Hold'em Bonus;
- Ultimate Texas Hold'em;
- Mississippi Stud Poker;
- Fortune Pai Gow Poker;
- Pai Gow House Way;
- Pai Gow Joker behaviour;
- Pai Gow settlement;
- multi-seat integration flows.

---

# Running Individual Tests

A specific test module can be run with:

```bash
python -m unittest tests.test_dueling_8s_integration -v
```

For example:

```bash
python -m unittest tests.test_royal_three_pictures_integration -v
```

or:

```bash
python -m unittest tests.test_poker_integration -v
```

---

# Docker

ETG Sim includes a production-oriented Docker configuration.

## Build

```bash
docker compose build
```

For a completely fresh build:

```bash
docker compose build --no-cache
```

## Start

```bash
docker compose up -d
```

## Check status

```bash
docker compose ps
```

A healthy deployment should report the simulator as:

```text
healthy
```

## View logs

```bash
docker compose logs -f simulator
```

or:

```bash
docker compose logs --tail=100 simulator
```

## Stop

```bash
docker compose down
```

The persistent database volume is retained by a normal `docker compose down`.

---

# Docker Database Persistence

Docker Compose mounts:

```text
/app/data
```

to a named Docker volume.

The container uses:

```text
DB_PATH=/app/data/etg_sim.db
```

This means the SQLite database survives normal container replacement and image rebuilds.

A normal:

```bash
docker compose down
```

does **not** remove the database volume.

Be careful with:

```bash
docker compose down -v
```

because `-v` removes the named volume and therefore deletes the containerized SQLite database.

---

# Production Server

The Docker image serves Flask through Waitress rather than Flask's development server.

The container currently listens on:

```text
0.0.0.0:8060
```

and exposes:

```text
8060
```

The application is started with the Waitress WSGI entry point:

```text
app:app
```

---

# Docker Health Check

The Docker image includes a health check against:

```text
http://127.0.0.1:8060/api/state
```

The container is considered healthy only when the application responds successfully.

A working deployment can also be checked manually:

```bash
curl -i http://localhost:8060/api/state
```

A successful response should return:

```text
HTTP/1.1 200 OK
```

The portal can similarly be checked with:

```bash
curl -I http://localhost:8060/
```

---

# Continuous Integration

ETG Sim uses GitHub Actions.

The CI workflow is stored at:

```text
.github/workflows/tests.yml
```

CI runs on pushes and pull requests targeting `main`.

It currently performs two independent checks.

## Python Tests

GitHub:

1. checks out the repository;
2. installs Python 3.12;
3. installs `requirements.txt`;
4. creates a temporary test database;
5. runs the complete unit and integration suite.

The test command is:

```bash
python -m unittest discover -s tests -v
```

## Docker Build

GitHub independently verifies that the production Docker image builds successfully:

```bash
docker build -t etg-sim:test .
```

A change is therefore checked against both:

```text
                  Push / Pull Request
                           │
               ┌───────────┴───────────┐
               │                       │
               ▼                       ▼
       Python 3.12 Tests          Docker Build
               │                       │
         Unit + Integration       Production Image
               │                       │
               └───────────┬───────────┘
                           │
                           ▼
                         PASS
```

---

# Deployment Verification

Before deploying a new release, the recommended verification sequence is:

```bash
python -m unittest discover -s tests
```

Then:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose ps
```

Check logs:

```bash
docker compose logs --tail=100 simulator
```

Check application state:

```bash
curl -i http://localhost:8060/api/state
```

Check the portal:

```bash
curl -I http://localhost:8060/
```

Finally, manually verify representative game pages in the browser.

---

# Static Asset Cache Busting

ETG Sim generates a static version identifier when the application starts:

```python
app.jinja_env.globals["static_v"] = int(time.time())
```

Templates can append this value to JavaScript/static asset URLs so browsers load the current frontend after a server restart.

HTML responses are also configured with no-cache headers.

---

# Security Notes

## Never commit `.env`

The following should remain private:

- production `SECRET_KEY`;
- production `CONTROL_PIN`;
- any future credentials or API secrets.

`.env` is intentionally excluded by `.gitignore` and `.dockerignore`.

## Production secrets

Production values should be configured through the deployment platform's secret/environment-variable system rather than stored in source control.

## SQLite files

Runtime SQLite files are excluded from Git:

```gitignore
data/*.db*
```

This includes database files, WAL/SHM files, and local database backups.

---

# Git Hygiene

Generated files should not be committed.

Examples include:

```text
venv/
.venv/
__pycache__/
*.pyc
.DS_Store
.env
*.log
.pytest_cache/
.coverage
htmlcov/
data/*.db*
```

Git should contain source code and configuration templates, not local runtime state.

---

# Game Rule References

The project may contain a `GameRules/` directory containing game-rule reference documents used during implementation and verification.

These documents are reference material rather than runtime application dependencies.

Whether they are included in a public repository should be determined separately based on redistribution rights and repository-size considerations.

The simulator itself does not require the PDFs to execute.

---

# Development Principles

The project follows several practical principles.

## Backend-authoritative settlement

Game results and payouts should be determined by backend game logic rather than trusted from browser state.

## Game logic separated from presentation

Game engines are kept separate from table rendering so rules can be tested independently.

## Deterministic integration testing

Where appropriate, integration tests patch shoes/decks/dice outcomes to verify exact API and settlement behaviour.

## Multi-seat isolation

Seat-specific wagers and outcomes are kept isolated so one player's side wagers or hand state cannot accidentally affect another seat.

## Fresh-deployment bootstrap

A deployment should not require copying a developer's local database.

The application must be able to initialize itself from source and environment configuration.

## Reproducible deployment

Python dependencies are pinned and the Docker image defines the production Python environment.

---

# Recommended Development Workflow

Before beginning work:

```bash
git pull
```

Create a branch:

```bash
git checkout -b feature/my-change
```

Make changes and run:

```bash
python -m unittest discover -s tests
```

For deployment-sensitive changes, also run:

```bash
docker compose build
```

Commit:

```bash
git add .
git commit -m "Describe the change"
```

Push:

```bash
git push -u origin feature/my-change
```

Then open a pull request into `main`.

GitHub Actions will automatically run the test suite and Docker build.

---

# Current Validation Baseline

The current release-preparation baseline has been verified with:

```text
Python unit/integration tests: 418 passing
Fresh SQLite bootstrap:        PASS
Fresh Docker build:            PASS
Docker health check:           PASS
/api/state:                    HTTP 200
Portal:                        HTTP 200
```

Production Docker uses Python 3.12 and Waitress.

---

# Pre-Release Checklist

Before publishing or deploying a new version:

- [ ] Full unit/integration suite passes
- [ ] No `.env` file is staged
- [ ] No SQLite database is staged
- [ ] No `__pycache__` files are staged
- [ ] No `.DS_Store` files are staged
- [ ] Dependencies are intentional and pinned
- [ ] Fresh Docker image builds
- [ ] Docker container becomes healthy
- [ ] `/api/state` returns HTTP 200
- [ ] Portal returns HTTP 200
- [ ] Representative solo games load
- [ ] Multiplayer interface loads
- [ ] Operator interface loads
- [ ] Projector interface loads
- [ ] GitHub Actions passes

---

# Project Status

ETG Sim is currently in active development.

The current deployment-preparation baseline includes:

- a working Flask application factory;
- SQLite automatic database bootstrap;
- persistent Docker storage;
- Waitress production serving;
- Docker health checks;
- pinned Python dependencies;
- automated unit and integration testing;
- GitHub Actions CI;
- multiple completed ETG game families;
- standardized card-game frontend layouts.

Future changes should preserve the automated regression baseline and add tests for new game rules or API behaviour.

---

# Disclaimer

ETG Sim is a **simulation and software-development project**.

It does not process real-money wagers and should not be treated as a certified gaming system.

Game implementations are intended to reproduce the rules represented by the project's reference material, but production or regulated gaming use would require independent verification, certification, security review, and any applicable regulatory approvals.

---

# License

No license has been specified yet.

Before making the repository public, choose an appropriate software license or explicitly keep the repository private/proprietary.

Third-party game-rule documents and other reference materials, if retained in the repository, may have separate ownership and redistribution terms and are not automatically covered by the software's license.