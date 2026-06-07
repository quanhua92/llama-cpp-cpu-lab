#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
OUTPUT_DIR="$SCRIPT_DIR/examples/gpu"

NO_REASONING=false
SKIP_EXISTING=false
PROMPTS_FLAG=()
QUESTION_FLAG=()
    while [[ "${1:-}" == --* ]]; do
    case "$1" in
        --no-reasoning) NO_REASONING=true; shift ;;
        --skip-existing) SKIP_EXISTING=true; shift ;;
        --ngl) N_GL="$2"; shift 2 ;;
        --prompts) PROMPTS_FLAG=(--prompts "$2"); shift 2 ;;
        --question) QUESTION_FLAG=(--question "$2"); shift 2 ;;
        --name) NAME_FLAG=(--name "$2"); shift 2 ;;
        *) echo "Unknown flag: $1"; exit 1 ;;
    esac
done

SERVE_EXTRA=()
if [ "$NO_REASONING" = true ]; then
    SERVE_EXTRA+=("--no-reasoning")
fi
if [ "${N_GL:-}" != "" ]; then
    SERVE_EXTRA+=("--ngl" "$N_GL")
fi

PY_EXTRA=()
if [ "$SKIP_EXISTING" = true ]; then
    PY_EXTRA+=("--skip-existing")
fi

declare -a ALL_KEYS=(
    "qwen2.5-0.5b"
    "qwen3.5-0.8b"
    "llama3.2-1b"
    "llama3.2-3b"
    "qwen2.5-1.5b"
    "qwen2.5-coder-1.5b"
    "deepseek-r1-1.5b"
    "gemma2-2b"
    "qwen3.5-2b"
    "qwen2.5-3b"
    "smollm3-3b"
    "phi4-mini"
    "qwen3.5-4b"
    "gemma4-e2b"
    "gemma4-qat-e2b"
    "gemma4-e4b"
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
    echo ""
    echo "============================================"
    echo "  Examples: $key"
    echo "============================================"

    ALL_PROMPTS="${PROMPTS_FLAG[1]:-ask,reflect}"
    ALL_DONE=true
    for p in ${ALL_PROMPTS//,/ }; do
        [ ! -f "$OUTPUT_DIR/${key}_${p}.md" ] && ALL_DONE=false && break
    done
    if [ "$SKIP_EXISTING" = true ] && [ "$ALL_DONE" = true ]; then
        echo "  Skipping (all files exist)"
        continue
    fi

    PORT=$(pick_port)

    ./stop.sh "$PORT" 2>/dev/null || true
    sleep 1

    echo "  -> Starting server..."
    ./serve_gpu.sh "$key" "$PORT" "${SERVE_EXTRA[@]}"
    sleep 2

    echo "  -> Waiting for server to be ready..."
    for i in $(seq 1 120); do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/v1/models" 2>/dev/null | grep -q 200; then
            echo "  -> Server ready (${i}s)"
            sleep 2
            break
        fi
        sleep 1
    done

    echo "  -> Generating examples..."
    uv run --active python scripts/generate_examples.py \
        --port "$PORT" \
        --output-dir "$OUTPUT_DIR" \
        --model-key "$key" \
        "${PY_EXTRA[@]}" \
        "${PROMPTS_FLAG[@]}" \
        "${QUESTION_FLAG[@]}" \
        "${NAME_FLAG[@]}"

    ./stop.sh "$PORT" 2>/dev/null || true
    sleep 1
done

echo ""
echo "All examples done. Output in $OUTPUT_DIR"
echo "Mode: $(if [ "$NO_REASONING" = true ]; then echo nothink; else echo think; fi)"
