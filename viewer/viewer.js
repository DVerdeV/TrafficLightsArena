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
const TREE_ASSETS = ["small", "large"].map((size) => {
  const image = new Image();
  image.src = `assets/tree_${size}.png`;
  image.addEventListener("load", draw);
  return image;
});

const canvas = document.querySelector("#arena");
const ctx = canvas.getContext("2d");
const state = { replay: null, playhead: 0, playing: true, speed: 1, stamp: 0 };

function worldPoint(x, y) {
  return { x: x * WORLD_WIDTH, y: y * WORLD_HEIGHT };
}

function roadPoints(road) {
  const points = road.points?.length ? road.points : [{ x: road.x1, y: road.y1 }, { x: road.x2, y: road.y2 }];
  return points.map((point) => worldPoint(point.x, point.y));
}

function distanceToSegment(point, start, end) {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const lengthSquared = dx * dx + dy * dy;
  const amount = lengthSquared
    ? Math.max(0, Math.min(1, ((point.x - start.x) * dx + (point.y - start.y) * dy) / lengthSquared))
    : 0;
  return Math.hypot(point.x - (start.x + dx * amount), point.y - (start.y + dy * amount));
}

function distanceToRoads(point, replay) {
  return Math.min(...replay.map.roads.flatMap((road) => {
    const points = roadPoints(road);
    return points.slice(0, -1).map((start, index) => distanceToSegment(point, start, points[index + 1]));
  }));
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

function drawTree(x, y, seed, size = 24) {
  const image = TREE_ASSETS[seed % TREE_ASSETS.length];
  if (!image.complete || !image.naturalWidth) return;
  ctx.save();
  ctx.globalAlpha = 0.76;
  ctx.translate(x, y);
  ctx.rotate(((seed % 7) - 3) * 0.04);
  ctx.drawImage(image, -size / 2, -size / 2, size, size);
  ctx.restore();
}

function drawCityBlocks(replay) {
  if (replay.scenario.id === "northbound-morning") {
    ctx.fillStyle = "#9eb9b9";
    ctx.fillRect(1035, 0, 165, WORLD_HEIGHT);
    ctx.fillStyle = "#9eaa91";
    ctx.fillRect(1017, 0, 18, WORLD_HEIGHT);
    ctx.strokeStyle = "rgba(216, 227, 223, 0.35)";
    ctx.lineWidth = 2;
    for (let y = 18; y < WORLD_HEIGHT; y += 38) {
      ctx.beginPath();
      ctx.moveTo(1050, y);
      ctx.lineTo(1185, y + 9);
      ctx.stroke();
    }
    for (let y = 45; y < WORLD_HEIGHT; y += 82) drawTree(1008, y, y, 28);
  } else if (replay.scenario.id === "balanced-grid") {
    ctx.fillStyle = "#d9d5c8";
    ctx.beginPath();
    ctx.roundRect(405, 240, 390, 255, 8);
    ctx.fill();
    ctx.strokeStyle = "rgba(185, 180, 167, 0.45)";
    ctx.lineWidth = 1;
    for (let x = 425; x < 780; x += 28) {
      ctx.beginPath();
      ctx.moveTo(x, 250);
      ctx.lineTo(x, 485);
      ctx.stroke();
    }
    ctx.fillStyle = "#b7c5bf";
    ctx.beginPath();
    ctx.arc(600, 366, 34, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#90aaa8";
    ctx.beginPath();
    ctx.arc(600, 366, 24, 0, Math.PI * 2);
    ctx.fill();
    [[445, 278], [755, 278], [445, 458], [755, 458]].forEach(([x, y], index) => drawTree(x, y, index, 30));
  } else {
    ctx.fillStyle = "#aebba0";
    ctx.beginPath();
    ctx.roundRect(245, 258, 170, 118, 18);
    ctx.fill();
    ctx.strokeStyle = "rgba(216, 211, 195, 0.8)";
    ctx.lineWidth = 8;
    ctx.beginPath();
    ctx.moveTo(260, 352);
    ctx.bezierCurveTo(300, 295, 355, 340, 402, 278);
    ctx.stroke();
    [[270, 280], [310, 350], [350, 285], [393, 345]].forEach(([x, y], index) => drawTree(x, y, index, 29));
  }

  for (let row = 0; row < 7; row += 1) {
    for (let col = 0; col < 12; col += 1) {
      const seed = row * 31 + col * 17 + replay.map.rows * 13 + replay.map.cols;
      const center = { x: 48 + col * 101 + ((seed * 7) % 19) - 9, y: 42 + row * 103 + ((seed * 11) % 17) - 8 };
      if (distanceToRoads(center, replay) < 82) continue;
      if (replay.scenario.id === "northbound-morning" && center.x > 990) continue;
      if (replay.scenario.id === "balanced-grid" && center.x > 385 && center.x < 815 && center.y > 220 && center.y < 515) continue;
      if (replay.scenario.id === "city-rush" && center.x > 225 && center.x < 435 && center.y > 235 && center.y < 395) continue;
      const width = 48 + (seed % 37);
      const height = 34 + ((seed * 3) % 39);
      const left = center.x - width / 2;
      const top = center.y - height / 2;
      ctx.fillStyle = "#c4c3ba";
      ctx.beginPath();
      ctx.roundRect(left - 8, top - 8, width + 16, height + 16, 3);
      ctx.fill();
      ctx.fillStyle = "rgba(79, 77, 72, 0.2)";
      ctx.beginPath();
      ctx.roundRect(left + 4, top + 5, width, height, 2);
      ctx.fill();
      ctx.fillStyle = BUILDING_COLORS[seed % BUILDING_COLORS.length];
      ctx.beginPath();
      ctx.roundRect(left, top, width, height, 2);
      ctx.fill();
      ctx.fillStyle = "rgba(119, 123, 118, 0.42)";
      ctx.fillRect(left + 8, top + 8, Math.max(10, width * 0.24), Math.max(7, height * 0.2));
      const treeX = left + width + 9;
      const treeY = top + 7;
      if (seed % 3 === 0) drawTree(treeX, treeY, seed, 23 + (seed % 5));
    }
  }
}

function strokeRoads(replay, width, color) {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.lineCap = "butt";
  ctx.lineJoin = "round";
  for (const road of replay.map.roads) {
    const points = roadPoints(road);
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (const point of points.slice(1)) ctx.lineTo(point.x, point.y);
    ctx.stroke();
  }
}

function drawRoads(replay) {
  strokeRoads(replay, CURB_WIDTH, "#aaa99f");
  strokeRoads(replay, ROAD_WIDTH, "#41413d");
  ctx.strokeStyle = "rgba(214, 211, 197, 0.48)";
  ctx.lineWidth = 1;
  for (const road of replay.map.roads) {
    const points = roadPoints(road);
    for (let index = 0; index < points.length - 1; index += 1) {
      const start = points[index];
      const end = points[index + 1];
      const length = Math.hypot(end.x - start.x, end.y - start.y);
      const normalX = -(end.y - start.y) / length;
      const normalY = (end.x - start.x) / length;
      for (const offset of [-ROAD_WIDTH / 2 + 5, ROAD_WIDTH / 2 - 5]) {
        ctx.beginPath();
        ctx.moveTo(start.x + normalX * offset, start.y + normalY * offset);
        ctx.lineTo(end.x + normalX * offset, end.y + normalY * offset);
        ctx.stroke();
      }
    }
  }

  ctx.strokeStyle = "rgba(210, 174, 97, 0.78)";
  ctx.lineWidth = 2;
  ctx.setLineDash([14, 12]);
  for (const road of replay.map.roads) {
    const points = roadPoints(road);
    for (let index = 0; index < points.length - 1; index += 1) {
      ctx.beginPath();
      ctx.moveTo(points[index].x, points[index].y);
      ctx.lineTo(points[index + 1].x, points[index + 1].y);
      ctx.stroke();
    }
  }
  ctx.setLineDash([]);
}

function drawOrientedRect(cx, cy, tangentX, tangentY, length, width) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(Math.atan2(tangentY, tangentX));
  ctx.fillRect(-length / 2, -width / 2, length, width);
  ctx.restore();
}

function intersectionTangents(replay, intersection) {
  const center = worldPoint(intersection.x, intersection.y);
  return replay.map.roads.flatMap((road) => {
    const points = roadPoints(road);
    const index = points.findIndex((point) => Math.hypot(point.x - center.x, point.y - center.y) < 1);
    if (index === -1) return [];
    const start = points[Math.max(0, index - 1)];
    const end = points[Math.min(points.length - 1, index + 1)];
    const length = Math.hypot(end.x - start.x, end.y - start.y);
    return [{ x: (end.x - start.x) / length, y: (end.y - start.y) / length }];
  });
}

function drawCrosswalks(cx, cy, tangents) {
  ctx.fillStyle = "rgba(231, 228, 217, 0.72)";
  for (const tangent of tangents) {
    const normal = { x: -tangent.y, y: tangent.x };
    for (const side of [-1, 1]) {
      for (let offset = -38; offset <= 38; offset += 12.6667) {
        drawOrientedRect(
          cx + tangent.x * side * 49 + normal.x * offset,
          cy + tangent.y * side * 49 + normal.y * offset,
          tangent.x,
          tangent.y,
          10,
          8,
        );
      }
      drawOrientedRect(cx + tangent.x * side * 61, cy + tangent.y * side * 61, normal.x, normal.y, 36, 3);
    }
  }
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
    ctx.beginPath();
    ctx.arc(x, y, INTERSECTION_SIZE / 2, 0, Math.PI * 2);
    ctx.fill();
    drawCrosswalks(x, y, intersectionTangents(replay, item));
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
