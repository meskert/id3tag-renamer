"""Tag management routes."""
from typing import List, Optional
from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from ..config import config
from ..dependencies import require_user
from ..services import get_files_data


router = APIRouter()
templates = Jinja2Templates(directory=config.TEMPLATE_DIR)


def get_manager():
    """Get the global MusicManager instance."""
    from ..web import manager

    return manager


@router.get("/update_tags")
async def update_tags_get(username: str = Depends(require_user)):
    """Redirect GET requests to update_tags back to home."""
    return RedirectResponse(url="/", status_code=303)


@router.post("/update_tags")
async def update_tags(
    request: Request,
    artist: Optional[str] = Form(None),
    album: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    track: Optional[str] = Form(None),
    genre: Optional[str] = Form(None),
    date: Optional[str] = Form(None),
    comment: Optional[str] = Form(None),
    new_filename: Optional[str] = Form(None),
    album_art: Optional[UploadFile] = File(None),
    selected_files: List[int] = Form(default=[]),
    clear_tags: List[str] = Form(default=[]),
    direct_apply: bool = Form(False),
    username: str = Depends(require_user),
):
    """Update tags for selected files."""
    manager = get_manager()

    if not manager.directory:
        return RedirectResponse(url="/", status_code=303)

    # Get selected files
    if not selected_files:
        return RedirectResponse(url="/", status_code=303)

    files_to_process = [
        manager.files[i] for i in selected_files if i < len(manager.files)
    ]

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

    if album_art and album_art.filename:
        content = await album_art.read()
        if content:
            tags["album_art"] = content

    manager.update_tags(tags, files_to_process, clear_tags=clear_tags)

    # Handle filename rename if provided (for single file edits)
    if new_filename and len(files_to_process) == 1:
        music_file = files_to_process[0]
        current_stem = music_file.path.stem

        # Only add rename change if filename actually changed
        if new_filename != current_stem:
            new_path = music_file.path.parent / (new_filename + music_file.path.suffix)
            manager._pending_changes.append({
                "type": "rename",
                "old_path": music_file.path,
                "new_path": new_path
            })

    if direct_apply:
        manager.apply(dry_run=False)
        manager.scan()
        files_data = get_files_data(manager)
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "directory": str(manager.directory),
                "files": files_data,
                "changes": [],
                "mode": "manual",
                "selected_indices": [],
                "music_root": str(config.DEFAULT_MUSIC_DIR),
            },
        )

    changes = manager.apply(dry_run=True)

    files_data = get_files_data(manager)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "directory": str(manager.directory),
            "files": files_data,
            "changes": changes,
            "mode": "manual",
            "selected_indices": selected_files,
            "music_root": str(config.DEFAULT_MUSIC_DIR),
            "artist": artist,
            "album": album,
            "title": title,
            "track": track,
            "genre": genre,
            "date": date,
            "comment": comment,
            "clear_tags": clear_tags,
        },
    )
