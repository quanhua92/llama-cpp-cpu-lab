#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODEL_DIR="$SCRIPT_DIR/models"
REPO_DIR="$SCRIPT_DIR/repo"
SERVER="$REPO_DIR/build/bin/llama-server"

declare -A MODELS
MODELS["smollm3-3b"]="ggml-org/SmolLM3-3B-GGUF|SmolLM3-Q4_K_M.gguf|SmolLM3 3B (Q4_K_M) — best small model 2025"
MODELS["qwen2.5-0.5b"]="Qwen/Qwen2.5-0.5B-Instruct-GGUF|qwen2.5-0.5b-instruct-q4_k_m.gguf|Qwen2.5 0.5B (Q4_K_M)"
MODELS["qwen2.5-1.5b"]="Qwen/Qwen2.5-1.5B-Instruct-GGUF|qwen2.5-1.5b-instruct-q4_k_m.gguf|Qwen2.5 1.5B (Q4_K_M)"
MODELS["qwen2.5-3b"]="Qwen/Qwen2.5-3B-Instruct-GGUF|qwen2.5-3b-instruct-q4_k_m.gguf|Qwen2.5 3B (Q4_K_M)"
MODELS["qwen2.5-coder-1.5b"]="Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF|qwen2.5-coder-1.5b-instruct-q4_k_m.gguf|Qwen2.5 Coder 1.5B (Q4_K_M)"
MODELS["llama3.2-1b"]="hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF|llama-3.2-1b-instruct-q4_k_m.gguf|Llama 3.2 1B (Q4_K_M)"
MODELS["llama3.2-3b"]="hugging-quants/Llama-3.2-3B-Instruct-Q4_K_M-GGUF|llama-3.2-3b-instruct-q4_k_m.gguf|Llama 3.2 3B (Q4_K_M)"
MODELS["gemma4-e2b"]="unsloth/gemma-4-E2B-it-GGUF|gemma-4-E2B-it-Q4_K_M.gguf|Gemma 4 E2B (Q4_K_M, 5B total, 2.3B active) — MoE, multimodal, 128K ctx"
MODELS["gemma4-e4b"]="unsloth/gemma-4-E4B-it-GGUF|gemma-4-E4B-it-Q4_K_M.gguf|Gemma 4 E4B (Q4_K_M, 8B total, 4.5B active) — MoE, multimodal, 128K ctx"
MODELS["qwen3.5-0.8b"]="unsloth/Qwen3.5-0.8B-GGUF|Qwen3.5-0.8B-Q4_K_M.gguf|Qwen3.5 0.8B (Q4_K_M)"
MODELS["qwen3.5-2b"]="unsloth/Qwen3.5-2B-GGUF|Qwen3.5-2B-Q4_K_M.gguf|Qwen3.5 2B (Q4_K_M)"
MODELS["qwen3.5-4b"]="unsloth/Qwen3.5-4B-GGUF|Qwen3.5-4B-Q4_K_M.gguf|Qwen3.5 4B (Q4_K_M)"
MODELS["gemma2-2b"]="bartowski/gemma-2-2b-it-GGUF|gemma-2-2b-it-Q4_K_M.gguf|Gemma 2 2B IT (Q4_K_M) — Dense, no MoE"
MODELS["deepseek-r1-1.5b"]="unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF|DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf|DeepSeek-R1-Distill-Qwen-1.5B (Q4_K_M) — RL-reasoning distilled"
MODELS["phi4-mini"]="unsloth/Phi-4-mini-instruct-GGUF|Phi-4-mini-instruct-Q4_K_M.gguf|Phi-4 Mini 3.8B (Q4_K_M) — Microsoft instruction-tuned"
MODELS["gemma4-qat-e2b"]="google/gemma-4-E2B-it-qat-q4_0-gguf|gemma-4-E2B_q4_0-it.gguf|gemma-4-E2B-it-qat-q4_0.gguf|Gemma 4 E2B QAT (Q4_0, 5B total, 2.3B active) — MoE, QAT quantized"
MODELS["gemma4-qat-e4b"]="google/gemma-4-E4B-it-qat-q4_0-gguf|gemma-4-E4B_q4_0-it.gguf|gemma-4-E4B-it-qat-q4_0.gguf|Gemma 4 E4B QAT (Q4_0, 8B total, 4.5B active) — MoE, QAT quantized"
MODELS["gemma4-qat-12b"]="google/gemma-4-12B-it-qat-q4_0-gguf|gemma-4-12b-it-qat-q4_0.gguf|gemma-4-12b-it-qat-q4_0.gguf|Gemma 4 12B QAT (Q4_0, Dense) — QAT quantized"
MODELS["gemma4-qat-26b"]="google/gemma-4-26B-A4B-it-qat-q4_0-gguf|gemma-4-26B_q4_0-it.gguf|gemma-4-26B-A4B-it-qat-q4_0.gguf|Gemma 4 26B-A4B QAT (Q4_0, 27B total, ~4B active) — MoE, QAT quantized"
MODELS["gemma4-qat-31b"]="google/gemma-4-31B-it-qat-q4_0-gguf|gemma-4-31B_q4_0-it.gguf|gemma-4-31B-it-qat-q4_0.gguf|Gemma 4 31B QAT (Q4_0, Dense, 33B) — QAT quantized"

