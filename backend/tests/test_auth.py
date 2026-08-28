import os
from datetime import timedelta
from typing import Any

os.environ.setdefault("APP_NAME", "DermaScan AI")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("API_PREFIX", "/api")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DATABASE", "dermascan_ai_test")
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-auth-tests-at-least-32-bytes",
)
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")

from bson import ObjectId
from fastapi.testclient import TestClient

from app.api.dependencies import get_users_collection
from app.core.security import create_access_token
from app.main import create_app


class InsertOneResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class FakeUsersCollection:
    def __init__(self) -> None:
        self.documents: dict[ObjectId, dict[str, Any]] = {}

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        if "email" in query:
            for document in self.documents.values():
                if document["email"] == query["email"]:
                    return document.copy()
            return None

        if "_id" in query:
            document = self.documents.get(query["_id"])
            return document.copy() if document else None

        return None

    async def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        inserted_id = ObjectId()
        stored_document = document.copy()
        stored_document["_id"] = inserted_id
        self.documents[inserted_id] = stored_document
        return InsertOneResult(inserted_id)


def registration_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "full_name": " Example User ",
        "email": "USER@example.com ",
        "password": "StrongPassword123",
        "confirm_password": "StrongPassword123",
        "age_group": "18-25",
        "location": " India ",
        "accept_terms": True,
    }
    payload.update(overrides)
    return payload


def create_test_client() -> tuple[TestClient, FakeUsersCollection]:
    fake_collection = FakeUsersCollection()
    app = create_app(enable_lifespan=False)
    app.dependency_overrides[get_users_collection] = lambda: fake_collection
    return TestClient(app), fake_collection


def register_user(client: TestClient, **overrides: Any) -> dict[str, Any]:
    response = client.post("/api/auth/register", json=registration_payload(**overrides))
    assert response.status_code == 201
    return response.json()


def test_successful_registration() -> None:
    client, collection = create_test_client()

    data = register_user(client)

    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == "user@example.com"
    assert data["user"]["full_name"] == "Example User"
    assert data["user"]["location"] == "India"
    stored_user = next(iter(collection.documents.values()))
    assert stored_user["password_hash"] != "StrongPassword123"
    assert "password_hash" not in data["user"]


def test_duplicate_email_rejection() -> None:
    client, _ = create_test_client()
    register_user(client)

    response = client.post("/api/auth/register", json=registration_payload())

    assert response.status_code == 409
    assert response.json()["detail"] == "An account with this email already exists."


def test_invalid_email_rejection() -> None:
    client, _ = create_test_client()

    response = client.post(
        "/api/auth/register",
        json=registration_payload(email="not-an-email"),
    )

    assert response.status_code == 422


def test_weak_password_rejection() -> None:
    client, _ = create_test_client()

    response = client.post(
        "/api/auth/register",
        json=registration_payload(password="short", confirm_password="short"),
    )

    assert response.status_code == 422


def test_password_mismatch_rejection() -> None:
    client, _ = create_test_client()

    response = client.post(
        "/api/auth/register",
        json=registration_payload(confirm_password="DifferentPassword123"),
    )

    assert response.status_code == 422


def test_terms_not_accepted_rejection() -> None:
    client, _ = create_test_client()

    response = client.post(
        "/api/auth/register",
        json=registration_payload(accept_terms=False),
    )

    assert response.status_code == 422


def test_successful_login() -> None:
    client, _ = create_test_client()
    register_user(client)

    response = client.post(
        "/api/auth/login",
        json={"email": "USER@example.com", "password": "StrongPassword123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["user"]["email"] == "user@example.com"


def test_invalid_password_rejection() -> None:
    client, _ = create_test_client()
    register_user(client)

    response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "WrongPassword123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_unregistered_email_rejection() -> None:
    client, _ = create_test_client()

    response = client.post(
        "/api/auth/login",
        json={"email": "missing@example.com", "password": "StrongPassword123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_protected_route_without_token() -> None:
    client, _ = create_test_client()

    response = client.get("/api/users/me")

    assert response.status_code == 401


def test_protected_route_with_valid_token() -> None:
    client, _ = create_test_client()
    auth_data = register_user(client)

    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {auth_data['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_protected_route_with_invalid_token() -> None:
    client, _ = create_test_client()

    response = client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication token."


def test_protected_route_with_expired_token() -> None:
    client, collection = create_test_client()
    register_user(client)
    user_id = str(next(iter(collection.documents.keys())))
    expired_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(minutes=-1),
    )

    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication token has expired."
