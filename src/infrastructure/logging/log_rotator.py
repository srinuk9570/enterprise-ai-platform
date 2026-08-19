"""
Log rotation and archival management.
"""
import logging
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import threading
import time

from src.shared.config import settings

logger = logging.getLogger(__name__)


class LogRotator:
    """
    Manages log rotation, compression, and cleanup.
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path(settings.LOG_FILE_PATH).parent
        self.compression_enabled = True
        self.retention_days = 30
        self.max_total_size_gb = 10
        
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = False
    
    def rotate_logs(self) -> List[Path]:
        """
        Rotate all log files.
        Returns list of rotated files.
        """
        rotated_files = []
        
        for log_file in self.log_dir.glob("*.log"):
            if self._should_rotate(log_file):
                rotated = self._rotate_file(log_file)
                if rotated:
                    rotated_files.append(rotated)
        
        return rotated_files
    
    def _should_rotate(self, log_file: Path) -> bool:
        """Check if a log file should be rotated."""
        # Rotate if file is older than 1 day
        if log_file.stat().st_mtime < (datetime.now() - timedelta(days=1)).timestamp():
            return True
        
        # Rotate if file is larger than 100 MB
        if log_file.stat().st_size > 100 * 1024 * 1024:
            return True
        
        return False
    
    def _rotate_file(self, log_file: Path) -> Optional[Path]:
        """
        Rotate a single log file.
        """
        try:
            # Generate rotated filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated_name = f"{log_file.stem}.{timestamp}.log"
            rotated_path = log_file.parent / rotated_name
            
            # Move current log to rotated
            shutil.move(str(log_file), str(rotated_path))
            
            # Compress if enabled
            if self.compression_enabled:
                compressed_path = self._compress_file(rotated_path)
                logger.info(f"Rotated and compressed: {log_file.name} -> {compressed_path.name}")
                return compressed_path
            else:
                logger.info(f"Rotated: {log_file.name} -> {rotated_path.name}")
                return rotated_path
                
        except Exception as e:
            logger.error(f"Error rotating {log_file}: {e}")
            return None
    
    def _compress_file(self, file_path: Path) -> Path:
        """
        Compress a file using gzip.
        """
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove original file
        file_path.unlink()
        
        return compressed_path
    
    def cleanup_old_logs(self, days: Optional[int] = None) -> int:
        """
        Delete log files older than retention period.
        Returns number of files deleted.
        """
        retention_days = days or self.retention_days
        cutoff_time = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        
        # Find all rotated log files
        patterns = ["*.log.*", "*.log.*.gz", "*.log.[0-9]*"]
        
        for pattern in patterns:
            for log_file in self.log_dir.glob(pattern):
                if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_time:
                    try:
                        log_file.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error deleting {log_file}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old log files")
        
        return deleted_count
    
    def check_disk_usage(self) -> float:
        """
        Check total size of log directory in GB.
        """
        total_size = 0
        
        for log_file in self.log_dir.glob("**/*"):
            if log_file.is_file():
                total_size += log_file.stat().st_size
        
        return total_size / (1024 ** 3)  # Convert to GB
    
    def enforce_size_limit(self) -> int:
        """
        Delete oldest log files until total size is under limit.
        Returns number of files deleted.
        """
        current_size_gb = self.check_disk_usage()
        
        if current_size_gb <= self.max_total_size_gb:
            return 0
        
        # Get all log files sorted by modification time (oldest first)
        log_files = []
        for pattern in ["*.log.*", "*.log.*.gz"]:
            log_files.extend(self.log_dir.glob(pattern))
        
        log_files.sort(key=lambda p: p.stat().st_mtime)
        
        deleted_count = 0
        target_size = self.max_total_size_gb * 0.8  # Target 80% of max
        
        for log_file in log_files:
            if self.check_disk_usage() <= target_size:
                break
            
            try:
                size = log_file.stat().st_size
                log_file.unlink()
                deleted_count += 1
                current_size_gb -= size / (1024 ** 3)
            except Exception as e:
                logger.error(f"Error deleting {log_file}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} log files to enforce size limit")
        
        return deleted_count
    
    def start_background_cleanup(self, interval_hours: int = 24) -> None:
        """
        Start background thread for periodic cleanup.
        """
        if self._running:
            return
        
        self._running = True
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            args=(interval_hours,),
            daemon=True,
        )
        self._cleanup_thread.start()
        logger.info(f"Background log cleanup started (interval: {interval_hours}h)")
    
    def stop_background_cleanup(self) -> None:
        """
        Stop background cleanup thread.
        """
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        logger.info("Background log cleanup stopped")
    
    def _cleanup_loop(self, interval_hours: int) -> None:
        """
        Background cleanup loop.
        """
        while self._running:
            time.sleep(interval_hours * 3600)
            
            try:
                self.cleanup_old_logs()
                self.enforce_size_limit()
            except Exception as e:
                logger.error(f"Error in log cleanup: {e}")
    
    def get_log_stats(self) -> dict:
        """
        Get statistics about log files.
        """
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_gb": 0.0,
            "oldest_file": None,
            "newest_file": None,
            "by_type": {},
        }
        
        log_files = list(self.log_dir.glob("*"))
        
        for log_file in log_files:
            if log_file.is_file():
                stats["total_files"] += 1
                size = log_file.stat().st_size
                stats["total_size_bytes"] += size
                
                # Track by extension
                ext = log_file.suffix or "no_ext"
                if ext not in stats["by_type"]:
                    stats["by_type"][ext] = {"count": 0, "size_bytes": 0}
                stats["by_type"][ext]["count"] += 1
                stats["by_type"][ext]["size_bytes"] += size
                
                # Track oldest/newest
                mtime = log_file.stat().st_mtime
                if stats["oldest_file"] is None or mtime < stats["oldest_file"][1]:
                    stats["oldest_file"] = (str(log_file.name), mtime)
                if stats["newest_file"] is None or mtime > stats["newest_file"][1]:
                    stats["newest_file"] = (str(log_file.name), mtime)
        
        stats["total_size_gb"] = stats["total_size_bytes"] / (1024 ** 3)
        
        if stats["oldest_file"]:
            stats["oldest_file"] = {
                "name": stats["oldest_file"][0],
                "mtime": datetime.fromtimestamp(stats["oldest_file"][1]).isoformat(),
            }
        if stats["newest_file"]:
            stats["newest_file"] = {
                "name": stats["newest_file"][0],
                "mtime": datetime.fromtimestamp(stats["newest_file"][1]).isoformat(),
            }
        
        return stats