"""
SQLite database connection management with connection pooling.
"""
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Dict, Any
from datetime import datetime
import json
import logging

from src.shared.config import settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Thread-safe SQLite connection manager with connection pooling.
    """
    
    _instance: Optional["DatabaseConnection"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "DatabaseConnection":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        self.db_path = Path(settings.DATABASE_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connection pool (simple list for SQLite)
        self._pool: list[sqlite3.Connection] = []
        self._pool_size = 5
        self._pool_lock = threading.Lock()
        
        # Initialize database
        self.initialize_database()
        
        self._initialized = True
        logger.info(f"Database initialized at {self.db_path}")
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        # IMPORTANT: Remove PARSE_DECLTYPES to avoid timestamp conversion issues
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            detect_types=0,  # DISABLE type detection completely
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -20000")
        conn.execute("PRAGMA temp_store = MEMORY")
        
        return conn
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool or create new one."""
        with self._pool_lock:
            if self._pool:
                conn = self._pool.pop()
                try:
                    conn.execute("SELECT 1")
                    return conn
                except sqlite3.Error:
                    pass
        
        return self._create_connection()
    
    def return_connection(self, conn: sqlite3.Connection) -> None:
        """Return connection to the pool."""
        with self._pool_lock:
            if len(self._pool) < self._pool_size:
                try:
                    conn.rollback()
                    self._pool.append(conn)
                except sqlite3.Error:
                    pass
    
    @contextmanager
    def get_cursor(self, commit: bool = True) -> Generator[sqlite3.Cursor, None, None]:
        """Get a database cursor with automatic commit/rollback."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def execute(self, query: str, params: tuple = ()) -> Optional[sqlite3.Cursor]:
        """Execute a query and return cursor."""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor
    
    def execute_many(self, query: str, params_list: list[tuple]) -> None:
        """Execute many queries."""
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch a single row as dictionary."""
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def fetch_all(self, query: str, params: tuple = ()) -> list[Dict[str, Any]]:
        """Fetch all rows as list of dictionaries."""
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def initialize_database(self) -> None:
        """Create all tables if they don't exist."""
        with self.get_cursor() as cursor:
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    full_name TEXT,
                    role TEXT NOT NULL DEFAULT 'user',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    is_verified INTEGER NOT NULL DEFAULT 0,
                    avatar_url TEXT,
                    bio TEXT,
                    preferences TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                    last_login_at TEXT,
                    email_verified_at TEXT
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
            
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    system_prompt TEXT,
                    model_parameters TEXT DEFAULT '{}',
                    tags TEXT DEFAULT '[]',
                    is_pinned INTEGER NOT NULL DEFAULT 0,
                    is_favorite INTEGER NOT NULL DEFAULT 0,
                    total_tokens INTEGER NOT NULL DEFAULT 0,
                    message_count INTEGER NOT NULL DEFAULT 0,
                    summary TEXT,
                    category TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at)")
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL,
                    token_count INTEGER NOT NULL DEFAULT 0,
                    model_used TEXT,
                    generation_time_ms REAL,
                    finish_reason TEXT,
                    is_edited INTEGER NOT NULL DEFAULT 0,
                    edited_at TEXT,
                    original_content TEXT,
                    message_metadata TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                    UNIQUE(conversation_id, sequence_number)
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)")
            
            # Assets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    asset_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    mime_type TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    prompt TEXT,
                    model_used TEXT,
                    generation_params TEXT DEFAULT '{}',
                    generation_time_ms REAL,
                    tags TEXT DEFAULT '[]',
                    is_favorite INTEGER NOT NULL DEFAULT 0,
                    is_public INTEGER NOT NULL DEFAULT 0,
                    view_count INTEGER NOT NULL DEFAULT 0,
                    download_count INTEGER NOT NULL DEFAULT 0,
                    conversation_id TEXT,
                    chart_configuration_id TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_user_id ON assets(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_asset_type ON assets(asset_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_created_at ON assets(created_at)")
            
            # API Keys table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    key_hash TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    prefix TEXT NOT NULL,
                    scopes TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    last_used_at TEXT,
                    expires_at TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Audit logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
        
        logger.info("Database tables initialized")


# Singleton instance
db_connection = DatabaseConnection()