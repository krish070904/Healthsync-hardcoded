import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('Starting MCP Server...');

// Start the server process
const serverProcess = spawn('node', ['mcp-server-fixed.js'], {
  cwd: __dirname,
  stdio: 'inherit',
  detached: false
});

// Handle server process events
serverProcess.on('error', (err) => {
  console.error('Failed to start server process:', err);
});

console.log('MCP Server process started with PID:', serverProcess.pid);
console.log('Press Ctrl+C to stop the server');

// Keep the parent process running
process.on('SIGINT', () => {
  console.log('Stopping MCP Server...');
  serverProcess.kill();
  process.exit();
});