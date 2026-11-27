def test_admin_can_create_and_list_users(client, admin_headers):
    res = client.post(
        "/users/", json={"username": "teacher", "password": "pw", "role": "faculty"}, headers=admin_headers
    )
    assert res.status_code == 200
    assert res.json()["role"] == "faculty"

    usernames = [u["username"] for u in client.get("/users/", headers=admin_headers).json()]
    assert usernames == ["admin", "teacher"]


def test_duplicate_username_is_rejected(client, admin_headers):
    payload = {"username": "teacher", "password": "pw", "role": "faculty"}
    client.post("/users/", json=payload, headers=admin_headers)
    res = client.post("/users/", json=payload, headers=admin_headers)
    assert res.status_code == 400


def test_non_admin_cannot_create_users(client, faculty_headers):
    res = client.post(
        "/users/", json={"username": "x", "password": "pw", "role": "admin"}, headers=faculty_headers
    )
    assert res.status_code == 403


def test_admin_cannot_delete_own_account(client, admin_headers):
    admin_id = client.get("/users/", headers=admin_headers).json()[0]["id"]
    assert client.delete(f"/users/{admin_id}", headers=admin_headers).status_code == 400


def test_section_crud(client, admin_headers):
    created = client.post("/sections/", json={"name": "IT-A", "academic_year": "2025-26"}, headers=admin_headers)
    assert created.status_code == 200
    section_id = created.json()["id"]

    updated = client.put(
        f"/sections/{section_id}", json={"name": "IT-B", "academic_year": "2025-26"}, headers=admin_headers
    )
    assert updated.json()["name"] == "IT-B"

    assert client.get(f"/sections/{section_id}", headers=admin_headers).status_code == 200
    assert client.delete(f"/sections/{section_id}", headers=admin_headers).status_code == 200
    assert client.get(f"/sections/{section_id}", headers=admin_headers).status_code == 404


def test_duplicate_section_name_is_rejected(client, admin_headers):
    body = {"name": "IT-A", "academic_year": "2025-26"}
    client.post("/sections/", json=body, headers=admin_headers)
    assert client.post("/sections/", json=body, headers=admin_headers).status_code == 400


def test_faculty_can_list_but_not_create_sections(client, faculty_headers):
    assert client.get("/sections/", headers=faculty_headers).status_code == 200
    res = client.post("/sections/", json={"name": "X", "academic_year": "2025-26"}, headers=faculty_headers)
    assert res.status_code == 403
