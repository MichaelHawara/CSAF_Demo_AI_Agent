#!/usr/bin/env bash
# One-command launcher for the Nozama demo (backend + frontend) on macOS and Linux.
# The Windows equivalent is run.ps1 / run.bat.
#
#   ./run.sh              set up if needed, then start both servers
#   ./run.sh --setup      only install/prepare, do not start anything
#   ./run.sh --kill       free ports 8000 and 5173 first (stops a stale backend/frontend)
#
# If the file is not executable yet:  chmod +x run.sh   (or run:  bash run.sh)
# Press Ctrl+C in this terminal to stop both servers.
# Needs: Python 3.10+, Node 18+ with npm, bash.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT/backend"
FRONT_DIR="$ROOT/frontend"
VENV_DIR="$BACKEND_DIR/.venv"
VENV_PY="$VENV_DIR/bin/python"
REQ_FILE="$BACKEND_DIR/requirements.txt"
REQ_STAMP="$VENV_DIR/.requirements.sha256"
ENV_FILE="$ROOT/.env"
ENV_EXAMPLE="$ROOT/.env.example"
BACKEND_PORT=8000
FRONTEND_PORT=5173

SETUP_ONLY=0
KILL_PORTS=0
for arg in "$@"; do
  case "$arg" in
    --setup) SETUP_ONLY=1 ;;
    --kill) KILL_PORTS=1 ;;
    -h|--help)
      sed -n '2,11p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

step() { printf '\033[36m==> %s\033[0m\n' "$1"; }
warn() { printf '\033[33mWARNING: %s\033[0m\n' "$1" >&2; }
die()  { printf '\033[31mERROR: %s\033[0m\n' "$1" >&2; exit 1; }

# --- Prerequisites ---------------------------------------------------------
find_python() {
  local candidate
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
      command -v "$candidate"
      return 0
    fi
  done
  return 1
}

command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1 ||
  die "Node.js / npm was not found. Install Node 18+ from https://nodejs.org (or: brew install node) and re-run."

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  else
    shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

# --- .env ------------------------------------------------------------------
if [[ ! -f "$ENV_FILE" && ! -f "$BACKEND_DIR/.env" && -f "$ENV_EXAMPLE" ]]; then
  step "Creating .env from .env.example (mock mode; add GEMINI_API_KEY to use Gemini)"
  cp "$ENV_EXAMPLE" "$ENV_FILE"
fi

# --- Python environment ----------------------------------------------------
# A .venv copied over from Windows has Scripts/ instead of bin/ and cannot run here.
if [[ -d "$VENV_DIR" && ! -x "$VENV_PY" ]]; then
  warn "backend/.venv was created on another operating system; recreating it."
  rm -rf "$VENV_DIR"
fi

if [[ ! -x "$VENV_PY" ]]; then
  step "Creating Python virtual environment (backend/.venv)"
  PYTHON="$(find_python)" || die "Python 3.10+ was not found. Install it from https://www.python.org (or: brew install python) and re-run."
  "$PYTHON" -m venv "$VENV_DIR" || die "Could not create the virtual environment."
fi

REQ_HASH="$(sha256_of "$REQ_FILE")"
INSTALLED_HASH=""
[[ -f "$REQ_STAMP" ]] && INSTALLED_HASH="$(tr -d '[:space:]' < "$REQ_STAMP")"
if [[ "$REQ_HASH" != "$INSTALLED_HASH" ]]; then
  step "Installing Python requirements"
  "$VENV_PY" -m pip install --disable-pip-version-check -r "$REQ_FILE" || die "pip install failed."
  printf '%s\n' "$REQ_HASH" > "$REQ_STAMP"
fi

# --- Frontend packages -----------------------------------------------------
# node_modules installed on Windows holds Windows-only native binaries (esbuild, rollup)
# and cannot run here, so reinstall it.
if [[ -d "$FRONT_DIR/node_modules/@esbuild" ]] && ls "$FRONT_DIR/node_modules/@esbuild" | grep -q '^win32'; then
  warn "frontend/node_modules was installed on Windows; reinstalling for this system."
  rm -rf "$FRONT_DIR/node_modules"
fi

if [[ ! -d "$FRONT_DIR/node_modules" ]]; then
  step "Installing frontend packages (npm install)"
  (cd "$FRONT_DIR" && npm install) || die "npm install failed."
fi

if [[ "$SETUP_ONLY" == 1 ]]; then
  step "Setup complete. Run ./run.sh to start the demo."
  exit 0
fi

# --- Ports -----------------------------------------------------------------
port_in_use() {
  "$VENV_PY" - "$1" <<'PY'
import socket, sys
try:
    socket.create_connection(("localhost", int(sys.argv[1])), timeout=1).close()
except OSError:
    sys.exit(1)
PY
}

free_port() {
  local port="$1" pids
  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      step "Stopping whatever is listening on port $port"
      # shellcheck disable=SC2086
      kill $pids 2>/dev/null || true
      sleep 1
    fi
  else
    warn "lsof is not installed, so port $port cannot be freed automatically."
  fi
}

if [[ "$KILL_PORTS" == 1 ]]; then
  free_port "$BACKEND_PORT"
  free_port "$FRONTEND_PORT"
fi

# --- Start servers ---------------------------------------------------------
PIDS=()

kill_tree() {
  local pid="$1" child
  for child in $(pgrep -P "$pid" 2>/dev/null || true); do
    kill_tree "$child"
  done
  kill "$pid" 2>/dev/null || true
}

cleanup() {
  trap - INT TERM EXIT
  if [[ ${#PIDS[@]} -gt 0 ]]; then
    echo
    step "Stopping the demo"
    for pid in "${PIDS[@]}"; do kill_tree "$pid"; done
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if port_in_use "$BACKEND_PORT"; then
  warn "Port $BACKEND_PORT is already in use - the backend may already be running (possibly old code). Skipping backend start. Use ./run.sh --kill to restart it."
else
  step "Starting backend on http://127.0.0.1:$BACKEND_PORT"
  (cd "$BACKEND_DIR" && exec "$VENV_PY" -m uvicorn app.main:app --reload --host 127.0.0.1 --port "$BACKEND_PORT") &
  PIDS+=($!)
fi

if port_in_use "$FRONTEND_PORT"; then
  warn "Port $FRONTEND_PORT is already in use - the frontend may already be running. Skipping frontend start. Use ./run.sh --kill to restart it."
else
  step "Starting frontend on http://localhost:$FRONTEND_PORT (browser opens automatically)"
  (cd "$FRONT_DIR" && exec npm run dev) &
  PIDS+=($!)
fi

echo
printf '\033[32mNozama demo is starting.\033[0m\n'
echo "  Shop:     http://localhost:$FRONTEND_PORT/"
echo "  Control:  http://localhost:$FRONTEND_PORT/control"
echo "  X-Ray:    http://localhost:$FRONTEND_PORT/xray"
echo "  API docs: http://127.0.0.1:$BACKEND_PORT/docs"
echo "Press Ctrl+C to stop."

if [[ ${#PIDS[@]} -gt 0 ]]; then
  wait
fi
