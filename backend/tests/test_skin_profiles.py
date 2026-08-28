import os
from typing import Any

os.environ.setdefault("APP_NAME", "DermaScan AI")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("API_PREFIX", "/api")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DATABASE", "dermascan_ai_test")
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-profile-tests-at-least-32-bytes",
)
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")

from bson import ObjectId
from fastapi.testclient import TestClient

from app.api.dependencies import get_skin_profiles_collection, get_users_collection
from app.main import create_app


class InsertOneResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class UpdateResult:
    modified_count = 1


class DeleteResult:
    def __init__(self, deleted_count: int) -> None:
        self.deleted_count = deleted_count


class FakeUsersCollection:
    def __init__(self) -> None:
        self.documents: dict[ObjectId, dict[str, Any]] = {}

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.documents.values():
            if all(document.get(key) == value for key, value in query.items()):
                return document.copy()
        return None

    async def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        inserted_id = ObjectId()
        self.documents[inserted_id] = {**document, "_id": inserted_id}
        return InsertOneResult(inserted_id)


class FakeSkinProfilesCollection:
    def __init__(self) -> None:
        self.documents: dict[ObjectId, dict[str, Any]] = {}

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.documents.values():
            if all(document.get(key) == value for key, value in query.items()):
                return document.copy()
        return None

    async def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        inserted_id = ObjectId()
        self.documents[inserted_id] = {**document, "_id": inserted_id}
        return InsertOneResult(inserted_id)

    async def update_one(
        self,
        query: dict[str, Any],
        operation: dict[str, Any],
    ) -> UpdateResult:
        for document in self.documents.values():
            if all(document.get(key) == value for key, value in query.items()):
                document.update(operation["$set"])
                break
        return UpdateResult()

    async def delete_one(self, query: dict[str, Any]) -> DeleteResult:
        for document_id, document in list(self.documents.items()):
            if all(document.get(key) == value for key, value in query.items()):
                del self.documents[document_id]
                return DeleteResult(1)
        return DeleteResult(0)


def create_test_client() -> tuple[TestClient, FakeSkinProfilesCollection]:
    users = FakeUsersCollection()
    profiles = FakeSkinProfilesCollection()
    app = create_app(enable_lifespan=False)
    app.dependency_overrides[get_users_collection] = lambda: users
    app.dependency_overrides[get_skin_profiles_collection] = lambda: profiles
    return TestClient(app), profiles


def register_user(client: TestClient, email: str = "profile@example.com") -> str:
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Profile User",
            "email": email,
            "password": "StrongPassword123",
            "confirm_password": "StrongPassword123",
            "age_group": "18-25",
            "location": "India",
            "accept_terms": True,
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def profile_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "age_group": "18-25",
        "oiliness_level": "High",
        "dryness_level": "Moderate",
        "is_sensitive": True,
        "known_allergies": [" Added fragrance ", "added FRAGRANCE"],
        "current_products": ["Cleanser", "Moisturizer"],
        "budget_min": 200,
        "budget_max": 1000,
        "preferred_brands": ["Minimalist", "Cetaphil"],
        "ingredients_to_avoid": ["Drying alcohol"],
        "fragrance_preference": "Fragrance-free only",
        "country": " India ",
        "experience_level": "Beginner",
        "additional_notes": "  Skin sometimes feels irritated.  ",
    }
    payload.update(overrides)
    return payload


def create_profile(client: TestClient, token: str, **overrides: Any):
    return client.post(
        "/api/skin-profile",
        headers=auth_headers(token),
        json=profile_payload(**overrides),
    )


def test_create_profile_successfully() -> None:
    client, collection = create_test_client()
    token = register_user(client)

    response = create_profile(client, token)

    assert response.status_code == 201
    data = response.json()
    assert data["country"] == "India"
    assert data["is_complete"] is True
    assert "user_id" in data
    assert next(iter(collection.documents.values()))["user_id"] == ObjectId(data["user_id"])


def test_reject_request_without_authentication() -> None:
    client, _ = create_test_client()
    response = client.post("/api/skin-profile", json=profile_payload())
    assert response.status_code == 401


