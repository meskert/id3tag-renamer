"""API routes for AJAX requests."""
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import Response
from pydantic import BaseModel
from ..config import config
from ..dependencies import require_user
from ..services import get_safe_path
from ..services.metadata_service import MetadataLookupService


router = APIRouter(prefix="/api")


def get_manager():
    """Get the global MusicManager instance."""
    from ..web import manager

    return manager


@router.get("/directories")
async def list_directories(path: str = "", username: str = Depends(require_user)):
    """
    List directories within the MUSIC_DIR root.

    Args:
        path: Path relative to DEFAULT_MUSIC_DIR

    Returns:
        Dictionary with directories list and current path
    """
    root = Path(config.DEFAULT_MUSIC_DIR).resolve()
    target = get_safe_path(path)

    if not target.is_dir():
        # Fallback to root relative path if target is not a directory
        rel_to_root = ""
        try:
            rel_to_root = str(target.relative_to(root))
            if rel_to_root == ".":
                rel_to_root = ""
        except ValueError:
            pass
        return {"directories": [], "current_path": rel_to_root}

    directories = []
    # Add parent directory if not at root
    if target != root:
        directories.append(
            {
                "name": "..",
                "path": str(target.parent.relative_to(root))
                if target.parent != root
                else "",
            }
        )

    for item in sorted(target.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            directories.append({"name": item.name, "path": str(item.relative_to(root))})

    return {
        "directories": directories,
        "current_path": str(target.relative_to(root)) if target != root else "",
        "full_path": str(target),
    }


@router.get("/album_art/{index}")
async def get_album_art(index: int, username: str = Depends(require_user)):
    """
    Get album art for a specific file.

    Args:
        index: File index in the manager's file list

    Returns:
        Image data as response
    """
    manager = get_manager()

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


class LookupRequest(BaseModel):
    """Request model for metadata lookup."""
    file_indices: List[int]
    use_fingerprint: bool = True


class ApplyMetadataRequest(BaseModel):
    """Request model for applying metadata to multiple files."""
    updates: List[dict]  # List of {index: int, tags: dict}
    apply_directly: bool = False


@router.post("/apply_metadata")
async def apply_metadata(
    request: ApplyMetadataRequest = Body(...),
    username: str = Depends(require_user)
):
    """
    Apply metadata to multiple files.

    Args:
        request: ApplyMetadataRequest with file indices and tags

    Returns:
        Dictionary with status and message
    """
    manager = get_manager()

    if not manager.files:
        raise HTTPException(status_code=400, detail="No files loaded")

    # Clear any previous pending changes
    manager._pending_changes = []

    for update in request.updates:
        index = update.get("index")
        tags = update.get("tags")

        if index is None or tags is None:
            continue

        if index < 0 or index >= len(manager.files):
            continue

        music_file = manager.files[index]
        
        # We want to accumulate changes for all files
        # update_tags clears _pending_changes by default, so we need to be careful
        # Let's use a temporary list to store all changes and then set it to manager._pending_changes
        
        # Calculate changes for this file
        changes = {}
        for key, value in tags.items():
            if not value:
                continue
            
            old_value = music_file.get_tag(key)
            if old_value != value:
                changes[key] = value
        
        if changes:
            manager._pending_changes.append({
                "type": "tag",
                "path": music_file.path,
                "changes": changes,
                "raw_tags": tags
            })

    return {"status": "success", "message": f"Updated {len(request.updates)} files"}


@router.post("/lookup_metadata")
async def lookup_metadata(
    request: LookupRequest = Body(...),
    username: str = Depends(require_user)
):
    """
    Lookup metadata for selected files using online sources.

    Args:
        request: LookupRequest with file indices and lookup options

    Returns:
        Dictionary with lookup results for each file
    """
    manager = get_manager()

    if not manager.files:
        raise HTTPException(status_code=400, detail="No files loaded")

    results = []

    for index in request.file_indices:
        if index < 0 or index >= len(manager.files):
            results.append({
                "index": index,
                "error": "Invalid file index",
                "matches": []
            })
            continue

        music_file = manager.files[index]

        # Get existing tags
        existing_tags = {
            "artist": music_file.get_tag("artist"),
            "album": music_file.get_tag("album"),
            "title": music_file.get_tag("title"),
            "track": music_file.get_tag("track"),
            "genre": music_file.get_tag("genre"),
            "date": music_file.get_tag("date"),
        }

        try:
            # Perform lookup
            matches = MetadataLookupService.lookup_file(
                music_file.path,
                existing_tags,
                use_fingerprint=request.use_fingerprint
            )

            # Check if fingerprinting was requested but no matches found
            warning = None
            if request.use_fingerprint and len(matches) == 0 and existing_tags.get("artist"):
                warning = "Acoustic fingerprinting unavailable. Install chromaprint (fpcalc) for better accuracy."

            results.append({
                "index": index,
                "filename": music_file.path.name,
                "existing_tags": existing_tags,
                "matches": [match.to_dict() for match in matches],
                "warning": warning,
                "error": None
            })

        except Exception as e:
            results.append({
                "index": index,
                "filename": music_file.path.name,
                "existing_tags": existing_tags,
                "matches": [],
                "warning": None,
                "error": str(e)
            })

    return {"results": results}
