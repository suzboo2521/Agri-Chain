from app.blockchain.chain import Blockchain
from app.qr.codes import sha256_obj


def test_genesis_and_link():
    bc = Blockchain(difficulty=1)
    assert bc.chain[0].index == 0
    bc.add_transaction({"batch_id": "X", "event_type": "HARVEST"})
    block = bc.mine_pending_transactions()
    assert block.previous_hash == bc.chain[0].hash
    valid, reason, failed = bc.is_chain_valid()
    assert valid is True
    assert failed is None


def test_tamper_detection():
    bc = Blockchain(difficulty=1)
    bc.add_transaction({"batch_id": "X", "quantity_kg": 2500})
    bc.mine_pending_transactions()
    bc.chain[1].transactions[0]["quantity_kg"] = 9999
    valid, reason, failed = bc.is_chain_valid()
    assert valid is False
    assert failed == 1
    assert "hash" in (reason or "").lower() or "mismatch" in (reason or "").lower()


def test_hash_stable():
    a = sha256_obj("hello")
    b = sha256_obj("hello")
    c = sha256_obj("hello!")
    assert a == b
    assert a != c
    assert len(a) == 64
