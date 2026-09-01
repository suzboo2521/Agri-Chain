import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import {
  getBlockchain,
  resetLedger,
  tamperDemo,
  verifyBlockchain,
  type ChainBlock,
  type TamperResponse,
  type VerifyResponse,
} from "../lib/api";
import { formatWhen, friendlyError, shortHash } from "../lib/format";
import { EmptyState, HashLine, LoadingLabel, Modal, PageHeader, Panel } from "../components/ui";
import { cn } from "../lib/cn";

export function BlockchainPage() {
  const [chain, setChain] = useState<ChainBlock[]>([]);
  const [selected, setSelected] = useState<ChainBlock | null>(null);
  const [verify, setVerify] = useState<VerifyResponse | null>(null);
  const [before, setBefore] = useState<VerifyResponse | null>(null);
  const [tamper, setTamper] = useState<TamperResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [warn, setWarn] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [blocks, v] = await Promise.all([getBlockchain(), verifyBlockchain()]);
      setChain(blocks);
      setVerify(v);
    } catch (e) {
      setError(friendlyError(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onVerify() {
    setBusy(true);
    try {
      const v = await verifyBlockchain();
      setVerify(v);
      toast.message(v.valid ? "Chain is intact." : "Integrity compromised.");
    } catch (e) {
      toast.error(friendlyError(e));
    } finally {
      setBusy(false);
    }
  }

  async function onTamper() {
    setWarn(false);
    setBusy(true);
    try {
      const prior = await verifyBlockchain();
      setBefore(prior);
      const result = await tamperDemo();
      setTamper(result);
      const [blocks, after] = await Promise.all([getBlockchain(), verifyBlockchain()]);
      setChain(blocks);
      setVerify(after);
      toast.error("Ledger mutated without re-mining.");
    } catch (e) {
      toast.error(friendlyError(e));
    } finally {
      setBusy(false);
    }
  }

  async function onReset() {
    setBusy(true);
    try {
      await resetLedger();
      setTamper(null);
      setBefore(null);
      await load();
      toast.success("Ledger reset to genesis.");
    } catch (e) {
      toast.error(friendlyError(e));
    } finally {
      setBusy(false);
    }
  }

  const compromised = verify && !verify.valid;

  return (
    <div>
      <PageHeader
        kicker="Ledger"
        title="Blockchain explorer"
        subtitle="Each node is a mined block. Genesis is block 0. Hashes come from the live chain."
        backTo="/"
      />
      {loading ? <LoadingLabel>Loading chain</LoadingLabel> : null}
      {error ? (
        <EmptyState title="Chain unavailable" message={error} onRetry={() => void load()} />
      ) : null}
      <div className="mb-6 flex flex-wrap gap-2">
        <button className="btn-primary" type="button" disabled={busy} onClick={() => void onVerify()}>
          {busy ? "Verifying blockchain" : "Verify blockchain"}
        </button>
        <button className="btn-danger" type="button" onClick={() => setWarn(true)}>
          Tamper demo
        </button>
        <button className="btn-ghost" type="button" disabled={busy} onClick={() => void onReset()}>
          Reset ledger
        </button>
      </div>
      {verify ? (
        <p
          className={cn(
            "mb-6 rounded-organ px-4 py-3 text-sm",
            compromised ? "bg-alert-soft text-alert" : "bg-emerald-100 text-emerald-800",
          )}
        >
          {verify.message} · {verify.blocks} blocks
        </p>
      ) : null}
      {before && tamper ? (
        <Panel className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-alert">
            Before / after tamper
          </p>
          <p className="mt-2 text-sm">
            Before: {before.valid ? "valid" : "invalid"} · After:{" "}
            {verify?.valid ? "valid" : "invalid"}
          </p>
          <p className="mt-1 text-sm text-charcoal-600">
            Block {tamper.block_index} · {tamper.field}: {String(tamper.old_value)} →{" "}
            {String(tamper.new_value)}
          </p>
        </Panel>
      ) : null}
      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <ol className="space-y-0">
            {chain.map((block, i) => (
              <li key={block.hash} className="flex flex-col items-center">
                <button
                  type="button"
                  onClick={() => setSelected(block)}
                  className={cn(
                    "flex h-20 w-20 flex-col items-center justify-center rounded-full border-2 bg-cream-50 text-center shadow-panel",
                    selected?.index === block.index
                      ? "border-gold-500"
                      : "border-emerald-600",
                  )}
                >
                  <span className="text-[10px] uppercase tracking-[0.14em] text-sage-700">
                    Block
                  </span>
                  <span className="font-display text-xl text-forest-900">{block.index}</span>
                </button>
                {i < chain.length - 1 ? (
                  <span className="h-8 w-px bg-gold-400" aria-hidden />
                ) : null}
              </li>
            ))}
          </ol>
        </div>
        <Panel className="lg:col-span-3">
          {selected ? (
            <div>
              <h2 className="font-display text-2xl text-forest-900">Block {selected.index}</h2>
              <p className="mt-1 text-sm text-charcoal-600">{formatWhen(selected.timestamp)}</p>
              <div className="mt-4 space-y-3">
                <HashLine label="Hash" value={selected.hash} />
                <HashLine label="Previous" value={selected.previous_hash} />
                <p className="text-sm">Nonce {selected.nonce}</p>
                <p className="text-sm">{selected.transactions.length} transaction(s)</p>
                <ul className="space-y-2 text-sm">
                  {selected.transactions.map((tx, i) => (
                    <li key={i} className="rounded-2xl bg-sage-50 p-3">
                      <p className="font-semibold">
                        {tx.event_type} · {tx.batch_id}
                      </p>
                      <p className="text-charcoal-600">
                        {tx.actor_id} · {tx.location}
                      </p>
                      {tx.data_hash ? (
                        <p className="hash mt-1">{shortHash(tx.data_hash)}</p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <p className="text-sm text-charcoal-600">Select a block node to inspect it.</p>
          )}
        </Panel>
      </div>
      <Modal
        open={warn}
        title="Tamper the live ledger?"
        onClose={() => setWarn(false)}
        footer={
          <>
            <button className="btn-ghost" type="button" onClick={() => setWarn(false)}>
              Cancel
            </button>
            <button className="btn-danger" type="button" onClick={() => void onTamper()}>
              Yes, mutate a transaction
            </button>
          </>
        }
      >
        <p>
          This demo writes a bad value into an existing mined transaction without
          re-mining. The next verify call should report a compromised chain. Use
          Reset ledger to restore genesis.
        </p>
      </Modal>
    </div>
  );
}
