
import json
import sqlite3
import logging

from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Store the database inside app/data/
APP_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = APP_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "chat_history.db"


def get_connection():
    """
    Create a SQLite database connection.
    """

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def get_current_time():
    """
    Return the current UTC timestamp.
    """

    return datetime.now(timezone.utc).isoformat()


def initialize_conversation_database():
    """
    Create conversation and message tables if they
    do not already exist.
    """

    connection = get_connection()

    try:

        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sources_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,

                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE,

                CHECK (role IN ('user', 'assistant'))
            );

            CREATE INDEX IF NOT EXISTS
                idx_conversations_document_id
            ON conversations(document_id);

            CREATE INDEX IF NOT EXISTS
                idx_messages_conversation_id
            ON messages(conversation_id);

            CREATE INDEX IF NOT EXISTS
                idx_conversations_updated_at
            ON conversations(updated_at);
            """
        )

        connection.commit()

        logger.info(
            "Conversation database initialized successfully."
        )

    finally:
        connection.close()


def create_conversation(
    document_id: str,
    title: str
) -> str:
    """
    Create a new conversation for an uploaded document.
    """

    conversation_id = uuid4().hex
    current_time = get_current_time()

    connection = get_connection()

    try:

        connection.execute(
            """
            INSERT INTO conversations (
                id,
                document_id,
                title,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                document_id,
                title[:100],
                current_time,
                current_time
            )
        )

        connection.commit()

        return conversation_id

    finally:
        connection.close()


def get_conversation(conversation_id: str):
    """
    Retrieve conversation metadata.
    """

    connection = get_connection()

    try:

        row = connection.execute(
            """
            SELECT *
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,)
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def save_message(
    conversation_id: str,
    role: str,
    content: str,
    sources: list = None
) -> dict:
    """
    Save a user or assistant message.
    """

    if role not in ("user", "assistant"):
        raise ValueError("Invalid message role.")

    if not content or not content.strip():
        raise ValueError("Message content cannot be empty.")

    current_time = get_current_time()

    sources_json = json.dumps(
        sources or [],
        ensure_ascii=False
    )

    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            INSERT INTO messages (
                conversation_id,
                role,
                content,
                sources_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                role,
                content,
                sources_json,
                current_time
            )
        )

        connection.execute(
            """
            UPDATE conversations
            SET updated_at = ?
            WHERE id = ?
            """,
            (current_time, conversation_id)
        )

        connection.commit()

        return {
            "id": cursor.lastrowid,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "sources": sources or [],
            "created_at": current_time
        }

    finally:
        connection.close()


def get_recent_messages(
    conversation_id: str,
    limit: int = 10
) -> list:
    """
    Retrieve the latest messages in chronological order.
    """

    if not 1 <= limit <= 50:
        raise ValueError("Message limit must be between 1 and 50.")

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (conversation_id, limit)
        ).fetchall()

        messages = [
            dict(row)
            for row in reversed(rows)
        ]

        return messages

    finally:
        connection.close()


def get_conversation_messages(
    conversation_id: str
) -> list:
    """
    Retrieve the complete message history.
    """

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                id,
                conversation_id,
                role,
                content,
                sources_json,
                created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,)
        ).fetchall()

        messages = []

        for row in rows:

            message = dict(row)

            message["sources"] = json.loads(
                message.pop("sources_json")
            )

            messages.append(message)

        return messages

    finally:
        connection.close()


def list_conversations(
    document_id: str
) -> list:
    """
    List all conversations associated with a document.
    """

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                c.id,
                c.document_id,
                c.title,
                c.created_at,
                c.updated_at,
                COUNT(m.id) AS message_count
            FROM conversations c
            LEFT JOIN messages m
                ON c.id = m.conversation_id
            WHERE c.document_id = ?
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            """,
            (document_id,)
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def delete_conversation(conversation_id: str) -> bool:
    """
    Delete a conversation and all its messages.
    """

    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            DELETE FROM conversations
            WHERE id = ?
            """,
            (conversation_id,)
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()
