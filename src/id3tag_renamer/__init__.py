from typing import List, Optional, Callable
import os
import re
from pathlib import Path
import mutagen

class MusicFile:
    """Represents a single music file and its tags."""
    def __init__(self, path: Path):
        self.path = path
        try:
            self.tags = mutagen.File(str(path))
        except Exception:
            self.tags = None

    def get_supported_tags(self) -> List[str]:
        """Returns a list of supported tag names."""
        # Standard ID3 tags: artist, album, title, track, genre, date, comment
        return ["artist", "album", "title", "track", "genre", "date", "comment"]

    def get_tag(self, key: str) -> str:
        """Helper to get tag value as string."""
        if not self.tags:
            return ""

        # Mapping common keys
        mapping = {
            "artist": ["TPE1", "artist", "\xa9ART", "Artist"],
            "album": ["TALB", "album", "\xa9ALB", "Album"],
            "title": ["TIT2", "title", "\xa9NAM", "Title"],
            "track": ["TRCK", "tracknumber", "trkn", "TrackNumber"],
            "genre": ["TCON", "genre", "\xa9GEN", "Genre"],
            "date": ["TDRC", "TYER", "date", "\xa9DAY", "Date", "Year"],
            "comment": ["description", "DESCRIPTION", "comment", "COMMENT", "COMM", "\xa9CMT", "Comment"],
        }

        keys = mapping.get(key, [key])
        for k in keys:
            try:
                # Special handling for COMM frame in ID3
                if k == "COMM":
                    for frame in self.tags.getall("COMM"):
                        return str(frame.text[0])
                
                if k in self.tags:
                    val = self.tags[k]
                    if isinstance(val, list):
                        if len(val) > 0:
                            return str(val[0])
                        return ""
                    return str(val)
            except (ValueError, KeyError, Exception):
                continue
        return ""

    def set_tag(self, key: str, value: str):
        """Helper to set tag value."""
        if not self.tags:
            return

        # Album art is handled by set_album_art
        if key == "album_art":
            self.set_album_art(value)
            return

        # Mapping common keys
        mapping = {
            "artist": ["TPE1", "artist", "\xa9ART", "Artist"],
            "album": ["TALB", "album", "\xa9ALB", "Album"],
            "title": ["TIT2", "title", "\xa9NAM", "Title"],
            "track": ["TRCK", "tracknumber", "trkn", "TrackNumber"],
            "genre": ["TCON", "genre", "\xa9GEN", "Genre"],
            "date": ["TDRC", "date", "\xa9DAY", "Date"],
            "comment": ["description", "DESCRIPTION", "comment", "COMMENT", "COMM", "\xa9CMT", "Comment"],
        }

        keys = mapping.get(key, [key])

        # Special handling for ID3 (mp3)
        import mutagen.id3
        import mutagen.mp3
        if isinstance(self.tags, (mutagen.id3.ID3, mutagen.mp3.MP3)):
            tags_obj = self.tags if isinstance(self.tags, mutagen.id3.ID3) else self.tags.tags
            if tags_obj is None:
                if hasattr(self.tags, "add_tags"):
                    self.tags.add_tags()
                    tags_obj = self.tags.tags
                else:
                    return

            for k in keys:
                if k in ["TPE1", "TALB", "TIT2", "TRCK", "TCON", "TDRC"]:
                    frame_class = getattr(mutagen.id3, k)
                    tags_obj.setall(k, [frame_class(encoding=3, text=[value])])
                    return
                elif k == "COMM":
                    tags_obj.delall("COMM")
                    tags_obj.add(mutagen.id3.COMM(encoding=3, lang="eng", desc="", text=[value]))
                    return

        # For other formats (FLAC, M4A) or if above didn't return
        for k in keys:
            try:
                # For FLAC/Vorbis, keys are often lowercase and value is a list of strings
                if hasattr(self.tags, "tags") and hasattr(self.tags.tags, "vendor"): # Likely Vorbis/FLAC
                    self.tags[k] = [value]
                else:
                    self.tags[k] = value
                return
            except (ValueError, KeyError, Exception):
                continue

        # If not found, add the first supported key for this format (guard against invalid keys)
        try:
            self.tags[keys[0]] = value
        except (ValueError, KeyError, Exception):
            # Common Vorbis convention is lowercase keys
            try:
                self.tags[str(keys[0]).lower()] = value
            except Exception:
                return

    def set_album_art(self, image_data: bytes):
        """Set album art for the file."""
        if not self.tags:
            return

        import mutagen.id3
        import mutagen.mp3
        import mutagen.flac
        import mutagen.mp4

        # Detect image type
        mime = "image/jpeg"
        if image_data.startswith(b"\x89PNG\r\n\x1a\n"):
            mime = "image/png"

        # MP3 (ID3)
        if isinstance(self.tags, (mutagen.id3.ID3, mutagen.mp3.MP3)):
            tags_obj = self.tags if isinstance(self.tags, mutagen.id3.ID3) else self.tags.tags
            if tags_obj is None:
                if hasattr(self.tags, "add_tags"):
                    self.tags.add_tags()
                    tags_obj = self.tags.tags
                else:
                    return

            # Remove old APIC frames
            tags_obj.delall("APIC")
            tags_obj.add(
                mutagen.id3.APIC(
                    encoding=3,
                    mime=mime,
                    type=3,  # cover front
                    desc="Front Cover",
                    data=image_data,
                )
            )

        # FLAC (Vorbis comments)
        elif isinstance(self.tags, mutagen.flac.FLAC):
            picture = mutagen.flac.Picture()
            picture.data = image_data
            picture.type = 3
            picture.mime = mime
            picture.desc = "Front Cover"

            self.tags.clear_pictures()
            self.tags.add_picture(picture)

        # M4A (MP4)
        elif isinstance(self.tags, mutagen.mp4.MP4):
            cover_format = mutagen.mp4.AtomDataType.JPEG
            if mime == "image/png":
                cover_format = mutagen.mp4.AtomDataType.PNG

            try:
                self.tags["covr"] = [mutagen.mp4.MP4Cover(image_data, imageformat=cover_format)]
            except Exception:
                pass

    def get_album_art(self) -> Optional[bytes]:
        """Extract album art from the file."""
        if not self.tags:
            return None

        import mutagen.id3
        import mutagen.mp3
        import mutagen.flac
        import mutagen.mp4

        # MP3 (ID3)
        if isinstance(self.tags, (mutagen.id3.ID3, mutagen.mp3.MP3)):
            tags_obj = self.tags if isinstance(self.tags, mutagen.id3.ID3) else self.tags.tags
            if tags_obj:
                for frame in tags_obj.getall("APIC"):
                    return frame.data

        # FLAC
        elif isinstance(self.tags, mutagen.flac.FLAC):
            if self.tags.pictures:
                return self.tags.pictures[0].data

        # M4A
        elif isinstance(self.tags, mutagen.mp4.MP4):
            if "covr" in self.tags:
                return bytes(self.tags["covr"][0])

        return None

    def save_tags(self):
        """Save changes to the file."""
        if self.tags:
            try:
                self.tags.save()
            except Exception:
                pass

    def __repr__(self):
        return f"MusicFile({self.path})"

