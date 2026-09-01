"""Step 02 — Registration.

Every test starts from a temp database holding the seeded Demo User, so counts
are asserted per email rather than as table totals.
"""

from werkzeug.security import check_password_hash

from database.db import get_db, get_user_by_email

VALID = {
    "name": "Asha Menon",
    "email": "asha.menon@example.com",
    "password": "password123",
}


def count_users(email):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM users WHERE email = ?", (email,)
        ).fetchone()[0]
    finally:
        conn.close()


def test_get_register_renders(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Create your account" in response.data


def test_post_is_no_longer_405(client):
    response = client.post("/register", data=VALID)
    assert response.status_code != 405


def test_valid_post_creates_user_and_redirects(client):
    response = client.post("/register", data=VALID)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    row = get_user_by_email(VALID["email"])
    assert row is not None
    assert row["name"] == "Asha Menon"
    assert row["password_hash"] != VALID["password"]
    assert check_password_hash(row["password_hash"], VALID["password"])
    assert count_users(VALID["email"]) == 1


def test_duplicate_email_rejected(client):
    client.post("/register", data=VALID)
    response = client.post("/register", data=dict(VALID, name="Someone Else"))

    assert response.status_code == 400
    assert b"already exists" in response.data
    assert count_users(VALID["email"]) == 1


def test_seeded_email_is_also_a_duplicate(client):
    response = client.post(
        "/register",
        data={"name": "Impostor", "email": "demo@spendly.com", "password": "password123"},
    )

    assert response.status_code == 400
    assert b"already exists" in response.data
    assert count_users("demo@spendly.com") == 1


def test_short_password_rejected(client):
    response = client.post(
        "/register",
        data={"name": "Short Pass", "email": "short@example.com", "password": "short12"},
    )

    assert response.status_code == 400
    assert b"at least 8 characters" in response.data
    assert get_user_by_email("short@example.com") is None


def test_blank_name_rejected(client):
    response = client.post(
        "/register",
        data={"name": "   ", "email": "blank@example.com", "password": "password123"},
    )

    assert response.status_code == 400
    assert b"enter your name" in response.data
    assert get_user_by_email("blank@example.com") is None


def test_invalid_email_rejected(client):
    response = client.post(
        "/register",
        data={"name": "No At Sign", "email": "not-an-email", "password": "password123"},
    )

    assert response.status_code == 400
    assert b"valid email address" in response.data


def test_email_is_normalised(client):
    client.post(
        "/register",
        data={
            "name": "Case Test",
            "email": "  Case.Test@Example.COM  ",
            "password": "password123",
        },
    )

    assert get_user_by_email("case.test@example.com") is not None


def test_error_keeps_input_but_not_password(client):
    response = client.post(
        "/register",
        data={"name": "Kept Name", "email": "kept@example.com", "password": "short12"},
    )

    assert b'value="Kept Name"' in response.data
    assert b'value="kept@example.com"' in response.data
    assert b"short12" not in response.data
