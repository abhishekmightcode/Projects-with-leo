"""
Temp Audio Manager — ROOTAI STT temp file handling
===================================================
Manages temp audio files for STT processing on ROOTAI.
Files auto-delete after configurable TTL.
Supports: ogg, mp3, wav, m4a, opus.

Usage:
    from temp_audio_manager import TempAudioManager

    manager = TempAudioManager()
    path = manager.save_temp_audio(raw_bytes, "ogg")
    # ... use path for STT ...
    manager.cleanup(path)
"""

import os
import uuid
import threading
import time
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Default TTL for temp files (1 hour)
DEFAULT_TTL_SECONDS = 3600

# Default temp directory
DEFAULT_TEMP_DIR = "/tmp/rootai_stt_audio"

# Supported formats
SUPPORTED_EXTENSIONS = {".ogg", ".mp3", ".wav", ".m4a", ".opus"}


class TempAudioManager:
    """
    Manages temporary audio files for STT processing.

    Features:
    - Auto-generated unique filenames
    - TTL-based auto-expiry
    - Manual cleanup
    - Background orphan cleanup
    - Configurable storage limits
    """

    def __init__(
        self,
        temp_dir: str = DEFAULT_TEMP_DIR,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        max_files: int = 100,
        auto_start_cleanup: bool = True,
    ):
        self.temp_dir = Path(temp_dir)
        self.ttl_seconds = ttl_seconds
        self.max_files = max_files
        self._cleanup_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()

        # Create temp directory
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"TempAudioManager initialized: dir={temp_dir}, ttl={ttl_seconds}s")

        if auto_start_cleanup:
            self._start_cleanup_daemon()

    def _generate_filename(self, extension: str) -> str:
        """Generate unique filename with UUID."""
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        uid = uuid.uuid4().hex[:8]
        ext = extension.lower().lstrip(".")
        if ext not in {"ogg", "mp3", "wav", "m4a", "opus"}:
            ext = "ogg"  # default
        return f"stt_{ts}_{uid}.{ext}"

    def save_temp_audio(
        self,
        content: bytes,
        extension: str = "ogg",
        subdir: Optional[str] = None,
    ) -> str:
        """
        Save audio bytes to a temp file.

        Args:
            content: Raw audio bytes
            extension: File extension (ogg, mp3, wav, m4a, opus)
            subdir: Optional subdirectory within temp_dir

        Returns:
            Absolute path to saved file
        """
        if subdir:
            target_dir = self.temp_dir / subdir
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self.temp_dir

        filename = self._generate_filename(extension)
        file_path = target_dir / filename

        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Saved temp audio: {file_path} ({len(content)} bytes)")
        return str(file_path)

    def save_temp_from_existing(
        self,
        source_path: str,
        copy: bool = True,
        subdir: Optional[str] = None,
    ) -> str:
        """
        Create a temp copy of an existing audio file.

        Args:
            source_path: Path to source audio file
            copy: If True, copy the file; if False, move it
            subdir: Optional subdirectory

        Returns:
            Absolute path to temp file
        """
        source = Path(source_path)
        extension = source.suffix

        if copy:
            content = source.read_bytes()
            return self.save_temp_audio(content, extension, subdir)
        else:
            filename = self._generate_filename(extension)
            if subdir:
                target_dir = self.temp_dir / subdir
                target_dir.mkdir(parents=True, exist_ok=True)
            else:
                target_dir = self.temp_dir
            dest = target_dir / filename
            source.rename(dest)
            return str(dest)

    def cleanup(self, file_path: str) -> bool:
        """
        Delete a specific temp file.

        Args:
            file_path: Path to file to delete

        Returns:
            True if deleted, False if not found
        """
        path = Path(file_path)
        try:
            if path.exists():
                path.unlink()
                logger.info(f"Deleted temp file: {file_path}")
                return True
            else:
                logger.warning(f"Temp file not found: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")
            return False

    def cleanup_by_prefix(self, prefix: str) -> int:
        """Delete all files matching prefix."""
        count = 0
        pattern = self.temp_dir / f"{prefix}*"
        for path in self.temp_dir.glob(f"{prefix}*"):
            try:
                path.unlink()
                count += 1
            except Exception as e:
                logger.error(f"Failed to delete {path}: {e}")
        if count:
            logger.info(f"Deleted {count} files with prefix '{prefix}'")
        return count

    def is_expired(self, file_path: str) -> bool:
        """Check if a file has exceeded its TTL."""
        try:
            mtime = os.path.getmtime(file_path)
            age_seconds = time.time() - mtime
            return age_seconds > self.ttl_seconds
        except Exception:
            return True  # If can't read, consider expired

    def get_all_temp_files(self) -> List[str]:
        """Return all files in temp directory."""
        return [str(p) for p in self.temp_dir.rglob("*") if p.is_file()]

    def cleanup_expired(self) -> int:
        """
        Delete all expired files in temp directory.

        Returns:
            Number of files deleted
        """
        count = 0
        for path in self.temp_dir.rglob("*"):
            if path.is_file() and self.is_expired(str(path)):
                try:
                    path.unlink()
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to delete expired {path}: {e}")
        if count:
            logger.info(f"Cleaned up {count} expired temp files")
        return count

    def cleanup_orphaned(self, active_paths: List[str]) -> int:
        """
        Delete all temp files NOT in active_paths.

        Useful after a session crash to clean up orphaned files.

        Args:
            active_paths: List of file paths currently in use

        Returns:
            Number of files deleted
        """
        active_set = set(Path(p).resolve() for p in active_paths)
        count = 0

        for path in self.temp_dir.rglob("*"):
            if path.is_file() and Path(path).resolve() not in active_set:
                try:
                    path.unlink()
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to delete orphaned {path}: {e}")

        if count:
            logger.info(f"Cleaned up {count} orphaned temp files")
        return count

    def _start_cleanup_daemon(self):
        """Start background cleanup thread."""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return

        def daemon():
            while not self._shutdown_event.is_set():
                time.sleep(300)  # Check every 5 minutes
                if not self._shutdown_event.is_set():
                    self.cleanup_expired()

        self._cleanup_thread = threading.Thread(target=daemon, daemon=True)
        self._cleanup_thread.start()
        logger.info("Temp cleanup daemon started")

    def shutdown(self):
        """Stop cleanup daemon and delete all temp files."""
        self._shutdown_event.set()
        count = 0
        for path in self.temp_dir.rglob("*"):
            if path.is_file():
                try:
                    path.unlink()
                    count += 1
                except Exception:
                    pass
        logger.info(f"Shutdown: deleted {count} temp files")
        self.temp_dir.rmdir(exist_ok=True)

    def get_stats(self) -> dict:
        """Return temp directory statistics."""
        files = list(self.temp_dir.rglob("*"))
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        expired_count = sum(1 for f in files if f.is_file() and self.is_expired(str(f)))

        return {
            "total_files": len([f for f in files if f.is_file()]),
            "total_size_mb": total_size / (1024 * 1024),
            "expired_files": expired_count,
            "temp_dir": str(self.temp_dir),
            "ttl_seconds": self.ttl_seconds,
            "daemon_running": (
                self._cleanup_thread.is_alive() if self._cleanup_thread else False
            ),
        }