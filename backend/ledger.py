"""Process-wide singletons: one Blockchain + one SQLite store.

The chain lives *only* here, inside the FastAPI process, and is persisted to
``chain.json`` so restarts don't lose state. The Streamlit UI and all
seed/demo scripts talk to this via HTTP — they never build their own chain,
which guarantees a single authoritative ledger.
"""
from __future__ import annotations

from config import CHAIN_PATH, DB_PATH, DIFFICULTY

from backend.blockchain import Blockchain
from backend.database import Database

_chain: Blockchain | None = None
_db: Database | None = None


def get_chain() -> Blockchain:
    global _chain
    if _chain is None:
        if CHAIN_PATH.exists():
            try:
                _chain = Blockchain.load(CHAIN_PATH, difficulty=DIFFICULTY)
            except Exception:
                _chain = Blockchain(difficulty=DIFFICULTY)
        else:
            _chain = Blockchain(difficulty=DIFFICULTY)
    return _chain


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database(DB_PATH)
    return _db


def persist() -> None:
    if _chain is not None:
        _chain.save(CHAIN_PATH)


def reset_all() -> None:
    """Wipe chain + DB back to a clean genesis state (used by /debug/reset)."""
    global _chain
    _chain = Blockchain(difficulty=DIFFICULTY)
    get_db().reset()
    persist()
