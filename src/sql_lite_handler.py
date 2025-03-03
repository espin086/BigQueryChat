"""
This module provides a `DatabaseManager` class to interact with an SQLite
database for storing and retrieving chat conversations and messages.
It includes methods for creating tables, inserting conversations/messages,
retrieving conversation history, and deleting records.

Dependencies:
- logging (For logging errors and information)
- sqlite3 (For database interactions)
- config (For retrieving database configurations)
"""

import logging
import sqlite3
from .utils import config


class DatabaseManager:
    """
    A class to manage SQLite database operations for storing and retrieving
    chatbot conversation history.

    Attributes:
        db_path (str): The path to the SQLite database file.

    Methods:
        create_db_if_not_there(): Ensures the necessary database tables exist.
        save_conversation(topic): Saves a new conversation and returns its ID.
        save_message(conversation_id, sender, message): Saves a message linked to a conversation.
        delete_conversation(conversation_id): Deletes a conversation and its messages.
        get_all_topics(): Retrieves all conversation topics.
        get_conversation_id_by_topic(conversation_to_delete): Gets the conversation ID by topic.
        get_all_conversations(): Retrieves all conversations ordered by timestamp.
        get_messages_by_conversation(conversation_id): Retrieves all messages for a
            specific conversation.
    """

    def __init__(self):
        """Initialize the DatabaseManager with the database path."""
        self.db_path = config.DATABASE

    def _connect(self):
        """Connect to the database."""
        return sqlite3.connect(self.db_path)

    def create_db_if_not_there(self):
        """Create the database and tables if they do not exist."""
        logging.info("Checking and creating database if not present.")
        conn = self._connect()
        c = conn.cursor()

        try:
            c.execute(
                f"""CREATE TABLE IF NOT EXISTS {config.TABLE_CONVERSATIONS}
                        (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            topic TEXT,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                        )"""
            )
            c.execute(
                f"""CREATE TABLE IF NOT EXISTS {config.TABLE_MESSAGES}
                        (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            conversation_id INTEGER,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            sender TEXT,
                            message TEXT,
                            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                        )"""
            )
            conn.commit()
            logging.info(
                "Successfully created or ensured the table %s and %s exists.",
                config.TABLE_CONVERSATIONS,
                config.TABLE_MESSAGES,
            )
        except Exception as e:
            logging.error("Failed to create tables: %s", e)
        finally:
            conn.close()

    def save_conversation(self, topic):
        """Save a conversation to the database."""
        conn = self._connect()
        c = conn.cursor()
        try:
            c.execute(
                """
                INSERT INTO conversations (topic)
                VALUES (?)
                """,
                (topic,),
            )
            conn.commit()
            return c.lastrowid
        finally:
            conn.close()

    def save_message(self, conversation_id, sender, message):
        """Save a message to the database."""
        conn = self._connect()
        c = conn.cursor()
        try:
            c.execute(
                """
                INSERT INTO messages (conversation_id, sender, message)
                VALUES (?, ?, ?)
                """,
                (conversation_id, sender, message),
            )
            conn.commit()
        finally:
            conn.close()

    def delete_conversation(self, conversation_id):
        """Delete a conversation and its messages."""
        conn = self._connect()
        c = conn.cursor()
        try:
            c.execute(
                "DELETE FROM messages WHERE conversation_id = ?", (conversation_id,)
            )
            c.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()
        finally:
            conn.close()

    def get_all_topics(self):
        """Retrieve all conversation topics."""
        try:
            with self._connect() as conn:
                c = conn.cursor()
                return c.execute("SELECT topic FROM conversations").fetchall()
        except sqlite3.Error as e:
            logging.error("Failed to fetch all topics: %s", e)
            return []

    def get_conversation_id_by_topic(self, conversation_to_delete):
        """Retrieve the ID of a conversation by its topic."""
        try:
            with self._connect() as conn:
                c = conn.cursor()
                result = c.execute(
                    "SELECT id FROM conversations WHERE topic = ?",
                    (conversation_to_delete,),
                ).fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            logging.error("Failed to fetch conversation ID by topic: %s", e)
            return None

    def get_all_conversations(self):
        """Retrieve all conversations with details ordered by timestamp (descending)."""
        try:
            with self._connect() as conn:
                c = conn.cursor()
                return c.execute(
                    "SELECT id, topic, timestamp FROM conversations ORDER BY timestamp DESC"
                ).fetchall()
        except sqlite3.Error as e:
            logging.error("Failed to fetch all conversations: %s", e)
            return []

    def get_messages_by_conversation(self, conversation_id):
        """Retrieve all messages for a specific conversation, ordered by timestamp."""
        try:
            with self._connect() as conn:
                c = conn.cursor()
                return c.execute(
                    """
                    SELECT sender, message FROM messages
                    WHERE conversation_id = ? ORDER BY timestamp
                    """,
                    (conversation_id,),
                ).fetchall()
        except sqlite3.Error as e:
            logging.error("Failed to fetch messages by conversation: %s", e)
            return []