def test_reject_duplicate_profile() -> None:
    client, _ = create_test_client()
    token = register_user(client)
    assert create_profile(client, token).status_code == 201
    response = create_profile(client, token)
    assert response.status_code == 409
    assert response.json()["detail"] == "A skin profile already exists for this user."


def test_retrieve_current_user_profile() -> None:
    client, _ = create_test_client()
    token = register_user(client)
    created = create_profile(client, token).json()
    response = client.get("/api/skin-profile", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_reject_access_with_invalid_token() -> None:
    client, _ = create_test_client()
    response = client.get(
        "/api/skin-profile",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_update_profile_successfully() -> None:
    client, _ = create_test_client()
    token = register_user(client)
    create_profile(client, token)
    response = client.put(
        "/api/skin-profile",
        headers=auth_headers(token),
        json=profile_payload(oiliness_level="Low", country="India"),
    )
    assert response.status_code == 200
    assert response.json()["oiliness_level"] == "Low"


def test_update_preserves_created_at() -> None:
    client, _ = create_test_client()
    token = register_user(client)
    original = create_profile(client, token).json()
    updated = client.put(
        "/api/skin-profile",
        headers=auth_headers(token),
        json=profile_payload(country="Sri Lanka"),
    ).json()
    assert updated["created_at"] == original["created_at"]


def test_update_changes_updated_at() -> None:
    client, _ = create_test_client()
    token = register_user(client)
    original = create_profile(client, token).json()
    updated = client.put(
        "/api/skin-profile",
        headers=auth_headers(token),
        json=profile_payload(country="Sri Lanka"),
    ).json()
    assert updated["updated_at"] > original["updated_at"]


def test_reject_invalid_age_group() -> None:
    client, _ = create_test_client()
    token = register_user(client)
    assert create_profile(client, token, age_group="Unknown").status_code == 422


def test_reject_invalid_oiliness_level() -> None:
    client, _ = create_test_client()
    token = register_user(client)
    assert create_profile(client, token, oiliness_level="Very oily").status_code == 422


def test_reject_invalid_dryness_level() -> None:
    client, _ = create_test_client()
    token = register_user(client)
    assert create_profile(client, token, dryness_level="Very dry").status_code == 422


def test_reject_negative_budget() -> None:
    client, _ = create_test_client()
    token = register_user(client)
    assert create_profile(client, token, budget_min=-1).status_code == 422


def test_reject_maximum_budget_below_minimum() -> None:
    client, _ = create_test_client()
    token = register_user(client)
    response = create_profile(client, token, budget_min=1000, budget_max=200)
    assert response.status_code == 422


def test_remove_duplicate_array_items() -> None:
    client, _ = create_test_client()
    token = register_user(client)
    data = create_profile(client, token).json()
    assert data["known_allergies"] == ["Added fragrance"]


def test_return_404_when_profile_does_not_exist() -> None:
    client, _ = create_test_client()
    token = register_user(client)
    response = client.get("/api/skin-profile", headers=auth_headers(token))
    assert response.status_code == 404
    assert response.json()["detail"] == "Skin profile not found."


def test_user_cannot_access_another_users_profile() -> None:
    client, _ = create_test_client()
    first_token = register_user(client, "first@example.com")
    second_token = register_user(client, "second@example.com")
    assert create_profile(client, first_token).status_code == 201
    response = client.get("/api/skin-profile", headers=auth_headers(second_token))
    assert response.status_code == 404


def test_completion_status_without_and_with_profile() -> None:
    client, _ = create_test_client()
    token = register_user(client)
    empty_status = client.get("/api/skin-profile/status", headers=auth_headers(token)).json()
    assert empty_status == {
        "exists": False,
        "is_complete": False,
        "next_route": "/skin-profile",
    }
    create_profile(client, token)
    complete_status = client.get("/api/skin-profile/status", headers=auth_headers(token)).json()
    assert complete_status == {
        "exists": True,
        "is_complete": True,
        "next_route": "/face-scan",
    }


def test_user_id_cannot_be_supplied_in_request_body() -> None:
    client, _ = create_test_client()
    token = register_user(client)
    response = create_profile(client, token, user_id=str(ObjectId()))
    assert response.status_code == 422
