const WORLD_WIDTH = 1200;
const WORLD_HEIGHT = 700;
const ROAD_WIDTH = 82;
const CURB_WIDTH = 102;
const INTERSECTION_SIZE = 88;
const FRAME_DURATION = 80;
const CAR_COLORS = ["#26251e", "#3478a8", "#1f8a65", "#cf2d56", "#e2ac37"];
const BUILDING_COLORS = ["#ebe8de", "#b8b4a8", "#d5c2ad", "#aeb9b1", "#c7c4ba"];
const CAR_ASSETS = ["black", "blue", "green", "red", "yellow"].map((color) => {
  const image = new Image();
  image.src = `assets/car_${color}_small_1.png`;
  image.addEventListener("load", draw);
  return image;
});

const canvas = document.querySelector("#arena");
const ctx = canvas.getContext("2d");
const state = { replay: null, playhead: 0, playing: true, speed: 1, stamp: 0 };

function worldPoint(x, y) {
  return { x: x * WORLD_WIDTH, y: y * WORLD_HEIGHT };
}

function roadEndpoint(value, size) {
  if (value < 0.05) return 0;
  if (value > 0.95) return size;
  return value * size;
}

function resize() {
  const box = canvas.getBoundingClientRect();
  const scale = Math.min(devicePixelRatio, 2);
  canvas.width = Math.floor(box.width * scale);
  canvas.height = Math.floor(box.height * scale);
  draw();
}

function prepareCanvas() {
  ctx.setTransform(canvas.width / WORLD_WIDTH, 0, 0, canvas.height / WORLD_HEIGHT, 0, 0);
  ctx.imageSmoothingEnabled = false;
  ctx.fillStyle = "#d2d1c8";
  ctx.fillRect(0, 0, WORLD_WIDTH, WORLD_HEIGHT);
}

