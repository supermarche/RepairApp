export const resourceTypes = [
  { value: "all", label: "All resource types" },
  { value: "community", label: "Repair Cafe / community" },
  { value: "tools", label: "Tool access" },
  { value: "workshop", label: "Workshop / makerspace" },
  { value: "guidance", label: "Knowledge / guidance" },
  { value: "commercial", label: "Commercial repair" },
  { value: "disposal", label: "Recycling / safe disposal" },
];

export const localResources = [
  {
    id: "demo-repair-cafe",
    name: "Repair Cafe Demo Hub",
    type: "community",
    categories: ["electrical", "furniture", "tool", "household", "unknown"],
    services: ["diagnosis", "minor repair", "guidance"],
    location: "Community Center, Main Square 4",
    lat: 51.1522,
    lng: 14.9881,
    description: "Volunteer repair support for everyday objects and first diagnosis.",
    source: "demo-data",
  },
  {
    id: "demo-tool-library",
    name: "Tool Library Corner",
    type: "tools",
    categories: ["furniture", "tool", "household"],
    services: ["borrow tools", "basic guidance"],
    location: "Library Annex, Workshop Street 8",
    lat: 51.1506,
    lng: 14.9836,
    description: "Borrow hand tools and measuring tools for low-risk repairs.",
    source: "demo-data",
  },
  {
    id: "demo-makerspace",
    name: "Maker Space Prototype Lab",
    type: "workshop",
    categories: ["tool", "household", "furniture"],
    services: ["3D printing", "small fabrication", "workbench access"],
    location: "Innovation Yard, Hall B",
    lat: 51.1571,
    lng: 14.9943,
    description: "Workshop access for brackets, sleeves, clamps, and small custom parts.",
    source: "future-osm-import",
  },
  {
    id: "demo-knowledge",
    name: "Open Repair Knowledge Desk",
    type: "guidance",
    categories: ["electrical", "furniture", "tool", "household", "unknown"],
    services: ["repair manuals", "triage", "maintenance tips"],
    location: "Online and at the community desk",
    lat: 51.1545,
    lng: 14.9871,
    description: "Helps identify repair manuals, common fixes, and safe first checks.",
    source: "demo-data",
  },
  {
    id: "demo-electronics-service",
    name: "Certified Electronics Service",
    type: "commercial",
    categories: ["electrical"],
    services: ["electrical safety check", "battery service", "device repair"],
    location: "Service Lane 12",
    lat: 51.1488,
    lng: 14.9918,
    description: "Professional repair for electrical devices, batteries, cables, and internal faults.",
    source: "future-osm-import",
  },
  {
    id: "demo-battery-dropoff",
    name: "Safe Battery Drop-Off",
    type: "disposal",
    categories: ["electrical"],
    services: ["battery disposal", "e-waste collection", "safe handling advice"],
    location: "Recycling Point North, Gate 2",
    lat: 51.1602,
    lng: 14.9784,
    description: "Safe disposal point for swollen batteries, damaged electronics, and e-waste.",
    source: "future-osm-import",
  },
  {
    id: "demo-furniture-fix",
    name: "Furniture Fix Workshop",
    type: "community",
    categories: ["furniture", "household"],
    services: ["wood repair", "stability check", "fastener replacement"],
    location: "Craft Hall, Timber Road 5",
    lat: 51.1466,
    lng: 14.9855,
    description: "Community support for chairs, shelves, tables, and small household furniture.",
    source: "demo-data",
  },
  {
    id: "demo-appliance-shop",
    name: "Appliance Maintenance Shop",
    type: "commercial",
    categories: ["electrical", "household"],
    services: ["maintenance", "descaling", "spare parts", "professional repair"],
    location: "Market Street 18",
    lat: 51.1515,
    lng: 14.9962,
    description: "Commercial service for small appliances and routine maintenance.",
    source: "demo-data",
  },
  {
    id: "demo-reuse-point",
    name: "Circular Goods Reuse Point",
    type: "disposal",
    categories: ["furniture", "tool", "household", "unknown"],
    services: ["reuse assessment", "recycling", "donation intake"],
    location: "Reuse Center, Depot Road 3",
    lat: 51.1437,
    lng: 14.9749,
    description: "Checks whether items can be reused, donated, recycled, or safely disposed.",
    source: "future-osm-import",
  },
  {
    id: "demo-skill-share",
    name: "Neighborhood Skill Share",
    type: "guidance",
    categories: ["furniture", "tool", "household"],
    services: ["repair coaching", "material advice", "workaround ideas"],
    location: "Weekly pop-up at Community Center",
    lat: 51.1556,
    lng: 14.9812,
    description: "Local volunteers share practical repair knowledge for ordinary low-risk cases.",
    source: "demo-data",
  },
];

