const config = window.REPAIR_APP_CONFIG;
const kilometersPerDegreeLatitude = 111.32;

export async function resolveGermanLocation(query, fetchImpl = fetch) {
  const normalizedQuery = String(query ?? "").trim();

  if (!normalizedQuery) {
    throw new Error("Enter a German city or postcode.");
  }

  const params = new URLSearchParams({
    q: normalizedQuery,
    format: "jsonv2",
    countrycodes: "de",
    limit: String(config.maxGeocodingResults),
  });
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), config.geocodingBrowserTimeoutMs);
  let response;

  try {
    response = await fetchImpl(`${config.geocodingEndpoint}?${params}`, {
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    throw new Error(`Geocoding request failed with HTTP ${response.status}`);
  }

  const results = await response.json();

  if (!Array.isArray(results)) {
    throw new Error("Geocoding response was malformed.");
  }

  if (results.length === 0) {
    throw new Error("No matching German city or postcode was found.");
  }

  const result = results[0] || {};
  const lat = parseCoordinate(result.lat);
  const lon = parseCoordinate(result.lon);

  if (!isValidCoordinate(lat, lon)) {
    throw new Error("Geocoding response contained invalid coordinates.");
  }

  return {
    displayName: result.display_name || normalizedQuery,
    lat,
    lon,
    bbox: buildLocalBbox(lat, lon),
  };
}

function buildLocalBbox(lat, lon) {
  // MVP approximation for a small local-radius search, not an administrative boundary.
  const latitudeDelta = config.localSearchRadiusKm / kilometersPerDegreeLatitude;
  const longitudeDelta =
    config.localSearchRadiusKm /
    (kilometersPerDegreeLatitude * Math.cos(lat * Math.PI / 180));

  return [
    lat - latitudeDelta,
    lon - longitudeDelta,
    lat + latitudeDelta,
    lon + longitudeDelta,
  ].map((value) => value.toFixed(6)).join(",");
}

function isValidCoordinate(lat, lon) {
  return Number.isFinite(lat) &&
    Number.isFinite(lon) &&
    lat >= -90 &&
    lat <= 90 &&
    lon >= -180 &&
    lon <= 180;
}

function parseCoordinate(value) {
  const normalizedValue = String(value ?? "").trim();
  return normalizedValue ? Number(normalizedValue) : NaN;
}
