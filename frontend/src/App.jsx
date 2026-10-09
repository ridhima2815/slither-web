import { useEffect, useState } from "react";
import GameCanvas from "./GameCanvas.jsx";
import { useGameSocket } from "./useGameSocket.js";

const KEYMAP = {
  ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right",
  w: "up", s: "down", a: "left", d: "right",
};

// Full class strings (not built up dynamically) so Tailwind can see them.
const MOOD_LABEL = { fed: "Fed", hungry: "Getting hungry", starving: "Starving", frozen: "Hunger paused" };
const MOOD_TEXT = { fed: "text-muted", hungry: "text-muted", starving: "text-danger", frozen: "text-ice" };
const MOOD_FILL = { fed: "bg-you", hungry: "bg-warn", starving: "bg-danger", frozen: "bg-ice" };
const CONN_LABEL = { open: "Live", connecting: "Connecting", reconnecting: "Reconnecting" };
const CONN_DOT = {
  open: "bg-you shadow-[0_0_8px_#4cf2c2]",
  connecting: "bg-warn",
  reconnecting: "bg-danger",
};
const TOAST_BORDER = { box: "border-lilac", starve: "border-danger", death: "border-danger" };

function moodOf(snake) {
  if (!snake) return "fed";
  if (snake.frozen) return "frozen";
  if (snake.starving) return "starving";
  return snake.hunger / snake.hungerMax < 0.35 ? "hungry" : "fed";
}

function Key({ children }) {
  return (
        <kbd className="inline-grid min-w-[22px] place-items-center rounded-md border border-b-2 border-lilac/30 px-1.5 text-[0.7rem] font-bold leading-4 text-ink">
      {children}
    </kbd>
  );
}

function Overlay({ title, text, action, onAction }) {
  return (
    <div className="absolute inset-0 grid place-content-center justify-items-center gap-2.5 bg-page/75 p-6 text-center backdrop-blur-sm">
      <h2 className="font-display text-[length:clamp(1.2rem,4.5vw,1.9rem)] font-extrabold leading-tight tracking-tight">
        {title}
      </h2>
      <p className="max-w-[34ch] text-muted">{text}</p>
      {action && (
        <button
          onClick={onAction}
          className="mt-1.5 cursor-pointer rounded-xl bg-you px-7 py-3 text-base font-bold text-[#06231c] hover:brightness-110 focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-[3px] focus-visible:outline-sun"
        >
          {action}
        </button>
      )}
    </div>
  );
}

