import { analyzeProblem } from "./analyzer.js";
import { resolveGermanLocation } from "./geocoding.js";
import {
  clearOsmResources,
  loadOsmResources,
  matchResources,
  resourceTypes,
  typeLabel,
} from "./resources.js";

const form = document.querySelector("#repair-form");
const category = document.querySelector("#category");
const problem = document.querySelector("#problem");
const exampleButtons = document.querySelectorAll("[data-example]");
const riskTitle = document.querySelector("#risk-title");
const riskBadge = document.querySelector("#risk-badge");
const safetyWarning = document.querySelector("#safety-warning");
const failureType = document.querySelector("#failure-type");
const signals = document.querySelector("#signals");
const actions = document.querySelector("#actions");
const recommendation = document.querySelector("#recommendation");
const prevention = document.querySelector("#prevention");
const resourceType = document.querySelector("#resource-type");
const resourceCategory = document.querySelector("#resource-category");
const locationForm = document.querySelector("#location-form");
const locationQuery = document.querySelector("#location-query");
const locationStatus = document.querySelector("#location-status");
const helpSummary = document.querySelector("#help-summary");
const resources = document.querySelector("#resources");
const mapElement = document.querySelector("#resource-map");
const loadOsmButton = document.querySelector("#load-osm");
const osmStatus = document.querySelector("#osm-status");

let latestResult = null;
let latestMatches = [];
let map = null;
let markerLayer = null;
let isOsmLoading = false;
let locationSearchSequence = 0;
let resourceSourceFilter = "all";
const locationFailureMessages = {
  timeout: "External map service did not respond in time.",
  rate_limited: "Public map service is temporarily limiting requests.",
  upstream_error: "External map service is temporarily unavailable.",
  malformed_response: "External map service returned an invalid response.",
};

resourceType.replaceChildren(
  ...resourceTypes.map((type) => {
    const option = document.createElement("option");
    option.value = type.value;
    option.textContent = type.label;
    return option;
  }),
);

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const result = analyzeProblem({
    category: category.value,
    description: problem.value,
  });

  latestResult = result;
  renderResult(result);
  renderResources();
});

resourceType.addEventListener("change", renderResources);
resourceCategory.addEventListener("change", renderResources);
locationForm.addEventListener("submit", handleLocationSearch);
loadOsmButton.addEventListener("click", handleLoadOsm);

exampleButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const example = button.dataset.example;

    if (example === "battery") {
      category.value = "electrical";
      problem.value = "My laptop battery is swollen and the case feels warm.";
    } else {
      category.value = "tool";
      problem.value = "My selfie stick is stuck and the clamp will not move.";
    }

    form.requestSubmit();
  });
});

function renderResult(result) {
  riskTitle.textContent = riskTitleText(result.riskLevel);
  riskBadge.textContent = result.riskLevel;
  riskBadge.className = `risk-badge ${result.riskLevel}`;

  failureType.textContent = result.failureType;
  signals.textContent = result.riskReasons.length
    ? result.riskReasons.join(", ")
    : "No specific safety risk keywords detected.";

  if (result.riskLevel === "high") {
    safetyWarning.classList.remove("hidden");
    safetyWarning.textContent = hasBatteryRisk(result)
      ? "Safety warning: stop using the device, do not attempt DIY disassembly, and confirm that any selected recycling location accepts lithium-ion batteries or electronic waste before visiting."
      : "Safety warning: this description contains high-risk signals. Avoid DIY repair and prioritize stopping use, professional help, replacement, or recycling.";
  } else if (result.riskLevel === "caution") {
    safetyWarning.classList.remove("hidden");
    safetyWarning.textContent =
      "Safety note: this description contains caution signals. Pause use, inspect carefully, and avoid repair steps that could make the item unstable or unsafe.";
  } else {
    safetyWarning.classList.add("hidden");
    safetyWarning.textContent = "";
  }

  actions.replaceChildren(
    ...result.actions.map((group) => {
      const card = document.createElement("article");
      card.className = "action-card";

      const heading = document.createElement("h4");
      heading.textContent = group.title;

      const list = document.createElement("ul");
      group.actions.forEach((action) => {
        const item = document.createElement("li");
        item.textContent = action;
        list.append(item);
      });

      card.append(heading, list);
      return card;
    }),
  );

  recommendation.textContent = result.recommendedNextStep;
  prevention.textContent = result.preventionTip;
}

function hasBatteryRisk(result) {
  return result.riskReasons.some((reason) => reason.toLowerCase().includes("battery"));
}

function renderResources() {
  if (!latestResult) {
    return;
  }

  const matches = matchResources({
    category: latestResult.category,
    riskLevel: latestResult.riskLevel,
    typeFilter: resourceType.value,
    categoryFilter: resourceCategory.value,
    sourceFilter: resourceSourceFilter,
  });
  latestMatches = matches;

  helpSummary.textContent = `${latestResult.helpNeeded}. Showing ${matches.length} matching resources, prioritized for ${latestResult.riskLevel} risk.`;
  updateMapMarkers(matches);

  resources.replaceChildren(
    ...matches.map((resource) => {
      const card = document.createElement("article");
      card.className = "resource-card";

      const heading = document.createElement("h4");
      heading.textContent = resource.name;

      const meta = document.createElement("p");
      meta.className = "resource-meta";
      meta.textContent = `${typeLabel(resource.type)} | ${resource.location}`;

      const description = document.createElement("p");
      description.textContent = resource.description;

      const services = document.createElement("p");
      services.className = "resource-services";
      services.textContent = `Services: ${resource.services.join(", ")}`;

      const reason = document.createElement("p");
      reason.className = "match-reason";
      reason.textContent = resource.matchReason;

      const source = document.createElement("span");
      source.className = "source-badge";
      source.textContent = resource.source;

      card.append(heading, meta, description, services, reason, source);
      return card;
    }),
  );
}

