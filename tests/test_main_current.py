import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
from models import Student

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_student():
    payload = {"name": "Alice", "email": "alice@test.com", "age": 22, "major": "Computer Science"}
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@test.com"
    assert data["age"] == 22
    assert data["major"] == "Computer Science"
    assert "id" in data


def test_list_students_empty():
    response = client.get("/students")
    assert response.status_code == 200
    assert response.json() == []


def test_list_students_with_data():
    client.post("/students", json={"name": "Bob", "email": "bob@test.com", "age": 20, "major": "Math"})
    client.post("/students", json={"name": "Carol", "email": "carol@test.com", "age": 23, "major": "Physics"})
    response = client.get("/students")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_student_by_id():
    resp = client.post("/students", json={"name": "Dave", "email": "dave@test.com", "age": 21, "major": "Engineering"})
    student_id = resp.json()["id"]
    response = client.get(f"/students/{student_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Dave"


def test_get_student_not_found():
    response = client.get("/students/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_delete_student():
    resp = client.post("/students", json={"name": "Eve", "email": "eve@test.com", "age": 24, "major": "Chemistry"})
    student_id = resp.json()["id"]
    response = client.delete(f"/students/{student_id}")
    assert response.status_code == 204
    get_resp = client.get(f"/students/{student_id}")
    assert get_resp.status_code == 404


def test_delete_student_not_found():
    response = client.delete("/students/999")
    assert response.status_code == 404


def test_duplicate_email():
    client.post("/students", json={"name": "Frank", "email": "frank@test.com", "age": 25, "major": "Biology"})
    response = client.post("/students", json={"name": "Frank2", "email": "frank@test.com", "age": 26, "major": "Biology"})
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_update_student():
    resp = client.post("/students", json={"name": "Grace", "email": "grace@test.com", "age": 22, "major": "Art"})
    student_id = resp.json()["id"]
    response = client.put(f"/students/{student_id}", json={"name": "Grace Hopper", "major": "Computer Science"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Grace Hopper"
    assert data["major"] == "Computer Science"
    assert data["email"] == "grace@test.com"

def test_update_student_not_found():
    response = client.put("/students/999", json={"name": "Nobody"})
    assert response.status_code == 404


def test_list_students_filter_by_major():
    client.post("/students", json={"name": "Alice", "email": "a@test.com", "age": 22, "major": "CS"})
    client.post("/students", json={"name": "Bob", "email": "b@test.com", "age": 23, "major": "Math"})
    client.post("/students", json={"name": "Carol", "email": "c@test.com", "age": 24, "major": "CS"})
    response = client.get("/students?major=CS")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(s["major"] == "CS" for s in data)


def test_student_stats():
    client.post("/students", json={"name": "Alice", "email": "a@test.com", "age": 20, "major": "CS"})
    client.post("/students", json={"name": "Bob", "email": "b@test.com", "age": 30, "major": "Math"})
    response = client.get("/students/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] == 2
    assert data["average_age"] == 25.0
    assert data["by_major"]["CS"] == 1
    assert data["by_major"]["Math"] == 1
