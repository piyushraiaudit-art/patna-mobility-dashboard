#!/usr/bin/env bash
# Launch the Patna Mobility Congestion Index dashboard.
#
# Usage:
#   ./run_dashboard.sh                  # opens at http://localhost:8501
#
# The script auto-detects the venv created by setup.sh; if that venv does
# not exist, it falls back to the system python3 (assumes deps are pip-installed).

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [[ -x "venv/bin/streamlit" ]]; then
    PY=venv/bin/python
    STREAMLIT=venv/bin/streamlit
elif command -v streamlit >/dev/null 2>&1; then
    PY=python3
    STREAMLIT=streamlit
else
    echo "ERROR: streamlit not found. Run setup.sh first, or:" >&2
    echo "  pip install -r requirements.txt" >&2
    exit 1
fi

echo "Launching Patna Congestion Index dashboard …"
echo "Opens at http://localhost:8501 (Ctrl+C to stop)."
exec "$STREAMLIT" run dashboard/app.py \
    --browser.gatherUsageStats false \
    --server.headless false
