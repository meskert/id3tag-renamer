"""File scanning and manipulation routes."""
from typing import List
from pathlib import Path
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ..config import config
from ..dependencies import require_user
from ..services import get_files_data, get_safe_path


router = APIRouter()
templates = Jinja2Templates(directory=config.TEMPLATE_DIR)


def get_manager():
    """Get the global MusicManager instance."""
    from ..web import manager

    return manager


@router.post("/scan")
async def scan_dir(
    directory: str = Form(""),
    mode: str = Form("rename"),
    username: str = Depends(require_user),
):
    """Scan a directory for music files."""
    manager = get_manager()

    if not directory or directory.strip() == "":
        manager.directory = None
        manager.files = []
        return RedirectResponse(url=f"/?mode={mode}", status_code=303)

    manager.directory = get_safe_path(directory)
    manager.scan()
    return RedirectResponse(url=f"/?mode={mode}", status_code=303)


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    mode: str = "rename",
    selected: str = None,
    preview: bool = False,
    username: str = Depends(require_user),
):
    """Display main page with file list."""
    manager = get_manager()
    files_data = get_files_data(manager)

    changes = []
    selected_indices = []
    if selected:
        try:
            selected_indices = [int(i) for i in selected.split(",")]
        except ValueError:
            pass

    if preview and selected_indices:
        changes = manager.apply(dry_run=True)

        # Enrich changes with root_rel_path
        root = Path(config.DEFAULT_MUSIC_DIR).resolve()
        for change in changes:
            path_val = change.get("old_path", change.get("path"))
            try:
                path_obj = Path(str(path_val))
                root_rel_path = str(path_obj.parent.relative_to(root))
                if root_rel_path == ".":
                    root_rel_path = ""
            except ValueError:
                root_rel_path = str(Path(str(path_val)).parent)

            change["root_rel_path"] = root_rel_path

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "directory": str(manager.directory) if manager.directory else "",
            "files": files_data,
            "changes": changes,
            "mode": mode,
            "selected_indices": selected_indices,
            "music_root": str(config.DEFAULT_MUSIC_DIR),
        },
    )


@router.get("/preview")
async def preview_get(username: str = Depends(require_user)):
    """Redirect GET requests to preview back to home."""
    return RedirectResponse(url="/", status_code=303)


@router.post("/preview")
async def preview(
    request: Request,
    pattern: str = Form(...),
    mode: str = Form("rename"),
    selected_files: List[int] = Form(default=[]),
    username: str = Depends(require_user),
):
    """Preview changes before applying them."""
    manager = get_manager()

    if not manager.directory:
        return RedirectResponse(url="/", status_code=303)

    # Get selected files or None for all files
    files_to_process = None
    if selected_files:
        files_to_process = [
            manager.files[i] for i in selected_files if i < len(manager.files)
        ]

    if mode == "rename":
        manager.rename_from_tags(pattern, files_to_process)
    else:
        manager.tag_from_path(pattern, files_to_process)

    changes = manager.apply(dry_run=True)

    # Enrich changes with root_rel_path
    root = Path(config.DEFAULT_MUSIC_DIR).resolve()
    for change in changes:
        path = change.get("old_path", change.get("path"))
        try:
            path_obj = Path(path)
            root_rel_path = str(path_obj.parent.relative_to(root))
            if root_rel_path == ".":
                root_rel_path = ""
        except ValueError:
            root_rel_path = str(Path(path).parent)

        change["root_rel_path"] = root_rel_path

    files_data = get_files_data(manager)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "directory": str(manager.directory),
            "files": files_data,
            "changes": changes,
            "pattern": pattern,
            "mode": mode,
            "selected_indices": selected_files,
            "music_root": str(config.DEFAULT_MUSIC_DIR),
        },
    )


@router.get("/apply")
async def apply_get(username: str = Depends(require_user)):
    """Redirect GET requests to apply back to home."""
    return RedirectResponse(url="/", status_code=303)


@router.post("/apply")
async def apply_changes(
    request: Request,
    pattern: str = Form(""),
    mode: str = Form("rename"),
    selected_files: List[int] = Form(default=[]),
    artist: str = Form(None),
    album: str = Form(None),
    title: str = Form(None),
    track: str = Form(None),
    genre: str = Form(None),
    date: str = Form(None),
    comment: str = Form(None),
    clear_tags: List[str] = Form(default=[]),
    username: str = Depends(require_user),
):
    """Apply changes to files."""
    manager = get_manager()

    if not manager.directory:
        return RedirectResponse(url="/", status_code=303)

    # Get selected files or None for all files
    files_to_process = None
    if selected_files:
        files_to_process = [
            manager.files[i] for i in selected_files if i < len(manager.files)
        ]

    if mode == "rename":
        manager.rename_from_tags(pattern, files_to_process)
    elif mode == "tag":
        manager.tag_from_path(pattern, files_to_process)
    elif mode == "manual":
        # For manual mode, if we lost the pending changes, we can reconstruct them
        # (excluding album art which is binary and not easily passed via hidden form field)
        if not manager._pending_changes:
            tags = {}
            if artist:
                tags["artist"] = artist
            if album:
                tags["album"] = album
            if title:
                tags["title"] = title
            if track:
                tags["track"] = track
            if genre:
                tags["genre"] = genre
            if date:
                tags["date"] = date
            if comment:
                tags["comment"] = comment
            if tags or clear_tags:
                manager.update_tags(tags, files_to_process, clear_tags=clear_tags)

    manager.apply(dry_run=False)

    # After apply, we want to stay on the same page with the same mode
    # Rescan to reflect the changes (e.g. new file names or updated tags)
    manager.scan()
    files_data = get_files_data(manager)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "directory": str(manager.directory),
            "files": files_data,
            "pattern": pattern,
            "mode": mode,
            "music_root": str(config.DEFAULT_MUSIC_DIR),
        },
    )
