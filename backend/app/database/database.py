
import aiosqlite
from pathlib import Path


DATABASE_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "knowra.db"
)


async def get_connection(database_path=DATABASE_PATH):
    """
    Open and return a database connection.
    """

    database_path = Path(database_path)

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = await aiosqlite.connect(database_path)
    connection.row_factory = aiosqlite.Row

    return connection


async def initialize_database(database_path=DATABASE_PATH):
    """
    Create the initial database schema if it does not exist.
    """

    connection = await get_connection(database_path)

    try:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS learner_concept_states (
                learner_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                knowledge_probability REAL NOT NULL,
                retention_anchor REAL NOT NULL,
                retention_anchor_at TEXT,
                attempts INTEGER NOT NULL DEFAULT 0,
                correct_attempts INTEGER NOT NULL DEFAULT 0,
                last_attempt_at TEXT,
                misconception_history TEXT NOT NULL DEFAULT '[]',
                PRIMARY KEY (learner_id, concept_id)
            )
            """
        )

        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS answer_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learner_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                selected_option_id TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                misconception_id TEXT,
                submitted_at TEXT NOT NULL
            )
            """
        )

        await connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_answer_events_learner
            ON answer_events (learner_id)
            """
        )

        await connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_answer_events_concept
            ON answer_events (learner_id, concept_id)
            """
        )

        await connection.commit()

    finally:
        await connection.close()
