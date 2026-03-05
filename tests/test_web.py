from fastapi.testclient import TestClient
import os
from pathlib import Path

# Setup environment variables before importing app
os.environ["MUSIC_DIR"] = str(Path("music").resolve())
os.environ["WEB_USERNAME"] = "testuser"
os.environ["WEB_PASSWORD"] = "testpass"

from id3tag_renamer.web import app, DEFAULT_MUSIC_DIR

client = TestClient(app)
auth = ("testuser", "testpass")

def test_list_directories():
    # Test root listing
    response = client.get("/api/directories", auth=auth)
    assert response.status_code == 200
    data = response.json()
    assert "directories" in data
    assert "current_path" in data
    assert "full_path" in data
    assert data["full_path"] == DEFAULT_MUSIC_DIR

def test_list_directories_traversal():
    # Attempt to traverse up from root
    response = client.get("/api/directories?path=../../", auth=auth)
    assert response.status_code == 200
    data = response.json()
    # Should be capped at root
    assert data["full_path"] == DEFAULT_MUSIC_DIR

def test_list_directories_sub():
    # Get a subdirectory from the music folder
    root = Path(DEFAULT_MUSIC_DIR)
    subdirs = [d for d in root.iterdir() if d.is_dir() and not d.name.startswith(".")]
    
    if subdirs:
        sub = subdirs[0]
        response = client.get(f"/api/directories?path={sub.name}", auth=auth)
        assert response.status_code == 200
        data = response.json()
        assert data["current_path"] == sub.name
        assert data["full_path"] == str(sub.resolve())

def test_scan_traversal():
    # Attempt to scan a traversal path
    response = client.post("/scan", data={"directory": "../../"}, auth=auth, follow_redirects=False)
    # Redirect to root "/"
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    
    # Verify manager directory is set to safe path (root)
    from id3tag_renamer.web import manager
    assert manager.directory == Path(DEFAULT_MUSIC_DIR).resolve()

def test_csrf_protection():
    # POST request without Origin/Referer should be rejected if Host mismatch is detected
    # If no Origin/Referer is present, our middleware allows it (for API-like usage or first request)
    # But if Origin is present and wrong, it should be rejected.
    response = client.post("/scan", 
                           data={"directory": "music"}, 
                           auth=auth,
                           headers={"Origin": "http://evil.com"})
    assert response.status_code == 403
    assert response.text == "CSRF Forbidden: Origin mismatch"

    # Correct Origin should pass
    response = client.post("/scan", 
                           data={"directory": "music"}, 
                           auth=auth,
                           headers={"Origin": "http://testserver"},
                           follow_redirects=False) # TestClient uses testserver as default host
    assert response.status_code == 303