function drawCityBlocks(replay) {
  const points = replay.map.intersections.map((item) => worldPoint(item.x, item.y));
  const streetXs = [...new Set(points.map((item) => item.x))].sort((a, b) => a - b);
  const streetYs = [...new Set(points.map((item) => item.y))].sort((a, b) => a - b);
  const xBounds = [0, ...streetXs, WORLD_WIDTH];
  const yBounds = [0, ...streetYs, WORLD_HEIGHT];

  for (let row = 0; row < yBounds.length - 1; row += 1) {
    for (let col = 0; col < xBounds.length - 1; col += 1) {
      const left = xBounds[col] + (col === 0 ? 15 : CURB_WIDTH / 2 + 14);
      const right = xBounds[col + 1] - (col === xBounds.length - 2 ? 15 : CURB_WIDTH / 2 + 14);
      const top = yBounds[row] + (row === 0 ? 15 : CURB_WIDTH / 2 + 14);
      const bottom = yBounds[row + 1] - (row === yBounds.length - 2 ? 15 : CURB_WIDTH / 2 + 14);
      const width = right - left;
      const height = bottom - top;
      if (width < 34 || height < 34) continue;

      ctx.fillStyle = "#c5c5bb";
      ctx.beginPath();
      ctx.roundRect(left, top, width, height, 3);
      ctx.fill();
      const inset = Math.min(16, width * 0.12, height * 0.12);
      const building = { x: left + inset, y: top + inset, width: width - inset * 2, height: height - inset * 2 };
      ctx.fillStyle = "rgba(79, 77, 72, 0.2)";
      ctx.beginPath();
      ctx.roundRect(building.x + 4, building.y + 5, building.width, building.height, 2);
      ctx.fill();
      ctx.fillStyle = BUILDING_COLORS[(row * 5 + col * 3) % BUILDING_COLORS.length];
      ctx.beginPath();
      ctx.roundRect(building.x, building.y, building.width, building.height, 2);
      ctx.fill();

      ctx.fillStyle = "rgba(77, 81, 71, 0.2)";
      ctx.beginPath();
      ctx.arc(right - 5, top + 12, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = (row + col) % 2 === 0 ? "#567663" : "#687a55";
      ctx.beginPath();
      ctx.arc(right - 7, top + 9, 5.5, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

function roadCoordinates(road) {
  return {
    x1: roadEndpoint(road.x1, WORLD_WIDTH),
    y1: roadEndpoint(road.y1, WORLD_HEIGHT),
    x2: roadEndpoint(road.x2, WORLD_WIDTH),
    y2: roadEndpoint(road.y2, WORLD_HEIGHT),
  };
}

function strokeRoads(replay, width, color) {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.lineCap = "butt";
  for (const road of replay.map.roads) {
    const { x1, y1, x2, y2 } = roadCoordinates(road);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }
}

function drawRoads(replay) {
  strokeRoads(replay, CURB_WIDTH, "#aaa99f");
  strokeRoads(replay, ROAD_WIDTH, "#41413d");
  ctx.strokeStyle = "rgba(214, 211, 197, 0.48)";
  ctx.lineWidth = 1;
  for (const road of replay.map.roads) {
    const { x1, y1, x2, y2 } = roadCoordinates(road);
    const horizontal = Math.abs(x2 - x1) > Math.abs(y2 - y1);
    for (const offset of [-ROAD_WIDTH / 2 + 5, ROAD_WIDTH / 2 - 5]) {
      ctx.beginPath();
      ctx.moveTo(x1 + (horizontal ? 0 : offset), y1 + (horizontal ? offset : 0));
      ctx.lineTo(x2 + (horizontal ? 0 : offset), y2 + (horizontal ? offset : 0));
      ctx.stroke();
    }
  }

  const points = replay.map.intersections.map((item) => worldPoint(item.x, item.y));
  const xs = [...new Set(points.map((item) => item.x))];
  const ys = [...new Set(points.map((item) => item.y))];
  ctx.strokeStyle = "rgba(210, 174, 97, 0.78)";
  ctx.lineWidth = 2;
  ctx.setLineDash([14, 12]);
  for (const y of ys) {
    let start = 0;
    for (const x of xs) {
      ctx.beginPath();
      ctx.moveTo(start, y);
      ctx.lineTo(x - INTERSECTION_SIZE / 2, y);
      ctx.stroke();
      start = x + INTERSECTION_SIZE / 2;
    }
    ctx.beginPath();
    ctx.moveTo(start, y);
    ctx.lineTo(WORLD_WIDTH, y);
    ctx.stroke();
  }
  for (const x of xs) {
    let start = 0;
    for (const y of ys) {
      ctx.beginPath();
      ctx.moveTo(x, start);
      ctx.lineTo(x, y - INTERSECTION_SIZE / 2);
      ctx.stroke();
      start = y + INTERSECTION_SIZE / 2;
    }
    ctx.beginPath();
    ctx.moveTo(x, start);
    ctx.lineTo(x, WORLD_HEIGHT);
    ctx.stroke();
  }
  ctx.setLineDash([]);
}

function drawCrosswalks(cx, cy) {
  ctx.fillStyle = "rgba(231, 228, 217, 0.72)";
  for (let offset = -28; offset <= 28; offset += 14) {
    ctx.fillRect(cx - 39, cy + offset - 3, 12, 6);
    ctx.fillRect(cx + 27, cy + offset - 3, 12, 6);
    ctx.fillRect(cx + offset - 3, cy - 39, 6, 12);
    ctx.fillRect(cx + offset - 3, cy + 27, 6, 12);
  }
  ctx.fillRect(cx - 50, cy - 37, 3, 32);
  ctx.fillRect(cx + 47, cy + 5, 3, 32);
  ctx.fillRect(cx + 5, cy - 50, 32, 3);
  ctx.fillRect(cx - 37, cy + 47, 32, 3);
}

function signalColor(phase, axis) {
  if (phase === `${axis}_GREEN`) return "#45b982";
  if (phase === "YELLOW") return "#e2ac37";
  return "#cf2d56";
}

function drawSignal(x, y, color) {
  ctx.fillStyle = "#171711";
  ctx.beginPath();
  ctx.roundRect(x - 5, y - 7, 10, 14, 3);
  ctx.fill();
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, 3.2, 0, Math.PI * 2);
  ctx.fill();
}

function drawIntersections(replay, frame) {
  for (const item of replay.map.intersections) {
    const { x, y } = worldPoint(item.x, item.y);
    ctx.fillStyle = "#41413d";
    ctx.fillRect(x - INTERSECTION_SIZE / 2, y - INTERSECTION_SIZE / 2, INTERSECTION_SIZE, INTERSECTION_SIZE);
    drawCrosswalks(x, y);
    const phase = frame.signals[item.id] || "ALL_RED";
    drawSignal(x + 36, y - 36, signalColor(phase, "NS"));
    drawSignal(x - 36, y + 36, signalColor(phase, "NS"));
    drawSignal(x + 36, y + 36, signalColor(phase, "EW"));
    drawSignal(x - 36, y - 36, signalColor(phase, "EW"));
    ctx.fillStyle = "#f7f7f4";
    ctx.font = "9px ui-monospace, monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(item.id, x, y);
  }
}

function interpolateAngle(from, to, amount) {
  const delta = ((to - from + 540) % 360) - 180;
  return from + delta * amount;
}

function drawCars(frame, nextFrame, amount) {
  const nextVehicles = new Map(nextFrame.vehicles.map((vehicle) => [vehicle[0], vehicle]));
  for (const [id, x, y, heading] of frame.vehicles) {
    const next = nextVehicles.get(id);
    const renderX = next ? x + (next[1] - x) * amount : x;
    const renderY = next ? y + (next[2] - y) * amount : y;
    const renderHeading = next ? interpolateAngle(heading, next[3], amount) : heading;
    ctx.save();
    ctx.translate(renderX * WORLD_WIDTH, renderY * WORLD_HEIGHT);
    ctx.rotate(((renderHeading + 90) * Math.PI) / 180);
    const image = CAR_ASSETS[id % CAR_ASSETS.length];
    if (image.complete && image.naturalWidth) {
      ctx.drawImage(image, -7, -13, 14, 26);
    } else {
      ctx.fillStyle = CAR_COLORS[id % CAR_COLORS.length];
      ctx.beginPath();
      ctx.roundRect(-7, -13, 14, 26, 3);
      ctx.fill();
    }
    ctx.restore();
  }
}

function draw() {
  const replay = state.replay;
  if (!replay || replay.frames.length === 0) return;
  const frameIndex = Math.floor(state.playhead);
  const frame = replay.frames[frameIndex];
  const hasNext = frameIndex + 1 < replay.frames.length;
  const nextFrame = hasNext ? replay.frames[frameIndex + 1] : frame;
  const amount = hasNext ? state.playhead - frameIndex : 0;
  prepareCanvas();
  drawCityBlocks(replay);
  drawRoads(replay);
  drawIntersections(replay, frame);
  drawCars(frame, nextFrame, amount);

  document.querySelector("#completed").textContent = `${frame.completed} / ${replay.metrics.spawned}`;
  document.querySelector("#wait").textContent = `${frame.waiting.toLocaleString()}t`;
  document.querySelector("#tick").textContent = `${String(frame.tick).padStart(3, "0")} / ${replay.frames.length}`;
  document.querySelector("#progress").style.width = `${(state.playhead / Math.max(replay.frames.length - 1, 1)) * 100}%`;
}

async function refresh() {
  try {
    const status = await fetch(`../.arena/status.json?t=${Date.now()}`).then((response) => response.json());
    if (!status.ok) {
      const error = document.querySelector("#error");
      error.hidden = false;
      error.textContent = status.traceback;
      return;
    }
    document.querySelector("#error").hidden = true;
    const replay = await fetch(`../.arena/replay.json?t=${Date.now()}`).then((response) => response.json());
    if (replay.score !== state.replay?.score || replay.scenario.id !== state.replay?.scenario.id) {
      state.replay = replay;
      state.playhead = 0;
      document.querySelector("#scenario").textContent = replay.scenario.name;
      document.querySelector("#score").textContent = replay.score.toLocaleString();
      draw();
    }
  } catch {}
}

function animate(timestamp) {
  if (state.playing && state.replay) {
    const elapsed = state.stamp ? timestamp - state.stamp : 0;
    state.playhead = (state.playhead + (elapsed * state.speed) / FRAME_DURATION) % state.replay.frames.length;
  }
  state.stamp = timestamp;
  draw();
  requestAnimationFrame(animate);
}

document.querySelector("#toggle").addEventListener("click", (event) => {
  state.playing = !state.playing;
  event.currentTarget.textContent = state.playing ? "Ⅱ" : "▶";
  event.currentTarget.setAttribute("aria-label", state.playing ? "Pause replay" : "Play replay");
});
document.querySelector("#reset").addEventListener("click", () => {
  state.playhead = 0;
  draw();
});
for (const button of document.querySelectorAll("[data-speed]")) {
  button.addEventListener("click", () => {
    state.speed = Number(button.dataset.speed);
    for (const item of document.querySelectorAll("[data-speed]")) item.classList.toggle("active", item === button);
  });
}
addEventListener("resize", resize);
resize();
refresh();
setInterval(refresh, 800);
requestAnimationFrame(animate);
