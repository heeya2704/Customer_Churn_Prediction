// One-time local setup: creates .venv (if missing), installs Python dev
// dependencies into it, and installs the frontend's npm packages.
import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const isWin = process.platform === 'win32'
const venvPython = isWin
  ? join(root, '.venv', 'Scripts', 'python.exe')
  : join(root, '.venv', 'bin', 'python')

function run(cmd, args, cwd = root) {
  console.log(`\n> ${cmd} ${args.join(' ')}`)
  // npm is a .cmd shim on Windows, which needs a shell to launch.
  const result = spawnSync(cmd, args, { cwd, stdio: 'inherit', shell: isWin && cmd === 'npm' })
  if (result.status !== 0) process.exit(result.status ?? 1)
}

if (!existsSync(venvPython)) {
  run(isWin ? 'python' : 'python3', ['-m', 'venv', '.venv'])
}
run(venvPython, ['-m', 'pip', 'install', '-r', 'requirements-dev.txt'])
run('npm', ['install'])
run('npm', ['install'], join(root, 'frontend'))

console.log('\nSetup complete. Start both servers with: npm run dev')
