"""Test fixtures for Spendly.

The important detail: app.py calls init_db()/seed_db() at import time, so the
database has to be repointed at a temp file *before* `import app` runs. get_db()
reads database.db.DB_PATH at call time, so reassigning that module global is
enough — even though app.py used `from database.db import ...`.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def app(tmp_path):
    import database.db as db

    db.DB_PATH = tmp_path / "test.db"

    # First test triggers app.py's startup wiring against the temp DB; later
    # tests reuse the cached module, so seed explicitly to keep every test
    # starting from the same state (Demo User + 8 expenses).
    import app as app_module

    db.init_db()
    db.seed_db()

    app_module.app.config.update(TESTING=True)
    return app_module.app


@pytest.fixture
def client(app):
    return app.test_client()
