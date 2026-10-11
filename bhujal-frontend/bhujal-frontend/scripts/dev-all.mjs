import { spawn } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Locate project root containing backend/app.py
let currentDir = __dirname;
let rootDir = null;
for (let i = 0; i < 5; i++) {
  if (fs.existsSync(path.join(currentDir, 'backend', 'app.py'))) {
    rootDir = currentDir;
    break;
  }
  const parent = path.dirname(currentDir);
  if (parent === currentDir) break;
  currentDir = parent;
}

if (!rootDir) {
  rootDir = path.resolve(__dirname, '..', '..');
}

const frontendDir = path.resolve(__dirname, '..');

console.log('\x1b[36m%s\x1b[0m', '═══════════════════════════════════════════════════════════');
console.log('\x1b[36m%s\x1b[0m', '🌊  BHUJAL FULL-STACK DEV RUNNER (FastAPI + Vite)         ');
console.log('\x1b[36m%s\x1b[0m', '═══════════════════════════════════════════════════════════');
console.log(`📂 Project Root: ${rootDir}`);
console.log(`🌐 Frontend Dir: ${frontendDir}\n`);

const isWindows = process.platform === 'win32';

// 1. Start Python backend
console.log('\x1b[32m%s\x1b[0m', '🚀 [1/2] Starting Python FastAPI Backend on http://127.0.0.1:8000 ...');
const backend = spawn('python', ['-m', 'uvicorn', 'backend.app:app', '--reload', '--port', '8000'], {
  cwd: rootDir,
  stdio: 'inherit',
  shell: isWindows,
});

// 2. Start Vite frontend
console.log('\x1b[34m%s\x1b[0m', '⚡ [2/2] Starting Vite Frontend on http://localhost:5173 ...\n');
const frontend = spawn(isWindows ? 'npx.cmd' : 'npx', ['vite', '--host', '0.0.0.0'], {
  cwd: frontendDir,
  stdio: 'inherit',
  shell: isWindows,
});

const cleanup = () => {
  console.log('\n\x1b[33m%s\x1b[0m', '🛑 Shutting down Bhujal full-stack processes...');
  try {
    if (isWindows && backend.pid) {
      spawn('taskkill', ['/pid', backend.pid.toString(), '/f', '/t']);
    } else {
      backend.kill('SIGTERM');
    }
  } catch (e) {}

  try {
    if (isWindows && frontend.pid) {
      spawn('taskkill', ['/pid', frontend.pid.toString(), '/f', '/t']);
    } else {
      frontend.kill('SIGTERM');
    }
  } catch (e) {}

  process.exit(0);
};

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