class MusicManager:
    """Core class for manipulating music files."""
    def __init__(self, directory: Optional[str] = None):
        self.directory = Path(directory) if directory else None
        self.files: List[MusicFile] = []
        self._pending_changes = []

    def scan(self, recursive: bool = True):
        """Scan directory for music files."""
        if not self.directory or not self.directory.is_dir():
            return

        self.files = []
        extensions = ('.mp3', '.flac', '.m4a')
        
        if recursive:
            iterator = self.directory.rglob('*')
        else:
            iterator = self.directory.glob('*')
            
        for path in iterator:
            if path.suffix.lower() in extensions:
                self.files.append(MusicFile(path))

    def _process_pattern(self, pattern: str, music_file: 'MusicFile') -> str:
        """Process pattern with support for slicing on any tag."""
        import re

        # Pattern to match any tag with optional slice notation: {tagname} or {tagname[start:end]}
        tag_pattern = r'\{(\w+)(?:\[(-?\d*):?(-?\d*)\])?\}'

        # Get tag values
        tag_values = {
            'filename': music_file.path.stem,
        }
        for tag in music_file.get_supported_tags():
            tag_values[tag] = music_file.get_tag(tag) or f"Unknown {tag.capitalize()}"
        
        # Override some defaults if they are empty
        if not tag_values.get('artist') or tag_values['artist'] == "Unknown Artist":
            tag_values['artist'] = "Unknown Artist"
        if not tag_values.get('album') or tag_values['album'] == "Unknown Album":
            tag_values['album'] = "Unknown Album"
        if not tag_values.get('title') or tag_values['title'] == f"Unknown Title":
            tag_values['title'] = music_file.path.stem
        if not tag_values.get('track') or tag_values['track'] == "Unknown Track":
            tag_values['track'] = "00"

        def replace_tag(match):
            tag_name = match.group(1)
            start_str = match.group(2)
            end_str = match.group(3)

            # Get the tag value
            value = tag_values.get(tag_name, f"{{{tag_name}}}")

            # No slice notation, return full value
            if start_str is None and end_str is None:
                return value

            # Parse start and end indices
            start = int(start_str) if start_str else None
            end = int(end_str) if end_str else None

            # Apply Python slicing
            return value[start:end]

        # Replace all tag patterns with slicing support
        return re.sub(tag_pattern, replace_tag, pattern)

    def rename_from_tags(self, pattern: str, selected_files: Optional[List[MusicFile]] = None):
        """Plan renaming files based on a tag pattern.

        Args:
            pattern: The rename pattern to use
            selected_files: List of files to rename. If None, all files are renamed.
        """
        self._pending_changes = []
        files_to_process = selected_files if selected_files is not None else self.files

        for music_file in files_to_process:
            new_name = self._process_pattern(pattern, music_file)

            # Ensure extension is kept
            if not new_name.endswith(music_file.path.suffix):
                new_name += music_file.path.suffix

            # Use relative path if pattern doesn't specify absolute one
            # and make it relative to the directory being scanned
            new_path = self.directory / new_name
            if new_path != music_file.path:
                self._pending_changes.append({
                    "type": "rename",
                    "old_path": music_file.path,
                    "new_path": new_path
                })

    def tag_from_path(self, mask: str, selected_files: Optional[List[MusicFile]] = None):
        """Plan updating tags based on a file path mask.
        
        Mask format examples: 
        %artist%/%title%
        %artist% - %title%
        """
        self._pending_changes = []
        files_to_process = selected_files if selected_files is not None else self.files

        # Escape special regex characters in mask except for %tag%
        # Convert %tag% to named capturing group (?P<tag>.*)
        regex_pattern = re.escape(mask)
        # We need to unescape the % signs and the tags
        # re.escape makes %artist% -> \%artist\%
        regex_pattern = regex_pattern.replace(r'\%', '%')
        
        supported_tags = MusicFile(None).get_supported_tags()
        for tag in supported_tags:
            regex_pattern = regex_pattern.replace(f'%{tag}%', f'(?P<{tag}>.+?)')
        
        # Ensure it matches the whole string or at least the relevant part from the end
        # We'll match against the relative path from the scanned directory
        regex_pattern = regex_pattern + '$'
        
        try:
            # Add basic timeout/complexity check could be hard with re module
            # but at least we can catch errors
            regex = re.compile(regex_pattern)
        except (re.error, OverflowError):
            # Fallback or error handling
            return

        for music_file in files_to_process:
            # Get relative path from the root directory
            try:
                rel_path = str(music_file.path.relative_to(self.directory))
            except ValueError:
                rel_path = music_file.path.name
            
            # Remove extension for matching if mask doesn't have it
            if not mask.endswith(music_file.path.suffix):
                match_path = rel_path[:-len(music_file.path.suffix)]
            else:
                match_path = rel_path

            match = regex.search(match_path)
            if match:
                new_tags = match.groupdict()
                changes = {}
                for tag, value in new_tags.items():
                    old_value = music_file.get_tag(tag)
                    if old_value != value:
                        changes[tag] = value
                
                if changes:
                    self._pending_changes.append({
                        "type": "tag",
                        "path": music_file.path,
                        "changes": changes
                    })

    def update_tags(self, tags: dict, selected_files: Optional[List[MusicFile]] = None):
        """Plan manual tag updates.
        
        Args:
            tags: Dictionary of tag keys and values to set.
            selected_files: List of MusicFile objects to update.
        """
        self._pending_changes = []
        files_to_process = selected_files if selected_files is not None else self.files

        for music_file in files_to_process:
            changes = {}
            for key, value in tags.items():
                if not value and key != "album_art":
                    continue
                
                if key == "album_art":
                    # For album art, we just indicate it's being updated
                    changes[key] = "<binary data>"
                else:
                    old_value = music_file.get_tag(key)
                    if old_value != value:
                        changes[key] = value
            
            if changes:
                self._pending_changes.append({
                    "type": "tag",
                    "path": music_file.path,
                    "changes": changes,
                    "raw_tags": tags # Store raw tags to use during apply (e.g. for binary data)
                })

    def remove_substring_from_filenames(self, start_pos: int, length: int):
        """Plan removing a substring from filenames by position.

        Args:
            start_pos: Starting position (0-based). Negative values count from the end.
            length: Number of characters to remove.
        """
        self._pending_changes = []
        for music_file in self.files:
            old_filename = music_file.path.stem

            # Handle negative indexing
            if start_pos < 0:
                actual_start = len(old_filename) + start_pos
            else:
                actual_start = start_pos

            # Ensure we don't go out of bounds
            if actual_start < 0:
                actual_start = 0
            if actual_start >= len(old_filename):
                continue

            # Remove the substring
            new_filename = old_filename[:actual_start] + old_filename[actual_start + length:]

            # Clean up multiple spaces and trim
            new_filename = ' '.join(new_filename.split()).strip()

            if new_filename and new_filename != old_filename:
                new_path = music_file.path.parent / (new_filename + music_file.path.suffix)
                if new_path != music_file.path:
                    self._pending_changes.append({
                        "type": "rename",
                        "old_path": music_file.path,
                        "new_path": new_path
                    })

    def apply(self, dry_run: bool = True, callback: Optional[Callable] = None):
        """Execute the planned changes."""
        results = []
        for change in self._pending_changes:
            # ...
            if change["type"] == "rename":
                if not dry_run:
                    try:
                        # Ensure parent directory exists
                        change["new_path"].parent.mkdir(parents=True, exist_ok=True)
                        os.rename(change["old_path"], change["new_path"])
                        change["success"] = True
                    except Exception as e:
                        change["success"] = False
                        change["error"] = str(e)
                else:
                    change["success"] = True # Predicted success
            elif change["type"] == "tag":
                if not dry_run:
                    try:
                        music_file = MusicFile(change["path"])
                        # If tags didn't load, we might need to try loading them as ID3 if it's an MP3
                        if music_file.tags is None and change["path"].suffix.lower() == ".mp3":
                            import mutagen.id3
                            try:
                                music_file.tags = mutagen.id3.ID3(str(change["path"]))
                            except Exception:
                                pass

                        # If we have raw_tags, it's a manual update which might include binary data
                        tags_to_use = change.get("raw_tags", change.get("changes", {}))
                        print(f"Applying tags to {change['path']}: tags_to_use = {tags_to_use}")
                        tags_written = []
                        for tag, value in tags_to_use.items():
                            if tag == "album_art" and value == "<binary data>":
                                # This shouldn't happen if we use raw_tags correctly
                                continue
                            if not value and tag != "album_art":
                                print(f"Skipping empty tag: {tag}")
                                continue
                            print(f"Setting {tag} = {repr(value)}")
                            music_file.set_tag(tag, value)
                            tags_written.append(tag)

                        if tags_written:
                            print(f"Saving tags: {tags_written}")
                            music_file.save_tags()
                            change["tags_written"] = tags_written
                        else:
                            print("No tags to save")
                            change["tags_written"] = []
                        change["success"] = True
                    except Exception as e:
                        import traceback
                        change["success"] = False
                        change["error"] = str(e)
                        change["traceback"] = traceback.format_exc()
                        print(f"Error applying tag change to {change.get('path')}: {e}")
                        print(traceback.format_exc())
                else:
                    change["success"] = True
            
            results.append(change)
            if callback:
                callback(change)
                
        if not dry_run:
            self._pending_changes = []
        return results
