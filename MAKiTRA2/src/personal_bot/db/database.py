from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
import sqlite3


class Database:
    """The only class responsible for communicating with SQLite."""

    def __init__(self, database_path: Path) -> None:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")

    def execute(
        self,
        statement: str,
        parameters: Sequence[object] = (),
    ) -> sqlite3.Cursor:
        return self._connection.execute(statement, parameters)

    def execute_script(self, script: str) -> None:
        self._connection.executescript(script)

    @contextmanager
    def transaction(self) -> Iterator[None]:
        self._connection.execute("BEGIN IMMEDIATE")

        try:
            yield
        except Exception:
            self._connection.rollback()
            raise
        else:
            self._connection.commit()

    def close(self) -> None:
        self._connection.close()
