# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Always invoke the venv interpreter by path. Shell activation does not persist between tool calls, and the system `python` here is a sandboxed Microsoft Store build that silently redirects `pip install` to global user site-packages instead of failing — a bare `pip install -r requirements.txt` will appear to succeed while polluting the global environment and downgrading its packages.

```bash
venv/Scripts/python.exe app.py                          # dev server → http://127.0.0.1:5001
venv/Scripts/python.exe -m pip install -r requirements.txt
venv/Scripts/python.exe -m pytest                       # full suite
venv/Scripts/python.exe -m pytest tests/test_auth.py::test_login_success   # single test
venv/Scripts/python.exe -m pytest -k "expense" -v       # by name pattern
```

The app runs on **port 5001**, not Flask's default 5000 (`app.py:55`). `debug=True` is hardcoded there, so the reloader is always on — a second `app.py` process will fail with a port conflict rather than picking another port.

The SQLite file is `expense_tracker.db` at the repo root and is gitignored — it is a disposable local artifact, safe to delete and rebuild via `init_db()` / `seed_db()`.

## Architecture

**This is a teaching scaffold, not a finished app.** Roughly half the codebase is deliberate stubs annotated with numbered course steps: `database/db.py` is "Step 1 — Database Setup", and `app.py:26-51` marks five routes as student work for Steps 3, 4, 7, 8, and 9. Treat those placeholders as the assignment, not as bugs. Implement the step you are asked for; do not bulk-fill the remaining stubs as a side effect.

Only three routes are live (`/`, `/register`, `/login` — all render-only). The other five return plain strings.

**Flat single-module Flask.** `Flask(__name__)` is instantiated at module scope in `app.py:3` and every route attaches to it directly. There is no application factory, no blueprints, and no config module. Nothing currently imports `database/`, so wiring the data layer in is part of Step 1.

**Data layer contract.** `database/db.py:1-6` specifies the interface to build: `get_db()` returning a `sqlite3` connection with `row_factory` set and foreign keys enabled, `init_db()` using `CREATE TABLE IF NOT EXISTS`, and `seed_db()` for dev data. Raw `sqlite3` from the stdlib — no ORM, and none is pinned. Keep query code inside this package rather than in route handlers; the package exists specifically to hold that separation.

**Templates: one level of Jinja2 inheritance.** `base.html` is the only parent and owns the entire chrome — font links, navbar, `<main>`, footer, and the `main.js` tag. It exposes `title`, `head`, `content`, and `scripts`; children override only `title` and `content`. New pages should extend it and add markup through those blocks rather than repeating the shell. Internal links use `url_for()`, so route function renames propagate — but form `action` attributes are currently hardcoded (`login.html:20`, `register.html:20`) and will not.

**CSS is a token system, not ad-hoc styles.** `static/css/style.css` opens with a `:root` block of ~20 custom properties and follows with twelve labeled sections. Style new UI by reusing the existing vocabulary — `--ink` / `--ink-soft` / `--ink-muted` / `--ink-faint` for text, `--paper` / `--paper-warm` / `--paper-card` for surfaces, `--accent` (`#1a472a`) plus `--accent-light`, `--danger` / `--danger-light`, and the `--font-*`, `--radius-*`, `--max-width` / `--auth-width` tokens. Hardcoding hex values or fonts breaks visual consistency with the existing pages. There is no build step or preprocessor; edit the file directly.

Amounts are Indian rupees (₹) throughout the markup and copy. The product is branded **Spendly**.

## Current blocking gaps

Beyond the intentional step stubs, these will bite immediately:

- **Auth forms return 405.** Both templates POST, but `app.py:15` and `app.py:20` declare no `methods=`, making the routes GET-only. They need `methods=["GET", "POST"]` before any form submission works.
- **No `SECRET_KEY` and no `app.config` setup**, so sessions are unavailable — this blocks login/logout (Step 3) until added.
- **No `tests/` directory and no `conftest.py`.** `pytest-flask` is pinned but needs an `app` fixture supplied in `conftest.py`; `pytest` currently collects 0 items.
- Both auth templates render `{{ error }}` (`login.html:16`, `register.html:16`), which no route passes yet. Harmless under Jinja2's falsy-undefined, and it documents the intended POST-handler contract.

## Conventions

Dependencies in `requirements.txt` are pinned to exact versions (`==`). Keep that style when adding any.

`app.py` uses full-width `# ---- #` banner comments to separate route groups, and `style.css` uses the matching `/* ---- */` form for its sections. Match the surrounding convention when extending either file.
