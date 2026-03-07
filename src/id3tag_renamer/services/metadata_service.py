"""Online metadata lookup service using MusicBrainz and AcoustID."""
from typing import Optional, List, Dict, Any
from pathlib import Path
import musicbrainzngs
import acoustid
import logging
import os

logger = logging.getLogger(__name__)

# Configure MusicBrainz API
musicbrainzngs.set_useragent(
    "ID3Tag-Renamer",
    "0.1.0",
    "https://github.com/yourusername/id3tag-renamer"
)

# MusicBrainz rate limit is 1 request per second (enforced by the library)
# AcoustID has built-in rate limiting to 3 requests per second


class MetadataMatch:
    """Represents a single metadata match result."""

    def __init__(
        self,
        score: float,
        title: str,
        artist: str,
        album: Optional[str] = None,
        track: Optional[str] = None,
        date: Optional[str] = None,
        genre: Optional[str] = None,
        mbid: Optional[str] = None,
    ):
        self.score = score
        self.title = title
        self.artist = artist
        self.album = album
        self.track = track
        self.date = date
        self.genre = genre
        self.mbid = mbid  # MusicBrainz ID

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "score": round(self.score * 100, 1),  # Convert to percentage
            "title": self.title,
            "artist": self.artist,
            "album": self.album or "",
            "track": self.track or "",
            "date": self.date or "",
            "genre": self.genre or "",
            "mbid": self.mbid or "",
        }


