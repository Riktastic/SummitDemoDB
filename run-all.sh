#!/bin/bash
# Build a complete ERP CSV demo dataset from a real Odoo Docker instance.
# 
# Steps:
# 1. Ensures Docker is running.
# 2. Initializes Odoo with demo data (one-time).
# 3. Starts the Odoo web UI.
# 4. Generates extra realistic records via the Odoo API.
# 5. Exports all configured tables to csv_export/.
# 6. (Optional) Creates a GitHub release package with all export formats.
#
# Usage: ./run-all.sh [--create-release]

set -e

CREATE_RELEASE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --create-release)
            CREATE_RELEASE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--create-release]"
            echo "  --create-release    Create a GitHub release package after data generation"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to check if Docker is ready
test_docker_ready() {
    docker info > /dev/null 2>&1
    return $?
}

# --- Start Docker if needed ---
if ! test_docker_ready; then
    echo "Docker not running. Please start Docker and try again."
    exit 1
fi

echo "Docker ready."

# --- 1. Initialize Odoo database ---
echo ""
echo "[1/5] Initializing Odoo database..."
docker-compose -f "$PROJECT_ROOT/docker-compose.yml" up web --remove-orphans --force-recreate -d

WEB_CONTAINER="powerbiexample-web-1"
WEB_EXIT=$(docker wait "$WEB_CONTAINER")
echo "  init container finished with exit code $WEB_EXIT"

if [ "$WEB_EXIT" -ne 0 ]; then
    docker logs "$WEB_CONTAINER"
    echo "Odoo initialization failed (exit $WEB_EXIT)."
    exit 1
fi

# Configure Odoo API settings
export ODOO_URL="http://localhost:8069"
export ODOO_DB="odoo_demo"
export ODOO_USER="admin"
export ODOO_PASSWORD="admin"

# --- 2. Start the web UI ---
echo ""
echo "[2/5] Starting Odoo web UI..."
docker-compose -f "$PROJECT_ROOT/docker-compose.yml" up web-frontend -d

# Wait until the Odoo JSON-RPC endpoint is actually responding
HEALTH_URL="$ODOO_URL/jsonrpc"
MAX_WAIT=300
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    PAYLOAD='{"jsonrpc":"2.0","method":"call","params":{"service":"common","method":"version","args":[],"kwargs":{}},"id":1}'
    
    if curl -s -X POST -H "Content-Type: application/json" -d "$PAYLOAD" "$HEALTH_URL" > /dev/null 2>&1; then
        break
    fi
    
    sleep 5
    ELAPSED=$((ELAPSED + 5))
    echo "  waiting for Odoo API ($ELAPSED s)..."
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "Odoo web UI did not become ready within $MAX_WAIT seconds."
    exit 1
fi

# --- 3. Ensure Python virtual environment exists ---
echo ""
echo "[3/5] Preparing Python environment..."
VENV_PATH="$PROJECT_ROOT/.venv"

if [ ! -f "$VENV_PATH/bin/python" ]; then
    python3 -m venv "$VENV_PATH"
fi

"$VENV_PATH/bin/python" -m pip install -r "$PROJECT_ROOT/requirements.txt" > /dev/null 2>&1

# --- 4. Generate extra data ---
echo ""
echo "[4/5] Generating extra ERP data via Odoo API..."
# Default scale is tuned to finish quickly while still being visualization-rich.
export GEN_CUSTOMERS=${GEN_CUSTOMERS:-200}
export GEN_SUPPLIERS=${GEN_SUPPLIERS:-100}
export GEN_PRODUCTS=${GEN_PRODUCTS:-300}
export GEN_SALE_ORDERS=${GEN_SALE_ORDERS:-500}
export GEN_PURCHASE_ORDERS=${GEN_PURCHASE_ORDERS:-300}

"$VENV_PATH/bin/python" "$PROJECT_ROOT/generate_data.py"

# --- 5. Export to CSV ---
echo ""
echo "[5/5] Exporting database tables to CSV..."
docker-compose -f "$PROJECT_ROOT/docker-compose.yml" up exporter --remove-orphans --force-recreate -d

EXPORTER_CONTAINER="powerbiexample-exporter-1"
EXPORTER_EXIT=$(docker wait "$EXPORTER_CONTAINER")
echo "  exporter container finished with exit code $EXPORTER_EXIT"

if [ "$EXPORTER_EXIT" -ne 0 ]; then
    docker logs "$EXPORTER_CONTAINER"
    echo "CSV export failed (exit $EXPORTER_EXIT)."
    exit 1
fi

echo ""
echo "Done. CSV files are in $PROJECT_ROOT/csv_export/"
echo "Odoo web UI is running at http://localhost:8069 (admin / admin)"

# --- 6. Create GitHub release package (optional) ---
if [ "$CREATE_RELEASE" = true ]; then
    echo ""
    echo "[6/6] Creating GitHub release package..."
    bash "$PROJECT_ROOT/create_release.sh"
    if [ $? -ne 0 ]; then
        echo "Warning: Release package creation failed, but data generation completed successfully."
    fi
fi
