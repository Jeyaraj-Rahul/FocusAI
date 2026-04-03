const focusScore = document.getElementById("focus-score");
const focusState = document.getElementById("focus-state");
const focusMessage = document.getElementById("focus-message");
const heroState = document.getElementById("hero-state");
const heroMessage = document.getElementById("hero-message");
const usageList = document.getElementById("usage-list");
const warningPopup = document.getElementById("warning-popup");
const warningText = document.getElementById("warning-text");
const soundEnabled = document.getElementById("sound-enabled");
const cameraPreview = document.getElementById("camera-preview");
const cameraBadge = document.getElementById("camera-badge");
const cameraOverlay = document.getElementById("camera-overlay");
const statusIndicator = document.getElementById("status-indicator");
const statusIndicatorText = document.getElementById("status-indicator-text");
const summaryFocus = document.getElementById("summary-focus");
const summaryDistractions = document.getElementById("summary-distractions");
const summaryDeepTime = document.getElementById("summary-deep-time");
const summaryIssue = document.getElementById("summary-issue");
const summaryTotalTime = document.getElementById("summary-total-time");

let tabSwitchCount = 0;
let previousState = "";
let audioContext;
let audioUnlocked = false;
const graphLabels = [];
const graphPoints = [];

// Create the Chart.js line graph once, then keep pushing new values into it.
const focusChart = new Chart(document.getElementById("focus-chart"), {
  type: "line",
  data: {
    labels: graphLabels,
    datasets: [
      {
        label: "Focus Score",
        data: graphPoints,
        borderColor: "#38bdf8",
        backgroundColor: "rgba(56, 189, 248, 0.16)",
        borderWidth: 3,
        tension: 0.35,
        fill: true,
        pointRadius: 0,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 500,
    },
    plugins: {
      legend: {
        labels: {
          color: "#ffffff",
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: "#94a3b8",
        },
        grid: {
          color: "rgba(148, 163, 184, 0.12)",
        },
      },
      y: {
        min: 0,
        max: 100,
        ticks: {
          color: "#94a3b8",
        },
        grid: {
          color: "rgba(148, 163, 184, 0.12)",
        },
      },
    },
  },
});

function getAudioContext() {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) {
    return null;
  }

  if (!audioContext) {
    audioContext = new AudioContextClass();
  }

  return audioContext;
}

async function unlockAudio() {
  const context = getAudioContext();
  if (!context) {
    return false;
  }

  if (context.state === "suspended") {
    await context.resume();
  }

  audioUnlocked = context.state === "running";
  return audioUnlocked;
}

function playAlertSound() {
  if (!soundEnabled.checked) {
    return;
  }

  const context = getAudioContext();
  if (!context || !audioUnlocked || context.state !== "running") {
    return;
  }

  const oscillator = context.createOscillator();
  const gainNode = context.createGain();
  const now = context.currentTime;

  oscillator.type = "triangle";
  oscillator.frequency.setValueAtTime(740, now);
  oscillator.frequency.exponentialRampToValueAtTime(520, now + 0.28);
  gainNode.gain.setValueAtTime(0.0001, now);
  gainNode.gain.exponentialRampToValueAtTime(0.09, now + 0.03);
  gainNode.gain.exponentialRampToValueAtTime(0.0001, now + 0.32);

  oscillator.connect(gainNode);
  gainNode.connect(context.destination);
  oscillator.start(now);
  oscillator.stop(now + 0.32);
}

function showWarningPopup(message) {
  warningText.textContent = message;
  warningPopup.classList.add("show");
  window.clearTimeout(showWarningPopup.timeoutId);
  showWarningPopup.timeoutId = window.setTimeout(() => {
    warningPopup.classList.remove("show");
  }, 3200);
}

function getStateClassName(state) {
  if (state === "Deep Focus") {
    return "state-deep";
  }
  if (state === "Mild Distraction") {
    return "state-mild";
  }
  if (state === "Fatigue") {
    return "state-fatigue";
  }
  return "state-high";
}

function getIndicatorClass(state) {
  if (state === "Deep Focus") {
    return "deep";
  }
  if (state === "Mild Distraction") {
    return "mild";
  }
  if (state === "Fatigue") {
    return "fatigue";
  }
  return "high";
}

function updateGraph(score) {
  const now = new Date();
  const label = now.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  graphLabels.push(label);
  graphPoints.push(score);

  // Keep the graph compact and readable by storing only the latest 12 points.
  if (graphLabels.length > 12) {
    graphLabels.shift();
    graphPoints.shift();
  }

  focusChart.update();
}

function renderUsage(data) {
  if (!data.sites || data.sites.length === 0) {
    usageList.innerHTML = '<div class="empty-state">No website usage data yet.</div>';
    return;
  }

  usageList.innerHTML = data.sites
    .map((site) => {
      const timeSpent = data.time_spent[site] || 0;
      const category = data.category[site] || "Neutral";
      const categoryClass = category.toLowerCase();
      const categoryIcon =
        category === "Productive" ? "●" : category === "Distracting" ? "▲" : "■";

      return `
        <div class="usage-item">
          <div class="usage-site">${site}</div>
          <div class="usage-time">${formatSeconds(timeSpent)}</div>
          <div class="usage-category ${categoryClass}">${categoryIcon} ${category}</div>
        </div>
      `;
    })
    .join("");
}

