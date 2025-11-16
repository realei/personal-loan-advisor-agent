"""Multi-user conversation memory management using MongoDB.

This module provides persistent, multi-user conversation history storage
for the Personal Loan Advisor Agent with integrated evaluation support.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.collection import Collection

from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class ConversationMemory:
    """MongoDB-based conversation memory for multi-user support with evaluation."""

    def __init__(
        self,
        mongodb_uri: str = "mongodb://admin:password123@localhost:27017/",
        database_name: str = "loan_advisor",
        enable_evaluation: bool = True,
    ):
        """Initialize conversation memory with MongoDB.

        Args:
            mongodb_uri: MongoDB connection URI
            database_name: Name of the database to use
            enable_evaluation: Enable automatic evaluation of responses
        """
        self.client = MongoClient(mongodb_uri)
        self.db: Database = self.client[database_name]

        # Collections
        self.sessions: Collection = self.db["sessions"]
        self.messages: Collection = self.db["messages"]
        self.evaluations: Collection = self.db["evaluations"]

        # Current session info
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None

        # Evaluation manager (lazy initialization)
        self.enable_evaluation = enable_evaluation
        self._evaluation_manager = None

        self._init_indexes()

    def _init_indexes(self):
        """Initialize database indexes for performance."""
        # Index on session_id and timestamp for fast message retrieval
        self.messages.create_index([("session_id", ASCENDING), ("timestamp", ASCENDING)])

        # Index on user_id for user-specific queries
        self.sessions.create_index([("user_id", ASCENDING), ("last_active", DESCENDING)])

        # Index on session_id for fast lookups
        self.sessions.create_index("session_id", unique=True)

        # Evaluation indexes
        self.evaluations.create_index([("session_id", ASCENDING), ("created_at", DESCENDING)])
        self.evaluations.create_index("evaluation_id", unique=True)
        self.evaluations.create_index([("user_id", ASCENDING), ("status", ASCENDING)])

    def start_session(self, user_id: str) -> str:
        """Start a new conversation session for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Session ID
        """
        session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.user_id = user_id
        self.session_id = session_id

        session_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now(),
            "last_active": datetime.now(),
            "message_count": 0,
        }

        self.sessions.insert_one(session_doc)
        logger.info(f"Started new session: {session_id} for user: {user_id}")
        return session_id

    def resume_session(self, session_id: str) -> bool:
        """Resume an existing session.

        Args:
            session_id: Session ID to resume

        Returns:
            True if session exists and was resumed, False otherwise
        """
        session = self.sessions.find_one({"session_id": session_id})
        if session:
            self.session_id = session_id
            self.user_id = session["user_id"]

            # Update last_active timestamp
            self.sessions.update_one(
                {"session_id": session_id},
                {"$set": {"last_active": datetime.now()}}
            )
            logger.info(f"Resumed session: {session_id} for user: {self.user_id}")
            return True

        logger.warning(f"Failed to resume session: {session_id} (not found)")
        return False

    def add_message(self, role: str, content: str):
        """Add a message to the current session.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        if not self.session_id:
            raise ValueError("No active session. Call start_session() or resume_session() first.")

        message_doc = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
        }

        self.messages.insert_one(message_doc)

        # Update session last_active and message_count
        self.sessions.update_one(
            {"session_id": self.session_id},
            {
                "$set": {"last_active": datetime.now()},
                "$inc": {"message_count": 1}
            }
        )

    def get_conversation_history(
        self,
        limit: Optional[int] = None,
        include_system: bool = False
    ) -> list[dict]:
        """Get conversation history for the current session.

        Args:
            limit: Maximum number of messages to retrieve (most recent)
            include_system: Whether to include system messages

        Returns:
            List of messages in format: [{"role": "user", "content": "..."}, ...]
        """
        if not self.session_id:
            return []

        query = {"session_id": self.session_id}
        if not include_system:
            query["role"] = {"$ne": "system"}

        cursor = self.messages.find(query).sort("timestamp", ASCENDING)

        if limit:
            cursor = cursor.limit(limit)

        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in cursor
        ]

    def get_user_sessions(self, user_id: str, limit: int = 10) -> list[dict]:
        """Get all sessions for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return

        Returns:
            List of session info
        """
        cursor = self.sessions.find(
            {"user_id": user_id}
        ).sort("last_active", DESCENDING).limit(limit)

        return [
            {
                "session_id": session["session_id"],
                "created_at": session["created_at"],
                "last_active": session["last_active"],
                "message_count": session.get("message_count", 0),
            }
            for session in cursor
        ]

    def delete_session(self, session_id: Optional[str] = None):
        """Delete a session and all its messages.

        Args:
            session_id: Session to delete (default: current session)
        """
        target_id = session_id or self.session_id
        if not target_id:
            return

        # Delete all messages in the session
        self.messages.delete_many({"session_id": target_id})

        # Delete the session
        self.sessions.delete_one({"session_id": target_id})

        if target_id == self.session_id:
            self.session_id = None
            self.user_id = None

    def clear_session(self):
        """Clear the current session from memory (keep in DB)."""
        self.session_id = None
        self.user_id = None

    def get_session_info(self) -> Optional[dict]:
        """Get information about the current session.

        Returns:
            Session information or None if no active session
        """
        if not self.session_id:
            return None

        session = self.sessions.find_one({"session_id": self.session_id})
        if session:
            return {
                "session_id": session["session_id"],
                "user_id": session["user_id"],
                "created_at": session["created_at"],
                "last_active": session["last_active"],
                "message_count": session.get("message_count", 0),
            }
        return None

    def get_total_users(self) -> int:
        """Get total number of unique users.

        Returns:
            Count of unique users
        """
        return len(self.sessions.distinct("user_id"))

    def get_total_sessions(self) -> int:
        """Get total number of sessions across all users.

        Returns:
            Total session count
        """
        return self.sessions.count_documents({})

    def get_user_message_count(self, user_id: str) -> int:
        """Get total message count for a user across all sessions.

        Args:
            user_id: User identifier

        Returns:
            Total message count
        """
        return self.messages.count_documents({"user_id": user_id})

    @property
    def evaluation_manager(self):
        """Get or create evaluation manager (lazy initialization).

        Returns:
            EvaluationManager instance
        """
        if self._evaluation_manager is None and self.enable_evaluation:
            from src.evaluation.evaluation_manager import EvaluationManager
            self._evaluation_manager = EvaluationManager(
                evaluations_collection=self.evaluations
            )
        return self._evaluation_manager

    def evaluate_interaction(
        self,
        user_input: str,
        agent_output: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Submit an evaluation for the current interaction (async).

        Args:
            user_input: User's input message
            agent_output: Agent's response
            context: Context information (user profile, loan details, etc.)
            metadata: Additional metadata

        Returns:
            Evaluation ID or None if evaluation is disabled
        """
        if not self.enable_evaluation:
            logger.debug("Evaluation disabled, skipping")
            return None

        if not self.session_id:
            logger.warning("No active session, cannot evaluate interaction")
            return None

        logger.debug(f"Submitting evaluation for session {self.session_id}")

        return self.evaluation_manager.evaluate_async(
            session_id=self.session_id,
            user_id=self.user_id,
            user_input=user_input,
            agent_output=agent_output,
            context=context,
            metadata=metadata,
        )

    def get_session_evaluations(self, limit: Optional[int] = None):
        """Get all evaluations for the current session.

        Args:
            limit: Maximum number of results

        Returns:
            List of evaluation documents
        """
        if not self.session_id or not self.enable_evaluation:
            return []

        return self.evaluation_manager.get_session_evaluations(
            self.session_id,
            limit=limit
        )

    def get_session_evaluation_stats(self) -> Dict[str, Any]:
        """Get evaluation statistics for the current session.

        Returns:
            Statistics dictionary
        """
        if not self.session_id or not self.enable_evaluation:
            return {}

        return self.evaluation_manager.get_session_statistics(self.session_id)

    def close(self):
        """Close MongoDB connection and cleanup."""
        if self._evaluation_manager:
            self._evaluation_manager.close()
        if self.client:
            self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
