# AgriChain — End-to-End Test Results

This document captures the results of the automated test suite and the
standalone tamper-detection demonstration. Reproduce any time with:

```bash
python -m pytest -v          # full automated suite
python scripts/tamper_demo.py  # offline tamper "money shot"
```

**Environment:** Python 3.13.7 · pytest 9.1 · macOS (darwin). Tests mine at the
faster `TEST_DIFFICULTY = 2` and run against an **isolated temporary ledger**, so
the seeded `chain.json` (36 blocks) and `agrichain.db` are never modified.

---

## 1. Automated test suite — `pytest`

**Result: 21 passed in ~1.1s** ✅

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/.../AgriChain
configfile: pytest.ini
testpaths: tests
collected 21 items

tests/test_api.py::test_health_reports_running_and_valid PASSED          [  4%]
tests/test_api.py::test_register_creates_batch_and_advances_chain PASSED [  9%]
tests/test_api.py::test_event_records_and_advances_status PASSED         [ 14%]
tests/test_api.py::test_batch_history_and_404 PASSED                     [ 19%]
tests/test_api.py::test_tamper_then_reset_round_trip PASSED              [ 23%]
tests/test_api.py::test_tamper_without_data_returns_400 PASSED           [ 28%]
tests/test_api.py::test_stats_shape PASSED                               [ 33%]
tests/test_api.py::test_risk_scoring PASSED                              [ 38%]
tests/test_api.py::test_sensor_stream_records_readings PASSED            [ 42%]
tests/test_api.py::test_document_upload_and_verify PASSED                [ 47%]
tests/test_api.py::test_document_verify_without_record_404 PASSED        [ 52%]
tests/test_api.py::test_qr_endpoint_returns_png PASSED                   [ 57%]
tests/test_blockchain.py::test_genesis_block_is_valid_and_linked PASSED  [ 61%]
tests/test_blockchain.py::test_mining_produces_proof_of_work_and_advances_chain PASSED [ 66%]
tests/test_blockchain.py::test_previous_hash_links_across_multiple_blocks PASSED [ 71%]
tests/test_blockchain.py::test_tampering_with_stored_transaction_breaks_validation PASSED [ 76%]
tests/test_blockchain.py::test_tampering_with_block_hash_breaks_validation PASSED [ 80%]
tests/test_blockchain.py::test_save_and_load_round_trip PASSED           [ 85%]
tests/test_blockchain.py::test_get_batch_history_filters_by_batch PASSED [ 90%]
tests/test_blockchain.py::test_data_hash_is_deterministic_and_order_independent PASSED [ 95%]
tests/test_blockchain.py::test_block_from_dict_to_dict_round_trip PASSED [100%]

============================== 21 passed in 1.08s ==============================
```

### What each group proves

| Suite | Tests | What it verifies |
|-------|-------|------------------|
| `test_blockchain.py` | 9 | Genesis integrity, proof-of-work (hash has N leading zeros), previous-hash linking across blocks, **tamper detection** (editing a stored tx or a link breaks validation), `save()`/`load()` round-trip, batch-history filtering, deterministic `data_hash`, block (de)serialisation. |
| `test_api.py` | 12 | Health, batch registration + chain growth, event recording + status advance, batch history + 404, **tamper → verify-invalid → reset → verify-valid** round-trip, stats, rule-based risk scoring, IoT sensor streaming + anomaly flag, **document upload → verify MATCH → verify MODIFIED**, document 404, QR PNG bytes. |

---

## 2. Tamper-detection demonstration — `scripts/tamper_demo.py`

A standalone, in-process proof (no server needed). Builds a chain, proves it is
valid, silently edits a stored transaction **without re-mining**, and shows that
validation now fails.

```text
============================================================
 AgriChain — Tamper Detection Demonstration
============================================================

Blocks mined: 3
Chain valid? -> True   (expected: True)

--- Attacker silently edits a stored transaction ---
  RICE-KONASE-2026-0001  quantity_kg: 2500  ->  9999999

Chain valid? -> False   (expected: False)

============================================================
  ⚠  INTEGRITY COMPROMISED — tampering detected!
  The recomputed block hash no longer matches the mined hash.
============================================================
```

---

## 3. Isolation check (post-run)

After the suite runs, the live ledger is confirmed intact:

```text
chain.json blocks: 36 | valid: True
batches in db: 5
events in db: 35
```

The temp-ledger fixture (`tests/conftest.py`) guarantees the seeded demo state
is never disturbed by tests.

## 4. Model training (reproducible artifacts)

`python -m scripts.train_models` regenerates all ML artifacts deterministically
(`RANDOM_SEED = 42`):

```text
[risk] saved  -> ai/models/risk_model.joblib
[risk] chart  -> ai/models/feature_importance.png
[risk] top factors: temperature=0.44, delay_hours=0.31, quality_score=0.17
[anomaly] trained on 500 readings -> ai/models/anomaly_model.joblib
✅ All models trained.
```