async function handleLocationSearch(event) {
  event.preventDefault();

  const sequence = ++locationSearchSequence;
  clearOsmResources();
  resourceSourceFilter = "none";
  clearResourceDisplay();
  setLocationStatus("loading", "Resolving location and loading live OpenStreetMap resources...");

  if (!locationQuery.value.trim()) {
    showLocalFallback();
    setLocationStatus(
      "invalid_location",
      "Enter a German city or postcode. Showing local Görlitz demo fallback.",
    );
    return;
  }

  try {
    const resolvedLocation = await resolveGermanLocation(locationQuery.value);

    if (sequence !== locationSearchSequence) {
      return;
    }

    centerMapOnLocation(resolvedLocation);
    const loaded = await loadOsmResources({ bbox: resolvedLocation.bbox });

    if (sequence !== locationSearchSequence) {
      return;
    }

    if (loaded.length === 0) {
      showLocalFallback();
      setLocationStatus(
        "no_results",
        `No live OpenStreetMap resources found near ${resolvedLocation.displayName}. Showing local Görlitz demo fallback.`,
      );
      return;
    }

    resourceSourceFilter = "osm";
    renderResources();
    setLocationStatus(
      "success",
      `Loaded ${loaded.length} live OpenStreetMap resources near ${resolvedLocation.displayName}.`,
    );
  } catch (error) {
    if (sequence !== locationSearchSequence) {
      return;
    }

    showLocalFallback();

    if (error.code === "no_acceptable_location") {
      setLocationStatus(
        "invalid_location",
        `${error.message} Showing local Görlitz demo fallback.`,
      );
      return;
    }

    const failure = getLocationFailure(error);
    console.error(`Live location search failed: ${failure.state}`, error);
    setLocationStatus(
      failure.state,
      `${failure.message} Showing local Görlitz demo fallback.`,
    );
  }
}

async function handleLoadOsm() {
  if (isOsmLoading) {
    return;
  }

  const sequence = ++locationSearchSequence;
  clearOsmResources();
  resourceSourceFilter = "local";
  renderResources();
  isOsmLoading = true;
  loadOsmButton.disabled = true;
  osmStatus.textContent = "Loading one bounded Overpass query for the Gorlitz area...";

  try {
    const loaded = await loadOsmResources();

    if (sequence !== locationSearchSequence) {
      return;
    }

    resourceSourceFilter = loaded.length > 0 ? "osm" : "local";
    osmStatus.textContent = loaded.length > 0
      ? `Loaded ${loaded.length} OpenStreetMap resources for the Görlitz demo area.`
      : "No new OpenStreetMap resources found for this query. Showing local Görlitz demo fallback.";
    renderResources();
  } catch (error) {
    if (sequence !== locationSearchSequence) {
      return;
    }

    console.error("Live Görlitz OSM request failed.", error);
    osmStatus.textContent = `Live OSM request failed. Showing local Görlitz demo fallback. ${error.message}`;
    renderResources();
  } finally {
    isOsmLoading = false;
    loadOsmButton.disabled = false;
  }
}

function initMap() {
  if (!window.L || !mapElement) {
    osmStatus.textContent =
      "Leaflet could not be loaded. The list remains available as fallback.";
    return;
  }

  map = window.L.map(mapElement, {
    scrollWheelZoom: false,
  }).setView([51.152, 14.988], 13);

  window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  markerLayer = window.L.layerGroup().addTo(map);
}

function updateMapMarkers(matches) {
  if (!map || !markerLayer) {
    return;
  }

  markerLayer.clearLayers();

  const markers = matches
    .filter((resource) => Number.isFinite(resource.lat) && Number.isFinite(resource.lng))
    .map((resource) => {
      const marker = window.L.marker([resource.lat, resource.lng]);
      marker.bindPopup(
        `<strong>${escapeHtml(resource.name)}</strong><br>` +
          `${escapeHtml(typeLabel(resource.type))}<br>` +
          `${escapeHtml(resource.location)}<br>` +
          `${escapeHtml(resource.description)}<br>` +
          `<span>${escapeHtml(resource.source)}</span>`,
      );
      marker.addTo(markerLayer);
      return marker;
    });

  if (markers.length > 0) {
    const group = window.L.featureGroup(markers);
    map.fitBounds(group.getBounds().pad(0.18), {
      maxZoom: 14,
    });
  } else {
    map.setView([51.152, 14.988], 13);
  }
}

function clearResourceDisplay() {
  latestMatches = [];
  resources.replaceChildren();

  if (markerLayer) {
    markerLayer.clearLayers();
  }
}

function showLocalFallback() {
  resourceSourceFilter = "local";
  renderResources();
}

function setLocationStatus(state, message) {
  locationStatus.dataset.state = state;
  locationStatus.textContent = message;
}

function getLocationFailure(error) {
  const state = Object.hasOwn(locationFailureMessages, error?.code)
    ? error.code
    : "upstream_error";

  return {
    state,
    message: locationFailureMessages[state],
  };
}

function centerMapOnLocation({ lat, lon }) {
  if (map) {
    map.setView([lat, lon], 13);
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function riskTitleText(level) {
  if (level === "high") {
    return "High safety risk detected";
  }

  if (level === "caution") {
    return "Use caution before acting";
  }

  return "Low immediate safety risk";
}

initMap();
