"""Standalone, in-process tamper-detection demo (no server required).

This is the reproducible "money shot": build a chain, prove it is valid,
silently modify a stored transaction, and prove validation now fails.
Ideal as a fallback if the network/UI misbehaves during judging.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.blockchain import Blockchain  # noqa: E402

BANNER = "=" * 60


def main() -> int:
    print(BANNER)
    print(" AgriChain — Tamper Detection Demonstration")
    print(BANNER)

    chain = Blockchain(difficulty=3)

    chain.add_transaction(
        {
            "batch_id": "RICE-KONASE-2026-0001",
            "event_type": "HARVEST",
            "actor_id": "FARMER-001",
            "location": "Konaseema",
            "data": {"crop": "Rice", "quantity_kg": 2500},
        }
    )
    chain.mine_pending_transactions()

    chain.add_transaction(
        {
            "batch_id": "RICE-KONASE-2026-0001",
            "event_type": "QUALITY_CHECK",
            "actor_id": "INSPECTOR-001",
            "location": "Amalapuram",
            "data": {"grade": "A", "moisture_percent": 12.4},
        }
    )
    chain.mine_pending_transactions()

    print(f"\nBlocks mined: {len(chain.chain)}")
    print(f"Chain valid? -> {chain.is_chain_valid()}   (expected: True)")
    assert chain.is_chain_valid() is True

    print("\n--- Attacker silently edits a stored transaction ---")
    tx = chain.chain[1].transactions[0]
    print(f"  {tx['batch_id']}  quantity_kg: {tx['data']['quantity_kg']}  ->  9999999")
    tx["data"]["quantity_kg"] = 9999999

    valid = chain.is_chain_valid()
    print(f"\nChain valid? -> {valid}   (expected: False)")
    assert valid is False

    print("\n" + BANNER)
    print("  ⚠  INTEGRITY COMPROMISED — tampering detected!")
    print("  The recomputed block hash no longer matches the mined hash.")
    print(BANNER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
