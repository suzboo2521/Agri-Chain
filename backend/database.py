"""Off-chain SQLite store for AgriChain.

The blockchain holds only compact, hash-linked event records (plus a
``data_hash`` for large payloads). The full data, uploaded documents and raw
sensor readings live here, off-chain. Document tamper-evidence works by
recomputing a file's SHA-256 and comparing it with the hash recorded on-chain.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional


def calculate_data_hash(data: dict[str, Any]) -> str:
    """Deterministic SHA-256 of a JSON-serialisable dict."""
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def calculate_file_hash(filepath: str, chunk_size: int = 4096) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as fh:
        while chunk := fh.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: str) -> None:
        self.path = str(path)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.init_db()

    # -- schema -------------------------------------------------------------
    def init_db(self) -> None:
        c = self.conn
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS batches (
                batch_id       TEXT PRIMARY KEY,
                crop           TEXT NOT NULL,
                farmer         TEXT NOT NULL,
                location       TEXT NOT NULL,
                quantity_kg    REAL NOT NULL,
                quality_grade  TEXT,
                status         TEXT DEFAULT 'REGISTERED',
                created_at     TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id    TEXT NOT NULL,
                event_type  TEXT NOT NULL,
                actor_id    TEXT NOT NULL,
                location    TEXT,
                timestamp   TEXT NOT NULL,
                data_json   TEXT,
                data_hash   TEXT,
                block_index INTEGER
            );
            CREATE TABLE IF NOT EXISTS documents (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id    TEXT NOT NULL,
                filename    TEXT NOT NULL,
                filepath    TEXT,
                sha256      TEXT NOT NULL,
                uploaded_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id     TEXT NOT NULL,
                temperature  REAL,
                humidity     REAL,
                gps_lat      REAL,
                gps_lon      REAL,
                timestamp    TEXT NOT NULL,
                anomaly_flag INTEGER DEFAULT 0
            );
            """
        )
        c.commit()

    def reset(self) -> None:
        for tbl in ("batches", "events", "documents", "sensor_readings"):
            self.conn.execute(f"DELETE FROM {tbl};")
        self.conn.commit()

    # -- batches ------------------------------------------------------------
    def next_sequence(self, crop: str, location: str, year: int) -> int:
        prefix = f"{crop[:4].upper()}-{location[:6].upper()}-{year}-"
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM batches WHERE batch_id LIKE ?",
            (prefix + "%",),
        ).fetchone()
        return int(row["n"]) + 1

    def create_batch(
        self,
        batch_id: str,
        crop: str,
        farmer: str,
        location: str,
        quantity_kg: float,
        quality_grade: str,
    ) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO batches
               (batch_id, crop, farmer, location, quantity_kg, quality_grade, status, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (batch_id, crop, farmer, location, quantity_kg, quality_grade,
             "REGISTERED", _now()),
        )
        self.conn.commit()

    def get_batch(self, batch_id: str) -> Optional[dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM batches WHERE batch_id = ?", (batch_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_batches(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM batches ORDER BY created_at DESC"
        ).fetchall()
        batches = [dict(r) for r in rows]
        event_counts = {
            r["batch_id"]: int(r["n"])
            for r in self.conn.execute(
                "SELECT batch_id, COUNT(*) AS n FROM events GROUP BY batch_id"
            )
        }
        alerted = {
            r["batch_id"]
            for r in self.conn.execute(
                "SELECT DISTINCT batch_id FROM sensor_readings WHERE anomaly_flag=1"
            )
        }
        for b in batches:
            b["events"] = event_counts.get(b["batch_id"], 0)
            b["has_alert"] = b["batch_id"] in alerted
        return batches

    def set_status(self, batch_id: str, status: str) -> None:
        self.conn.execute(
            "UPDATE batches SET status = ? WHERE batch_id = ?", (status, batch_id)
        )
        self.conn.commit()

    # -- events -------------------------------------------------------------
    def insert_event(
        self,
        batch_id: str,
        event_type: str,
        actor_id: str,
        location: str,
        timestamp: str,
        data: dict[str, Any],
        data_hash: str,
        block_index: int,
    ) -> None:
        self.conn.execute(
            """INSERT INTO events
               (batch_id, event_type, actor_id, location, timestamp, data_json, data_hash, block_index)
               VALUES (?,?,?,?,?,?,?,?)""",
            (batch_id, event_type, actor_id, location, timestamp,
             json.dumps(data), data_hash, block_index),
        )
        self.conn.commit()

    def get_events(self, batch_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM events WHERE batch_id = ? ORDER BY id", (batch_id,)
        ).fetchall()
        return [self._event_row(r) for r in rows]

    def recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (int(limit),)
        ).fetchall()
        return [self._event_row(r) for r in rows]

    def event_counts_by_type(self) -> dict[str, int]:
        return {
            r["event_type"]: int(r["n"])
            for r in self.conn.execute(
                "SELECT event_type, COUNT(*) AS n FROM events GROUP BY event_type"
            )
        }

    @staticmethod
    def _event_row(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        raw = d.pop("data_json", None)
        try:
            d["data"] = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            d["data"] = {}
        return d

    # -- documents ----------------------------------------------------------
    def insert_document(
        self, batch_id: str, filename: str, filepath: str, sha256: str
    ) -> None:
        self.conn.execute(
            """INSERT INTO documents (batch_id, filename, filepath, sha256, uploaded_at)
               VALUES (?,?,?,?,?)""",
            (batch_id, filename, filepath, sha256, _now()),
        )
        self.conn.commit()

    def list_documents(self, batch_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM documents WHERE batch_id = ? ORDER BY id", (batch_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    # -- sensor readings ----------------------------------------------------
    def insert_sensor_reading(
        self,
        batch_id: str,
        temperature: float,
        humidity: float,
        gps_lat: float,
        gps_lon: float,
        timestamp: str,
        anomaly_flag: int = 0,
    ) -> None:
        self.conn.execute(
            """INSERT INTO sensor_readings
               (batch_id, temperature, humidity, gps_lat, gps_lon, timestamp, anomaly_flag)
               VALUES (?,?,?,?,?,?,?)""",
            (batch_id, temperature, humidity, gps_lat, gps_lon, timestamp, anomaly_flag),
        )
        self.conn.commit()

    def get_sensor_readings(self, batch_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM sensor_readings WHERE batch_id = ? ORDER BY id", (batch_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def recent_sensor_readings(self, limit: int = 400) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM sensor_readings ORDER BY id DESC LIMIT ?", (int(limit),)
        ).fetchall()
        return [dict(r) for r in rows]

    def list_all_documents(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM documents ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    # -- aggregate stats (regulator dashboard) ------------------------------
    def stats(self) -> dict[str, int]:
        c = self.conn
        total = c.execute("SELECT COUNT(*) n FROM batches").fetchone()["n"]
        quality_failures = c.execute(
            "SELECT COUNT(DISTINCT batch_id) n FROM events "
            "WHERE event_type='QUALITY_CHECK' AND data_json LIKE '%\"quality_status\": \"FAILED\"%'"
        ).fetchone()["n"]
        temp_alerts = c.execute(
            "SELECT COUNT(DISTINCT batch_id) n FROM sensor_readings WHERE anomaly_flag=1"
        ).fetchone()["n"]
        return {
            "total_batches": int(total),
            "quality_failures": int(quality_failures),
            "temperature_alerts": int(temp_alerts),
        }
