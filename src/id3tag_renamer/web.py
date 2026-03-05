from fastapi import FastAPI, Request, Form, BackgroundTasks, Depends, HTTPException, status, UploadFile, File, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
import os
import secrets
from id3tag_renamer import MusicManager
import uvicorn
from typing import Optional, List

app = FastAPI(title="ID3Tag-Renamer")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
security = HTTPBasic()

# Authentication configuration
WEB_USERNAME = os.getenv("WEB_USERNAME")
WEB_PASSWORD = os.getenv("WEB_PASSWORD")

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    # If no credentials are set in environment, anyone can access (or maybe block?
    # User said they "can be provided", implying they're optional or expected.
    # Usually, if we want login, they must be set.
    if not WEB_USERNAME or not WEB_PASSWORD:
        # For security, we should probably require them if this is exposed.
        # But if the user didn't set them, we'll allow access for now, as before.
        return credentials.username

    is_correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"), WEB_USERNAME.encode("utf8")
    )
    is_correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"), WEB_PASSWORD.encode("utf8")
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Default music directory for Docker environment
DEFAULT_MUSIC_DIR = os.getenv("MUSIC_DIR", "/music")

def _get_files_data():
    files_data = []
    root = Path(DEFAULT_MUSIC_DIR).resolve()
    for i, f in enumerate(manager.files):
        try:
            rel_path = str(f.path.parent.relative_to(manager.directory))
            if rel_path == ".":
                rel_path = ""
        except ValueError:
            rel_path = ""

        try:
            root_rel_path = str(f.path.parent.relative_to(root))
            if root_rel_path == ".":
                root_rel_path = ""
        except ValueError:
            root_rel_path = str(f.path.parent)

        data = {
            "index": i,
            "name": f.path.name,
            "rel_path": rel_path,
            "root_rel_path": root_rel_path,
        }
        for tag in f.get_supported_tags():
            tag_value = f.get_tag(tag)
            data[tag] = tag_value
            # Debug print for first file only
            if i == 0:
                print(f"File {f.path.name}: {tag} = {repr(tag_value)}")

        files_data.append(data)
    return files_data

manager = MusicManager(directory=None)

def get_safe_path(path_str: str) -> Path:
    """Helper to ensure a path is within the DEFAULT_MUSIC_DIR."""
    root = Path(DEFAULT_MUSIC_DIR).resolve()
    # Handle both relative and absolute paths by anchoring to root
    if os.path.isabs(path_str):
        # If absolute, it MUST start with root
        try:
            target = Path(path_str).resolve()
        except Exception:
            return root
    else:
        # If relative, anchor to root
        target = (root / path_str.lstrip("/")).resolve()
    
    if not str(target).startswith(str(root)):
        return root
    return target

# Middleware to protect against CSRF for state-changing requests
@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        # Check Origin and Referer for basic CSRF protection
        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")
        host = request.headers.get("Host")
        
        # In a real-world scenario with reverse proxy, we'd need to be more careful
        # about what the expected Origin/Referer is. 
        # For now, we'll check if it's the same host if provided.
        if origin and host not in origin:
             return Response("CSRF Forbidden: Origin mismatch", status_code=403)
        elif not origin and referer and host not in referer:
             return Response("CSRF Forbidden: Referer mismatch", status_code=403)
             
    return await call_next(request)

@app.post("/scan")
async def scan_dir(
    directory: str = Form(""), 
    mode: str = Form("rename"),
    username: str = Depends(get_current_username)
):
    if not directory or directory.strip() == "":
        manager.directory = None
        manager.files = []
        return RedirectResponse(url=f"/?mode={mode}", status_code=303)
        
    manager.directory = get_safe_path(directory)
    manager.scan()
    return RedirectResponse(url=f"/?mode={mode}", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, mode: str = "rename", username: str = Depends(get_current_username)):
    # No automatic scan on load
    
    files_data = _get_files_data()
        
    return templates.TemplateResponse(request, "index.html", {
        "directory": str(manager.directory) if manager.directory else "",
        "files": files_data,
        "pending": [],
        "mode": mode,
        "music_root": str(DEFAULT_MUSIC_DIR)
    })

@app.get("/preview")
async def preview_get(username: str = Depends(get_current_username)):
    """Redirect GET requests to preview back to home"""
    return RedirectResponse(url="/", status_code=303)

@app.post("/preview")
async def preview(
    request: Request,
    pattern: str = Form(...),
    mode: str = Form("rename"),
    selected_files: List[int] = Form(default=[]),
    username: str = Depends(get_current_username)
):
    if not manager.directory:
        return RedirectResponse(url="/", status_code=303)

    # manager.scan()  # Removed automatic scan on preview

    # Get selected files or None for all files
    files_to_process = None
    if selected_files:
        files_to_process = [manager.files[i] for i in selected_files if i < len(manager.files)]

    if mode == "rename":
        manager.rename_from_tags(pattern, files_to_process)
    else:
        manager.tag_from_path(pattern, files_to_process)

    changes = manager.apply(dry_run=True)

    # Enrich changes with root_rel_path
    root = Path(DEFAULT_MUSIC_DIR).resolve()
    for change in changes:
        path = change.get('old_path', change.get('path'))
        try:
            path_obj = Path(path)
            root_rel_path = str(path_obj.parent.relative_to(root))
            if root_rel_path == ".": root_rel_path = ""
        except ValueError:
            root_rel_path = str(Path(path).parent)

        change['root_rel_path'] = root_rel_path

    files_data = _get_files_data()

    return templates.TemplateResponse(request, "index.html", {
        "directory": str(manager.directory),
        "files": files_data,
        "changes": changes,
        "pattern": pattern,
        "mode": mode,
        "selected_indices": selected_files,  # Pass selected indices to template
        "music_root": str(DEFAULT_MUSIC_DIR)
    })

