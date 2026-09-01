# Spec: Registration

## Overview

Turn `/register` from a render-only page into the app's first write path. The template
at `templates/register.html` already POSTs name, email and password, but `app.py:15`
declares no `methods=`, so every submission returns 405. This step adds POST handling:
server-side validation, a werkzeug password hash, an insert into `users`, and a redirect
to `/login` on success — re-rendering the form with `{{ error }}` on failure. It sits
between Step 1 (data layer) and Step 3 (sessions), so registration deliberately does
**not** log the new user in: `session` and `flash()` both need a `SECRET_KEY` that does
not exist yet.

## Depends on

- **Step 1 — Database Setup: NOT COMPLETE.** `database/db.py` is still the 6-line stub
  on this branch *and* on `origin/main`, and nothing imports `database/`. The `users`
  table and `get_db()` must exist before any of this runs. Implement `01-database-setup.md`
  first, or this step has nothing to insert into.
- **`app.py:1` is a syntax error.** The committed first line is
  `!ddfrom flask import Flask, render_template`. The app cannot start at all until the
  stray `!dd` is removed. Fixed as part of this step (see *Files to change*).
- No dependency on Step 3. Do not add session handling here.

## Routes

- `GET /register` — render the registration form — public
- `POST /register` — validate input, create the user, redirect to `/login` — public

No new URL paths. `@app.route("/register")` gains `methods=["GET", "POST"]`; the existing
function keeps the name `register` so `url_for('register')` in `base.html:23` and
`login.html:39` keeps resolving.

## Database changes

No database changes. Uses the `users` table exactly as specified in
`.claude/specs/01-database-setup.md` — `id`, `name`, `email` (UNIQUE NOT NULL),
`password_hash`, `created_at`. Verified against `database/db.py`: the file is a stub, so
the table does not exist yet and is created by Step 1's `init_db()`, not by this step.
Duplicate-email detection relies on that UNIQUE constraint plus a pre-check lookup.

## Templates

- **Create:** none.
- **Modify:** `templates/register.html`
  - Line 20: replace the hardcoded `action="/register"` with `action="{{ url_for('register') }}"`.
  - Repopulate `name` and `email` on an error re-render (`value="{{ name or '' }}"`,
    `value="{{ email or '' }}"`); never repopulate the password field.
  - Add `minlength="8"` to the password input so the browser matches the server rule
    already promised by the "Min. 8 characters" placeholder.
  - The `{% if error %}` block at lines 16–18 and the `.auth-error` class it uses
    (`style.css:413`) already exist — no new markup or CSS needed.

## Files to change

- `app.py`
  - Remove the `!dd` prefix on line 1; import `redirect`, `request`, `url_for` alongside
    `Flask` and `render_template`.
  - Import the data-layer helpers from `database.db`.
  - Add `methods=["GET", "POST"]` to the `/register` route and implement the POST branch.
  - Keep the existing `# ---- #` banner comment layout; leave the Step 3/4/7/8/9 stubs
    returning their placeholder strings.
- `database/db.py`
  - Add `get_user_by_email(email)` and `create_user(name, email, password_hash)`
    alongside the Step 1 functions. All SQL for this feature lives here, not in the route.
- `templates/register.html` — as above.

## Files to create

None. (No `tests/` or `conftest.py` in this step — `pytest-flask` still has no `app`
fixture, so the checklist below is verified by running the app.)

## New dependencies

No new dependencies. `flask==3.1.3` and `werkzeug==3.1.6` are already pinned in
`requirements.txt`; `sqlite3` is stdlib.

## Rules for implementation

- **No SQLAlchemy or ORMs.** Raw `sqlite3` from the standard library only.
- **Parameterised queries only.** `?` placeholders — never f-strings, `%`, `.format()`,
  or string concatenation in SQL.
- **Passwords hashed with werkzeug.** `generate_password_hash` from `werkzeug.security`.
  Never store, print, or log the plaintext password.
- **Use CSS variables — never hardcode hex values.** Reuse `--ink*`, `--paper*`,
  `--accent*`, `--danger*`, `--radius-*` and the existing `.auth-*` / `.form-*` classes.
- **All templates extend `base.html`.**
- Keep query code inside `database/` — route handlers call helpers, they do not open
  cursors (CLAUDE.md architecture rule).
- No `session[...]`, no `flash()`, no auto-login. Both need a `SECRET_KEY`, which Step 3 adds.
- Do not implement the other stub routes as a side effect.
- Validation, server-side, in this order: `name` non-empty after `.strip()`; `email`
  non-empty and containing `@`; `password` at least 8 characters. Store the email
  `.strip().lower()`.
- Duplicate email → a friendly message such as "An account with that email already
  exists."; also wrap the insert in a `try/except sqlite3.IntegrityError` so a race
  cannot 500.
- On any validation failure, re-render `register.html` with `error`, `name` and `email` —
  do not redirect and do not lose the user's input.
- On success, `return redirect(url_for("login"))`.
- If you add a dependency anyway, pin it with `==`.

## Definition of done

- [ ] `venv/Scripts/python.exe app.py` starts with no `SyntaxError` and serves
      http://127.0.0.1:5001/register
- [ ] `POST /register` no longer returns 405
- [ ] Submitting valid details redirects to `/login` and creates exactly one `users` row
- [ ] `venv/Scripts/python.exe -c "import sqlite3;print(sqlite3.connect('expense_tracker.db').execute('select email,password_hash from users').fetchall())"`
      shows a `pbkdf2:`/`scrypt:` hash — the plaintext password appears nowhere in the DB
- [ ] Submitting the same email twice shows the duplicate-email error and leaves the row count at one
- [ ] A 7-character password is rejected by the server, not just the browser —
      verify with `curl.exe -i -X POST http://127.0.0.1:5001/register -d "name=A&email=a@b.com&password=short"`
- [ ] Blank name and malformed email each render a visible `.auth-error` message
- [ ] After an error, name and email are still filled in and the password box is empty
- [ ] The page still shows the `base.html` navbar and footer; no hex colours were added
- [ ] `/logout`, `/profile`, `/expenses/*` still return their Step 3/4/7/8/9 placeholder strings
