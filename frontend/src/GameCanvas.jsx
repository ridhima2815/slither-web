import { useEffect, useRef } from "react";

// Pure renderer: draws whatever the server last sent. No game rules in here.
const CELL = 28;

const C = {
  board: "#17102A",
  grid: "rgba(190,170,255,0.065)",
  sun: "#dbae19",
  lilac: "#B79CFF",
  ice: "#BFEFFF",
  you: { head: [124, 255, 217], tail: [20, 150, 140], glow: "#4CF2C2" },
};

const mix = (a, b, t) =>
  `rgb(${Math.round(a[0] + (b[0] - a[0]) * t)},${Math.round(a[1] + (b[1] - a[1]) * t)},${Math.round(
    a[2] + (b[2] - a[2]) * t
  )})`;

const thickness = (k) => CELL * (0.9 - 0.28 * k); // k: 0 at head, 1 at tail

function drawBoard(ctx, px, grid) {
  ctx.fillStyle = C.board;
  ctx.fillRect(0, 0, px, px);
  ctx.strokeStyle = C.grid;
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let i = 1; i < grid; i++) {
    ctx.moveTo(i * CELL + 0.5, 0);
    ctx.lineTo(i * CELL + 0.5, px);
    ctx.moveTo(0, i * CELL + 0.5);
    ctx.lineTo(px, i * CELL + 0.5);
  }
  ctx.stroke();
}

function drawFood(ctx, [x, y], t, calm) {
  const cx = x * CELL + CELL / 2;
  const cy = y * CELL + CELL / 2;
  const r = CELL * (0.50 + (calm ? 0 : 0.035 * Math.sin(t / 170 + x * 1.7)));
  ctx.save();
  ctx.shadowColor = C.sun;
  ctx.shadowBlur = 18;
  ctx.fillStyle = C.sun;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
  ctx.fillStyle = "rgba(255,255,255,0.8)";
  ctx.beginPath();
  ctx.arc(cx - r * 0.3, cy - r * 0.3, r * 0.26, 0, Math.PI * 2);
  ctx.fill();
}

function drawBox(ctx, [x, y, ttl], t, calm) {
  if (ttl < 45 && Math.floor(t / 130) % 2 === 0) return; // blink when about to vanish
  const cx = x * CELL + CELL / 2;
  const cy = y * CELL + CELL / 2;
  const s = CELL * 0.72;
  ctx.save();
  ctx.translate(cx, cy);
  if (!calm) ctx.rotate(Math.sin(t / 380 + x) * 0.14);
  ctx.shadowColor = C.lilac;
  ctx.shadowBlur = 16;
  ctx.fillStyle = C.lilac;
  ctx.beginPath();
  ctx.roundRect(-s / 2, -s / 2, s, s, s * 0.26);
  ctx.fill();
  ctx.shadowBlur = 0;
  ctx.fillStyle = "#2A1654";
  ctx.font = `800 ${CELL * 0.5}px Unbounded, sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("?", 0, CELL * 0.02);
  ctx.restore();
}

function drawSnake(ctx, snake, t) {
  const body = snake.body;
  const n = body.length;
  if (!n) return;
  const pal = C.you;
  const span = Math.max(n - 1, 1);

  ctx.save();
  if (!snake.alive) ctx.globalAlpha = 0.35;
  else if (snake.starving) ctx.globalAlpha = 0.6 + 0.3 * Math.sin(t / 60);
  ctx.shadowColor = pal.glow;
  ctx.shadowBlur = 14;

  for (let i = n - 1; i >= 0; i--) {
    const [x, y] = body[i];
    const k = i / span;
    const size = thickness(k);
    const pad = (CELL - size) / 2;
    ctx.fillStyle = mix(pal.head, pal.tail, k);
    ctx.beginPath();
    ctx.roundRect(x * CELL + pad, y * CELL + pad, size, size, size * 0.38);
    ctx.fill();

    if (i < n - 1) {
      // bridge the gap to the next segment (skipped across a screen-edge wrap)
      const [px, py] = body[i + 1];
      if (Math.abs(px - x) + Math.abs(py - y) === 1) {
        const w = thickness(Math.min(1, (i + 0.5) / span));
        const ax = x * CELL + CELL / 2;
        const ay = y * CELL + CELL / 2;
        const bx = px * CELL + CELL / 2;
        const by = py * CELL + CELL / 2;
        ctx.fillStyle = mix(pal.head, pal.tail, Math.min(1, (i + 0.5) / span));
        if (ay === by) ctx.fillRect(Math.min(ax, bx), ay - w / 2, Math.abs(bx - ax), w);
        else ctx.fillRect(ax - w / 2, Math.min(ay, by), w, Math.abs(by - ay));
      }
    }
  }
  ctx.restore();

  // eyes + status ring on the head
  const [hx, hy] = body[0];
  const cx = hx * CELL + CELL / 2;
  const cy = hy * CELL + CELL / 2;
  const [fx, fy] = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[snake.dir];
  const [ox, oy] = [-fy, fx];
  ctx.save();
  if (!snake.alive) ctx.globalAlpha = 0.5;
  for (const side of [-1, 1]) {
    const ex = cx + fx * CELL * 0.14 + ox * side * CELL * 0.2;
    const ey = cy + fy * CELL * 0.14 + oy * side * CELL * 0.2;
    ctx.fillStyle = "#fff";
    ctx.beginPath();
    ctx.arc(ex, ey, CELL * 0.12, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#1A0F2E";
    ctx.beginPath();
    ctx.arc(ex + fx * CELL * 0.04, ey + fy * CELL * 0.04, CELL * 0.065, 0, Math.PI * 2);
    ctx.fill();
  }
  if (snake.frozen) {
    ctx.strokeStyle = C.ice;
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.arc(cx, cy, CELL * 0.78, 0, Math.PI * 2);
    ctx.stroke();
  }
  ctx.restore();
}

export default function GameCanvas({ stateRef }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let raf;

    const frame = (t) => {
      const s = stateRef.current;
      const grid = s?.grid ?? 30;
      const px = grid * CELL;
      if (canvas.width !== px * dpr) {
        canvas.width = px * dpr;
        canvas.height = px * dpr;
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      drawBoard(ctx, px, grid);
      if (s) {
        s.food.forEach((f) => drawFood(ctx, f, t, calm));
        s.boxes.forEach((b) => drawBox(ctx, b, t, calm));
        s.snakes.forEach((sn) => drawSnake(ctx, sn, t));
      }
      raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
  }, [stateRef]);

  return <canvas ref={canvasRef} className="block aspect-square h-auto w-full" aria-label="Game board" />;
}
