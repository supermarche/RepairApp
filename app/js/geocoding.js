const config = window.REPAIR_APP_CONFIG;
const kilometersPerDegreeLatitude = 111.32;
const germanPostcodePattern = /^\d{5}$/;
const settlementTypes = new Set([
  "city",
  "hamlet",
  "isolated_dwelling",
  "locality",
  "municipality",
  "settlement",
  "town",
  "village",
]);

export async function resolveGermanLocation(query, fetchImpl = fetch) {
  const normalizedQuery = String(query ?? "").trim();

  if (!normalizedQuery) {
    throw new Error("Enter a German city or postcode.");
  }

  const isPostcode = germanPostcodePattern.test(normalizedQuery);
  const params = new URLSearchParams({
    format: "jsonv2",
    countrycodes: "de",
    layer: "address",
    limit: String(config.maxGeocodingResults),
  });

  if (isPostcode) {
    params.set("postalcode", normalizedQuery);
  } else {
    params.set("city", normalizedQuery);
    params.set("featureType", "settlement");
    params.set("namedetails", "1");
  }

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
    throw noAcceptableLocationError();
  }

  const acceptedResult = results
    .map((item) => getAcceptableResult(item, isPostcode, normalizedQuery))
    .find(Boolean);

  if (!acceptedResult) {
    throw noAcceptableLocationError();
  }

  const { result, displayName } = acceptedResult;
  const lat = parseCoordinate(result.lat);
  const lon = parseCoordinate(result.lon);

  if (!isValidCoordinate(lat, lon)) {
    throw new Error("Geocoding response contained invalid coordinates.");
  }

  return {
    displayName,
    lat,
    lon,
    bbox: buildLocalBbox(lat, lon),
  };
}

function getAcceptableResult(result, isPostcode, query) {
  if (!result || typeof result !== "object") {
    return null;
  }

  const addressType = String(result.addresstype || "").toLowerCase();
  const type = String(result.type || "").toLowerCase();

  if (isPostcode) {
    return addressType === "postcode" || type === "postcode"
      ? { result, displayName: result.display_name || query }
      : null;
  }

  const isSettlement = settlementTypes.has(addressType) ||
    result.category === "place" && settlementTypes.has(type);
  const matchingName = getResultNames(result).find(({ value }) =>
    normalizeLocationName(value) === normalizeLocationName(query),
  );

  return isSettlement && matchingName
    ? {
      result,
      displayName: matchingName.canExpose ? matchingName.value : query,
    }
    : null;
}

function getResultNames(result) {
  const namedetails = result.namedetails || {};
  const namedetailNames = Object.entries(namedetails)
    .filter(([key, value]) =>
      (key === "name" || key.startsWith("name:")) &&
      typeof value === "string" &&
      value.trim()
    )
    .map(([, value]) => ({ value: value.trim(), canExpose: true }));
  const displayName = String(result.display_name || "").split(",")[0].trim();

  return displayName
    ? [...namedetailNames, { value: displayName, canExpose: false }]
    : namedetailNames;
}

function normalizeLocationName(value) {
  return String(value || "")
    .normalize("NFKC")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
}

function noAcceptableLocationError() {
  const error = new Error("No acceptable German city or postcode was found.");
  error.code = "no_acceptable_location";
  return error;
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