usage() {
    echo "Usage: $0 [model] [port] [--no-reasoning] [--chat-template <name>] [--chat-template-file <path>] [extra flags...]"
    echo ""
    echo "Available models:"
    for key in "${!MODELS[@]}"; do
        IFS='|' read -r _ _ desc <<< "${MODELS[$key]}"
        printf "  %-20s %s\n" "$key" "$desc"
    done
    echo ""
    echo "Examples:"
    echo "  $0                                               # default gemma4-qat-26b :8080"
    echo "  $0 llama3.2-1b                                   # llama on 8080"
    echo "  $0 qwen2.5-1.5b 8081                             # qwen on 8081"
    echo "  $0 gemma4-e2b --chat-template gemma              # force gemma template"
    echo "  $0 qwen3.5-0.8b 8081 --chat-template chatml      # use chatml template"
    echo "  $0 qwen3.5-0.8b --jinja --chat-template-file ./path/to/template.jinja  # custom Jinja template"
    echo ""
    echo "Flags:"
    echo "  --no-reasoning     Disable thinking (chain-of-thought) for speed"
    exit 0
}

# Parse: model, optional port, then extra flags for llama-server
MODEL_KEY="${1:-gemma4-qat-26b}"
if [ "$MODEL_KEY" = "--help" ] || [ "$MODEL_KEY" = "-h" ]; then usage; fi
shift 2>/dev/null || true

if [ -z "${MODELS[$MODEL_KEY]:-}" ]; then
    echo "Unknown model: $MODEL_KEY"
    usage
fi

# Next arg: either a port number or a flag
if [[ "${1:-}" =~ ^[0-9]+$ ]]; then
    PORT="$1"
    shift
else
    PORT=8080
fi

EXTRA_ARGS=("$@")

# Handle --no-reasoning → --reasoning off
FILTERED_ARGS=()
for arg in "${EXTRA_ARGS[@]}"; do
    if [ "$arg" = "--no-reasoning" ]; then
        FILTERED_ARGS+=("--reasoning" "off")
    else
        FILTERED_ARGS+=("$arg")
    fi
done
EXTRA_ARGS=("${FILTERED_ARGS[@]}")

PIDFILE="$SCRIPT_DIR/run/server.${PORT}.pid"
LOG="$SCRIPT_DIR/run/server.${PORT}.log"

ENTRY="${MODELS[$MODEL_KEY]}"
PIPE_COUNT=$(echo "$ENTRY" | tr -cd '|' | wc -c)
if [ "$PIPE_COUNT" -ge 3 ]; then
    IFS='|' read -r HF_REPO REMOTE_FILE LOCAL_FILE DISPLAY <<< "$ENTRY"
else
    IFS='|' read -r HF_REPO GGUF_FILE DISPLAY <<< "$ENTRY"
    REMOTE_FILE="$GGUF_FILE"
    LOCAL_FILE="$GGUF_FILE"
fi
MODEL_URL="https://huggingface.co/$HF_REPO/resolve/main/$REMOTE_FILE"
MODEL_PATH="$MODEL_DIR/$LOCAL_FILE"

mkdir -p "$MODEL_DIR"

if [ ! -f "$MODEL_PATH" ]; then
    echo "Downloading $DISPLAY..."
    wget -O "$MODEL_PATH" "$MODEL_URL"
fi

if [ -f "$PIDFILE" ]; then
    OLD_PID=$(cat "$PIDFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Killing existing server on port $PORT (PID $OLD_PID)..."
        kill "$OLD_PID"
        sleep 1
    fi
    rm -f "$PIDFILE"
fi

if [ -f "$LOG" ] && [ -s "$LOG" ]; then
    mv "$LOG" "${LOG}.$(date +%Y%m%d_%H%M%S)"
fi

echo "Starting $DISPLAY on http://0.0.0.0:$PORT (PID -> $PIDFILE)"
echo "Extra args: ${EXTRA_ARGS[*]:-(none)}"
nohup "$SERVER" \
    -m "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port "$PORT" \
    -c 8192 \
    --flash-attn auto \
    -t 8 \
    -ngl 99 \
    "${EXTRA_ARGS[@]}" \
    > "$LOG" 2>&1 &

PID=$!
echo "$PID" > "$PIDFILE"
echo "Started (PID $PID). Log: $LOG"
