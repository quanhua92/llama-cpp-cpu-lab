#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
RESULTS_DIR="$SCRIPT_DIR/results/gpu"
mkdir -p "$RESULTS_DIR"

# Parse flags
NO_REASONING=false
while [[ "${1:-}" == --* ]]; do
    case "$1" in
        --no-reasoning) NO_REASONING=true; shift ;;
        --ngl) N_GL="$2"; shift 2 ;;
        *) echo "Unknown flag: $1"; exit 1 ;;
    esac
done

SUFFIX="_think"
SERVE_EXTRA=()
CLIENT_EXTRA=("--reasoning")
if [ "$NO_REASONING" = true ]; then
    SUFFIX="_nothink"
    SERVE_EXTRA+=("--no-reasoning")
    CLIENT_EXTRA=()
fi
if [ "${N_GL:-}" != "" ]; then
    SERVE_EXTRA+=("--ngl" "$N_GL")
fi

declare -a ALL_KEYS=(
    "smollm3-3b"
    "qwen2.5-0.5b"
    "qwen2.5-1.5b"
    "qwen2.5-3b"
    "qwen2.5-coder-1.5b"
    "llama3.2-1b"
    "llama3.2-3b"
    "gemma4-e2b"
    "gemma4-e4b"
    "qwen3.5-0.8b"
    "qwen3.5-2b"
    "qwen3.5-4b"
    "gemma2-2b"
    "deepseek-r1-1.5b"
    "phi4-mini"
    "gemma4-qat-e2b"
    "gemma4-qat-e4b"
    "gemma4-qat-12b"
    "gemma4-qat-26b-a4b"
    "gemma4-qat-31b"
    "qwen3.6-35b-a3b"
    "qwen3.6-27b"
)

if [ $# -gt 0 ]; then
    MODEL_KEYS=("$@")
    for key in "${MODEL_KEYS[@]}"; do
        found=0
        for k in "${ALL_KEYS[@]}"; do
            [ "$k" = "$key" ] && found=1 && break
        done
        if [ "$found" -eq 0 ]; then
            echo "Unknown model: $key"
            echo "Available: ${ALL_KEYS[*]}"
            exit 1
        fi
    done
else
    MODEL_KEYS=("${ALL_KEYS[@]}")
fi

pick_port() {
    local attempt=0
    while [ $attempt -lt 5 ]; do
        local port=$(( 12345 + RANDOM % 1000 ))
        if [ ! -f "$SCRIPT_DIR/run/server.${port}.pid" ]; then
            echo "  Picked port: $port" >&2
            echo "$port"
            return
        fi
        echo "  Port $port in use, retrying... ($((attempt+1))/5)" >&2
        attempt=$((attempt + 1))
        sleep 5
    done
    echo "ERROR: Could not find a free port after 5 attempts" >&2
    exit 1
}

for key in "${MODEL_KEYS[@]}"; do
    PORT=$(pick_port)
    LOG="$SCRIPT_DIR/run/server.${PORT}.log"

    echo ""
    echo "============================================"
    echo "  Benchmarking: $key (port $PORT)"
    echo "============================================"

    # Kill any leftover from a previous interrupted run on this port
    ./stop.sh "$PORT" 2>/dev/null || true
    sleep 1
    > "$LOG"  # clear log

    # Start server
    echo "  -> Starting server..."
    ./serve_gpu.sh "$key" "$PORT" "${SERVE_EXTRA[@]}"
    sleep 2

    # Wait for server HTTP endpoint
    echo "  -> Waiting for server to be ready..."
    for i in $(seq 1 120); do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/v1/models" 2>/dev/null | grep -q 200; then
            echo "  -> Server ready (${i}s)"
            sleep 2
            break
        fi
        sleep 1
    done

    # Run profile
    echo "  -> Running profile..."
    output_file="$RESULTS_DIR/${key}${SUFFIX}.txt"
    uv run --active python scripts/profile_client.py --port "$PORT" "${CLIENT_EXTRA[@]}" --output "$output_file" 2>&1 | tee "$output_file"

    # Cleanup this server
    ./stop.sh "$PORT" 2>/dev/null || true
    sleep 1
done

echo ""
echo "All benchmarks done. Results in $RESULTS_DIR"
echo "Mode: ${SUFFIX#_} (thinking=${NO_REASONING})"

# Validate: check for failures
echo ""
echo "================ VALIDATION ================"
ALL_OK=true
for f in "$RESULTS_DIR"/*${SUFFIX}.txt; do
    [ -f "$f" ] || continue
    total=$(grep -c "\[Q" "$f" 2>/dev/null || echo 0)
    fails=$(grep -c "Failed\." "$f" 2>/dev/null || echo 0)
    if [ "$total" -gt 0 ] && [ "$fails" -gt 0 ]; then
        echo "  FAIL: $(basename "$f") — $fails/$total questions failed"
        ALL_OK=false
    fi
done
if [ "$ALL_OK" = true ]; then
    echo "  All results OK — no failures detected."
else
    echo "  WARNING: Some results have failures. Check logs above."
fi
