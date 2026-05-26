"""
Temp Audio Manager — VSustainAI
=================================
Manages temp audio files for STT processing.
VSustainAI workspace: /home/aiops/agents/vss/

Supports: ogg, mp3, wav, m4a, opus
TTL: 1 hour
"""

import os, uuid, threading, time, logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 3600
DEFAULT_TEMP_DIR = "/tmp/vsustainai_stt_audio"
SUPPORTED_EXTENSIONS = {".ogg", ".mp3", ".wav", ".m4a", ".opus"}


class TempAudioManager:
    """
    Manages temporary audio files for VSustainAI STT.
    Auto-cleanup daemon runs every 5 minutes.
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

        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"VSustainAI TempAudioManager: dir={temp_dir}, ttl={ttl_seconds}s")

        if auto_start_cleanup:
            self._start_cleanup_daemon()

    def _generate_filename(self, extension: str) -> str:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        uid = uuid.uuid4().hex[:8]
        ext = extension.lower().lstrip(".")
        if ext not in {"ogg", "mp3", "wav", "m4a", "opus"}:
            ext = "ogg"
        return f"vss_stt_{ts}_{uid}.{ext}"

    def save_temp_audio(self, content: bytes, extension: str = "ogg", subdir: Optional[str] = None) -> str:
        if subdir:
            target_dir = self.temp_dir / subdir
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self.temp_dir

        filename = self._generate_filename(extension)
        file_path = target_dir / filename

        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"VSustainAI saved temp audio: {file_path}")
        return str(file_path)

    def save_temp_from_existing(self, source_path: str, copy: bool = True, subdir: Optional[str] = None) -> str:
        source = Path(source_path)
        extension = source.suffix

        if copy:
            content = source.read_bytes()
            return self.save_temp_audio(content, extension, subdir)
        else:
            filename = self._generate_filename(extension)
            target_dir = self.temp_dir / subdir if subdir else self.temp_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            dest = target_dir / filename
            source.rename(dest)
            return str(dest)

    def cleanup(self, file_path: str) -> bool:
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"VSustainAI deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Cleanup failed {file_path}: {e}")
            return False

    def is_expired(self, file_path: str) -> bool:
        try:
            age_seconds = time.time() - os.path.getmtime(file_path)
            return age_seconds > self.ttl_seconds
        except Exception:
            return True

    def get_all_temp_files(self) -> List[str]:
        return [str(p) for p in self.temp_dir.rglob("*") if p.is_file()]

    def cleanup_expired(self) -> int:
        count = 0
        for path in self.temp_dir.rglob("*"):
            if path.is_file() and self.is_expired(str(path)):
                try:
                    path.unlink()
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to delete expired {path}: {e}")
        if count:
            logger.info(f"VSustainAI cleaned up {count} expired files")
        return count

    def _start_cleanup_daemon(self):
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return

        def daemon():
            while not self._shutdown_event.is_set():
                time.sleep(300)
                if not self._shutdown_event.is_set():
                    self.cleanup_expired()

        self._cleanup_thread = threading.Thread(target=daemon, daemon=True)
        self._cleanup_thread.start()
        logger.info("VSustainAI temp cleanup daemon started")

    def shutdown(self):
        self._shutdown_event.set()
        count = 0
        for path in self.temp_dir.rglob("*"):
            if path.is_file():
                try:
                    path.unlink()
                    count += 1
                except Exception:
                    pass
        logger.info(f"VSustainAI shutdown: deleted {count} temp files")

    def get_stats(self) -> dict:
        files = list(self.temp_dir.rglob("*"))
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        return {
            "total_files": len([f for f in files if f.is_file()]),
            "total_size_mb": total_size / (1024 * 1024),
            "expired_files": sum(1 for f in files if f.is_file() and self.is_expired(str(f))),
            "temp_dir": str(self.temp_dir),
            "ttl_seconds": self.ttl_seconds,
            "daemon_running": self._cleanup_thread.is_alive() if self._cleanup_thread else False,
        }