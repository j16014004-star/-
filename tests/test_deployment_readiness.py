from app.core.config import Settings
from pathlib import Path


def test_database_url_encodes_special_characters():
    config = Settings(DB_USER="app", DB_PASSWORD="a@b:c/d", DB_HOST="db.internal")
    assert "a%40b%3Ac%2Fd" in config.DATABASE_URL


def test_health_routes_are_registered():
    from app.main import app

    paths = app.openapi()["paths"]
    assert "/api/health/live" in paths
    assert "/api/health/ready" in paths


def test_nginx_api_routes_take_priority_over_static_asset_regex():
    config = Path("deploy/nginx/ai-career.conf").read_text(encoding="utf-8")
    assert "location ^~ /api/" in config
    assert "location ^~ /uploads/" in config