let osmResources = [];
let osmResourceGeneration = 0;

const config = window.REPAIR_APP_CONFIG;
const adapterErrorCodes = new Set([
  "timeout",
  "rate_limited",
  "upstream_error",
  "malformed_response",
  "configuration_error",
]);

const osmTypeToUiType = {
  "electronics-repair": "commercial",
  "professional-repair": "commercial",
  "bicycle-repair": "commercial",
  tools: "tools",
  "community-support": "community",
  recycling: "disposal",
};

const priorityByRisk = {
  high: ["commercial", "disposal", "guidance", "community", "workshop", "tools"],
  caution: ["guidance", "community", "commercial", "tools", "workshop", "disposal"],
  low: ["community", "tools", "guidance", "workshop", "commercial", "disposal"],
};

export function matchResources({
  category,
  riskLevel,
  typeFilter = "all",
  categoryFilter = "all",
  sourceFilter = "all",
}) {
  const selectedCategory = categoryFilter === "all" ? category : categoryFilter;
  const priorities = priorityByRisk[riskLevel] || priorityByRisk.low;

  return getResources(sourceFilter)
    .filter((resource) => typeFilter === "all" || resource.type === typeFilter)
    .filter((resource) =>
      selectedCategory === "all" ||
      selectedCategory === "unknown" ||
      resource.categories.includes(selectedCategory) ||
      resource.categories.includes("unknown"),
    )
    .map((resource) => ({
      ...resource,
      matchReason: getMatchReason(resource, riskLevel),
      score: getScore(resource, priorities, selectedCategory),
    }))
    .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));
}

export function typeLabel(type) {
  return resourceTypes.find((item) => item.value === type)?.label || type;
}

export async function loadOsmResources(options = {}) {
  const { bbox, fetchImpl } = typeof options === "function"
    ? { fetchImpl: options }
    : options;
  const endpoint = validateEndpoint(config?.overpassEndpoint, "Overpass");
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), config.overpassBrowserTimeoutMs);
  const generation = osmResourceGeneration;
  let response;

  try {
    response = await (fetchImpl || fetch)(endpoint, {
      method: "POST",
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "User-Agent": "RepairApp-Hackathon-MVP/1.0",
      },
      body: new URLSearchParams({ data: buildOverpassQuery(bbox) }),
      signal: controller.signal,
    });
  } catch (error) {
    throw classifyRequestError(error, "Overpass");
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    throw adapterError(
      response.status === 429 ? "rate_limited" : "upstream_error",
      `Overpass request failed with HTTP ${response.status}.`,
    );
  }

  let data;

  try {
    data = await response.json();
  } catch (error) {
    throw preserveOrCreateAdapterError(
      error,
      "malformed_response",
      "Malformed Overpass response.",
    );
  }

  if (!data || !Array.isArray(data.elements)) {
    throw adapterError(
      "malformed_response",
      "Malformed Overpass response: expected elements array",
    );
  }

  const normalized = data.elements
    .map(normalizeOsmElement)
    .filter(Boolean);

  if (generation !== osmResourceGeneration) {
    return [];
  }

  osmResources = dedupeResources([...osmResources, ...normalized], localResources);
  return osmResources;
}

export function getOsmResourceCount() {
  return osmResources.length;
}

export function clearOsmResources() {
  osmResourceGeneration += 1;
  osmResources = [];
}

export function clearOsmResourcesForTest() {
  clearOsmResources();
}

