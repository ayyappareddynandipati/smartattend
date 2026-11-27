"""Shared fixtures: in-memory database, stubbed face service and auth helpers."""

import sys
import types

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Replace the DeepFace/TensorFlow service with a stub so tests run fast without ML models.
_face_stub = types.ModuleType("app.services.face_recognition")
_face_stub.face_service = types.SimpleNamespace(
    preprocess_image=lambda img: [],
    generate_embedding=lambda face: None,
    compute_similarity=lambda a, b: 0.0,
)
sys.modules["app.services.face_recognition"] = _face_stub

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, get_db  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.main import app  # noqa: E402
from app.models.models import User  # noqa: E402

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    return TestClient(app)


def make_user(db, username, password, role, first_login=0):
    user = User(
        username=username,
        hashed_password=get_password_hash(password),
        role=role,
        first_login=first_login,
    )
    db.add(user)
    db.commit()
    return user


def login(client, username, password):
    return client.post("/auth/token", data={"username": username, "password": password})


def auth_header(client, username, password):
    token = login(client, username, password).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers(client, db):
    make_user(db, "admin", "admin-pass", "admin")
    return auth_header(client, "admin", "admin-pass")


@pytest.fixture()
def faculty_headers(client, db):
    make_user(db, "teacher", "teacher-pass", "faculty")
    return auth_header(client, "teacher", "teacher-pass")
