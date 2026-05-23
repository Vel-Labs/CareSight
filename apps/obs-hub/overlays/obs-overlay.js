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
  alert_feed: [
    { type: "event_created", time: "7:41 PM", label: "Possible floor-stay", detail: "Living Room | Human review required", status: "Unreviewed", tone: "attention" },
    { type: "draft_prepared", time: "7:42 PM", label: "Caregiver alert drafted", detail: "Local Gemma | Validated", status: "Prepared", tone: "cool" },
    { type: "action_staged", time: "7:42 PM", label: "iMessage caregiver alert", detail: "iMessage | Human-approved lane", status: "Staged", tone: "cool" }
  ],
  camera_cards: [
    { camera_id: "living_room", display_id: "C1", zone: "Living Room", status_label: "Live priority feed", source: "Webcam", icon: "camera-live", tone: "cool" },
    { camera_id: "kitchen", display_id: "C2", zone: "Kitchen", status_label: "Not configured", source: "No local source", icon: "camera-off", tone: "muted" },
    { camera_id: "hallway", display_id: "C3", zone: "Hallway", status_label: "Not configured", source: "No local source", icon: "camera-off", tone: "muted" },
    { camera_id: "bedroom", display_id: "C4", zone: "Bedroom", status_label: "Not configured", source: "No local source", icon: "camera-off", tone: "muted" }
  ],
  handoff_status: { label: "Review required", status: "review_required", tone: "attention" },
  constraints: ["Raw video stays local", "Human review required", "No emergency dispatch", "Not a medical device"]
};

const overlayParams = new URLSearchParams(window.location.search);

