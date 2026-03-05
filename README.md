# ID3Tag-Renamer

A web-based music file organizer for managing ID3 tags and renaming files based on metadata. Perfect for home server deployments with Docker support.

## Features

### 🎵 Multiple Operation Modes
- **Rename from Tags**: Generate filenames from ID3 tag patterns (e.g., `{artist} - {title}.mp3`)
- **Tag from Filename**: Extract metadata from filename patterns (e.g., `%artist% - %title%`)
- **Manual Tag Update**: Directly edit tags for single or multiple files

### 🏷️ Comprehensive Tag Support
- Artist, Album, Title, Track Number
- Genre, Date, Comment
- Album Art (JPEG/PNG)
- Supports MP3, FLAC, and M4A formats

### ✨ Advanced Features
- **Multi-file Editing**: Select multiple files and batch-update tags
- **Smart Field Population**: Shows `<multiple values>` when selected files have different tag values
- **Single File Editing**: Quick-edit modal for individual files
- **Real-time Preview**: See changes before applying them
- **Directory Browser**: Navigate your music collection with an intuitive file browser
- **Sortable Table**: Click column headers to sort files
- **Resizable Columns**: Drag column borders to adjust widths
- **Horizontal Scroll**: View all tag columns comfortably

## Quick Start with Docker Compose

### Prerequisites
- Docker and Docker Compose installed
- A music directory on your server

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/id3tag-renamer.git
cd id3tag-renamer
```

2. **Create docker-compose.yml**
```yaml
version: '3.8'

services:
  id3tag-renamer:
    build: .
    container_name: id3tag-renamer
    ports:
      - "8000:8000"
    volumes:
      - /path/to/your/music:/music
    environment:
      - MUSIC_DIR=/music
      - WEB_USERNAME=admin          # Optional: HTTP Basic Auth username
      - WEB_PASSWORD=your_password  # Optional: HTTP Basic Auth password
    restart: unless-stopped
