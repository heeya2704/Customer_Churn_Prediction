// Runs Python with the given arguments, preferring the project virtualenv
// (.venv) so npm scripts work without activating it first. Falls back to
// `python` on PATH when no virtualenv exists.
//   node scripts/py.mjs -m pytest
import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const venvPython =
  process.platform === 'win32'
    ? join(root, '.venv', 'Scripts', 'python.exe')
    : join(root, '.venv', 'bin', 'python')
const python = existsSync(venvPython) ? venvPython : 'python'

const child = spawn(python, process.argv.slice(2), { cwd: root, stdio: 'inherit' })

child.on('error', (err) => {
  console.error(`Failed to start "${python}": ${err.message}`)
  console.error('Run "npm run setup" to create the virtualenv and install dependencies.')
  process.exit(1)
})
child.on('exit', (code) => process.exit(code ?? 0))
