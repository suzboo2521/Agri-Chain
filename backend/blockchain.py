"""Custom Proof-of-Work blockchain for AgriChain.

Design notes
------------
* A block's ``hash`` is computed from its *content* (index, timestamp,
  transactions, previous_hash, nonce) — the stored ``hash`` field itself is
  excluded from the digest, and serialization is canonical
  (``json.dumps(sort_keys=True)``).
* ``is_chain_valid()`` recomputes every block's hash from its *current*
  transactions and compares it to the stored, mined hash. Mutating a stored
  transaction without re-mining therefore breaks validation — this is exactly
  what powers the tamper-detection demo.
* Only lightweight event records (with a ``data_hash`` for large payloads) are
  ever placed on-chain; the full data lives off-chain in SQLite.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any


class Block:
    def __init__(
        self,
        index: int,
        transactions: list[dict[str, Any]],
        previous_hash: str,
        timestamp: float | None = None,
        nonce: int = 0,
        hash: str | None = None,
    ) -> None:
        self.index = index
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = hash if hash is not None else self.compute_hash()

    def compute_hash(self) -> str:
        """SHA-256 over canonical content (excludes the stored ``hash``)."""
        block_string = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "transactions": self.transactions,
                "previous_hash": self.previous_hash,
                "nonce": self.nonce,
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty: int) -> None:
        """Increment the nonce until the hash has ``difficulty`` leading zeros."""
        target = "0" * difficulty
        self.hash = self.compute_hash()
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.compute_hash()

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Block":
        return cls(
            index=d["index"],
            transactions=d["transactions"],
            previous_hash=d["previous_hash"],
            timestamp=d["timestamp"],
            nonce=d["nonce"],
            hash=d["hash"],
        )


class Blockchain:
    GENESIS_PREVIOUS_HASH = "0"

    def __init__(self, difficulty: int = 3) -> None:
        self.difficulty = difficulty
        self.chain: list[Block] = []
        self.pending_transactions: list[dict[str, Any]] = []
        self.create_genesis_block()

    # -- construction -------------------------------------------------------
    def create_genesis_block(self) -> None:
        genesis = Block(0, [], self.GENESIS_PREVIOUS_HASH)
        genesis.mine_block(self.difficulty)
        self.chain = [genesis]
        self.pending_transactions = []

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    # -- transactions & mining ---------------------------------------------
    def add_transaction(self, transaction: dict[str, Any]) -> None:
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self) -> Block:
        """Pack all pending transactions into a block, mine, append, clear."""
        block = Block(
            index=len(self.chain),
            transactions=list(self.pending_transactions),
            previous_hash=self.get_latest_block().hash,
        )
        block.mine_block(self.difficulty)
        self.chain.append(block)
        self.pending_transactions = []
        return block

    # -- validation ---------------------------------------------------------
    def is_chain_valid(self) -> bool:
        # genesis integrity
        genesis = self.chain[0]
        if genesis.hash != genesis.compute_hash():
            return False
        if genesis.previous_hash != self.GENESIS_PREVIOUS_HASH:
            return False
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            # 1) content still hashes to the stored hash?
            if current.hash != current.compute_hash():
                return False
            # 2) linkage to the previous block intact?
            if current.previous_hash != previous.hash:
                return False
        return True

    # -- queries ------------------------------------------------------------
    def get_batch_history(self, batch_id: str) -> list[dict[str, Any]]:
        """All transactions for a batch, in chain order, with block context."""
        history: list[dict[str, Any]] = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.get("batch_id") == batch_id:
                    history.append(
                        {
                            "block_index": block.index,
                            "block_hash": block.hash,
                            "timestamp": block.timestamp,
                            "transaction": tx,
                        }
                    )
        return history

    def all_transactions(self) -> list[dict[str, Any]]:
        return [tx for block in self.chain for tx in block.transactions]

    # -- persistence --------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "difficulty": self.difficulty,
            "chain": [b.to_dict() for b in self.chain],
            "pending_transactions": self.pending_transactions,
        }

    def save(self, path) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load(cls, path, difficulty: int = 3) -> "Blockchain":
        with open(path) as f:
            data = json.load(f)
        bc = cls.__new__(cls)  # bypass __init__ so we don't re-create genesis
        bc.difficulty = data.get("difficulty", difficulty)
        bc.chain = [Block.from_dict(b) for b in data["chain"]]
        bc.pending_transactions = data.get("pending_transactions", [])
        return bc
