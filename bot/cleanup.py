"""
Automatic Cleanup Policy & Temporary Data Garbage Collector
Deletes temporary files and downloaded Telegram blobs after verified processing.
"""

import os
import time
from pathlib import Path


class FileCleanupWorker:
    """
    Worker tasked with ensuring raw temporary video fragments and sensitive packets are safely removed.
    """

    def __init__(self, target_dir: Path, max_age_seconds: int = 60):
        self.target_dir = Path(target_dir)
        self.max_age_seconds = max_age_seconds

    def cleanup_old_files(self) -> int:
        """
        Scans target directory and removes files older than max_age_seconds.
        Returns count of deleted files.
        """
        if not self.target_dir.exists():
            return 0

        deleted_count = 0
        now = time.time()

        for file_path in self.target_dir.glob("*"):
            if file_path.is_file():
                try:
                    file_age = now - file_path.stat().st_mtime
                    if file_age > self.max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
                except Exception as e:
                    print(f"⚠️ Error deleting temporary file {file_path}: {e}")

        return deleted_count

    @staticmethod
    def safe_delete_file(file_path: Path):
        """
        Immediately removes a specific temporary file after successful processing.
        """
        try:
            p = Path(file_path)
            if p.exists():
                p.unlink()
        except Exception as e:
            print(f"⚠️ Failed to immediately delete {file_path}: {e}")
