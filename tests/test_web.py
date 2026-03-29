from fastapi.testclient import TestClient
import os
from pathlib import Path

# Setup environment variables before importing app
os.environ["MUSIC_DIR"] = str(Path("music").resolve())
os.environ["WEB_USERNAME"] = "testuser"
os.environ["WEB_PASSWORD"] = "testpass"

from id3tag_renamer.web import app
from id3tag_renamer.config import config

DEFAULT_MUSIC_DIR = config.DEFAULT_MUSIC_DIR

client = TestClient(app)

SAME_ORIGIN = {"Origin": "http://testserver"}


def get_session_cookie():
    # /login is CSRF-exempt so no Origin needed
    resp = client.post("/login", data={"username": "testuser", "password": "testpass"}, follow_redirects=False)
    assert resp.status_code == 303
    return resp.cookies["session"]

def test_list_directories():
    session = get_session_cookie()
    response = client.get("/api/directories", cookies={"session": session})
    assert response.status_code == 200
    data = response.json()
    assert "directories" in data
    assert "current_path" in data
    assert "full_path" in data
    assert data["full_path"] == DEFAULT_MUSIC_DIR

def test_list_directories_traversal():
    session = get_session_cookie()
    response = client.get("/api/directories?path=../../", cookies={"session": session})
    assert response.status_code == 200
    data = response.json()
    assert data["full_path"] == DEFAULT_MUSIC_DIR

def test_list_directories_sub():
    session = get_session_cookie()
    root = Path(DEFAULT_MUSIC_DIR)
    subdirs = [d for d in root.iterdir() if d.is_dir() and not d.name.startswith(".")]

    if subdirs:
        sub = subdirs[0]
        response = client.get(f"/api/directories?path={sub.name}", cookies={"session": session})
        assert response.status_code == 200
        data = response.json()
        assert data["current_path"] == sub.name
        assert data["full_path"] == str(sub.resolve())

def test_scan_traversal():
    session = get_session_cookie()
    response = client.post(
        "/scan",
        data={"directory": "../../"},
        cookies={"session": session},
        headers=SAME_ORIGIN,
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/")

    from id3tag_renamer.web import manager
    assert manager.directory == Path(DEFAULT_MUSIC_DIR).resolve()

def test_csrf_protection():
    session = get_session_cookie()

    # Evil origin → 403
    response = client.post(
        "/scan",
        data={"directory": "music"},
        cookies={"session": session},
        headers={"Origin": "http://evil.com"},
    )
    assert response.status_code == 403
    assert "Origin mismatch" in response.text

    # No origin, evil referer → 403
    response = client.post(
        "/scan",
        data={"directory": "music"},
        cookies={"session": session},
        headers={"Referer": "http://evil.com/page"},
    )
    assert response.status_code == 403
    assert "Referer mismatch" in response.text

    # No origin, no referer → 403
    response = client.post(
        "/scan",
        data={"directory": "music"},
        cookies={"session": session},
    )
    assert response.status_code == 403
    assert "missing Origin/Referer" in response.text

    # Correct origin → passes (303 redirect)
    response = client.post(
        "/scan",
        data={"directory": "music"},
        cookies={"session": session},
        headers=SAME_ORIGIN,
        follow_redirects=False,
    )
    assert response.status_code == 303

def test_brute_force_lockout():
    from id3tag_renamer.routes.auth import _failed_attempts
    _failed_attempts.clear()

    # Exhaust the allowed attempts
    for _ in range(10):
        client.post("/login", data={"username": "testuser", "password": "wrong"})

    # Next attempt should be locked out
    response = client.post("/login", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 429
    assert "Too many failed attempts" in response.text

    _failed_attempts.clear()
