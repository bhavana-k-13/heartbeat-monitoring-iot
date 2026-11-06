const $ = id => document.getElementById(id);
const COLORS = {NORMAL: "#22c55e", WARNING: "#f59e0b", CRITICAL: "#ef4444"};

async function api(path, opts) {
  const res = await fetch(path, opts);
  let data = null;
  try { data = await res.json(); } catch (e) {}
  return {ok: res.ok, status: res.status, data};
}
const post = (p, body) => api(p, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body || {})});

function esc(s) { const d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }

function drawChart(readings) {
  const c = $("chart"), g = c.getContext("2d"), W = c.width, H = c.height;
  const pad = {l: 45, r: 15, t: 15, b: 25};
  g.clearRect(0, 0, W, H);
  const yMin = 30, yMax = 160;
  const X = i => pad.l + (readings.length <= 1 ? 0 : i * (W - pad.l - pad.r) / (readings.length - 1));
  const Y = v => pad.t + (1 - (Math.min(Math.max(v, yMin), yMax) - yMin) / (yMax - yMin)) * (H - pad.t - pad.b);
  g.fillStyle = "rgba(34,197,94,0.12)";
  g.fillRect(pad.l, Y(CFG.high), W - pad.l - pad.r, Y(CFG.low) - Y(CFG.high));
  g.strokeStyle = "#334155"; g.fillStyle = "#94a3b8"; g.font = "12px Segoe UI"; g.lineWidth = 1;
  for (let v = 40; v <= 160; v += 20) {
    g.beginPath(); g.moveTo(pad.l, Y(v)); g.lineTo(W - pad.r, Y(v)); g.stroke();
    g.fillText(v, 8, Y(v) + 4);
  }
  if (!readings.length) { g.fillText("No data yet", W / 2 - 30, H / 2); return; }
  g.strokeStyle = "#38bdf8"; g.lineWidth = 2; g.beginPath();
  readings.forEach((r, i) => i ? g.lineTo(X(i), Y(r.bpm)) : g.moveTo(X(i), Y(r.bpm)));
  g.stroke();
  readings.forEach((r, i) => { g.fillStyle = COLORS[r.status]; g.beginPath(); g.arc(X(i), Y(r.bpm), 4, 0, 6.3); g.fill(); });
}

function updateResponsePanel(alerts) {
  const p = $("responsePanel");
  if (!alerts.length) { p.className = "response idle"; p.textContent = "System idle. No abnormal reading yet."; return; }
  const a = alerts[0];
  p.className = "response " + a.level;
  p.innerHTML = "<b>" + esc(a.level) + "</b> at BPM " + esc(a.bpm) + "<br>" + esc(a.response_action || "");
}

async function refresh() {
  const [rd, st, al, sim] = await Promise.all([
    api("/api/readings?limit=40"), api("/api/stats"), api("/api/alerts"), api("/api/simulate/status")]);
  if (!rd.ok) return;
  const readings = rd.data;
  drawChart(readings);
  const last = readings[readings.length - 1];
  if (last) {
    $("bpmValue").textContent = last.bpm;
    $("statusBadge").textContent = last.status;
    $("statusBadge").className = "badge " + last.status;
    $("lastTime").textContent = "Last reading: " + last.created_at + " (" + last.source + ")";
  } else {
    $("bpmValue").textContent = "--"; $("statusBadge").textContent = "NO DATA"; $("statusBadge").className = "badge none";
    $("lastTime").textContent = "Waiting for readings...";
  }
  const s = st.data;
  $("sTotal").textContent = s.total; $("sAvg").textContent = s.average_bpm ?? "--";
  $("sMinMax").textContent = (s.min_bpm ?? "--") + " / " + (s.max_bpm ?? "--");
  $("sNormal").textContent = s.by_status.NORMAL; $("sWarning").textContent = s.by_status.WARNING;
  $("sCritical").textContent = s.by_status.CRITICAL; $("sAlerts").textContent = s.alerts;
  $("alertTable").querySelector("tbody").innerHTML = al.data.map(a =>
    `<tr><td>${esc(a.created_at)}</td><td class="lvl-${esc(a.level)}">${esc(a.level)}</td><td>${esc(a.bpm)}</td><td>${esc(a.message)}</td><td>${esc(a.response_action)}</td></tr>`).join("");
  $("readTable").querySelector("tbody").innerHTML = readings.slice().reverse().slice(0, 15).map(r =>
    `<tr><td>${r.id}</td><td>${esc(r.created_at)}</td><td>${r.bpm}</td><td class="lvl-${esc(r.status)}">${esc(r.status)}</td><td>${esc(r.source)}</td></tr>`).join("");
  updateResponsePanel(al.data);
  $("simState").textContent = "Auto simulator: " + (sim.data.running ? "running (" + sim.data.mode + ")" : "stopped");
}

$("btnManual").onclick = async () => {
  const v = $("manualBpm").value;
  if (v === "") { $("formMsg").textContent = "Please enter a BPM value."; return; }
  const r = await post("/api/readings", {bpm: Number(v), source: "manual"});
  $("formMsg").textContent = r.ok ? "" : (r.data && r.data.error) || "Error";
  if (r.ok) $("manualBpm").value = "";
  refresh();
};
$("btnOne").onclick = async () => { await post("/api/simulate/next", {mode: $("mode").value}); refresh(); };
$("btnStart").onclick = async () => { await post("/api/simulate/start", {mode: $("mode").value}); refresh(); };
$("btnStop").onclick = async () => { await post("/api/simulate/stop"); refresh(); };
$("btnClear").onclick = async () => { if (confirm("Delete all stored readings?")) { await api("/api/readings", {method: "DELETE"}); refresh(); } };

refresh();
setInterval(refresh, 2000);
