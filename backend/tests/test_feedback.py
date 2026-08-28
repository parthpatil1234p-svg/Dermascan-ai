from bson import ObjectId

from tests.feedback_fixtures import analysis_payload, auth, feedback_api_context, product_payload


def test_successful_analysis_feedback():
    context = feedback_api_context()
    response = context["client"].post(
        "/api/feedback", json=analysis_payload(context), headers=auth(context["token"])
    )
    assert response.status_code == 201
    assert response.json()["feedback_id"].startswith("FDB-")
    assert "selected consent preferences" in response.json()["acknowledgement"]


def test_successful_product_recommendation_feedback():
    context = feedback_api_context()
    response = context["client"].post(
        "/api/feedback", json=product_payload(context), headers=auth(context["token"])
    )
    assert response.status_code == 201
    assert response.json()["product_name"] == "Test Gentle Cleanser"


def test_successful_routine_and_report_feedback():
    context = feedback_api_context()
    routine = {
        "routine_report_id": context["routine_report_id"],
        "feedback_category": "routine_feedback",
        "routine_practicality": 4,
        "routine_difficulty": "manageable",
    }
    report = {
        "final_report_id": context["final_report_id"],
        "feedback_category": "report_feedback",
        "report_clarity": 5,
        "report_length": "appropriate",
        "technical_detail_level": "appropriate",
    }
    assert (
        context["client"]
        .post("/api/feedback", json=routine, headers=auth(context["token"]))
        .status_code
        == 201
    )
    assert (
        context["client"]
        .post("/api/feedback", json=report, headers=auth(context["token"]))
        .status_code
        == 201
    )


def test_rejects_unauthenticated_and_another_users_report():
    context = feedback_api_context()
    assert (
        context["client"].post("/api/feedback", json=analysis_payload(context)).status_code == 401
    )
    context["collections"]["final_reports"].documents[0]["user_id"] = ObjectId()
    response = context["client"].post(
        "/api/feedback", json=analysis_payload(context), headers=auth(context["token"])
    )
    assert response.status_code == 404


def test_rejects_unrelated_product_feedback():
    context = feedback_api_context()
    response = context["client"].post(
        "/api/feedback",
        json=product_payload(context, product_id="PRD-NOT-RECOMMENDED"),
        headers=auth(context["token"]),
    )
    assert response.status_code == 404


def test_validates_rating_category_and_reason_codes():
    context = feedback_api_context()
    client, headers = context["client"], auth(context["token"])
    assert (
        client.post(
            "/api/feedback", json=analysis_payload(context, overall_rating=0), headers=headers
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/feedback", json=analysis_payload(context, overall_rating=6), headers=headers
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/feedback",
            json=analysis_payload(context, feedback_category="unknown"),
            headers=headers,
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/feedback",
            json=analysis_payload(context, selected_reasons=["NOT_REAL"]),
            headers=headers,
        ).status_code
        == 422
    )


def test_sanitizes_script_and_flags_moderation():
    context = feedback_api_context()
    response = context["client"].post(
        "/api/feedback",
        json=analysis_payload(context, comment='<script>alert("x")</script> Useful'),
        headers=auth(context["token"]),
    )
    body = response.json()
    assert response.status_code == 201
    assert "<script>" not in body["comment"] and "&lt;script&gt;" in body["comment"]
    assert body["moderation_status"] == "flagged" and body["feedback_status"] == "flagged"


def test_comment_length_duplicate_and_rate_limits():
    context = feedback_api_context(max_per_hour=2)
    headers = auth(context["token"])
    assert (
        context["client"]
        .post("/api/feedback", json=analysis_payload(context, comment="x" * 1001), headers=headers)
        .status_code
        == 422
    )
    payload = analysis_payload(context)
    assert context["client"].post("/api/feedback", json=payload, headers=headers).status_code == 201
    assert context["client"].post("/api/feedback", json=payload, headers=headers).status_code == 409
    assert (
        context["client"]
        .post(
            "/api/feedback",
            json=analysis_payload(context, comment="Second distinct response"),
            headers=headers,
        )
        .status_code
        == 201
    )
    assert (
        context["client"]
        .post(
            "/api/feedback",
            json=analysis_payload(context, comment="Third response"),
            headers=headers,
        )
        .status_code
        == 429
    )


def test_update_preserves_created_date_and_withdraws():
    context = feedback_api_context()
    headers = auth(context["token"])
    created = (
        context["client"]
        .post("/api/feedback", json=analysis_payload(context), headers=headers)
        .json()
    )
    updated = context["client"].put(
        f"/api/feedback/{created['feedback_id']}",
        json=analysis_payload(context, overall_rating=3, comment="Updated feedback"),
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["feedback_status"] == "edited"
    assert updated.json()["created_at"] == created["created_at"]
    withdrawn = context["client"].delete(f"/api/feedback/{created['feedback_id']}", headers=headers)
    assert withdrawn.status_code == 200 and withdrawn.json()["feedback_status"] == "withdrawn"


def test_feedback_history_and_detail_enforce_ownership():
    context = feedback_api_context()
    headers = auth(context["token"])
    created = (
        context["client"]
        .post("/api/feedback", json=analysis_payload(context), headers=headers)
        .json()
    )
    assert (
        context["client"].get("/api/feedback", headers=headers).json()["pagination"]["total_items"]
        == 1
    )
    assert (
        context["client"]
        .get(f"/api/feedback/{created['feedback_id']}", headers=headers)
        .status_code
        == 200
    )
    assert (
        context["client"]
        .get(f"/api/feedback/{created['feedback_id']}", headers=auth(context["admin_token"]))
        .status_code
        == 404
    )


def test_stored_feedback_excludes_tokens_paths_and_client_user_id():
    context = feedback_api_context()
    payload = analysis_payload(context)
    payload["user_id"] = str(ObjectId())
    response = context["client"].post("/api/feedback", json=payload, headers=auth(context["token"]))
    stored = context["collections"]["feedback"].documents[0]
    assert response.status_code == 201
    assert str(stored["user_id"]) == str(context["owner"])
    assert "access_token" not in stored and "storage_reference" not in stored
