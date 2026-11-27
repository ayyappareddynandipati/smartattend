from tests.conftest import login, make_user


def test_login_returns_token_role_and_first_login_flag(client, db):
    make_user(db, "admin", "admin-pass", "admin", first_login=1)

    res = login(client, "admin", "admin-pass")

    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["role"] == "admin"
    assert body["first_login"] is True


def test_login_trims_username(client, db):
    make_user(db, "admin", "admin-pass", "admin")
    assert login(client, "  admin  ", "admin-pass").status_code == 200


def test_login_rejects_wrong_password(client, db):
    make_user(db, "admin", "admin-pass", "admin")
    res = login(client, "admin", "wrong")
    assert res.status_code == 401
    assert res.json()["detail"] == "Incorrect username or password"


def test_login_rejects_unknown_user(client, db):
    assert login(client, "nobody", "x").status_code == 401


def test_protected_route_requires_token(client, db):
    assert client.get("/sections/").status_code == 401


def test_protected_route_rejects_invalid_token(client, db):
    res = client.get("/sections/", headers={"Authorization": "Bearer not-a-jwt"})
    assert res.status_code == 401


def test_change_password_clears_first_login(client, db):
    make_user(db, "stu", "old-pass", "student", first_login=1)
    headers = {"Authorization": f"Bearer {login(client, 'stu', 'old-pass').json()['access_token']}"}

    res = client.post(
        "/users/change-password",
        json={"old_password": "old-pass", "new_password": "new-pass"},
        headers=headers,
    )

    assert res.status_code == 200
    assert login(client, "stu", "old-pass").status_code == 401
    new_login = login(client, "stu", "new-pass").json()
    assert new_login["first_login"] is False


def test_change_password_rejects_wrong_old_password(client, db):
    make_user(db, "stu", "old-pass", "student")
    headers = {"Authorization": f"Bearer {login(client, 'stu', 'old-pass').json()['access_token']}"}
    res = client.post(
        "/users/change-password",
        json={"old_password": "nope", "new_password": "new-pass"},
        headers=headers,
    )
    assert res.status_code == 400
