import { Link } from "react-router-dom";
import { cn } from "../lib/cn";
import { JOURNEY_STAGES } from "../lib/format";

const END = { label: "Consumer", image: "/images/consumer-qr.jpg" };

export function JourneyLine({ className }: { className?: string }) {
  const stages = [...JOURNEY_STAGES, END];
  return (
    <ol
      className={cn("flex gap-3 overflow-x-auto pb-2", className)}
      aria-label="Farm to consumer journey"
    >
      {stages.map((stage, i) => (
        <li key={stage.label} className="flex min-w-[7.5rem] flex-1 items-center">
          <div className="flex w-full flex-col items-center">
            <div className="relative h-16 w-full overflow-hidden rounded-2xl">
              <img
                src={stage.image}
                alt=""
                className="h-full w-full object-cover"
              />
              <div className="absolute inset-0 bg-forest-950/25" />
            </div>
            <p className="mt-2 text-center text-[11px] font-semibold uppercase tracking-[0.14em] text-forest-700">
              {stage.label}
            </p>
          </div>
          {i < stages.length - 1 ? (
            <span
              className="mx-1 mb-6 hidden h-px w-4 shrink-0 bg-gold-400 sm:block"
              aria-hidden
            />
          ) : null}
        </li>
      ))}
    </ol>
  );
}

export function JourneyActions() {
  const items = [
    { to: "/trace", label: "Trace", image: "/images/farmer-inspect.jpg" },
    { to: "/verify", label: "Verify", image: "/images/consumer-qr.jpg" },
    { to: "/qr", label: "QR", image: "/images/retail.jpg" },
    { to: "/register", label: "Register", image: "/images/harvest.jpg" },
    { to: "/iot", label: "IoT", image: "/images/iot-sensors.jpg" },
    { to: "/risk", label: "AI Risk", image: "/images/quality.jpg" },
    { to: "/blockchain", label: "Explorer", image: "/images/warehouse.jpg" },
    { to: "/documents", label: "Documents", image: "/images/collection.jpg" },
  ];
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => (
        <Link
          key={item.to}
          to={item.to}
          className="group relative isolate min-h-[9.5rem] overflow-hidden rounded-organ focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600"
        >
          <img
            src={item.image}
            alt=""
            className="absolute inset-0 h-full w-full object-cover transition duration-500 group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-forest-950 via-forest-950/35 to-transparent" />
          <span className="absolute bottom-4 left-4 font-display text-2xl text-cream-50">
            {item.label}
          </span>
        </Link>
      ))}
    </div>
  );
}
