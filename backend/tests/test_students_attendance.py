import io

import openpyxl

from app.models.models import AttendanceLog
from tests.conftest import login


def _create_section(client, headers, name="IT-A"):
    return client.post("/sections/", json={"name": name, "academic_year": "2025-26"}, headers=headers).json()["id"]


def _create_student(client, headers, section_id, roll="21A91A1201", name="Test Student"):
    return client.post(
        "/students/",
        data={"name": name, "roll_number": roll, "email": "", "section_id": section_id},
        headers=headers,
    )


def test_creating_student_creates_login_with_roll_number(client, admin_headers):
    section_id = _create_section(client, admin_headers)

    res = _create_student(client, admin_headers, section_id)

    assert res.status_code == 200
    assert res.json()["username"] == "21A91A1201"
    student_login = login(client, "21A91A1201", "21A91A1201").json()
    assert student_login["role"] == "student"
    assert student_login["first_login"] is True


def test_student_requires_existing_section(client, admin_headers):
    assert _create_student(client, admin_headers, section_id=999).status_code == 404


def test_duplicate_roll_number_is_rejected(client, admin_headers):
    section_id = _create_section(client, admin_headers)
    _create_student(client, admin_headers, section_id)
    assert _create_student(client, admin_headers, section_id).status_code == 400


def test_cannot_delete_section_with_students(client, admin_headers):
    section_id = _create_section(client, admin_headers)
    _create_student(client, admin_headers, section_id)
    assert client.delete(f"/sections/{section_id}", headers=admin_headers).status_code == 400


def test_deleting_student_removes_login(client, admin_headers):
    section_id = _create_section(client, admin_headers)
    student_id = _create_student(client, admin_headers, section_id).json()["id"]

    assert client.delete(f"/students/{student_id}", headers=admin_headers).status_code == 200
    assert login(client, "21A91A1201", "21A91A1201").status_code == 401


def _seed_session(client, db, admin_headers):
    section_id = _create_section(client, admin_headers)
    student_id = _create_student(client, admin_headers, section_id).json()["id"]
    _create_student(client, admin_headers, section_id, roll="21A91A1202", name="Absent Student")
    db.add(AttendanceLog(student_id=student_id, session_id="s1", status="Present", confidence_score=0.91))
    db.commit()
    return section_id


def test_student_sees_own_attendance(client, db, admin_headers):
    _seed_session(client, db, admin_headers)
    token = login(client, "21A91A1201", "21A91A1201").json()["access_token"]

    res = client.get("/attendance/my-logs", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    assert [log["session_id"] for log in res.json()] == ["s1"]


def test_my_logs_is_student_only(client, admin_headers):
    assert client.get("/attendance/my-logs", headers=admin_headers).status_code == 403


def test_export_csv_returns_report(client, db, admin_headers):
    _seed_session(client, db, admin_headers)

    res = client.get("/attendance/export/s1?format=csv", headers=admin_headers)

    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    lines = res.text.strip().splitlines()
    assert lines[0].startswith("Student ID,Name,Roll Number")
    assert "21A91A1201" in lines[1]


def test_export_excel_returns_xlsx(client, db, admin_headers):
    _seed_session(client, db, admin_headers)

    res = client.get("/attendance/export/s1?format=excel", headers=admin_headers)

    assert res.status_code == 200
    assert "attendance_s1.xlsx" in res.headers["content-disposition"]
    sheet = openpyxl.load_workbook(io.BytesIO(res.content))["Attendance"]
    assert sheet["C2"].value == "21A91A1201"


def test_export_unknown_session_returns_404(client, admin_headers):
    assert client.get("/attendance/export/missing", headers=admin_headers).status_code == 404


def test_complete_session_splits_present_and_absent(client, db, admin_headers):
    section_id = _seed_session(client, db, admin_headers)

    res = client.post("/attendance/session/s1/complete", data={"section_id": section_id}, headers=admin_headers)

    assert res.status_code == 200
    body = res.json()
    assert [s["roll_number"] for s in body["present_students"]] == ["21A91A1201"]
    assert [s["roll_number"] for s in body["absent_students"]] == ["21A91A1202"]