function classifyRequestError(error, serviceName) {
  if (adapterErrorCodes.has(error?.code)) {
    return error;
  }

  if (error?.name === "AbortError") {
    return adapterError("timeout", `${serviceName} request timed out.`);
  }

  return preserveOrCreateAdapterError(
    error,
    "upstream_error",
    `${serviceName} request failed.`,
  );
}

function preserveOrCreateAdapterError(error, code, message) {
  return adapterErrorCodes.has(error?.code)
    ? error
    : adapterError(code, message);
}

function adapterError(code, message) {
  const error = new Error(message);
  error.code = code;
  return error;
}

function validateEndpoint(value, serviceName) {
  if (typeof value !== "string" || !value.trim()) {
    throw adapterError("configuration_error", `${serviceName} endpoint configuration is invalid.`);
  }

  let endpoint;

  try {
    endpoint = new URL(value);
  } catch {
    throw adapterError("configuration_error", `${serviceName} endpoint configuration is invalid.`);
  }

  if (!["http:", "https:"].includes(endpoint.protocol)) {
    throw adapterError("configuration_error", `${serviceName} endpoint configuration is invalid.`);
  }

  return endpoint.toString();
}

function getResources(sourceFilter) {
  if (sourceFilter === "local") {
    return localResources;
  }

  if (sourceFilter === "osm") {
    return osmResources;
  }

  if (sourceFilter === "none") {
    return [];
  }

  return [...localResources, ...osmResources];
}

function getScore(resource, priorities, selectedCategory) {
  const priorityIndex = priorities.indexOf(resource.type);
  const typeScore = priorityIndex === -1 ? 0 : (priorities.length - priorityIndex) * 10;
  const categoryScore = resource.categories.includes(selectedCategory) ? 8 : 0;

  return typeScore + categoryScore;
}

function getMatchReason(resource, riskLevel) {
  if (resource.source === "OpenStreetMap") {
    return "Imported from OpenStreetMap and matched with the same local filter rules.";
  }

  if (riskLevel === "high" && resource.type === "commercial") {
    return "Prioritized because high-risk cases need qualified professional help.";
  }

  if (riskLevel === "high" && resource.type === "disposal") {
    return "Prioritized because safe disposal or recycling may be the safest outcome.";
  }

  if (riskLevel === "low" && ["community", "tools", "guidance", "workshop"].includes(resource.type)) {
    return "Prioritized for ordinary low-risk cases where local support can help before replacement.";
  }

  return "Matches the selected category and can support this repair decision.";
}

function buildOverpassQuery(bbox = config.gorlitzDemoBbox) {
  return `
[out:json][timeout:${config.overpassServerTimeoutSeconds}];
(
  node["craft"="electronics_repair"](${bbox});
  way["craft"="electronics_repair"](${bbox});
  node["repair"](${bbox});
  way["repair"](${bbox});
  node["shop"="repair"](${bbox});
  way["shop"="repair"](${bbox});
  node["service:bicycle:repair"="yes"](${bbox});
  way["service:bicycle:repair"="yes"](${bbox});
  node["service:bicycle:diy"="yes"](${bbox});
  way["service:bicycle:diy"="yes"](${bbox});
  node["service:bicycle:tools"="yes"](${bbox});
  way["service:bicycle:tools"="yes"](${bbox});
  node["amenity"="bicycle_repair_station"](${bbox});
  way["amenity"="bicycle_repair_station"](${bbox});
  node["amenity"="recycling"]["recycling_type"="centre"](${bbox});
  way["amenity"="recycling"]["recycling_type"="centre"](${bbox});
);
out center ${config.maxLiveResults};
`;
}

function normalizeOsmElement(element) {
  const tags = element.tags || {};
  const lat = element.lat ?? element.center?.lat;
  const lng = element.lon ?? element.center?.lon;

  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    return null;
  }

  const type = inferType(tags);
  const uiType = mapOsmTypeToUiType(type);

  return {
    id: `osm-${element.type}-${element.id}`,
    name: tags.name || fallbackName(type),
    type: uiType,
    osmType: type,
    categories: inferCategories(tags, type),
    services: inferServices(tags, type),
    location: formatAddress(tags),
    lat,
    lng,
    description: describeOsmResource(tags, type),
    source: "OpenStreetMap",
  };
}