function updateSummary(data) {
  summaryFocus.textContent = data.focus_percentage || "0%";
  summaryDistractions.textContent = data.distraction_count || "0";
  summaryDeepTime.textContent = data.deep_focus_time || "00:00:00";
  summaryIssue.textContent = data.main_issue || "none";
  summaryTotalTime.textContent = data.total_time || "00:00:00";
}

function updateDashboard(data) {
  const stateClassName = getStateClassName(data.state);
  const indicatorClass = getIndicatorClass(data.state);
  const isAlertState =
    data.state === "High Distraction" || data.state === "Fatigue";

  document.body.classList.remove("state-deep", "state-mild", "state-high", "state-fatigue");
  document.body.classList.add(stateClassName);

  focusScore.textContent = data.score;
  focusState.textContent = data.state;
  focusMessage.textContent = data.message;
  heroState.textContent = data.state;
  heroMessage.textContent = data.message;
  statusIndicator.className = `status-indicator ${indicatorClass}`;
  statusIndicatorText.textContent = data.state;

  // If the backend is updating normally and there is no camera error,
  // treat the backend camera stream as live.
  if (!data.last_error) {
    markCameraLive();
  }

  updateGraph(data.score);

  if (isAlertState && previousState !== data.state) {
    showWarningPopup(data.message);
    playAlertSound();
  }

  previousState = data.state;
}

function markCameraLive() {
  cameraBadge.textContent = "Live";
  cameraOverlay.classList.add("hidden");
}

function formatSeconds(totalSeconds) {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const hours = String(Math.floor(seconds / 3600)).padStart(2, "0");
  const minutes = String(Math.floor((seconds % 3600) / 60)).padStart(2, "0");
  const secs = String(seconds % 60).padStart(2, "0");
  return `${hours}:${minutes}:${secs}`;
}

async function fetchStatus() {
  try {
    const response = await fetch("/status");
    const data = await response.json();
    updateDashboard(data);
  } catch (error) {
    console.error("Could not fetch /status:", error);
  }
}

async function fetchUsage() {
  try {
    const response = await fetch("/usage");
    const data = await response.json();
    renderUsage(data);
  } catch (error) {
    console.error("Could not fetch /usage:", error);
  }
}

async function fetchSessionSummary() {
  try {
    const response = await fetch("/api/session-summary");
    const data = await response.json();
    updateSummary(data);
  } catch (error) {
    console.error("Could not fetch session summary:", error);
  }
}

async function sendTabActivity() {
  try {
    const response = await fetch("/api/tab-activity", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        is_hidden: document.hidden,
        tab_switch_count: tabSwitchCount,
      }),
    });

    const data = await response.json();
    console.log("Tab activity sent to backend:", data);
  } catch (error) {
    console.error("Failed to send tab activity:", error);
  }
}

async function sendUserActivity() {
  try {
    await fetch("/api/activity", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ active: true }),
    });
  } catch (error) {
    console.error("Failed to send user activity:", error);
  }
}

function setupCameraPreview() {
  cameraPreview.addEventListener("load", () => {
    markCameraLive();
  });

  cameraPreview.addEventListener("error", () => {
    cameraBadge.textContent = "Offline";
    cameraOverlay.classList.remove("hidden");
    cameraOverlay.textContent =
      "Could not load the backend camera stream. Check the Flask camera connection.";
  });

  // MJPEG image streams do not always fire a normal load event in every browser.
  // Use a short fallback so the overlay disappears once the stream starts.
  window.setTimeout(() => {
    markCameraLive();
  }, 1500);
}

document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    tabSwitchCount += 1;
  }
  console.log(
    `Tab visibility changed. Hidden: ${document.hidden}. Total switches: ${tabSwitchCount}`
  );
  sendTabActivity();
});

soundEnabled.addEventListener("change", async () => {
  if (soundEnabled.checked) {
    const ready = await unlockAudio();
    if (!ready) {
      soundEnabled.checked = false;
    }
  }
});

document.addEventListener(
  "click",
  () => {
    sendUserActivity();
    if (soundEnabled.checked && !audioUnlocked) {
      unlockAudio();
    }
  },
  { passive: true }
);

["mousemove", "keydown", "scroll"].forEach((eventName) => {
  let lastSentAt = 0;

  document.addEventListener(
    eventName,
    () => {
      const now = Date.now();
      if (now - lastSentAt > 5000) {
        lastSentAt = now;
        sendUserActivity();
      }
    },
    { passive: true }
  );
});

// Load the first dashboard state immediately, then keep it refreshed.
fetchStatus();
fetchUsage();
fetchSessionSummary();
sendTabActivity();
setupCameraPreview();

setInterval(fetchStatus, 2000);
setInterval(fetchUsage, 3000);
setInterval(fetchSessionSummary, 3000);
