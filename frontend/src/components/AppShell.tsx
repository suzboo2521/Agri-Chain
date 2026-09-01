import { useEffect, useState } from "react";
import {
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import {
  Activity,
  BarChart3,
  Boxes,
  FileStack,
  Home,
  Menu,
  QrCode,
  Radio,
  ScanSearch,
  ShieldCheck,
  Sprout,
  X,
} from "lucide-react";
import { health } from "../lib/api";
import { cn } from "../lib/cn";
import { Intro } from "./Intro";

const NAV = [
  { to: "/", label: "Home / Dashboard", icon: Home },
  { to: "/register", label: "Register batch", icon: Sprout },
  { to: "/trace", label: "Traceability", icon: ScanSearch },
  { to: "/verify", label: "Verify product", icon: ShieldCheck },
  { to: "/qr", label: "QR verification", icon: QrCode },
  { to: "/iot", label: "IoT monitoring", icon: Radio },
  { to: "/risk", label: "AI risk", icon: Activity },
  { to: "/documents", label: "Documents", icon: FileStack },
  { to: "/blockchain", label: "Blockchain explorer", icon: Boxes },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
];

export function AppShell() {
  const [introDone, setIntroDone] = useState(
    () => sessionStorage.getItem("agrichain-intro-seen") === "1",
  );
  const [menuOpen, setMenuOpen] = useState(false);
  const [online, setOnline] = useState<boolean | null>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const [params] = useSearchParams();

  useEffect(() => {
    const page = params.get("page");
    const batchId = params.get("batch_id") || params.get("batchId");
    if (page && page.toLowerCase() === "verify" && batchId) {
      navigate(`/verify/${encodeURIComponent(batchId)}`, { replace: true });
    }
  }, [params, navigate]);

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    let cancelled = false;
    const ping = async () => {
      try {
        const h = await health();
        if (!cancelled) setOnline(h.status === "running" || Boolean(h.message));
      } catch {
        if (!cancelled) setOnline(false);
      }
    };
    void ping();
    const id = window.setInterval(ping, 20000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  return (
    <>
      {!introDone ? <Intro onDone={() => setIntroDone(true)} /> : null}
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[90] focus:rounded-lg focus:bg-cream-50 focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <div className="min-h-screen bg-cream-100">
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
          <div className="absolute -left-24 top-0 h-72 w-72 rounded-full bg-sage-200/50 blur-3xl" />
          <div className="absolute -right-16 top-40 h-80 w-80 rounded-full bg-gold-300/20 blur-3xl" />
        </div>
        <header className="sticky top-0 z-40 border-b border-cream-200/80 bg-cream-50/80 backdrop-blur-md">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3 md:px-6">
            <NavLink to="/" className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-forest-800 text-gold-400">
                <Sprout className="h-4 w-4" aria-hidden />
              </span>
              <span className="font-display text-lg tracking-wide text-forest-900">
                AGRI-CHAIN
              </span>
            </NavLink>
            <div className="flex items-center gap-2">
              <p
                className="inline-flex items-center gap-2 rounded-full border border-cream-200 bg-cream-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em]"
                aria-live="polite"
              >
                <span
                  className={cn(
                    "h-2 w-2 rounded-full",
                    online === true && "bg-emerald-500",
                    online === false && "bg-alert",
                    online === null && "bg-sage-400",
                  )}
                />
                {online === true
                  ? "API online"
                  : online === false
                    ? "API offline"
                    : "API…"}
              </p>
              <NavLink
                to="/"
                className="hidden rounded-full px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-forest-700 hover:bg-sage-100 sm:inline"
              >
                Home
              </NavLink>
              <button
                type="button"
                className="inline-flex items-center gap-2 rounded-full border border-cream-300 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-forest-800 lg:hidden"
                onClick={() => setMenuOpen((v) => !v)}
                aria-expanded={menuOpen}
                aria-controls="mobile-menu"
              >
                {menuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
                Menu
              </button>
            </div>
          </div>
        </header>
        <div className="relative mx-auto flex max-w-7xl gap-8 px-4 py-6 md:px-6">
          <aside className="sticky top-24 hidden h-[calc(100vh-8rem)] w-56 shrink-0 lg:block">
            <nav aria-label="Primary" className="flex flex-col gap-1">
              {NAV.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-2 rounded-2xl px-3 py-2 text-sm text-forest-800 hover:bg-sage-100",
                      isActive && "bg-forest-800 text-cream-50 hover:bg-forest-800",
                    )
                  }
                >
                  <item.icon className="h-4 w-4 shrink-0" aria-hidden />
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </aside>
          {menuOpen ? (
            <div
              id="mobile-menu"
              className="fixed inset-0 z-40 bg-forest-950/40 lg:hidden"
              onClick={() => setMenuOpen(false)}
            >
              <nav
                className="absolute right-0 top-0 h-full w-72 overflow-y-auto bg-cream-50 p-5 shadow-panel"
                onClick={(e) => e.stopPropagation()}
                aria-label="Mobile"
              >
                <p className="mb-4 font-display text-xl text-forest-900">Menu</p>
                {NAV.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === "/"}
                    className="block rounded-xl px-3 py-2.5 text-forest-800 hover:bg-sage-100"
                  >
                    {item.label}
                  </NavLink>
                ))}
              </nav>
            </div>
          ) : null}
          <main id="main" className="min-w-0 flex-1 pb-16">
            <Outlet />
          </main>
        </div>
      </div>
    </>
  );
}
