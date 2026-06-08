#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

MODEL_KEY="${1:-gemma4-qat-26b-a4b}"
PORT=8100
CORPUS="$SCRIPT_DIR/tuning/corpus.txt"
SHORT_Q="What is 2+2? Answer in one sentence."
LONG_Q="Summarize the key themes and writing style in the text above in 3-5 sentences."

NGL_VALUES=(99 60 40 20)
CTX_VALUES=(8192 32768 65536)
T_VALUES=(8 16 24)
SPEC_VALUES=("none" "ngram-simple")
CTX_FILL=0.80
KV_QUANT_VALUES=("q8")

if [ ! -f "$CORPUS" ]; then
    echo "ERROR: Corpus not found at $CORPUS"
    echo "Download one: wget -O tuning/corpus.txt https://www.gutenberg.org/files/1661/1661-0.txt"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_DIR="$SCRIPT_DIR/tuning/gpu/$MODEL_KEY/$TIMESTAMP"
mkdir -p "$RUN_DIR"

SWEEP_LOG="$RUN_DIR/sweep.log"
SUMMARY="$RUN_DIR/summary.md"

cleanup() {
    ./stop.sh "$PORT" 2>/dev/null || true
}

log() {
    echo "$@" | tee -a "$SWEEP_LOG"
}

cleanup

echo "=== GPU Config Sweep (2-phase) ==="
log "$(date): Starting sweep"
log "Model: $MODEL_KEY"
log "ngl: ${NGL_VALUES[*]}"
log "ctx: ${CTX_VALUES[*]}"
log "threads: ${T_VALUES[*]}"
log "spec: ${SPEC_VALUES[*]}"
log "Short Q: $SHORT_Q"
log "Long Q: $LONG_Q"
log "Corpus: $CORPUS ($(wc -c < "$CORPUS") bytes)"
log "Ctx fill ratio: $CTX_FILL"
log "Results: $RUN_DIR"
log ""

