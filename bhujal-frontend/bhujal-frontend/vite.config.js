import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import net from 'node:net';

const BACKEND_URL = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';
let isBackendAlive = false;
let lastCheck = 0;
let checkInProgress = false;
let lastLoggedOffline = 0;

function checkBackendStatus(callback) {
  const now = Date.now();
  if (now - lastCheck < 3000) {
    return callback(isBackendAlive);
  }
  if (checkInProgress) {
    return callback(isBackendAlive);
  }
  checkInProgress = true;
  const socket = new net.Socket();
  socket.setTimeout(250);
  socket.on('connect', () => {
    if (!isBackendAlive) {
      console.log(
        '\x1b[32m%s\x1b[0m',
        `🟢 [Bhujal Proxy] Live FastAPI Backend detected on port 8000! Real-time AI agents & live scoring connected.`
      );
    }
    isBackendAlive = true;
    lastCheck = Date.now();
    checkInProgress = false;
    socket.destroy();
    callback(true);
  });
  const handleFail = () => {
    isBackendAlive = false;
    lastCheck = Date.now();
    checkInProgress = false;
    socket.destroy();
    callback(false);
  };
  socket.on('error', handleFail);
  socket.on('timeout', handleFail);
  socket.connect(8000, '127.0.0.1');
}

function createProxy(target) {
  return {
    target,
    changeOrigin: true,
    ws: true,
    bypass: async (req, res) => {
      const alive = await new Promise((resolve) => checkBackendStatus(resolve));
      if (!alive) {
        const now = Date.now();
        if (now - lastLoggedOffline > 30000) {
          lastLoggedOffline = now;
          console.log(
            '\x1b[33m%s\x1b[0m',
            `ℹ️  [Bhujal Proxy] FastAPI Backend at ${target} is currently offline.\n` +
            `   • Mode: Resilient offline fallback (mock/cached data active).\n` +
            `   • To connect live AI agents & database, start backend in a separate terminal:\n` +
            `       python -m uvicorn backend.app:app --port 8000\n` +
            `   • Or start both at once with: npm run dev:all`
          );
        }
        if (res && !res.headersSent && typeof res.writeHead === 'function') {
          res.writeHead(503, { 'Content-Type': 'application/json' });
          res.end(
            JSON.stringify({
              error: 'Backend offline',
              code: 'ECONNREFUSED',
              message: 'FastAPI backend service is offline. Serving frontend fallback.',
            })
          );
        }
        return false;
      }
      return null;
    },
    configure: (proxy) => {
      proxy.on('error', (err, req, res) => {
        if (err.code === 'ECONNREFUSED') {
          if (res && !res.headersSent && typeof res.writeHead === 'function') {
            res.writeHead(503, { 'Content-Type': 'application/json' });
            res.end(
              JSON.stringify({
                error: 'Backend offline',
                code: 'ECONNREFUSED',
                message: 'FastAPI backend service is offline.',
              })
            );
          }
          return;
        }
        console.warn(`[vite proxy error] ${req.url}:`, err.message);
      });
    },
  };
}

const apiRoutes = [
  '/meta',
  '/villages',
  '/sites',
  '/scenario',
  '/recommendation',
  '/observations',
  '/telemetry',
  '/agent',
  '/dpr',
  '/report',
  '/reports',
  '/pathways',
  '/participatory',
  '/aoi.geojson',
];

const proxyConfig = {};
for (const r of apiRoutes) {
  proxyConfig[r] = createProxy(BACKEND_URL);
}

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    ...(process.env.VITE_USE_MOCK !== 'true' ? { proxy: proxyConfig } : {}),
  },
});