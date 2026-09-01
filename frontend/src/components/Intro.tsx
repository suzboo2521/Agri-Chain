import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";

const INTRO_KEY = "agrichain-intro-seen";
const DURATION_MS = 2800;

export function Intro({ onDone }: { onDone: () => void }) {
  const alreadySeen =
    typeof sessionStorage !== "undefined" && sessionStorage.getItem(INTRO_KEY) === "1";
  const [phase, setPhase] = useState<"show" | "leave" | "gone">(
    alreadySeen ? "gone" : "show",
  );

  const finish = useCallback(() => {
    sessionStorage.setItem(INTRO_KEY, "1");
    setPhase((p) => (p === "gone" ? p : "leave"));
  }, []);

  useEffect(() => {
    if (alreadySeen) {
      onDone();
      return;
    }
    const t = window.setTimeout(finish, DURATION_MS);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" || e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        finish();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.clearTimeout(t);
      window.removeEventListener("keydown", onKey);
    };
  }, [alreadySeen, finish, onDone]);

  if (phase === "gone") return null;

  return (
    <motion.div
      className="fixed inset-0 z-[80] flex cursor-pointer items-end overflow-hidden bg-forest-950 md:items-center"
      initial={{ opacity: 1 }}
      animate={{ opacity: phase === "leave" ? 0 : 1 }}
      transition={{ duration: 0.4 }}
      onAnimationComplete={() => {
        if (phase === "leave") {
          setPhase("gone");
          onDone();
        }
      }}
      onClick={finish}
      role="dialog"
      aria-label="AGRI-CHAIN introduction"
    >
      <img
        src="/images/rice-field.jpg"
        alt="Cultivated rice fields at golden hour"
        className="absolute inset-0 h-full w-full object-cover"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-forest-950 via-forest-950/70 to-forest-900/25" />
      <div className="relative z-10 mx-auto max-w-3xl px-6 pb-16 pt-24 text-cream-50 md:pb-0">
        <p className="mb-4 text-xs font-semibold uppercase tracking-[0.35em] text-gold-400">
          Agricultural integrity
        </p>
        <h1 className="font-display text-5xl font-semibold tracking-tight text-cream-50 md:text-7xl">
          AGRI-CHAIN
        </h1>
        <p className="mt-6 max-w-xl text-lg leading-relaxed text-cream-100/90 md:text-xl">
          From farm to consumer, every journey is traceable, verifiable and
          protected by blockchain.
        </p>
        <p className="mt-10 text-xs uppercase tracking-[0.22em] text-sage-200">
          Continue
        </p>
      </div>
    </motion.div>
  );
}