const cssVarNames = {
  brand: { left: "--brand-left", top: "--brand-top" },
  clock: { right: "--clock-right", top: "--clock-top" },
  feedFrame: {
    left: "--feed-left",
    top: "--feed-top",
    width: "--feed-width",
    height: "--feed-height"
  },
  thumbs: {
    left: "--thumbs-left",
    top: "--thumbs-top",
    width: "--thumbs-width",
    height: "--thumbs-height"
  },
  eventPanel: {
    left: "--event-panel-left",
    right: "--event-panel-right",
    top: "--event-panel-top",
    width: "--event-panel-width"
  },
  activityStrip: {
    left: "--activity-left",
    right: "--activity-right",
    bottom: "--activity-bottom"
  },
  footer: {
    left: "--footer-left",
    right: "--footer-right",
    bottom: "--footer-bottom"
  },
  header: {
    left: "--mobile-header-left",
    right: "--mobile-header-right",
    top: "--mobile-header-top"
  },
  activityPanel: {
    left: "--mobile-activity-left",
    right: "--mobile-activity-right",
    top: "--mobile-activity-top",
    bottom: "--mobile-activity-bottom"
  }
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

function loadOverlayLayout() {
  return new Promise((resolve) => {
    if (window.CareSightOverlayLayout) {
      resolve(window.CareSightOverlayLayout);
      return;
    }
    const script = document.createElement("script");
    script.src = `../config/overlay_layout.js?t=${Date.now()}`;
    script.async = true;
    script.onload = () => resolve(window.CareSightOverlayLayout || null);
    script.onerror = () => resolve(null);
    document.head.appendChild(script);
    setTimeout(() => resolve(null), 1200);
  });
}

function setLayoutVars(values, mapping) {
  if (!values || !mapping) {
    return;
  }
  Object.entries(mapping).forEach(([key, cssName]) => {
    const value = values[key];
    if (value !== undefined && value !== null) {
      document.documentElement.style.setProperty(cssName, `${value}px`);
    }
  });
}

function applyLayoutGroup(layout, view) {
  const config = layout?.[view];
  if (!config) {
    return;
  }

  if (view === "escalation") {
    setLayoutVars(config.brand, cssVarNames.brand);
    setLayoutVars(config.clock, cssVarNames.clock);
    setLayoutVars(config.feedFrame || config.liveFeed, cssVarNames.feedFrame);
    setLayoutVars(config.thumbs, cssVarNames.thumbs);
    setLayoutVars(config.eventPanel, cssVarNames.eventPanel);
    setLayoutVars(config.activityStrip, cssVarNames.activityStrip);
    setLayoutVars(config.footer, cssVarNames.footer);
    if (Array.isArray(config.thumbsText)) {
      document.querySelectorAll(".thumb").forEach((node, index) => {
        if (config.thumbsText[index]) {
          node.textContent = config.thumbsText[index];
        }
      });
    }
    return;
  }

  if (view === "facetime") {
    setLayoutVars(config.header, cssVarNames.header);
    setLayoutVars(config.feedFrame || config.liveFeed, cssVarNames.feedFrame);
    setLayoutVars(config.eventPanel, cssVarNames.eventPanel);
    setLayoutVars(config.activityPanel, cssVarNames.activityPanel);
    setLayoutVars(config.footer, cssVarNames.footer);
  }
}

async function applyOverlayLayout(view) {
  const layout = await loadOverlayLayout();
  applyLayoutGroup(layout, view);
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
  if (value.includes("unreviewed") || value.includes("attention") || value.includes("waiting")) {
    return "attention";
  }
  if (value.includes("reviewed") || value.includes("logged") || value.includes("ready") || value.includes("complete") || value.includes("live")) {
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

function iconForType(type) {
  const icons = {
    event_created: "!",
    draft_prepared: "M",
    action_staged: "S",
    hermes_no_send_preflight_ready: "H",
    imessage_sent: "i",
    imessage_no_response_escalation_sent: "+",
    facetime_open_requested: "F",
    tts_playback_requested: "A",
    "camera-live": "C",
    camera: "C",
    "camera-off": "-"
  };
  return icons[type] || "•";
}

function renderAlertFeed(container, items) {
  container.innerHTML = "";
  items.forEach((item) => {
    const row = document.createElement("div");
    const tone = item.tone || statusClass(item.status);
    row.className = "alert-feed-item";
    row.innerHTML = `
      <div class="obs-icon ${tone}">${iconForType(item.type)}</div>
      <div class="alert-feed-copy">
        <div class="alert-feed-top">
          <span class="alert-feed-time">${item.time || ""}</span>
          <span class="alert-feed-status ${tone}">${item.status || "Logged"}</span>
        </div>
        <div class="alert-feed-label">${item.label || "CareSight activity"}</div>
        <div class="alert-feed-detail">${item.detail || ""}</div>
      </div>
    `;
    container.appendChild(row);
  });
}

function renderCameraCards(container, cards) {
  container.innerHTML = "";
  cards.slice(0, 4).forEach((card) => {
    const row = document.createElement("div");
    const tone = card.tone || statusClass(card.status_label);
    row.className = "camera-card";
    row.innerHTML = `
      <div class="obs-icon ${tone}">${iconForType(card.icon)}</div>
      <div>
        <div class="camera-card-title">${card.zone || "Camera"}</div>
        <div class="camera-card-meta">${card.display_id || ""} | ${card.status_label || "Configured"}</div>
        <div class="camera-card-source">${card.source || "Local source"}</div>
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
  setText("handoffStatus", data.handoff_status?.label || "Review required");
  setText("overlaySource", `Data: ${data.overlay_source || "unknown"}`);
  setText("overlayGeneratedAt", data.generated_at ? `Updated: ${formatObservedAt(data.generated_at)}` : "Updated: fixture");
  setText("mainFeedLabel", `Active feed: ${event.zone || "Living Room"}`);
  window.CareSightLivePreviewState = resolveLivePreview(data.live_preview);
  refreshLivePreviewOnly();
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
  const alertFeed = document.getElementById("alertFeed");
  if (alertFeed) {
    renderAlertFeed(alertFeed, data.alert_feed || fallbackData.alert_feed);
  }
  const cameraCards = document.getElementById("cameraCards");
  if (cameraCards) {
    renderCameraCards(cameraCards, data.camera_cards || fallbackData.camera_cards);
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
  window.CareSightLivePreviewState = resolveLivePreview(preview);
  refreshLivePreviewOnly();
}

function resolveLivePreview(preview) {
  if (overlayParams.get("feed") === "mjpeg") {
    return {
      available: true,
      stream: true,
      url: overlayParams.get("feed_url") || "http://127.0.0.1:8766/stream.mjpg"
    };
  }
  const fallbackUrl = "../config/live_preview.jpg";
  return {
    available: Boolean(preview?.available) || true,
    stream: false,
    url: preview?.url && preview.available ? preview.url : fallbackUrl
  };
}

function refreshLivePreviewOnly() {
  const image = document.getElementById("livePreviewImage");
  if (!image) {
    return;
  }
  const preview = window.CareSightLivePreviewState || resolveLivePreview(null);
  if (preview.stream) {
    if (image.src !== preview.url) {
      image.src = preview.url;
    }
    return;
  }
  image.src = `${preview.url}?t=${Date.now()}`;
}
