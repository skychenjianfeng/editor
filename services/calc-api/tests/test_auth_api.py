import json
import os

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import Client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "calcapi.settings")

import django

django.setup()


@pytest.fixture
def browser_client():
    return Client(enforce_csrf_checks=True)


def csrf_post(client, path, payload):
    client.get("/api/v1/auth/csrf")
    token = client.cookies["csrftoken"].value
    return client.post(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )


@pytest.mark.django_db
def test_register_me_logout_and_login(browser_client):
    registered = csrf_post(
        browser_client,
        "/api/v1/auth/register",
        {
            "email": "  User@Example.com ",
            "password": "Strong-pass-2026",
            "password_confirm": "Strong-pass-2026",
        },
    )
    assert registered.status_code == 201
    assert registered.json()["email"] == "user@example.com"

    me = browser_client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"

    logged_out = csrf_post(browser_client, "/api/v1/auth/logout", {})
    assert logged_out.status_code == 204
    assert browser_client.get("/api/v1/auth/me").status_code == 401

    logged_in = csrf_post(
        browser_client,
        "/api/v1/auth/login",
        {"email": "user@example.com", "password": "Strong-pass-2026"},
    )
    assert logged_in.status_code == 200


@pytest.mark.django_db
def test_register_rejects_duplicate_email_and_mismatched_password(browser_client):
    payload = {
        "email": "duplicate@example.com",
        "password": "Strong-pass-2026",
        "password_confirm": "Strong-pass-2026",
    }
    assert csrf_post(browser_client, "/api/v1/auth/register", payload).status_code == 201

    mismatch = csrf_post(
        browser_client,
        "/api/v1/auth/register",
        {
            "email": "mismatch@example.com",
            "password": "Strong-pass-2026",
            "password_confirm": "different",
        },
    )
    assert mismatch.status_code == 400
    assert "password" in mismatch.json()["errors"]

    duplicate = csrf_post(
        browser_client,
        "/api/v1/auth/register",
        {**payload, "email": "DUPLICATE@example.com"},
    )
    assert duplicate.status_code == 400
    assert "email" in duplicate.json()["errors"]


@pytest.mark.django_db
def test_register_rejects_weak_password(browser_client):
    response = csrf_post(
        browser_client,
        "/api/v1/auth/register",
        {
            "email": "weak@example.com",
            "password": "123",
            "password_confirm": "123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "注册信息有误"
    assert "password" in response.json()["errors"]


@pytest.mark.django_db
def test_register_rejects_invalid_email(browser_client):
    response = csrf_post(
        browser_client,
        "/api/v1/auth/register",
        {
            "email": "invalid email@example.com",
            "password": "Strong-pass-2026",
            "password_confirm": "Strong-pass-2026",
        },
    )

    assert response.status_code == 400
    assert response.json()["errors"]["email"] == ["请输入有效邮箱"]


@pytest.mark.django_db
def test_register_returns_duplicate_email_when_save_races(
    browser_client, monkeypatch
):
    user_model = get_user_model()

    def raise_integrity_error(*args, **kwargs):
        raise IntegrityError("duplicate email")

    monkeypatch.setattr(user_model, "save", raise_integrity_error)
    response = csrf_post(
        browser_client,
        "/api/v1/auth/register",
        {
            "email": "race@example.com",
            "password": "Strong-pass-2026",
            "password_confirm": "Strong-pass-2026",
        },
    )

    assert response.status_code == 400
    assert response.json()["errors"]["email"] == ["该邮箱已注册"]


def test_responses_include_security_headers(browser_client):
    response = browser_client.get("/api/v1/auth/csrf")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "same-origin"


@pytest.mark.django_db
def test_login_does_not_reveal_unknown_email(browser_client):
    get_user_model().objects.create_user(
        username="known@example.com",
        email="known@example.com",
        password="Strong-pass-2026",
    )
    wrong_password = csrf_post(
        browser_client,
        "/api/v1/auth/login",
        {"email": "known@example.com", "password": "wrong"},
    )
    unknown_email = csrf_post(
        browser_client,
        "/api/v1/auth/login",
        {"email": "unknown@example.com", "password": "wrong"},
    )
    assert wrong_password.status_code == unknown_email.status_code == 400
    assert wrong_password.json()["detail"] == unknown_email.json()["detail"]


def test_register_without_csrf_is_rejected(browser_client):
    response = browser_client.post(
        "/api/v1/auth/register",
        data=json.dumps(
            {
                "email": "csrf@example.com",
                "password": "Strong-pass-2026",
                "password_confirm": "Strong-pass-2026",
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 403
