from app.core.config import Settings


def test_database_url_encodes_special_characters():
    config = Settings(DB_USER="app", DB_PASSWORD="a@b:c/d", DB_HOST="db.internal")
    assert "a%40b%3Ac%2Fd" in config.DATABASE_URL


def test_health_routes_are_registered():
    from app.main import app

    paths = app.openapi()["paths"]
    assert "/api/health/live" in paths
    assert "/api/health/ready" in paths
