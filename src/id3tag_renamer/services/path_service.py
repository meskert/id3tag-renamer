"""Path safety and validation service."""
import os
from pathlib import Path
from ..config import config


def get_safe_path(path_str: str) -> Path:
    """
    Ensure a path is within the DEFAULT_MUSIC_DIR.

    Args:
        path_str: Path string (relative or absolute)

    Returns:
        Path object guaranteed to be within DEFAULT_MUSIC_DIR
    """
    root = Path(config.DEFAULT_MUSIC_DIR).resolve()

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