export default function App() {
  const { conn, state, stateRef, send } = useGameSocket();
  const [toasts, setToasts] = useState([]);

  // Keyboard -> text commands. That's all the input logic the client has.
  useEffect(() => {
    const onKey = (e) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const key = e.key.length === 1 ? e.key.toLowerCase() : e.key;
      if (KEYMAP[key]) {
        e.preventDefault();
        if (!e.repeat) send(KEYMAP[key]);
      } else if (key === "p") {
        if (!e.repeat) send("pause");
      } else if (key === " " || key === "Enter") {
        if (e.target.tagName !== "BUTTON") {   // a focused button handles its own click
          e.preventDefault();
          if (!e.repeat) send("start");        // the server decides if that means anything
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [send]);

  // Server events (box pickups, starvation, death) become short-lived toasts.
  useEffect(() => {
    if (!state?.events?.length) return;
    const fresh = state.events.map((ev, i) => ({ ...ev, id: `${state.tick}-${i}` }));
    setToasts((t) => [...t, ...fresh].slice(-4));
    setTimeout(() => {
      setToasts((t) => t.filter((x) => !fresh.some((f) => f.id === x.id)));
    }, 2200);
  }, [state?.tick]); // eslint-disable-line react-hooks/exhaustive-deps

  const you = state?.snakes.find((s) => s.id === "player");
  const status = state?.status;
  const pct = you ? Math.round((100 * you.hunger) / you.hungerMax) : 100;
  const mood = moodOf(you);

     return (
    <main className="mx-auto flex h-screen h-dvh max-w-[1100px] flex-col gap-3 p-3">
      <header className="flex h-9 shrink-0 items-center justify-between">
        <h1 className="flex items-center gap-2.5 font-display text-[length:clamp(1.1rem,2.4vw,1.5rem)] font-extrabold tracking-tight">
          <svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true"
               className="text-you drop-shadow-[0_0_8px_rgba(76,242,194,0.6)]">
            <path d="M4 24 C4 10 16 12 16 18 S28 26 28 8" fill="none" stroke="currentColor"
                  strokeWidth="5" strokeLinecap="round" />
          </svg>
          Slither-Web
        </h1>
        <span className="inline-flex items-center gap-2 text-sm font-semibold text-muted">
          <span className={`h-2.5 w-2.5 rounded-full ${CONN_DOT[conn]}`} />
          {CONN_LABEL[conn]}
        </span>
      </header>

      <div className="flex min-h-0 flex-1 flex-col gap-3 sm:flex-row sm:gap-5">
        {/* Arena slot: the board is the biggest square that fits the space left over. */}
        <div className="flex min-h-0 min-w-0 flex-1 items-center justify-center [container-type:size]">
          <div
            style={{ width: "min(100cqw, 100cqh)" }}
            className="relative aspect-square max-w-[760px] overflow-hidden rounded-2xl border-2 border-dashed border-lilac/30 bg-board shadow-[0_24px_60px_rgba(0,0,0,0.45)]"
          >
            <GameCanvas stateRef={stateRef} />

            {you?.starving && (
              <div className="pointer-events-none absolute inset-0 animate-throb bg-[radial-gradient(circle,transparent_55%,rgba(255,59,92,0.5))] motion-reduce:animate-none" />
            )}

            <div aria-live="polite"
                 className="pointer-events-none absolute left-1/2 top-3 grid w-max max-w-[92%] -translate-x-1/2 justify-items-center gap-1.5">
              {toasts.map((t) => (
                <div key={t.id}
                     className={`animate-pop rounded-full border-[1.5px] bg-page/90 px-3.5 py-1.5 text-sm font-bold motion-reduce:animate-none ${TOAST_BORDER[t.kind] ?? "border-lilac"}`}>
                  {t.text}
                </div>
              ))}
            </div>

            {conn !== "open" ? (
              <Overlay
                title={conn === "connecting" ? "Connecting to the server" : "Connection lost"}
                text={conn === "connecting" ? "Hang on a moment." : "Trying again. You can start a new run once it reconnects."}
              />
            ) : status === "ready" ? (
              <Overlay
                title="Slither-Web"
                text="Eat food to score and keep your hunger meter full. The dashed edge wraps around."
                action="Start game"
                onAction={() => send("start")}
              />
            ) : status === "paused" ? (
              <Overlay title="Paused" text="Press P to keep going." />
            ) : status === "gameover" ? (
              <Overlay
                title={state.reason}
                text={`You scored ${you?.score ?? 0}. Best this session: ${state.best}.`}
                action="Play again"
                onAction={() => send("start")}
              />
            ) : null}
          </div>
        </div>

        {/* Side panel: score, hunger, controls. Stacks under the board on narrow windows. */}
        <aside className="flex shrink-0 flex-col sm:w-56">
          <div className="my-auto grid gap-3">
            <section className="rounded-2xl border border-lilac/20 bg-white/[0.03] p-4">
              <div className="text-xs font-bold text-muted">Score</div>
              <div className="font-display text-[length:clamp(2rem,4.5vw,3.2rem)] font-extrabold leading-none tracking-tighter text-you tabular-nums">
                {you?.score ?? 0}
              </div>
              <div className="mt-3 flex gap-5 text-sm text-muted">
                <span>Length {you?.length ?? 0}</span>
                <span>Best {state?.best ?? 0}</span>
              </div>
            </section>

            <section className="rounded-2xl border border-lilac/20 bg-white/[0.03] p-4">
              <div className={`mb-2 flex justify-between gap-2 text-xs font-semibold ${MOOD_TEXT[mood]}`}>
                <span>Hunger</span>
                <span>{MOOD_LABEL[mood]}</span>
              </div>
              <div
                role="progressbar" aria-label="Hunger" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct}
                className={`h-3 overflow-hidden rounded-full bg-white/10 ${
                  mood === "starving" ? "animate-throb ring-[1.5px] ring-danger motion-reduce:animate-none" : ""
                }`}
              >
                <div
                  style={{ width: `${pct}%` }}
                  className={`h-full rounded-full transition-[width] duration-100 ease-linear motion-reduce:transition-none ${MOOD_FILL[mood]}`}
                />
              </div>
            </section>

            <section className="hidden gap-2.5 px-1 text-sm text-muted sm:grid">
              <span className="flex flex-wrap items-center gap-1">
                <Key>↑</Key><Key>↓</Key><Key>←</Key><Key>→</Key> steer
              </span>
              <span className="flex items-center gap-1.5">
                <Key>P</Key> pause <Key>Space</Key> start
              </span>
              <span className="flex items-center">
                <i className="mr-2 inline-block h-2.5 w-2.5 rounded-full bg-sun shadow-[0_0_8px_#ffd23f]" />
                Food: +10, refills hunger
              </span>
              <span className="flex items-center">
                <i className="mr-2 inline-block h-2.5 w-2.5 rounded-[3px] bg-lilac shadow-[0_0_8px_#b79cff]" />
                Mystery box: boost or surprise
              </span>
            </section>
          </div>
        </aside>
      </div>
    </main>
  );
}