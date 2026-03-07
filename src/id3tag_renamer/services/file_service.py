"""File data management service."""
from pathlib import Path
from typing import List, Dict, Any
from ..config import config


def get_files_data(manager) -> List[Dict[str, Any]]:
    """
    Extract file data from MusicManager for display.

    Args:
        manager: MusicManager instance

    Returns:
        List of dictionaries containing file information and tags
    """
    files_data = []
    root = Path(config.DEFAULT_MUSIC_DIR).resolve()

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
