import os
import sqlite3
from pathlib import Path

from tools.safety import redact_text


DB_PATH = Path(
    os.getenv(
        "AGENT_MEMORY_DB",
        str(Path(__file__).resolve().parent.parent / "agent_memory.db"),
    )
)


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    return connection


def save_memory(content: str) -> dict:
    """Save an important piece of information to persistent agent memory."""

    if not content or not content.strip():
        return {"success": False, "error": "Memory content cannot be empty."}

    content = redact_text(content.strip(), max_length=5000)

    if len(content) > 5000:
        return {"success": False, "error": "Memory is limited to 5000 characters."}

    connection = _connect()

    try:
        cursor = connection.execute(
            "INSERT INTO memories (content) VALUES (?)",
            (content,),
        )
        connection.commit()

        return {
            "success": True,
            "memory_id": cursor.lastrowid,
            "content": content,
        }
    finally:
        connection.close()


def search_memory(query: str) -> dict:
    """Search persistent memories for matching information."""

    if not query or not query.strip():
        return {"success": False, "error": "Search query cannot be empty."}

    connection = _connect()

    try:
        rows = connection.execute(
            """
            SELECT id, content, created_at
            FROM memories
            WHERE content LIKE ?
            ORDER BY id DESC
            LIMIT 20
            """,
            (f"%{query.strip()}%",),
        ).fetchall()

        return {
            "success": True,
            "query": query,
            "memories": [
                {"id": row[0], "content": row[1], "created_at": row[2]}
                for row in rows
            ],
        }
    finally:
        connection.close()


def list_memories() -> dict:
    """List recent persistent memories."""

    connection = _connect()

    try:
        rows = connection.execute(
            """
            SELECT id, content, created_at
            FROM memories
            ORDER BY id DESC
            LIMIT 50
            """
        ).fetchall()

        return {
            "success": True,
            "memories": [
                {"id": row[0], "content": row[1], "created_at": row[2]}
                for row in rows
            ],
        }
    finally:
        connection.close()
