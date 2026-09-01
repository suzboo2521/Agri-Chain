import { type ReactNode, useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { cn } from "../lib/cn";

export function PageHeader({
  kicker,
  title,
  subtitle,
  backTo = "/",
  backLabel = "BACK",
}: {
  kicker?: string;
  title: string;
  subtitle?: string;
  backTo?: string | null;
  backLabel?: string;
}) {
  return (
    <header className="mb-8">
      {backTo ? (
        <Link
          to={backTo}
          className="mb-4 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-forest-600 hover:text-forest-800"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          {backLabel}
        </Link>
      ) : null}
      {kicker ? (
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.28em] text-gold-600">
          {kicker}
        </p>
      ) : null}
      <h1 className="font-display text-3xl font-semibold text-forest-900 md:text-4xl">
        {title}
      </h1>
      {subtitle ? (
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-charcoal-600 md:text-base">
          {subtitle}
        </p>
      ) : null}
    </header>
  );
}

export function Panel({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return <div className={cn("organic-panel p-5 md:p-6", className)}>{children}</div>;
}

export function EmptyState({
  title,
  message,
  onRetry,
  actionLabel = "TRY AGAIN",
}: {
  title: string;
  message: string;
  onRetry?: () => void;
  actionLabel?: string;
}) {
  return (
    <div
      className="organic-panel flex flex-col items-start gap-4 px-6 py-10"
      role="status"
    >
      <p className="font-display text-xl text-forest-900">{title}</p>
      <p className="max-w-lg text-sm text-charcoal-600">{message}</p>
      {onRetry ? (
        <button type="button" className="btn-primary" onClick={onRetry}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}

export function LoadingLabel({ children }: { children: ReactNode }) {
  return (
    <div
      className="flex items-center gap-3 py-10 text-sm font-semibold uppercase tracking-[0.22em] text-forest-600"
      role="status"
      aria-live="polite"
    >
      <span className="h-2 w-2 animate-breathe rounded-full bg-emerald-600" />
      {children}
    </div>
  );
}

export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.16em] text-sage-700">
        {label}
      </span>
      {children}
      {hint ? <span className="mt-1 block text-xs text-charcoal-600">{hint}</span> : null}
    </label>
  );
}

export function Modal({
  open,
  title,
  children,
  onClose,
  footer,
}: {
  open: boolean;
  title: string;
  children: ReactNode;
  onClose: () => void;
  footer?: ReactNode;
}) {
  const titleId = useId();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    ref.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      prev?.focus();
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center">
      <button
        type="button"
        className="absolute inset-0 bg-forest-950/50 backdrop-blur-sm"
        aria-label="Close dialog"
        onClick={onClose}
      />
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className="relative w-full max-w-lg rounded-organ bg-cream-50 p-6 shadow-panel"
      >
        <h2 id={titleId} className="font-display text-2xl text-forest-900">
          {title}
        </h2>
        <div className="mt-4 text-sm text-charcoal-700">{children}</div>
        {footer ? <div className="mt-6 flex flex-wrap gap-2">{footer}</div> : null}
      </div>
    </div>,
    document.body,
  );
}

export function HashLine({ value, label = "Hash" }: { value: string; label?: string }) {
  return (
    <p className="text-xs text-charcoal-600">
      <span className="font-semibold uppercase tracking-[0.14em]">{label}</span>
      <span className="hash mt-1 block text-forest-800" title={value}>
        {value}
      </span>
    </p>
  );
}
