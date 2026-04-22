const http = require("http");
const https = require("https");

const DEFAULT_FALLBACK_TARGET = "http://127.0.0.1:8000";
const REQUIRED_ROUTES = ["/api/books", "/api/authors"];
const CACHE_TTL_MS = Number(process.env.FILTER_PROXY_CACHE_MS || 5000);
const REQUEST_TIMEOUT_MS = Number(process.env.FILTER_PROXY_TIMEOUT_MS || 700);

let cachedTarget = null;
let cachedAt = 0;

function parseList(value) {
  if (!value) {
    return [];
  }
  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter((entry) => entry.length > 0);
}

function unique(values) {
  return [...new Set(values)];
}

function normalizeUrl(url) {
  if (!url) {
    return null;
  }
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }
  return `http://${url}`;
}

function buildCandidates() {
  const explicitTargets = parseList(process.env.FILTER_API_TARGETS).map(
    normalizeUrl,
  );
  const singleTarget = normalizeUrl(process.env.FILTER_API_TARGET || "");

  const envPorts = parseList(process.env.FILTER_API_PORTS)
    .map((entry) => Number(entry))
    .filter((entry) => Number.isInteger(entry) && entry > 0);

  const backendPort = Number(process.env.BACKEND_PORT || "");
  const ports = [
    ...envPorts,
    ...(Number.isInteger(backendPort) && backendPort > 0 ? [backendPort] : []),
    8000,
    8001,
    8002,
    8010,
    8080,
  ];

  const portTargets = unique(ports).map((port) => `http://127.0.0.1:${port}`);

  return unique(
    [
      singleTarget,
      ...explicitTargets,
      ...portTargets,
      DEFAULT_FALLBACK_TARGET,
    ].filter(Boolean),
  );
}

function requestJson(url) {
  const client = url.startsWith("https://") ? https : http;

  return new Promise((resolve) => {
    const req = client.get(
      url,
      {
        timeout: REQUEST_TIMEOUT_MS,
        headers: { Accept: "application/json" },
      },
      (res) => {
        let data = "";
        res.on("data", (chunk) => {
          data += chunk;
        });
        res.on("end", () => {
          if (res.statusCode !== 200) {
            resolve(null);
            return;
          }
          try {
            resolve(JSON.parse(data));
          } catch {
            resolve(null);
          }
        });
      },
    );

    req.on("error", () => resolve(null));
    req.on("timeout", () => {
      req.destroy();
      resolve(null);
    });
  });
}

async function isCompatibleBackend(target) {
  const openapi = await requestJson(`${target}/openapi.json`);
  if (!openapi || !openapi.paths) {
    return false;
  }
  return REQUIRED_ROUTES.every((route) =>
    Object.prototype.hasOwnProperty.call(openapi.paths, route),
  );
}

async function resolveTarget() {
  const now = Date.now();
  if (cachedTarget && now - cachedAt <= CACHE_TTL_MS) {
    return cachedTarget;
  }

  const candidates = buildCandidates();
  for (const target of candidates) {
    // eslint-disable-next-line no-await-in-loop
    const ok = await isCompatibleBackend(target);
    if (ok) {
      cachedTarget = target;
      cachedAt = now;
      return target;
    }
  }

  cachedTarget = candidates[0] || DEFAULT_FALLBACK_TARGET;
  cachedAt = now;
  return cachedTarget;
}

module.exports = {
  "/api": {
    target: DEFAULT_FALLBACK_TARGET,
    secure: false,
    changeOrigin: true,
    logLevel: "warn",
    router: async () => resolveTarget(),
  },
};
