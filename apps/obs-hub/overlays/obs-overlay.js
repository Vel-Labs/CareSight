const fallbackData = {
  site: {
    name: "Maple Residence",
    mode: "Observation Mode"
  },
  current_event: {
    event_id: "EVT-2026-05-21-0042",
    display_id: "EVT-0042",
    display_label: "Possible floor-stay",
    zone: "Living Room",
    camera_id: "C1",
    observed_at: "2026-05-21T19:41:00-05:00",
    subject_label: "Resident",
    review_status: "unreviewed",
    escalation_state: "draft_caregiver_alert_prepared",
    suggested_next_step: "Check live feed and contact caregiver if concern remains"
  },
  recent_activity: [
    { time: "7:41 PM", label: "Possible floor-stay", zone: "Living Room", status: "Unreviewed" },
    { time: "7:14 PM", label: "Routine activity observed", zone: "Living Room", status: "Reviewed" },
    { time: "6:58 PM", label: "Last movement observed", zone: "Hallway", status: "Logged" },
    { time: "6:15 PM", label: "Evening routine observed", zone: "Bedroom", status: "Reviewed" }
  ],
  constraints: ["Raw video stays local", "Human review required", "No emergency dispatch", "Not a medical device"]
};

async function loadEventData() {
  const scriptData = await loadScriptEventData();
  if (scriptData) {
    return withOverlaySource(scriptData, "current_event.js");
  }
  const paths = ["../config/current_event.json", "../config/sample_event.json"];
  try {
    for (const path of paths) {
      const response = await fetch(path, { cache: "no-store" });
      if (response.ok) {
        return withOverlaySource(await response.json(), path);
      }
    }
  } catch {
    // file:// preview may block local fetches; fallback keeps overlays inspectable.
  }
  return withOverlaySource(fallbackData, "fallback");
}

function withOverlaySource(data, source) {
  return { ...data, overlay_source: source };
}

function loadScriptEventData() {
  return new Promise((resolve) => {
    const script = document.createElement("script");
    script.src = `../config/current_event.js?t=${Date.now()}`;
    script.async = true;
    script.onload = () => resolve(window.CareSightOverlayData || null);
    script.onerror = () => resolve(null);
    document.head.appendChild(script);
    setTimeout(() => resolve(null), 1200);
  });
}

function formatNow() {
  const now = new Date();
  return {
    date: now.toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" }),
    time: now.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })
  };
}

function formatObservedAt(value) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "7:41 PM";
  }
  return parsed.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

function humanizeState(value) {
  return String(value || "")
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function statusClass(status) {
  const value = String(status || "").toLowerCase();
  if (value.includes("unreviewed") || value.includes("attention")) {
    return "attention";
  }
  if (value.includes("reviewed") || value.includes("logged")) {
    return "cool";
  }
  return "";
}

function updateClock() {
  const now = formatNow();
  document.querySelectorAll("[data-now-date]").forEach((node) => {
    node.textContent = now.date;
  });
  document.querySelectorAll("[data-now-time]").forEach((node) => {
    node.textContent = now.time;
  });
}

function renderActivity(container, items) {
  container.innerHTML = "";
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "activity-item";
    row.innerHTML = `
      <div class="activity-dot ${statusClass(item.status)}"></div>
      <div>
        <div class="activity-time">${item.time}</div>
        <div class="activity-name">${item.label}</div>
        <div class="activity-meta">${item.zone} | <span class="${statusClass(item.status)}">${item.status}</span></div>
      </div>
    `;
    container.appendChild(row);
  });
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) {
    node.textContent = value;
  }
}

function renderEventPanel(data) {
  const event = data.current_event || fallbackData.current_event;
  setText("eventLabel", event.display_label || "Review required");
  setText("observedAt", formatObservedAt(event.observed_at));
  setText("subject", event.subject_label || "Resident");
  setText("reviewStatus", humanizeState(event.review_status || "unreviewed"));
  setText("escalation", humanizeState(event.escalation_state || "draft_caregiver_alert_prepared"));
  setText("eventId", event.display_id || shortEventId(event.event_id) || "not recorded");
  setText("suggested", event.suggested_next_step || "Review the local record and live feed.");
  setText("overlaySource", `Data: ${data.overlay_source || "unknown"}`);
  setText("overlayGeneratedAt", data.generated_at ? `Updated: ${formatObservedAt(data.generated_at)}` : "Updated: fixture");
  setText("mainFeedLabel", `Active feed: ${event.zone || "Living Room"}`);
  renderLivePreview(data.live_preview);
}

async function refreshOverlayData() {
  updateClock();
  const data = await loadEventData();
  renderEventPanel(data);
  document.querySelectorAll("[data-site-name]").forEach((node) => {
    node.textContent = data.site?.name || fallbackData.site.name;
  });
  document.querySelectorAll("[data-site-mode]").forEach((node) => {
    node.textContent = data.site?.mode || fallbackData.site.mode;
  });
  const activityGrid = document.getElementById("activityGrid");
  if (activityGrid) {
    renderActivity(activityGrid, data.recent_activity || fallbackData.recent_activity);
  }
  return data;
}

function shortEventId(eventId) {
  if (!eventId) {
    return "";
  }
  const value = String(eventId);
  if (value.length <= 18) {
    return value;
  }
  if (value.startsWith("evt_")) {
    return `${value.slice(0, 10)}...${value.slice(-6)}`;
  }
  return `${value.slice(0, 8)}...${value.slice(-6)}`;
}

function renderLivePreview(preview) {
  const image = document.getElementById("livePreviewImage");
  if (!image) {
    return;
  }
  const fallbackUrl = "../config/live_preview.jpg";
  const url = preview?.url && preview.available ? preview.url : fallbackUrl;
  image.src = `${url}?t=${Date.now()}`;
}
