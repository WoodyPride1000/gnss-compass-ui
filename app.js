/* app.js - GNSS Compass UI Logic with Simulator, UTM Toggle, Multilang Support, CSV Playback, Logging, and Control */

let useUTM = false;
let currentLang = 'ja';
let selfLatLng = [35.681236, 139.767125]; // 東京駅
let headingDeg = 90;
let debugMode = true;
let userMarker, headingLine, sectorPath;
let markers = [];
let animating = false;
window.selfAltitude = 0;
let sessionLog = [];
let routePoints = [];

const debugLog = (...args) => debugMode && console.log('[DEBUG]', ...args);

// 🌍 地図初期化（東京駅）
const map = L.map('map').setView(selfLatLng, 16);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap contributors',
  maxZoom: 19
}).addTo(map);

// 🧭 自己位置マーカーと方位線更新
function animateMarkerTo(latlng) {
  if (!userMarker) {
    userMarker = L.marker(latlng).addTo(map);
  } else {
    userMarker.setLatLng(latlng);
  }
}

function updateHeadingVisuals() {
  const angleRad = (headingDeg - 90) * (Math.PI / 180);
  const length = map.getSize().y * 0.3; // 地図縦の30%
  const dx = length * Math.cos(angleRad) * 0.00000899;
  const dy = length * Math.sin(angleRad) * 0.0000111;
  const target = [selfLatLng[0] + dy, selfLatLng[1] + dx];
  if (headingLine) {
    headingLine.setLatLngs([selfLatLng, target]);
  } else {
    headingLine = L.polyline([selfLatLng, target], { color: 'green', dashArray: '5, 5' }).addTo(map);
  }
}

// 扇形表示
function drawSector() {
  if (sectorPath) map.removeLayer(sectorPath);
  const radius = map.getSize().y * 0.2 * 0.00001;
  const angle = headingDeg;
  const span = 30; // デフォルト30度
  const points = [selfLatLng];
  for (let a = -span / 2; a <= span / 2; a += 5) {
    const rad = (angle + a - 90) * Math.PI / 180;
    const dx = radius * Math.cos(rad);
    const dy = radius * Math.sin(rad);
    points.push([selfLatLng[0] + dy, selfLatLng[1] + dx]);
  }
  sectorPath = L.polygon(points, { color: 'orange', fillOpacity: 0.2 }).addTo(map);
}

function updateSelfPosDisplay() {
  document.getElementById('latlng').textContent = `${selfLatLng[0].toFixed(6)}, ${selfLatLng[1].toFixed(6)}`;
  if (useUTM && window.UTM) {
    const utm = UTM.fromLatLon(selfLatLng[0], selfLatLng[1]);
    document.getElementById('utm').textContent = `${utm.zoneNum}${utm.zoneLetter} ${utm.easting.toFixed(2)}, ${utm.northing.toFixed(2)}`;
  } else {
    document.getElementById('utm').textContent = `--`;
  }
}

// 🌐 表示更新処理（GNSSまたはシミュレーションで使用）
function updatePosition(lat, lng, heading) {
  selfLatLng = [lat, lng];
  headingDeg = heading;
  updateSelfPosDisplay();
  animateMarkerTo(selfLatLng);
  updateHeadingVisuals();
  drawSector();
  document.getElementById('heading').textContent = `${headingDeg.toFixed(1)}°`;
  document.getElementById('gpsStatus').textContent = 'LIVE';
}

// 🌐 Socket.IO 受信（リアルGNSS）
const socket = io();
socket.on('gnss', (data) => {
  updatePosition(data.lat, data.lng, data.heading ?? 0.0);
  if (map.getCenter().lat === 35.681236 && map.getCenter().lng === 139.767125) {
    map.setView([data.lat, data.lng], 16); // 初回のみ地図中心を移動
  }
});

document.getElementById('toggleUTM').addEventListener('click', () => {
  useUTM = !useUTM;
  updateSelfPosDisplay();
});

document.getElementById('toggleLang').addEventListener('click', () => {
  currentLang = currentLang === 'ja' ? 'en' : 'ja';
  document.querySelectorAll('[data-label-ja]').forEach(el => {
    el.textContent = currentLang === 'ja' ? el.dataset.labelJa : el.dataset.labelEn;
  });
});

// 🧪 シミュレータON/OFFトグル
let simulatorMode = false;
let simulatorTimer = null;
document.getElementById('toggleSim').addEventListener('click', () => {
  simulatorMode = !simulatorMode;
  document.getElementById('toggleSim').textContent = simulatorMode ? 'シミュレーター停止' : 'シミュレーター起動';
  if (simulatorMode) {
    simulatorTimer = setInterval(() => {
      const lat = selfLatLng[0] + (Math.random() - 0.5) * 0.00005;
      const lng = selfLatLng[1] + (Math.random() - 0.5) * 0.00005;
      headingDeg = (headingDeg + 5) % 360;
      updatePosition(lat, lng, headingDeg);
      document.getElementById('gpsStatus').textContent = 'SIMULATED';
      sessionLog.push({ t: Date.now(), lat, lng, heading: headingDeg });
    }, 1000);
  } else {
    clearInterval(simulatorTimer);
  }
});

// 📡 CSVログ再生UI
const fileInput = document.getElementById('csvUpload');
fileInput?.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  const text = await file.text();
  const lines = text.trim().split('\n');
  let i = 0;
  const playNext = () => {
    if (i >= lines.length) return;
    const [ts, lat, lng, heading] = lines[i++].split(',');
    updatePosition(parseFloat(lat), parseFloat(lng), parseFloat(heading));
    setTimeout(playNext, 1000);
  };
  playNext();
});

// 🧭 ログ保存（終了時 or ボタン）
window.addEventListener('beforeunload', () => {
  localStorage.setItem('gnss-session-log', JSON.stringify(sessionLog));
});
document.getElementById('downloadLog')?.addEventListener('click', () => {
  const csv = sessionLog.map(r => `${r.t},${r.lat},${r.lng},${r.heading}`).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'gnss_log.csv';
  a.click();
});

// 🧠 地図クリックでルート記録
map.on('click', (e) => {
  const latlng = e.latlng;
  routePoints.push(latlng);
  L.circleMarker(latlng, { radius: 4, color: 'purple' }).addTo(map);
});

// 🔌 GPIO制御UI → Python連携（仮想）
document.getElementById('servoBtn')?.addEventListener('click', () => {
  fetch('/servo', {
    method: 'POST',
    body: JSON.stringify({ action: 'rotate', deg: headingDeg }),
    headers: { 'Content-Type': 'application/json' }
  });
});

// 🧼 デバッグモードトグル
const debugToggle = document.getElementById('toggleDebug');
debugToggle?.addEventListener('click', () => {
  debugMode = !debugMode;
  debugToggle.textContent = debugMode ? 'Debug: ON' : 'Debug: OFF';
});