@app.get("/apply")
async def apply_get(username: str = Depends(get_current_username)):
    """Redirect GET requests to apply back to home"""
    return RedirectResponse(url="/", status_code=303)

@app.post("/apply")
async def apply_changes(
    request: Request,
    pattern: str = Form(""),
    mode: str = Form("rename"),
    selected_files: List[int] = Form(default=[]),
    artist: Optional[str] = Form(None),
    album: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    track: Optional[str] = Form(None),
    genre: Optional[str] = Form(None),
    date: Optional[str] = Form(None),
    comment: Optional[str] = Form(None),
    username: str = Depends(get_current_username)
):
    if not manager.directory:
        return RedirectResponse(url="/", status_code=303)

    # Get selected files or None for all files
    files_to_process = None
    if selected_files:
        files_to_process = [manager.files[i] for i in selected_files if i < len(manager.files)]

    if mode == "rename":
        manager.rename_from_tags(pattern, files_to_process)
    elif mode == "tag":
        manager.tag_from_path(pattern, files_to_process)
    elif mode == "manual":
        # For manual mode, if we lost the pending changes, we can reconstruct them
        # (excluding album art which is binary and not easily passed via hidden form field)
        if not manager._pending_changes:
            tags = {}
            if artist: tags["artist"] = artist
            if album: tags["album"] = album
            if title: tags["title"] = title
            if track: tags["track"] = track
            if genre: tags["genre"] = genre
            if date: tags["date"] = date
            if comment: tags["comment"] = comment
            if tags:
                manager.update_tags(tags, files_to_process)

    manager.apply(dry_run=False)
    
    # After apply, we want to stay on the same page with the same mode
    # Rescan to reflect the changes (e.g. new file names or updated tags)
    manager.scan()
    files_data = _get_files_data()
        
    return templates.TemplateResponse(request, "index.html", {
        "directory": str(manager.directory),
        "files": files_data,
        "pattern": pattern,
        "mode": mode,
        "music_root": str(DEFAULT_MUSIC_DIR)
    })

@app.get("/update_tags")
async def update_tags_get(username: str = Depends(get_current_username)):
    """Redirect GET requests to update_tags back to home"""
    return RedirectResponse(url="/", status_code=303)

@app.post("/update_tags")
async def update_tags(
    request: Request,
    artist: Optional[str] = Form(None),
    album: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    track: Optional[str] = Form(None),
    genre: Optional[str] = Form(None),
    date: Optional[str] = Form(None),
    comment: Optional[str] = Form(None),
    album_art: Optional[UploadFile] = File(None),
    selected_files: List[int] = Form(default=[]),
    username: str = Depends(get_current_username)
):
    if not manager.directory:
        return RedirectResponse(url="/", status_code=303)

    # Get selected files
    if not selected_files:
         return RedirectResponse(url="/", status_code=303)
    
    files_to_process = [manager.files[i] for i in selected_files if i < len(manager.files)]

    tags = {}
    if artist: tags["artist"] = artist
    if album: tags["album"] = album
    if title: tags["title"] = title
    if track: tags["track"] = track
    if genre: tags["genre"] = genre
    if date: tags["date"] = date
    if comment: tags["comment"] = comment

    if album_art and album_art.filename:
        content = await album_art.read()
        if content:
            tags["album_art"] = content

    manager.update_tags(tags, files_to_process)
    changes = manager.apply(dry_run=True)

    files_data = _get_files_data()

    return templates.TemplateResponse(request, "index.html", {
        "directory": str(manager.directory),
        "files": files_data,
        "changes": changes,
        "mode": "manual",
        "selected_indices": selected_files,
        "music_root": str(DEFAULT_MUSIC_DIR),
        "artist": artist,
        "album": album,
        "title": title,
        "track": track,
        "genre": genre,
        "date": date,
        "comment": comment
    })

@app.get("/api/directories")
async def list_directories(
    path: str = "",
    username: str = Depends(get_current_username)
):
    """
    List directories within the MUSIC_DIR root.
    Path is relative to DEFAULT_MUSIC_DIR.
    """
    root = Path(DEFAULT_MUSIC_DIR).resolve()
    target = get_safe_path(path)

    if not target.is_dir():
        # Fallback to root relative path if target is not a directory
        rel_to_root = ""
        try:
             rel_to_root = str(target.relative_to(root))
             if rel_to_root == ".": rel_to_root = ""
        except ValueError:
             pass
        return {"directories": [], "current_path": rel_to_root}

    directories = []
    # Add parent directory if not at root
    if target != root:
        directories.append({
            "name": "..",
            "path": str(target.parent.relative_to(root)) if target.parent != root else ""
        })

    for item in sorted(target.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            directories.append({
                "name": item.name,
                "path": str(item.relative_to(root))
            })

    return {
        "directories": directories,
        "current_path": str(target.relative_to(root)) if target != root else "",
        "full_path": str(target)
    }

@app.get("/album_art/{index}")
async def get_album_art(index: int, username: str = Depends(get_current_username)):
    if index < 0 or index >= len(manager.files):
        raise HTTPException(status_code=404, detail="File not found")
    
    music_file = manager.files[index]
    art_data = music_file.get_album_art()
    
    if not art_data:
        raise HTTPException(status_code=404, detail="No album art found")
        
    # Detect mime type
    mime = "image/jpeg"
    if art_data.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
        
    return Response(content=art_data, media_type=mime)

def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    # proxy_headers=True is important when running behind a reverse proxy
    uvicorn.run(app, host=host, port=port, proxy_headers=True, forwarded_allow_ips="*")

if __name__ == "__main__":
    main()