function inferType(tags) {
  if (tags.amenity === "recycling" && tags.recycling_type === "centre") {
    return "recycling";
  }

  if (tags.amenity === "bicycle_repair_station") {
    return "tools";
  }

  if (tags["service:bicycle:repair"] === "yes") {
    return "bicycle-repair";
  }

  if (tags["service:bicycle:diy"] === "yes" || tags["service:bicycle:tools"] === "yes") {
    return "tools";
  }

  if (tags.craft === "electronics_repair") {
    return "electronics-repair";
  }

  if (tags.shop === "repair") {
    return "professional-repair";
  }

  if (tags.repair) {
    return tags.repair === "assisted_self_service" ? "community-support" : "professional-repair";
  }

  return "professional-repair";
}

function mapOsmTypeToUiType(type) {
  return osmTypeToUiType[type] || "guidance";
}

function inferCategories(tags, type) {
  if (type === "recycling") {
    return ["electrical", "household", "tool", "unknown"];
  }

  if (type === "bicycle-repair" || type === "tools" && isBicycleResource(tags)) {
    return ["tool", "unknown"];
  }

  if (type === "electronics-repair") {
    return ["electrical"];
  }

  return ["electrical", "household", "tool", "unknown"];
}

function inferServices(tags, type) {
  if (type === "recycling") {
    return ["recycling", "safe disposal", ...recyclingMaterialServices(tags)];
  }

  if (type === "tools" && tags.amenity === "bicycle_repair_station") {
    return ["public bicycle repair tools"];
  }

  if (type === "tools" && isBicycleResource(tags)) {
    return ["bicycle self-repair tools"];
  }

  if (type === "bicycle-repair") {
    return ["bicycle repair", "repair service"];
  }

  if (type === "electronics-repair") {
    return ["electronics repair", "professional repair"];
  }

  if (type === "community-support") {
    return ["assisted self-repair", "community support"];
  }

  if (tags.repair) {
    return [`repair=${tags.repair}`];
  }

  return ["repair support"];
}

function recyclingMaterialServices(tags) {
  const materials = [
    ["recycling:batteries", "accepts batteries"],
    ["recycling:electrical_appliances", "accepts electrical appliances"],
    ["recycling:small_appliances", "accepts small appliances"],
    ["recycling:electronics", "accepts electronics"],
  ];

  return materials
    .filter(([tag]) => tags[tag] === "yes")
    .map(([, label]) => label);
}

function isBicycleResource(tags) {
  return tags.amenity === "bicycle_repair_station" ||
    tags["service:bicycle:repair"] === "yes" ||
    tags["service:bicycle:diy"] === "yes" ||
    tags["service:bicycle:tools"] === "yes";
}

function formatAddress(tags) {
  const street = [tags["addr:street"], tags["addr:housenumber"]].filter(Boolean).join(" ");
  const city = tags["addr:city"];

  return [street, city].filter(Boolean).join(", ") || "Selected search area";
}

function describeOsmResource(tags, type) {
  if (tags.description) {
    return tags.description;
  }

  if (type === "recycling") {
    return "OpenStreetMap recycling centre candidate for safe disposal.";
  }

  return "OpenStreetMap repair-related place found in the selected search area.";
}

function fallbackName(type) {
  if (type === "recycling") {
    return "OSM recycling point";
  }

  if (type === "tools") {
    return "OSM repair tools";
  }

  return "OSM repair resource";
}

function dedupeResources(imported, fallbackResources) {
  const seen = new Set(fallbackResources.map(resourceKey));
  const unique = [];

  imported.forEach((resource) => {
    const key = resourceKey(resource);

    if (!seen.has(key)) {
      seen.add(key);
      unique.push(resource);
    }
  });

  return unique;
}

function resourceKey(resource) {
  const name = resource.name.toLowerCase().replace(/[^a-z0-9]/g, "");
  const location = resource.location.toLowerCase().replace(/[^a-z0-9]/g, "");
  const roundedLat = resource.lat ? resource.lat.toFixed(3) : "";
  const roundedLng = resource.lng ? resource.lng.toFixed(3) : "";

  return `${name}-${location}-${roundedLat}-${roundedLng}`;
}