class MetadataLookupService:
    """Service for looking up music metadata from online sources."""

    @staticmethod
    def lookup_by_fingerprint(file_path: Path, api_key: Optional[str] = None) -> List[MetadataMatch]:
        """
        Lookup metadata using acoustic fingerprint.

        Args:
            file_path: Path to the audio file
            api_key: AcoustID API key (default is public test key)

        Returns:
            List of MetadataMatch objects

        Raises:
            Exception: If fpcalc binary is not found or fingerprinting fails
        """
        matches = []

        try:
            # Get API key from parameter or environment variable
            if api_key is None:
                api_key = os.getenv('ACOUSTID_API_KEY')
                if not api_key:
                    raise Exception("AcoustID API key not provided. Set ACOUSTID_API_KEY environment variable or pass api_key parameter. Get a key at https://acoustid.org/new-application")

            # Check if fpcalc is available
            import shutil
            if not shutil.which('fpcalc'):
                raise Exception("fpcalc binary not found. Install chromaprint package (e.g., 'apt-get install libchromaprint-tools' or 'brew install chromaprint')")

            # Generate fingerprint
            try:
                logger.info(f"Generating fingerprint for: {file_path} (exists: {file_path.exists()})")
                duration, fingerprint = acoustid.fingerprint_file(str(file_path))
                logger.info(f"Fingerprint generated successfully: duration={duration}s")
            except acoustid.FingerprintGenerationError as e:
                raise Exception(f"Failed to generate fingerprint for {file_path}: {e}")

            # Lookup using the fingerprint
            import requests
            response = requests.get(
                'https://api.acoustid.org/v2/lookup',
                params={
                    'client': api_key,
                    'duration': int(duration),
                    'fingerprint': fingerprint,
                    'meta': 'recordings releasegroups'
                }
            )
            data = response.json()

            if data.get('status') != 'ok':
                error_msg = data.get('error', {}).get('message', 'Unknown error')
                raise Exception(f"AcoustID API error: {error_msg}")

            results_data = data.get('results', [])
            if not results_data:
                raise Exception("No fingerprint matches found")

            for result in results_data:
                score = result.get('score', 0)
                if score < 0.5:
                    continue

                recordings = result.get('recordings', [])
                for recording in recordings:
                    recording_id = recording.get('id')
                    title = recording.get('title', 'Unknown Title')

                    # Get artist name
                    artists = recording.get('artists', [])
                    artist = artists[0].get('name', 'Unknown Artist') if artists else 'Unknown Artist'

                    match = MetadataMatch(
                        score=score,
                        title=title,
                        artist=artist,
                        mbid=recording_id
                    )

                    # Try to get additional details from MusicBrainz
                    if recording_id:
                        try:
                            rec_data = musicbrainzngs.get_recording_by_id(
                                recording_id,
                                includes=["releases", "artist-credits", "tags"]
                            )

                            rec = rec_data.get("recording", {})

                            # Get release information (album)
                            releases = rec.get("release-list", [])
                            if releases:
                                release = releases[0]
                                match.album = release.get("title")
                                match.date = release.get("date")

                                # Get track number if available
                                medium_list = release.get("medium-list", [])
                                if medium_list:
                                    track_list = medium_list[0].get("track-list", [])
                                    for track in track_list:
                                        if track.get("recording", {}).get("id") == recording_id:
                                            match.track = track.get("number")
                                            break

                            # Get genre from tags
                            tags = rec.get("tag-list", [])
                            if tags:
                                # Get the most popular tag
                                match.genre = tags[0].get("name", "").title()

                        except Exception as e:
                            logger.warning(f"Failed to get additional details from MusicBrainz: {e}")

                    matches.append(match)

                    if len(matches) >= 5:  # Limit to top 5 matches
                        break

                if len(matches) >= 5:
                    break

        except Exception as e:
            logger.error(f"Fingerprint lookup failed: {e}")

        return matches

    @staticmethod
    def lookup_by_tags(
        artist: Optional[str] = None,
        album: Optional[str] = None,
        title: Optional[str] = None
    ) -> List[MetadataMatch]:
        """
        Lookup metadata by searching with existing tags.

        Args:
            artist: Artist name
            album: Album name
            title: Track title

        Returns:
            List of MetadataMatch objects
        """
        matches = []

        if not any([artist, album, title]):
            return matches

        try:
            # Build search query
            query_parts = []
            if title:
                query_parts.append(f'recording:"{title}"')
            if artist:
                query_parts.append(f'artist:"{artist}"')
            if album:
                query_parts.append(f'release:"{album}"')

            query = " AND ".join(query_parts)

            # Search MusicBrainz
            result = musicbrainzngs.search_recordings(
                query=query,
                limit=10
            )

            recordings = result.get("recording-list", [])

            for rec in recordings:
                score = int(rec.get("ext:score", 0)) / 100.0  # Convert to 0-1 range

                if score < 0.5:  # Skip low confidence matches
                    continue

                rec_title = rec.get("title", "Unknown Title")

                # Get artist name
                artist_credits = rec.get("artist-credit", [])
                rec_artist = "Unknown Artist"
                if artist_credits and isinstance(artist_credits, list):
                    rec_artist = artist_credits[0].get("artist", {}).get("name", "Unknown Artist")

                # Get release information
                releases = rec.get("release-list", [])
                rec_album = None
                rec_date = None
                rec_track = None

                if releases:
                    release = releases[0]
                    rec_album = release.get("title")
                    rec_date = release.get("date")

                    # Try to get track number
                    medium_list = release.get("medium-list", [])
                    if medium_list:
                        track_list = medium_list[0].get("track-list", [])
                        if track_list:
                            rec_track = track_list[0].get("number")

                # Get genre from tags
                rec_genre = None
                tags = rec.get("tag-list", [])
                if tags:
                    rec_genre = tags[0].get("name", "").title()

                match = MetadataMatch(
                    score=score,
                    title=rec_title,
                    artist=rec_artist,
                    album=rec_album,
                    track=rec_track,
                    date=rec_date,
                    genre=rec_genre,
                    mbid=rec.get("id")
                )

                matches.append(match)

                if len(matches) >= 5:  # Limit to top 5 matches
                    break

        except Exception as e:
            logger.error(f"Tag-based lookup failed: {e}")

        return matches

    @staticmethod
    def lookup_file(file_path: Path, existing_tags: Dict[str, str], use_fingerprint: bool = True) -> List[MetadataMatch]:
        """
        Lookup metadata for a file using multiple methods.

        Args:
            file_path: Path to the audio file
            existing_tags: Dictionary of existing tags (artist, album, title, etc.)
            use_fingerprint: Whether to use acoustic fingerprinting

        Returns:
            List of MetadataMatch objects, sorted by confidence score
        """
        matches = []
        fingerprint_error = None

        # Try fingerprint lookup first (more accurate)
        if use_fingerprint and file_path.exists():
            try:
                fp_matches = MetadataLookupService.lookup_by_fingerprint(file_path)
                matches.extend(fp_matches)
            except Exception as e:
                fingerprint_error = str(e)
                logger.warning(f"Fingerprint lookup failed: {e}")

        # If fingerprint didn't work or wasn't used, try tag-based search
        if not matches:
            try:
                tag_matches = MetadataLookupService.lookup_by_tags(
                    artist=existing_tags.get("artist"),
                    album=existing_tags.get("album"),
                    title=existing_tags.get("title")
                )
                matches.extend(tag_matches)
            except Exception as e:
                logger.warning(f"Tag-based lookup failed: {e}")

        # Sort by score (highest first) and remove duplicates
        matches.sort(key=lambda m: m.score, reverse=True)

        # Remove duplicates based on title + artist
        seen = set()
        unique_matches = []
        for match in matches:
            key = (match.title.lower(), match.artist.lower())
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)

        return unique_matches[:5]  # Return top 5
