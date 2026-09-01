"""Unit tests for the custom Proof-of-Work blockchain.

Covers hashing, mining/proof-of-work, previous-hash linking, tamper detection,
save/load round-trips and batch-history queries. Uses the fast TEST_DIFFICULTY
so the suite stays quick.
"""
from __future__ import annotations

import config
from backend.blockchain import Block, Blockchain
from backend.database import calculate_data_hash

D = config.TEST_DIFFICULTY  # leading-zero difficulty for tests


def _tx(batch_id, event_type="HARVEST", **data):
    return {
        "batch_id": batch_id,
        "event_type": event_type,
        "actor_id": "TESTER",
        "location": "Konaseema",
        "data": data,
    }


def test_genesis_block_is_valid_and_linked():
    bc = Blockchain(difficulty=D)
    assert len(bc.chain) == 1
    genesis = bc.chain[0]
    assert genesis.index == 0
    assert genesis.previous_hash == Blockchain.GENESIS_PREVIOUS_HASH
    assert genesis.hash == genesis.compute_hash()
    assert bc.is_chain_valid() is True


def test_mining_produces_proof_of_work_and_advances_chain():
    bc = Blockchain(difficulty=D)
    bc.add_transaction(_tx("RICE-001", quantity_kg=2500))
    assert bc.pending_transactions  # queued
    block = bc.mine_pending_transactions()

    assert block.index == 1
    assert block.hash.startswith("0" * D)          # proof-of-work satisfied
    assert block.hash == block.compute_hash()      # hash matches content
    assert block.previous_hash == bc.chain[0].hash  # linked to genesis
    assert bc.pending_transactions == []           # queue cleared
    assert bc.is_chain_valid() is True


def test_previous_hash_links_across_multiple_blocks():
    bc = Blockchain(difficulty=D)
    for i in range(3):
        bc.add_transaction(_tx("RICE-001", event_type="TRANSPORT", leg=i))
        bc.mine_pending_transactions()
    for i in range(1, len(bc.chain)):
        assert bc.chain[i].previous_hash == bc.chain[i - 1].hash
    assert bc.is_chain_valid() is True


def test_tampering_with_stored_transaction_breaks_validation():
    bc = Blockchain(difficulty=D)
    bc.add_transaction(_tx("RICE-001", quantity_kg=2500))
    bc.mine_pending_transactions()
    assert bc.is_chain_valid() is True

    # Attacker silently edits a stored value WITHOUT re-mining.
    bc.chain[1].transactions[0]["data"]["quantity_kg"] = 9999999
    assert bc.is_chain_valid() is False


def test_tampering_with_block_hash_breaks_validation():
    bc = Blockchain(difficulty=D)
    bc.add_transaction(_tx("RICE-001", quantity_kg=2500))
    bc.mine_pending_transactions()
    bc.chain[1].previous_hash = "0" * 64  # forge the link
    assert bc.is_chain_valid() is False


def test_save_and_load_round_trip(tmp_path):
    bc = Blockchain(difficulty=D)
    for i in range(2):
        bc.add_transaction(_tx("RICE-001", event_type="TRANSPORT", leg=i))
        bc.mine_pending_transactions()
    path = tmp_path / "chain.json"
    bc.save(path)

    loaded = Blockchain.load(path, difficulty=D)
    assert len(loaded.chain) == len(bc.chain)
    assert loaded.chain[-1].hash == bc.chain[-1].hash
    assert loaded.is_chain_valid() is True


def test_get_batch_history_filters_by_batch():
    bc = Blockchain(difficulty=D)
    bc.add_transaction(_tx("RICE-001", event_type="HARVEST"))
    bc.mine_pending_transactions()
    bc.add_transaction(_tx("MAIZ-002", event_type="HARVEST"))
    bc.mine_pending_transactions()
    bc.add_transaction(_tx("RICE-001", event_type="TRANSPORT"))
    bc.mine_pending_transactions()

    hist = bc.get_batch_history("RICE-001")
    assert len(hist) == 2
    assert {h["transaction"]["event_type"] for h in hist} == {"HARVEST", "TRANSPORT"}
    assert all(h["transaction"]["batch_id"] == "RICE-001" for h in hist)


def test_data_hash_is_deterministic_and_order_independent():
    a = calculate_data_hash({"crop": "Rice", "quantity_kg": 2500})
    b = calculate_data_hash({"quantity_kg": 2500, "crop": "Rice"})
    c = calculate_data_hash({"crop": "Rice", "quantity_kg": 2501})
    assert a == b       # canonical (sort_keys) → order independent
    assert a != c       # any change → different hash
    assert len(a) == 64  # SHA-256 hex digest


def test_block_from_dict_to_dict_round_trip():
    bc = Blockchain(difficulty=D)
    bc.add_transaction(_tx("RICE-001", quantity_kg=2500))
    block = bc.mine_pending_transactions()
    clone = Block.from_dict(block.to_dict())
    assert clone.to_dict() == block.to_dict()
    assert clone.hash == clone.compute_hash()