TOTAL_PHASE1=$(( ${#T_VALUES[@]} * ${#SPEC_VALUES[@]} ))
TOTAL_PHASE2=$(( ${#NGL_VALUES[@]} * ${#CTX_VALUES[@]} * ${#KV_QUANT_VALUES[@]} ))
TOTAL=$((TOTAL_PHASE1 + TOTAL_PHASE2))
RUN=0
SKIPS=0
FAILS=0

check_gpu_free() {
    [ -z "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -v "^$" || true)" ]
}

wait_gpu_free() {
    for attempt in 1 2 3 4 5; do
        sleep 3
        if check_gpu_free; then
            return 0
        fi
    done
    return 1
}

start_server() {
    local ngl="$1" ctx="$2" threads="$3" spec="$4" kv_quant="${5:-none}"
    cleanup
    for attempt in 1 2 3 4 5; do
        sleep 3
        if check_gpu_free; then
            break
        fi
    done
    if ! check_gpu_free; then
        return 1
    fi

    local spec_args=""
    if [ "$spec" != "none" ]; then
        spec_args="--spec-type $spec"
    fi

    local kv_args=""
    if [ "$kv_quant" != "none" ]; then
        kv_args="-ctk ${kv_quant}_0 -ctv ${kv_quant}_0"
    fi

    nohup ./serve_gpu.sh "$MODEL_KEY" "$PORT" --ngl "$ngl" -c "$ctx" -t "$threads" $spec_args $kv_args > "$RUN_DIR/serve.log" 2>&1 &
    SERVE_PID=$!

    for i in $(seq 1 30); do
        if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
            return 0
        fi
        if ! kill -0 "$SERVE_PID" 2>/dev/null; then
            return 2
        fi
        sleep 2
    done
    return 3
}

check_server_error() {
    if grep -qi "out of memory\|oom\|cuda\|cannot allocate\|failed to allocate" "$RUN_DIR/serve.log" 2>/dev/null; then
        echo "OOM"
        return 0
    fi
    echo "CRASH"
    return 1
}

run_ask() {
    local question="$1"
    local output_file="$2"
    local prompt_file="${3:-}"
    if [ -n "$prompt_file" ]; then
        uv run python scripts/ask.py --port "$PORT" --max-tokens 512 --prompt-file "$prompt_file" > "$output_file" 2>&1
    else
        uv run python scripts/ask.py --port "$PORT" --max-tokens 512 "$question" > "$output_file" 2>&1
    fi
}

post_health_sleep() {
    local ctx="$1"
    if [ "$ctx" -ge 32768 ]; then
        sleep 5
    elif [ "$ctx" -ge 16384 ]; then
        sleep 3
    else
        sleep 2
    fi
}

has_connection_error() {
    local file="$1"
    grep -qi "connection attempts failed\|connection refused\|timed out\|argument list too long" "$file" 2>/dev/null
}

extract_timing() {
    local file="$1"
    local line
    line=$(grep "TTFT:" "$file" 2>/dev/null || true)
    if [ -z "$line" ]; then
        echo "-"
        echo "-"
        return 1
    fi
    echo "$line" | grep -oP 'TTFT:\s*\K[0-9]+'
    echo "$line" | grep -oP '[0-9.]+\s*tok/s' | grep -oP '[0-9.]+'
    return 0
}

build_long_prompt() {
    local target_ctx="$1"
    local question="$2"
    local target_tokens=$(( $(echo "$target_ctx * $CTX_FILL" | bc -l | cut -d. -f1) ))
    local corpus_chars
    corpus_chars=$(wc -c < "$CORPUS")
    local chars_per_token=$(( corpus_chars / 150000 ))
    [ "$chars_per_token" -lt 1 ] && chars_per_token=4
    local char_limit=$(( target_tokens * chars_per_token ))

    python3 -c "
text = open('$CORPUS').read()
print(text[:$char_limit])
print()
print('$question')
" > "$RUN_DIR/prompt_draft.txt"
}

echo "# GPU Config Sweep: $MODEL_KEY" > "$SUMMARY"
echo "" >> "$SUMMARY"

log ""
log "========== PHASE 1: SPEED TUNING (threads x spec) =========="
log "ngl=99, ctx=8192, short prompt. Find best threads + speculative decoding."
log ""

echo "## Phase 1: Speed Tuning" >> "$SUMMARY"
echo "Config: ngl=99, ctx=8192, short prompt: \`$SHORT_Q\`" >> "$SUMMARY"
echo "" >> "$SUMMARY"
echo "| threads | spec | TTFT (ms) | tok/s |" >> "$SUMMARY"
echo "|---------|------|-----------|-------|" >> "$SUMMARY"

BEST_T="8"
BEST_SPEC="none"
BEST_TPS=0

for THREADS in "${T_VALUES[@]}"; do
    for SPEC in "${SPEC_VALUES[@]}"; do
        RUN=$((RUN + 1))
        LABEL="p1_t${THREADS}_spec${SPEC}"
        echo -n "[$RUN/$TOTAL] $LABEL ... "

        rc=0
        start_server 99 8192 "$THREADS" "$SPEC" || rc=$?

        if [ "$rc" -eq 1 ]; then
            echo "ABORT (GPU occupied)"
            log "ABORT: GPU occupied by external process"
            exit 1
        elif [ "$rc" -ne 0 ]; then
            echo "SKIP (server failed)"
            log "SKIP $LABEL: server failed"
            echo "| $THREADS | $SPEC | - | - |" >> "$SUMMARY"
            FAILS=$((FAILS + 1))
            continue
        fi

        sleep 2
        OUTPUT="$RUN_DIR/${LABEL}.txt"
        if run_ask "$SHORT_Q" "$OUTPUT"; then
            if has_connection_error "$OUTPUT"; then
                echo "SKIP (connection error)"
                log "SKIP $LABEL: connection error"
                echo "| $THREADS | $SPEC | - | - |" >> "$SUMMARY"
                SKIPS=$((SKIPS + 1))
            else
                TTFT_TOKS=$(extract_timing "$OUTPUT")
                TTFT=$(echo "$TTFT_TOKS" | sed -n '1p')
                TPS=$(echo "$TTFT_TOKS" | sed -n '2p')
                if [ "$TTFT" = "-" ]; then
                    echo "SKIP (no timing)"
                    log "SKIP $LABEL: no timing"
                    echo "| $THREADS | $SPEC | - | - |" >> "$SUMMARY"
                    SKIPS=$((SKIPS + 1))
                else
                    echo "TTFT: ${TTFT}ms | ${TPS} tok/s"
                    log "OK $LABEL: TTFT=${TTFT}ms tok/s=${TPS}"
                    echo "| $THREADS | $SPEC | $TTFT | $TPS |" >> "$SUMMARY"
                    if [ "$TPS" != "-" ] && python3 -c "exit(0 if float('$TPS') > float('$BEST_TPS') else 1)" 2>/dev/null; then
                        BEST_TPS="$TPS"
                        BEST_T="$THREADS"
                        BEST_SPEC="$SPEC"
                    fi
                fi
            fi
        else
            echo "SKIP (ask.py failed)"
            log "SKIP $LABEL: ask.py failed"
            echo "| $THREADS | $SPEC | - | - |" >> "$SUMMARY"
            SKIPS=$((SKIPS + 1))
        fi
    done
done

log ""
log "Best speed: t=$BEST_T spec=$BEST_SPEC (${BEST_TPS} tok/s)"

log ""
log "========== PHASE 2: CONTEXT + GPU OFFLOAD + KV QUANT SCALING (long prompts) =========="
log "threads=$BEST_T, spec=$BEST_SPEC. Sweep ngl x ctx x kv_quant with long prompts."
log ""

echo "" >> "$SUMMARY"
echo "## Phase 2: Context + GPU Offload + KV Quant Scaling (Long Prompts)" >> "$SUMMARY"
echo "Config: threads=$BEST_T, spec=$BEST_SPEC" >> "$SUMMARY"
echo "Long prompt: corpus (80% fill) + \`$LONG_Q\`" >> "$SUMMARY"
echo "" >> "$SUMMARY"
echo "| ngl | ctx | kv | est tokens | TTFT (ms) | tok/s | status |" >> "$SUMMARY"
echo "|-----|-----|----|------------|-----------|-------|--------|" >> "$SUMMARY"

FIT_MAP=()

for NGL in "${NGL_VALUES[@]}"; do
    for CTX in "${CTX_VALUES[@]}"; do
        for KV in "${KV_QUANT_VALUES[@]}"; do
            RUN=$((RUN + 1))
            LABEL="p2_ngl${NGL}_ctx${CTX}_kv${KV}"
            echo -n "[$RUN/$TOTAL] $LABEL ... "

            rc=0
            start_server "$NGL" "$CTX" "$BEST_T" "$BEST_SPEC" "$KV" || rc=$?

            if [ "$rc" -eq 1 ]; then
                echo "ABORT (GPU occupied)"
                log "ABORT: GPU occupied by external process"
                exit 1
            elif [ "$rc" -ne 0 ]; then
                ERR=$(check_server_error; echo $?)
                if [ "$ERR" = "0" ]; then
                    echo "OOM"
                    log "OOM $LABEL"
                    echo "| $NGL | $CTX | $KV | - | - | - | OOM |" >> "$SUMMARY"
                else
                    echo "CRASH"
                    log "CRASH $LABEL"
                    echo "| $NGL | $CTX | $KV | - | - | - | CRASH |" >> "$SUMMARY"
                fi
                FAILS=$((FAILS + 1))
                continue
            fi

            post_health_sleep "$CTX"

            PROMPT_FILE="$RUN_DIR/${LABEL}_prompt.txt"
            build_long_prompt "$CTX" "$LONG_Q"
            cp "$RUN_DIR/prompt_draft.txt" "$PROMPT_FILE"
            PROMPT_CHARS=$(wc -c < "$PROMPT_FILE")
            EST_TOKENS=$(( PROMPT_CHARS / 4 ))

            OUTPUT="$RUN_DIR/${LABEL}.txt"
            if run_ask "" "$OUTPUT" "$PROMPT_FILE"; then
                if has_connection_error "$OUTPUT"; then
                    echo "FAIL (connection error)"
                    log "FAIL $LABEL: connection error"
                    echo "| $NGL | $CTX | $KV | ~$EST_TOKENS | - | - | CONN_FAIL |" >> "$SUMMARY"
                    SKIPS=$((SKIPS + 1))
                else
                    TTFT_TOKS=$(extract_timing "$OUTPUT")
                    TTFT=$(echo "$TTFT_TOKS" | sed -n '1p')
                    TPS=$(echo "$TTFT_TOKS" | sed -n '2p')
                    if [ "$TTFT" = "-" ]; then
                        echo "FAIL (no timing)"
                        log "FAIL $LABEL: no timing"
                        echo "| $NGL | $CTX | $KV | ~$EST_TOKENS | - | - | NO_TIMING |" >> "$SUMMARY"
                        SKIPS=$((SKIPS + 1))
                    else
                        echo "TTFT: ${TTFT}ms | ${TPS} tok/s (prompt: ${PROMPT_CHARS} chars)"
                        log "OK $LABEL: TTFT=${TTFT}ms tok/s=${TPS} prompt=${PROMPT_CHARS}chars"
                        echo "| $NGL | $CTX | $KV | ~$EST_TOKENS | $TTFT | $TPS | FIT |" >> "$SUMMARY"
                        FIT_MAP+=("$NGL:$CTX:$KV")
                    fi
                fi
            else
                echo "FAIL (ask.py failed)"
                log "FAIL $LABEL: ask.py failed"
                echo "| $NGL | $CTX | $KV | ~$EST_TOKENS | - | - | ASK_FAIL |" >> "$SUMMARY"
                SKIPS=$((SKIPS + 1))
            fi
        done
    done
done

SUCCESS=$((TOTAL - SKIPS - FAILS))

log ""
log "$(date): Sweep complete"
log "Results: $RUN_DIR"
log "Total: $TOTAL | Success: $SUCCESS | Skipped: $SKIPS | Failed: $FAILS"
log ""
log "FIT combos (ngl:ctx:kv): ${FIT_MAP[*]}"
log ""
log "RECOMMENDATION (highest ngl per ctx that fits):"
for CTX in "${CTX_VALUES[@]}"; do
    best_ngl=""
    best_kv="none"
    for combo in "${FIT_MAP[@]}"; do
        ctx_part="${combo#*:}"
        ctx_only="${ctx_part%%:*}"
        kv_only="${ctx_part#*:}"
        ngl="${combo%%:*}"
        if [ "$ctx_only" = "$CTX" ]; then
            if [ -z "$best_ngl" ] || [ "$ngl" -gt "$best_ngl" ]; then
                best_ngl="$ngl"
                best_kv="$kv_only"
            fi
        fi
    done
    if [ -n "$best_ngl" ]; then
        log "  ctx=$CTX → ngl=$best_ngl, kv=$best_kv, threads=$BEST_T, spec=$BEST_SPEC"
    else
        log "  ctx=$CTX → no ngl fits with long prompt"
    fi
done

echo ""
echo "=== Done ==="
echo "Results: $RUN_DIR"
echo "Log: $SWEEP_LOG"
echo ""
cat "$SUMMARY"

cleanup
