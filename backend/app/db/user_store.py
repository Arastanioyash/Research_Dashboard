import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings
from app.core.security import hash_password


@dataclass(slots=True)
class User:
    username: str
    hashed_password: str


class UserStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._seed_default_user()

    def _connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    hashed_password TEXT NOT NULL
                )
                """
            )

    def _seed_default_user(self) -> None:
        if self.get_user("admin"):
            return
        self.create_user("admin", "admin1234")

    def create_user(self, username: str, password: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO users (username, hashed_password) VALUES (?, ?)",
                (username, hash_password(password)),
            )

    def get_user(self, username: str) -> User | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT username, hashed_password FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        if row is None:
            return None
        return User(username=row[0], hashed_password=row[1])


user_store = UserStore(get_settings().user_db_path)
