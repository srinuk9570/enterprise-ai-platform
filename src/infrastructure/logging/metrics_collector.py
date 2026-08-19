"""
Metrics collection for performance monitoring and observability.
"""
import logging
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from contextlib import contextmanager
import json
from pathlib import Path

from src.shared.config import settings

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """Container for metric values with statistics."""
    
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    last_value: float = 0.0
    values: List[float] = field(default_factory=list)
    
    def add(self, value: float) -> None:
        self.count += 1
        self.sum += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        self.last_value = value
        self.values.append(value)
        
        # Keep only last 100 values
        if len(self.values) > 100:
            self.values.pop(0)
    
    def avg(self) -> float:
        return self.sum / self.count if self.count > 0 else 0.0
    
    def percentile(self, p: float) -> float:
        if not self.values:
            return 0.0
        sorted_values = sorted(self.values)
        index = int(p * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "sum": self.sum,
            "avg": self.avg(),
            "min": self.min if self.min != float('inf') else 0,
            "max": self.max if self.max != float('-inf') else 0,
            "last": self.last_value,
            "p50": self.percentile(0.50),
            "p90": self.percentile(0.90),
            "p99": self.percentile(0.99),
        }


class MetricsCollector:
    """
    Collector for application metrics.
    Supports counters, gauges, histograms, and timers.
    """
    
    _instance: Optional["MetricsCollector"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "MetricsCollector":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, MetricValue] = defaultdict(MetricValue)
        self.timers: Dict[str, MetricValue] = defaultdict(MetricValue)
        
        self._metrics_lock = threading.RLock()
        self._start_time = datetime.utcnow()
        
        # Start background exporter
        self._export_interval = 60  # seconds
        self._export_thread = threading.Thread(target=self._export_loop, daemon=True)
        self._export_thread.start()
        
        self._initialized = True
        logger.info("MetricsCollector initialized")
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric.
        """
        key = self._build_key(name, tags)
        with self._metrics_lock:
            self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge metric.
        """
        key = self._build_key(name, tags)
        with self._metrics_lock:
            self.gauges[key] = value
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a value in a histogram.
        """
        key = self._build_key(name, tags)
        with self._metrics_lock:
            self.histograms[key].add(value)
    
    def record_timer(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a timer value.
        """
        key = self._build_key(name, tags)
        with self._metrics_lock:
            self.timers[key].add(duration_ms)
    
    @contextmanager
    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """
        Context manager for timing code blocks.
        
        Usage:
            with metrics.timer("llm.inference", {"model": "deepseek"}):
                response = llm.generate()
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.record_timer(name, duration_ms, tags)
    
    def timer_decorator(self, name: str, tags: Optional[Dict[str, str]] = None):
        """
        Decorator for timing function calls.
        
        Usage:
            @metrics.timer_decorator("api.endpoint", {"method": "POST"})
            async def create_user():
                ...
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                with self.timer(name, tags):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get counter value."""
        key = self._build_key(name, tags)
        with self._metrics_lock:
            return self.counters.get(key, 0)
    
    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value."""
        key = self._build_key(name, tags)
        with self._metrics_lock:
            return self.gauges.get(key, 0.0)
    
    def get_histogram_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get histogram statistics."""
        key = self._build_key(name, tags)
        with self._metrics_lock:
            if key in self.histograms:
                return self.histograms[key].to_dict()
            return {}
    
    def get_timer_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get timer statistics."""
        key = self._build_key(name, tags)
        with self._metrics_lock:
            if key in self.timers:
                return self.timers[key].to_dict()
            return {}
    
    def _build_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Build a unique key from name and tags."""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics as a dictionary.
        """
        with self._metrics_lock:
            metrics = {
                "uptime_seconds": (datetime.utcnow() - self._start_time).total_seconds(),
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {
                    key: mv.to_dict() for key, mv in self.histograms.items()
                },
                "timers": {
                    key: mv.to_dict() for key, mv in self.timers.items()
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        return metrics
    
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format.
        """
        lines = []
        
        with self._metrics_lock:
            # Counters
            for key, value in self.counters.items():
                name, labels = self._parse_key(key)
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{self._format_prometheus(name, labels)} {value}")
            
            # Gauges
            for key, value in self.gauges.items():
                name, labels = self._parse_key(key)
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{self._format_prometheus(name, labels)} {value}")
            
            # Histograms
            for key, mv in self.histograms.items():
                name, labels = self._parse_key(key)
                lines.append(f"# TYPE {name} histogram")
                lines.append(f"{self._format_prometheus(name + '_count', labels)} {mv.count}")
                lines.append(f"{self._format_prometheus(name + '_sum', labels)} {mv.sum}")
                lines.append(f"{self._format_prometheus(name + '_bucket', {**labels, 'le': '+Inf'})} {mv.count}")
            
            # Timers (as histograms)
            for key, mv in self.timers.items():
                name, labels = self._parse_key(key)
                lines.append(f"# TYPE {name}_seconds histogram")
                lines.append(f"{self._format_prometheus(name + '_seconds_count', labels)} {mv.count}")
                lines.append(f"{self._format_prometheus(name + '_seconds_sum', labels)} {mv.sum / 1000}")
        
        return "\n".join(lines)
    
    def _parse_key(self, key: str) -> tuple[str, Dict[str, str]]:
        """Parse a metric key into name and labels."""
        if '[' not in key:
            return key, {}
        
        name, tag_str = key.split('[', 1)
        tag_str = tag_str.rstrip(']')
        
        labels = {}
        for tag in tag_str.split(','):
            if '=' in tag:
                k, v = tag.split('=', 1)
                labels[k] = v
        
        return name, labels
    
    def _format_prometheus(self, name: str, labels: Dict[str, str]) -> str:
        """Format metric name with labels for Prometheus."""
        if not labels:
            return name
        
        label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
        return f"{name}{{{label_str}}}"
    
    def _export_loop(self) -> None:
        """
        Background loop to export metrics periodically.
        """
        while True:
            time.sleep(self._export_interval)
            self._export_metrics()
    
    def _export_metrics(self) -> None:
        """
        Export metrics to file.
        """
        try:
            metrics_path = Path(settings.BASE_DIR) / "data" / "metrics"
            metrics_path.mkdir(parents=True, exist_ok=True)
            
            # Export as JSON
            json_path = metrics_path / "metrics.json"
            with open(json_path, 'w') as f:
                json.dump(self.get_all_metrics(), f, indent=2, default=str)
            
            # Export as Prometheus
            prom_path = metrics_path / "metrics.prom"
            with open(prom_path, 'w') as f:
                f.write(self.export_prometheus())
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
    
    def reset(self) -> None:
        """
        Reset all metrics.
        """
        with self._metrics_lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.timers.clear()
            self._start_time = datetime.utcnow()
        
        logger.info("Metrics reset")


class PerformanceMonitor:
    """
    Monitor for tracking system performance metrics.
    """
    
    def __init__(self, metrics: MetricsCollector):
        self.metrics = metrics
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
    
    def start(self) -> None:
        """Start performance monitoring."""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop(self) -> None:
        """Stop performance monitoring."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Monitor loop collecting system metrics."""
        import psutil
        
        while self._running:
            try:
                # CPU
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics.set_gauge("system.cpu.percent", cpu_percent)
                
                # Memory
                memory = psutil.virtual_memory()
                self.metrics.set_gauge("system.memory.total", memory.total)
                self.metrics.set_gauge("system.memory.used", memory.used)
                self.metrics.set_gauge("system.memory.percent", memory.percent)
                
                # Disk
                disk = psutil.disk_usage('/')
                self.metrics.set_gauge("system.disk.total", disk.total)
                self.metrics.set_gauge("system.disk.used", disk.used)
                self.metrics.set_gauge("system.disk.percent", disk.percent)
                
                # Network
                net_io = psutil.net_io_counters()
                self.metrics.set_gauge("system.network.bytes_sent", net_io.bytes_sent)
                self.metrics.set_gauge("system.network.bytes_recv", net_io.bytes_recv)
                
                # Process
                process = psutil.Process()
                self.metrics.set_gauge("process.cpu.percent", process.cpu_percent())
                self.metrics.set_gauge("process.memory.rss", process.memory_info().rss)
                self.metrics.set_gauge("process.threads", process.num_threads())
                self.metrics.set_gauge("process.open_files", len(process.open_files()))
                
                time.sleep(10)  # Collect every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in performance monitor: {e}")
                time.sleep(30)