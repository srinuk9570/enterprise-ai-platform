"""
Loading spinner component for async operations.
"""
import streamlit as st
from typing import Optional, Callable, Any
from contextlib import contextmanager
import time
import threading


class LoadingSpinner:
    """
    Custom loading spinner with progress tracking.
    """
    
    def __init__(self, message: str = "Loading..."):
        self.message = message
        self._progress = 0
        self._status = ""
    
    @contextmanager
    def spinner(self, message: Optional[str] = None):
        """
        Context manager for loading spinner.
        
        Usage:
            with LoadingSpinner("Processing...").spinner():
                result = long_running_task()
        """
        msg = message or self.message
        
        with st.spinner(msg):
            yield
    
    def with_progress(self, total_steps: int = 100):
        """
        Create a progress-aware context.
        
        Usage:
            with spinner.with_progress(100) as progress:
                for i in range(100):
                    do_work()
                    progress(i + 1)
        """
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        class ProgressContext:
            def __init__(self, pb, st_text, total):
                self.pb = pb
                self.st = st_text
                self.total = total
                self.current = 0
            
            def update(self, value: int, message: Optional[str] = None):
                self.current = value
                self.pb.progress(min(value / self.total, 1.0))
                if message:
                    self.st.text(message)
                elif value < self.total:
                    self.st.text(f"Processing... {value}/{self.total}")
                else:
                    self.st.text("Complete!")
            
            def increment(self, message: Optional[str] = None):
                self.current += 1
                self.update(self.current, message)
        
        return ProgressContext(progress_bar, status_text, total_steps)


@contextmanager
def loading_spinner(message: str = "Loading..."):
    """
    Simple loading spinner context manager.
    
    Usage:
        with loading_spinner("Fetching data..."):
            data = fetch_data()
    """
    with st.spinner(message):
        yield


def with_loading(message: str = "Loading..."):
    """
    Decorator for functions that need a loading spinner.
    
    Usage:
        @with_loading("Processing data...")
        def process_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            with st.spinner(message):
                return func(*args, **kwargs)
        return wrapper
    return decorator


class AsyncLoader:
    """
    Async loader with status updates.
    """
    
    def __init__(self):
        self._status_container = None
        self._progress_bar = None
    
    def start(self, message: str = "Starting..."):
        """Initialize loader UI."""
        self._status_container = st.empty()
        self._progress_bar = st.progress(0)
        self._status_container.text(message)
    
    def update(self, progress: float, message: Optional[str] = None):
        """Update progress and message."""
        if self._progress_bar:
            self._progress_bar.progress(min(progress, 1.0))
        if message and self._status_container:
            self._status_container.text(message)
    
    def complete(self, message: str = "Complete!"):
        """Mark as complete."""
        if self._progress_bar:
            self._progress_bar.progress(1.0)
        if self._status_container:
            self._status_container.text(message)
    
    def error(self, message: str = "Error occurred"):
        """Show error state."""
        if self._status_container:
            self._status_container.error(message)
    
    def clear(self):
        """Clear loader UI."""
        if self._status_container:
            self._status_container.empty()
        if self._progress_bar:
            self._progress_bar.empty()


class BackgroundTaskLoader:
    """
    Loader for background tasks with status polling.
    """
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.loader = AsyncLoader()
    
    def run_with_polling(
        self,
        start_task: Callable,
        poll_status: Callable,
        interval: float = 1.0,
    ) -> Optional[Any]:
        """
        Run a task with polling for status updates.
        
        Args:
            start_task: Function that starts the task and returns task_id
            poll_status: Function that polls task status
            interval: Polling interval in seconds
        
        Returns:
            Task result or None if failed
        """
        self.loader.start("Starting task...")
        
        try:
            task_id = start_task()
            
            while True:
                status = poll_status(task_id)
                
                if status.get("status") == "completed":
                    self.loader.complete("Task completed!")
                    return status.get("result")
                elif status.get("status") == "failed":
                    self.loader.error(f"Task failed: {status.get('error', 'Unknown error')}")
                    return None
                elif status.get("status") == "running":
                    progress = status.get("progress", 0)
                    message = status.get("message", "Processing...")
                    self.loader.update(progress / 100, message)
                else:
                    self.loader.update(0.5, "Waiting...")
                
                time.sleep(interval)
                
        except Exception as e:
            self.loader.error(f"Error: {str(e)}")
            return None


def show_pulse_animation():
    """Show a pulsing animation while loading."""
    st.markdown("""
    <style>
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    .pulse-animation {
        animation: pulse 1.5s ease-in-out infinite;
        text-align: center;
        padding: 20px;
        font-size: 1.2em;
        color: #00d2ff;
    }
    </style>
    <div class="pulse-animation">
        ⏳ Processing...
    </div>
    """, unsafe_allow_html=True)


def show_skeleton_loader(lines: int = 5):
    """
    Show skeleton loader animation.
    """
    skeleton_html = """
    <style>
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    .skeleton {
        background: linear-gradient(90deg, #2d2d44 25%, #3d3d5c 50%, #2d2d44 75%);
        background-size: 1000px 100%;
        animation: shimmer 2s infinite;
        border-radius: 4px;
        height: 20px;
        margin: 10px 0;
    }
    .skeleton-short {
        width: 60%;
    }
    .skeleton-medium {
        width: 80%;
    }
    </style>
    """
    
    html = skeleton_html
    for i in range(lines):
        width_class = "skeleton-short" if i % 3 == 0 else "skeleton-medium"
        html += f'<div class="skeleton {width_class}"></div>'
    
    st.markdown(html, unsafe_allow_html=True)