"""Cache SQLite des réponses brutes Open-Meteo (6 h par cellule) et de la climatologie du sol.

Clé : (cellule, type, seau). Le scoring se recalcule toujours depuis le cache ; on ne rappelle
Open-Meteo que si le seau courant manque. Si Open-Meteo est injoignable, `latest` sert la
dernière réponse connue, marquée périmée par l'appelant.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BUCKET_HOURS = 6


def bucket_now(now: datetime) -> str:
    """Seau de 6 h en UTC : `2026-10-17T12`."""
    h = (now.hour // BUCKET_HOURS) * BUCKET_HOURS
    return now.astimezone(UTC).strftime("%Y-%m-%d") + f"T{h:02d}"


class WeatherCache:
    def __init__(self, path: Path | str = ":memory:"):
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS raw (
                cell_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                bucket TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (cell_id, kind, bucket)
            )
            """
        )
        self.db.commit()

    def get(self, cell_id: str, kind: str, bucket: str) -> Any | None:
        row = self.db.execute(
            "SELECT payload FROM raw WHERE cell_id = ? AND kind = ? AND bucket = ?",
            (cell_id, kind, bucket),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def latest(self, cell_id: str, kind: str) -> tuple[Any, str] | None:
        """Dernière réponse connue (payload, fetched_at), quel que soit le seau."""
        row = self.db.execute(
            "SELECT payload, fetched_at FROM raw WHERE cell_id = ? AND kind = ? "
            "ORDER BY fetched_at DESC LIMIT 1",
            (cell_id, kind),
        ).fetchone()
        return (json.loads(row[0]), row[1]) if row else None

    def put(self, cell_id: str, kind: str, bucket: str, payload: Any, now: datetime) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO raw VALUES (?, ?, ?, ?, ?)",
            (cell_id, kind, bucket, now.astimezone(UTC).isoformat(), json.dumps(payload)),
        )
        # On ne garde qu'un seau par (cellule, type) : le plus récent suffit au mode périmé.
        self.db.execute(
            "DELETE FROM raw WHERE cell_id = ? AND kind = ? AND bucket != ?",
            (cell_id, kind, bucket),
        )
        self.db.commit()

    def close(self) -> None:
        self.db.close()