```

3. **Update the music path**
   Edit `docker-compose.yml` and replace `/path/to/your/music` with your actual music directory path.

4. **Start the container**
```bash
docker-compose up -d
```

5. **Access the web interface**
   Open your browser and navigate to `http://your-server-ip:8000`

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MUSIC_DIR` | No | `/music` | Path to music directory inside container |
| `WEB_USERNAME` | No | None | HTTP Basic Auth username (optional) |
| `WEB_PASSWORD` | No | None | HTTP Basic Auth password (optional) |
| `HOST` | No | `0.0.0.0` | Server bind address |
| `PORT` | No | `8000` | Server port |

### Security Notes

- **Authentication**: Set `WEB_USERNAME` and `WEB_PASSWORD` if exposing to the internet
- **Network**: Consider using a reverse proxy (nginx, Traefik) with HTTPS for external access
- **File Access**: The container only has access to the mounted music directory
- **CSRF Protection**: Built-in CSRF middleware protects against cross-site attacks

## Usage Guide

### Getting Started

1. **Select Directory**
   - Click the "Browse" button in the navbar
   - Navigate to your music folder
   - Click "Select Directory" and then "Scan"

2. **Choose Operation Mode**
   Use the mode selector in the navbar:
   - **Rename from tags**: Create filenames from metadata
   - **Tag from filename**: Extract metadata from filenames
   - **Manual tag update**: Edit tags directly

### Rename from Tags

Create organized filenames based on ID3 tags.

**Pattern Syntax**: Use `{tag}` format
- `{artist} - {title}` → "Artist Name - Song Title.mp3"
- `{track} - {title}` → "01 - Song Title.mp3"
- `{artist}/{album}/{track} - {title}` → Creates folders!

**Supported Tags**: `{artist}`, `{album}`, `{title}`, `{track}`, `{genre}`, `{date}`, `{comment}`

**Slice Support**: `{artist[0:10]}` → First 10 characters

**Steps**:
1. Select mode: "Rename from tags"
2. Enter your pattern in the text field
3. Optionally select specific files (checkboxes)
4. Click "Preview" to see changes
5. Review changes in the modal
6. Click "Apply Changes" to rename files

### Tag from Filename

Extract metadata from existing filename patterns.

**Pattern Syntax**: Use `%tag%` format
- `%artist% - %title%` → Extracts from "Artist - Title.mp3"
- `%track% - %title%` → Extracts from "01 - Song.mp3"

**Steps**:
1. Select mode: "Tag from filename"
2. Enter the pattern matching your filenames
3. Optionally select specific files
4. Click "Preview"
5. Review extracted tags
6. Click "Apply Changes"

### Manual Tag Update

Edit tags directly with full control.

**Single File**:
1. Click the ✏️ button next to any file
2. Edit tags in the modal
3. Optionally upload new album art
4. Click "Preview Changes"
5. Click "Apply Changes"

**Multiple Files**:
1. Check the boxes next to files you want to edit
2. Switch to "Manual tag update" mode
3. Fields show:
   - **Same value**: If all selected files have identical tags
   - **`<multiple values>`**: If selected files have different tags
   - **Empty**: If all selected files have empty tags
4. Edit the fields you want to change
5. Leave fields unchanged to skip updating them
6. Click "Preview"
7. Review changes
8. Click "Apply Changes"

### Keyboard Shortcuts & Tips

- **Select All**: Use the checkbox in the table header
- **Sort**: Click any column header to sort
- **Resize Columns**: Drag the column borders
- **Clear Selection**: Uncheck "Select All" or manually uncheck files

## Technical Details

### Supported Audio Formats
- **MP3**: ID3v2 tags (TPE1, TALB, TIT2, etc.)
- **FLAC**: Vorbis comments (artist, album, title, description, etc.)
- **M4A**: iTunes-style tags (©ART, ©alb, ©nam, etc.)

### Tag Field Mappings

| Field | MP3 (ID3v2) | FLAC (Vorbis) | M4A (iTunes) |
|-------|-------------|---------------|--------------|
| Artist | TPE1 | artist | ©ART |
| Album | TALB | album | ©alb |
| Title | TIT2 | title | ©nam |
| Track | TRCK | tracknumber | trkn |
| Genre | TCON | genre | ©gen |
| Date | TDRC | date | ©day |
| Comment | COMM | description | ©cmt |

### Architecture
- **Backend**: FastAPI (Python)
- **Frontend**: Bootstrap 5 + Vanilla JavaScript
- **Tag Library**: Mutagen (Python)
- **Security**: HTTP Basic Auth, CSRF protection, path traversal prevention

## Development

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/id3tag-renamer.git
cd id3tag-renamer

# Install dependencies
pip install -e .

# Set environment variables
export MUSIC_DIR=/path/to/music
export WEB_USERNAME=admin
export WEB_PASSWORD=password

# Run the development server
python -m id3tag_renamer.web
```

### Building the Docker Image

```bash
docker build -t id3tag-renamer .
```

### Running without Docker

```bash
# Install package
pip install -e .

# Run directly
python -m id3tag_renamer.web

# Or use the CLI
id3tag-renamer --help
```

## Troubleshooting

### Files not showing up after scan
- Check that the directory path is correct
- Ensure the directory contains .mp3, .flac, or .m4a files
- Verify file permissions (container needs read/write access)

### Tags not being saved
- Check Docker logs: `docker logs id3tag-renamer`
- Verify file permissions in the mounted volume
- Ensure files are not read-only

### Cannot access web interface
- Verify the port mapping in docker-compose.yml
- Check if the container is running: `docker ps`
- Review logs: `docker logs id3tag-renamer`
- Ensure no firewall is blocking port 8000

### Authentication not working
- Verify `WEB_USERNAME` and `WEB_PASSWORD` are set in docker-compose.yml
- Restart the container after changing environment variables
- Clear browser cache and cookies

## Project Structure

```
id3tag-renamer/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
├── src/
│   └── id3tag_renamer/
│       ├── __init__.py       # Core tag manipulation logic
│       ├── web.py            # FastAPI web application
│       └── templates/
│           └── index.html    # Single-page web interface
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Audio tag handling by [Mutagen](https://mutagen.readthedocs.io/)
- UI powered by [Bootstrap 5](https://getbootstrap.com/)

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Made with ♥ for music lovers who appreciate organized collections**
