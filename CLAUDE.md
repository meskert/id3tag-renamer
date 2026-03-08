# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install for development (from repo root)
pip install -e ".[dev]"

# System dependencies required for audio fingerprinting
sudo apt-get install libchromaprint-tools ffmpeg  # Linux
brew install chromaprint ffmpeg                   # macOS

# Run the web app
python -m id3tag_renamer.web
# or after install:
id3tag-renamer

# Run tests
pytest tests/

# Run a single test
pytest tests/test_web.py::test_list_directories

# Format / lint
black src/ tests/
isort src/ tests/

# Docker
docker build -t id3tag-renamer .
docker-compose up -d
```

## Architecture

The app is a FastAPI web application for managing music file metadata (ID3/Vorbis/iTunes tags) and renaming files. It's designed as a home-server Docker deployment.

### Core Data Flow

1. **`MusicManager`** (`src/id3tag_renamer/__init__.py`) — the core engine. It holds a list of `MusicFile` objects after `scan()`, and accumulates planned changes in `_pending_changes`. Changes are executed with `apply(dry_run=False)`.
2. **`MusicFile`** (same file) — wraps a single audio file via `mutagen`. Abstracts over MP3 (ID3v2), FLAC (Vorbis comments), and M4A (iTunes atoms) with a unified `get_tag`/`set_tag` interface.
3. **Global `manager`** instance in `web.py` — the single shared `MusicManager` for all requests. Routes import it via `from ..web import manager`.

### Request Flow for Bulk Operations

All bulk operations follow a **preview → apply** pattern:
- `POST /preview` — calls `manager.rename_from_tags()` or `manager.tag_from_path()`, then `manager.apply(dry_run=True)` to populate `_pending_changes` and return a preview.
- `POST /apply` — re-runs the same operation and calls `manager.apply(dry_run=False)`, then re-scans.
- `POST /update_tags` (manual mode) — calls `manager.update_tags()` then `apply(dry_run=True)` for preview; the subsequent `POST /apply` reconstructs the changes from hidden form fields.

### Route Modules (`src/id3tag_renamer/routes/`)

| Module | Responsibility |
|--------|---------------|
| `files.py` | `GET /`, `POST /scan`, `POST /preview`, `POST /apply` |
| `tags.py` | `POST /update_tags` (manual tag editing) |
| `api.py` | `GET /api/directories`, `GET /api/album_art/{index}`, `POST /api/lookup_metadata`, `POST /api/apply_metadata` |
| `auth.py` | `GET/POST /login`, `POST /logout` |

### Services (`src/id3tag_renamer/services/`)

- **`file_service.py`** — `get_files_data(manager)` converts `MusicFile` list to dicts for template rendering.
- **`path_service.py`** — `get_safe_path(path_str)` prevents path traversal by anchoring all paths to `MUSIC_DIR`.
- **`metadata_service.py`** — `MetadataLookupService` performs online lookup via AcoustID fingerprinting (requires `fpcalc` binary) with MusicBrainz fallback when fingerprinting fails or is unavailable.

### Frontend (`src/id3tag_renamer/static/js/`)

Vanilla JS with Bootstrap 5:
- `table.js` — sortable, resizable columns, checkbox selection
- `browser.js` — AJAX directory browser modal
- `forms.js` — mode switching, form submission, multi-file `<multiple values>` display
- `preview.js` — preview modal handling
- `lookup.js` — online metadata lookup modal

### Authentication & Security

- Session-based auth via `itsdangerous` + `starlette.middleware.sessions`. Auth is optional: if `WEB_USERNAME`/`WEB_PASSWORD` env vars are not set, all routes pass through as `"guest"`.
- CSRF protection via `middleware/csrf.py` checks `Origin`/`Referer` headers on mutating requests.
- Path traversal prevention via `get_safe_path()` in all directory/scan operations.

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MUSIC_DIR` | `/music` | Root music directory (container path) |
| `WEB_USERNAME` / `WEB_PASSWORD` | unset | Enables HTTP session auth |
| `WEB_SESSION_SECRET` | random | Session signing key (set for persistence across restarts) |
| `ACOUSTID_API_KEY` | unset | Required for audio fingerprinting |
| `HOST` / `PORT` | `0.0.0.0`/`8000` | Server bind settings |
