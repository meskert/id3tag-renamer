"""API routes for AJAX requests."""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from ..config import config
from ..dependencies import require_user
from ..services import get_safe_path


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
