"""
Tests for Flask application factory pattern.

Verifies that dashboard.py supports the application factory pattern
for better testability and configuration flexibility.
"""

import pytest


def test_create_app_function_exists():
    """create_app() factory function must exist for testability."""
    from dashboard import create_app

    assert callable(create_app)


def test_create_app_returns_flask_instance():
    """create_app() should return a Flask application instance."""
    from dashboard import create_app

    app = create_app()
    assert app is not None
    assert hasattr(app, "run")
    assert hasattr(app, "test_client")


def test_multiple_instances_with_different_configs():
    """Factory pattern should allow multiple app instances with different configs."""
    from dashboard import create_app

    app1 = create_app()
    app2 = create_app()

    assert app1 is not app2, "Each call to create_app() should create a new instance"


def test_app_has_expected_endpoints():
    """App created by factory should have expected API endpoints."""
    from dashboard import create_app

    app = create_app()

    with app.test_client() as client:
        response = client.get("/api/overview")
        assert response.status_code == 200


def test_api_health_endpoint_accessible():
    """Health endpoint should be accessible from factory-created app."""
    from dashboard import create_app

    app = create_app()

    with app.test_client() as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.get_json()
        assert "checks" in data
