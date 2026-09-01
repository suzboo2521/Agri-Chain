# AgriChain — Security Analysis

How AgriChain resists tampering and fraud, what it deliberately does *not* claim,
and answers to the judging security questions.

---

## 1. Security goals

| Goal | Mechanism |
|------|-----------|
| **Integrity** — records can't be silently altered | SHA-256 content hashing + previous-hash linking; `is_chain_valid()` re-derives every hash |
| **Immutability by cost** | Proof-of-Work: changing a block means re-mining it *and every block after it* |
| **Traceability** — full auditable history | Every event is its own mined block; `get_batch_history()` reconstructs the journey |
| **Document authenticity** | File SHA-256 anchored on-chain; re-hash-and-compare detects any edit |
| **Data-off-chain integrity** | Off-chain payloads bound to the chain via `data_hash` |

## 2. How tampering is detected

A block's `hash` is a SHA-256 digest of its **contents** (index, timestamp,
transactions, previous_hash, nonce). Validation recomputes that digest and
compares it to the stored, mined hash, then checks that each block's
`previous_hash` matches the actual previous block.

Consequences:

- **Edit a stored transaction** (e.g. `quantity_kg 2500 → 9999999`) → the
  recomputed hash no longer matches the stored hash → `chain_valid = false`.
- **Forge a block hash / link** → the linkage check fails.
- **Rewrite history convincingly** → the attacker must re-mine the edited block
  *and* every subsequent block (each needs a fresh proof-of-work nonce), then
  replace the persisted ledger — infeasible to do silently.

This is demonstrated live via `POST /debug/tamper` → `GET /verify`, and offline
via `scripts/tamper_demo.py` (captured in [`TEST_RESULTS.md`](TEST_RESULTS.md)).

## 3. On-chain vs off-chain data

Only compact records go on-chain; bulk data lives in SQLite. Each on-chain
record carries a `data_hash = SHA-256(canonical_json(payload))`. If someone
alters the off-chain JSON, its recomputed `data_hash` diverges from the on-chain
value — so the off-chain store inherits the chain's tamper-evidence without
bloating the ledger.

## 4. Document verification

Certificates (organic, lab, phytosanitary, invoices) are stored off-chain under
`data/uploads/`, but their SHA-256 is recorded on-chain as a `DOCUMENT`
transaction. `POST /document/verify` re-hashes an uploaded file and compares:

- Identical file → **MATCH** (authentic).
- A single changed byte → completely different hash → **MODIFIED**.

## 5. Threat model & limitations (honest disclosure)

AgriChain is a **hackathon prototype**. It is transparent about what it does not
yet defend against:

| Threat | Status |
|--------|--------|
| Silent edit of stored data | ✅ Detected (hash mismatch) |
| Certificate forgery/alteration | ✅ Detected (file-hash mismatch) |
| **Garbage-in at source** (a farmer lies at registration) | ⚠ Not prevented — blockchain guarantees *integrity after recording*, not truth at input. Mitigated by trusted-actor identity (future work). |
| Actor impersonation | ⚠ No per-actor digital signatures yet (planned). `actor_id` is self-asserted. |
| Full-history rewrite by a single operator | ⚠ Single-node ledger: an operator with file access could re-mine the whole chain offline. A multi-node/permissioned network (future work) removes this. |
| Network transport security | ⚠ Local HTTP + open CORS for the demo; production needs TLS + auth. |
| Denial of service | ⚠ Out of scope for the prototype. |

## 6. Answers to the judging security questions

**Q: How does your system prevent tampering?**
Each block's hash is computed from its contents and linked to the previous
block. Any change to a stored record makes the recomputed hash disagree with the
stored hash, and `is_chain_valid()` fails. Proof-of-work makes re-mining costly,
and a change cascades to every later block.

**Q: What data is stored on-chain vs off-chain, and why?**
On-chain: compact event records + a `data_hash` + block metadata (small,
immutable, verifiable). Off-chain (SQLite): full payloads, documents and sensor
streams (large, queryable). The `data_hash` cryptographically ties the two so
off-chain data can't be altered undetected.

**Q: How do you verify a physical document (e.g. a certificate)?**
Upload it once — we compute and record its SHA-256 on-chain. Anyone can later
re-upload the file; if a single byte changed, the hash differs and we report
**MODIFIED**.

**Q: What stops someone printing a fake QR code?**
The QR only encodes a link to the verify page keyed by `batch_id`. A fake QR
either points to a non-existent batch (the consumer page shows "product not
found — possible counterfeit") or to a real batch whose on-chain history and
`chain_valid` status the consumer can inspect. The QR is a pointer, not the
trust anchor — the blockchain is.

**Q: Why proof-of-work here?**
It makes rewriting history computationally non-trivial and demonstrates the core
blockchain security property (immutability by cost) without external
dependencies. For production we would move to a permissioned, multi-node
consensus network.

**Q: What are the biggest limitations?**
Single-node ledger and self-asserted actor identity (no per-actor signatures
yet). Both are addressed in the roadmap via a permissioned network and
public-key actor identities.
