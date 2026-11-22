#!/usr/bin/env bash
# ==============================================================================
# Retail Intelligence Control Center - Universal Fault-Tolerant Runner
# Handles: venv, dependencies, .env, docker, sql server readiness, auto-initialization,
# port conflicts, headless config, and graceful fallbacks.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

VENV_PATH="${SCRIPT_DIR}/.venv"
PORT="${PORT:-8501}"
HOST="${HOST:-0.0.0.0}"

echo "================================================================="
echo "   Retail Intelligence Control Center - Universal Launch Engine  "
echo "================================================================="

# Case 1: Ensure .env exists
if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    if [ -f "${SCRIPT_DIR}/.env.example" ]; then
        echo "[*] Creating .env from .env.example..."
        cp "${SCRIPT_DIR}/.env.example" "${SCRIPT_DIR}/.env"
    else
        echo "[!] Warning: No .env or .env.example found."
    fi
fi

# Case 2: Ensure Virtual Environment and Dependencies
if [ ! -d "${VENV_PATH}" ]; then
    echo "[!] Virtual environment not found at: ${VENV_PATH}"
    echo "[*] Initializing Python virtual environment..."
    python3 -m venv "${VENV_PATH}"
    "${VENV_PATH}/bin/pip" install --upgrade pip setuptools wheel
    "${VENV_PATH}/bin/pip" install -r "${SCRIPT_DIR}/requirements.txt"
fi

STREAMLIT_BIN="${VENV_PATH}/bin/streamlit"
PYTHON_BIN="${VENV_PATH}/bin/python"

if [ ! -f "${STREAMLIT_BIN}" ]; then
    echo "[!] Installing missing Streamlit and core dependencies..."
    "${VENV_PATH}/bin/pip" install -r "${SCRIPT_DIR}/requirements.txt"
fi

# Case 3: Docker and SQL Server Health Check & Auto-start
if command -v docker >/dev/null 2>&1; then
    if ! docker ps --filter "name=retail_intelligence_dw" --format '{{.Names}}' | grep -q "retail_intelligence_dw"; then
        echo "[*] SQL Server container not running. Starting via docker compose..."
        if command -v docker-compose >/dev/null 2>&1; then
            docker-compose up -d || true
        else
            docker compose up -d || true
        fi

        # Wait up to 30 seconds for SQL Server port 1433 to accept connections
        echo "[*] Waiting for SQL Server 2022 to accept connections on port 1433..."
        WAIT_SECONDS=0
        while [ "${WAIT_SECONDS}" -lt 30 ]; do
            if (nc -z localhost 1433 2>/dev/null || ss -tln | grep -q ":1433 "); then
                echo "[✓] SQL Server port 1433 is open and ready."
                break
            fi
            sleep 2
            WAIT_SECONDS=$((WAIT_SECONDS + 2))
        done
    else
        echo "[✓] SQL Server container is running."
    fi
else
    echo "[!] Note: Docker command not detected. Assuming external or native SQL Server."
fi

# Case 4: Verify Database Data & Auto-Initialize if Warehouse is Empty
if "${PYTHON_BIN}" -c "from src.db.connection import db_manager; db_manager.test_connection()" 2>/dev/null; then
    echo "[✓] SQL Server connection verified."
    # Check if FactSales has records
    HAS_DATA=$("${PYTHON_BIN}" -c "
from src.db.connection import db_manager
try:
    with db_manager.session_scope() as cur:
        cur.execute('SELECT COUNT(*) AS cnt FROM dw.FactSales')
        print(cur.fetchone()['cnt'])
except Exception:
    print('0')
" 2>/dev/null || echo "0")

    if [ "${HAS_DATA}" -eq 0 ]; then
        echo "[*] Warehouse has 0 facts. Running automated non-destructive initialization..."
        "${PYTHON_BIN}" -m src.cli setup || true
        if [ ! -d "${SCRIPT_DIR}/data/synthetic/small_seed42" ]; then
            "${PYTHON_BIN}" -m src.cli generate --mode small --seed 42 || true
        fi
        "${PYTHON_BIN}" -m src.cli etl --input "${SCRIPT_DIR}/data/synthetic/small_seed42" || true
        "${PYTHON_BIN}" -m src.cli analytics || true
        echo "[✓] Automated warehouse initialization complete."
    else
        echo "[✓] Warehouse verified with ${HAS_DATA} sales facts."
    fi
else
    echo "[!] Could not connect to SQL Server immediately. Dashboard will launch in fault-tolerant offline mode."
fi

# Case 5: Ensure Missing Analytics Artifacts are Generated
if [ ! -f "${SCRIPT_DIR}/reports/generated/analytics/forecast_future.csv" ]; then
    echo "[*] Analytics model artifacts missing. Attempting generation..."
    "${PYTHON_BIN}" -m src.cli analytics 2>/dev/null || true
fi

# Case 6: Streamlit Headless Configuration
mkdir -p "${HOME}/.streamlit"
cat <<EOF > "${HOME}/.streamlit/credentials.toml"
[general]
email = ""
EOF

# Case 7: Port Conflict Detection & Auto-Resolution
# Check if requested port is in use
check_port() {
    local p="$1"
    if command -v ss >/dev/null 2>&1; then
        ss -tln | grep -q ":${p} " && return 0 || return 1
    elif command -v netstat >/dev/null 2>&1; then
        netstat -tln | grep -q ":${p} " && return 0 || return 1
    elif command -v lsof >/dev/null 2>&1; then
        lsof -i ":${p}" >/dev/null 2>&1 && return 0 || return 1
    fi
    return 1
}

# If current port is already running our Streamlit instance, check if responding
if check_port "${PORT}"; then
    if curl -s -I "http://localhost:${PORT}" 2>/dev/null | grep -q "uvicorn\|Streamlit"; then
        echo "[✓] Dashboard is already active and serving on http://localhost:${PORT}"
        echo "    Open http://localhost:${PORT} in your browser."
        exit 0
    else
        echo "[!] Port ${PORT} is occupied by another service. Finding next available port..."
        while check_port "${PORT}"; do
            PORT=$((PORT + 1))
        done
        echo "[✓] Selected alternative open port: ${PORT}"
    fi
fi

echo "================================================================="
echo "[✓] Starting Streamlit dashboard on http://${HOST}:${PORT}"
echo "    Local URL: http://localhost:${PORT}"
echo "================================================================="

exec "${STREAMLIT_BIN}" run "${SCRIPT_DIR}/dashboard/app.py" \
    --server.port="${PORT}" \
    --server.address="${HOST}" \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    "$@"
