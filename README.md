# Local LLM Lab

LLM serving and benchmarking using [llama.cpp](https://github.com/ggml-org/llama.cpp). Supports both CPU and GPU backends.

**Machine (CPU):** Intel i7-10700 (8C/16T, 2.9–4.8 GHz) · 64 GB RAM · x86_64
**Machine (GPU):** Intel i9-13900K (24C/32T, 0.8–5.8 GHz) · 64 GB RAM · NVIDIA RTX 4060 Ti 16 GB (Ada, SM 8.9) · x86_64
**llama.cpp:** [`4da6370`](https://github.com/ggml-org/llama.cpp/commit/4da6370d43f55a3f5ad576c5a1528b6ba9c53258)

## Contents

- [Benchmark Reports](#benchmark-reports)
- [Quick Start](#quick-start)
- [Curated Models](#curated-models)
- [Why CPU-Only LLMs?](#why-cpu-only-llms)
- [Gemma 4 QAT vs Q4_K_M Comparison](#gemma-4-qat-vs-q4_k_m-comparison)
- [Multiple Servers](#multiple-servers)
- [Benchmarking](#benchmarking)
- [API](#api)
- [Running as a Linux Service](#running-as-a-linux-service)
- [Server Configuration](server-configuration)
- [Adding a New Model](#adding-a-new-model)
- [Custom Models Directory](#custom-models-directory)
- [Downloading Models](#downloading-models)
- [Notes](#notes)

## Benchmark Reports

- [CPU Report](reports/cpu.md)
- [GPU Report](reports/gpu.md)
- [Gemma 4 QAT vs Q4_K_M Comparison](reports/gemma4-qat-comparison.md)
- [Qwen 3.6 35B-A3B vs Gemma 4 26B-A4B Comparison](reports/qwen3.6-35b-a3b-vs-gemma4-26b-a4b.md)
- [Vietnamese Fluency & Quality Report](reports/vietnamese-fluency.md)
- [GPU Context Scaling Report](reports/context-scaling-gpu.md)

## Quick Start

```bash
# CPU server (default gemma4-qat-26b-a4b on port 8080)
./serve_cpu.sh

# GPU server (default gemma4-qat-26b-a4b on port 8080)
./serve_gpu.sh

# Or pick a model + port
./serve_cpu.sh qwen2.5-0.5b 8081
./serve_gpu.sh qwen2.5-0.5b 8081

# Partial GPU offload for large models (>16GB on 16GB VRAM)
./serve_gpu.sh qwen3.6-35b-a3b --ngl 40

# Disable thinking for speed
./serve_cpu.sh gemma4-e2b --no-reasoning

# Kill a server
./stop.sh
./stop.sh 8888
./stop.sh 8081

# Ask the LLM a question (streaming, shows [think] + [out])
uv run python scripts/ask.py "explain TCP vs UDP"
uv run python scripts/ask.py --max-tokens 256 "what is a closure"

# Reflection agent: generate → critique → revise
uv run python scripts/reflect.py "write a fibonacci function"
uv run python scripts/reflect.py --port 8081 "explain async programming"

# Profile latency (benchmark suite)
uv run python scripts/profile_client.py
uv run python scripts/profile_client.py --reasoning

# Profile context scaling (corpus-filled prompts at different ctx sizes)
uv run python scripts/profile_context.py --port 8889
uv run python scripts/profile_context.py --port 8889 --ctx-sizes 2048 8192 32768 65536

# Run full benchmark suite (CPU)
bash run_cpu_benchmarks.sh

# Run full benchmark suite (GPU)
bash run_gpu_benchmarks.sh

# Generate example outputs (CPU)
./generate_examples_cpu.sh                              # all models
./generate_examples_cpu.sh gemma4-qat-26b-a4b              # single model
./generate_examples_cpu.sh --prompts ask               # only ask prompt
./generate_examples_cpu.sh --prompts reflect            # only reflect prompt
./generate_examples_cpu.sh --question "your prompt"    # custom question → _custom.md
./generate_examples_cpu.sh --question "your prompt" --name recursion  # → _recursion.md
./generate_examples_cpu.sh --no-reasoning --skip-existing

# Large models (12B+) can take 10-20 min per prompt.
# Use nohup to avoid shell timeout:
nohup ./generate_examples_cpu.sh gemma4-qat-12b > /tmp/examples.log 2>&1 &
nohup ./generate_examples_cpu.sh gemma4-qat-26b-a4b > /tmp/examples.log 2>&1 &
nohup ./generate_examples_cpu.sh gemma4-qat-31b > /tmp/examples.log 2>&1 &

# Or run all models in background, check progress:
nohup ./generate_examples_cpu.sh > /tmp/examples.log 2>&1 &
tail -f /tmp/examples.log
ls examples/cpu/*.md | wc -l  # count completed files

# Generate example outputs (GPU)
./generate_examples_gpu.sh
```

## Files

| File | Purpose |
|------|---------|
| `serve_cpu.sh` | Start llama-server (CPU, `-ngl 0`) on any port with any curated model |
| `serve_gpu.sh` | Start llama-server (GPU, `-ngl 99`, KV8 cache, configurable via `--ngl N`) on any port with any curated model |
| `stop.sh` | Kill server by port (default 8080) |
| `scripts/ask.py` | Single streaming LLM call: shows `[think]` + `[out]` + timing |
| `scripts/reflect.py` | Reflection agent: generate → critique → revise (3-step loop) |
| `scripts/profile_client.py` | Streaming benchmark: 10 fixed questions, TTFT, server decode/prompt speed |
| `scripts/profile_context.py` | Context scaling benchmark: fills prompts with corpus text at different ctx sizes, measures TTFT + decode speed |
| `scripts/analyze_results.py` | Parse benchmark results: overview, per-question, comparison, stability |
| `scripts/generate_examples.py` | Generate example outputs per model with streaming capture |
| `generate_examples_cpu.sh` | Run generate_examples across all models (CPU) → `examples/cpu/` |
| `generate_examples_gpu.sh` | Run generate_examples across all models (GPU) → `examples/gpu/` |
| `examples/` | Per-model example outputs (`cpu/` and `gpu/`) |
| `run_cpu_benchmarks.sh` | Run profile across all models (CPU) → `results/cpu/` |
| `run_gpu_benchmarks.sh` | Run profile across all models (GPU) → `results/gpu/` |
| `add-model-flow.md` | Guide for adding new GGUF models |
| `reports/cpu.md` | CPU benchmark results and analysis |
| `reports/gpu.md` | GPU benchmark results and analysis |
| `reports/gemma4-qat-comparison.md` | Gemma 4 QAT Q4_0 vs Q4_K_M benchmark comparison |
| `reports/vietnamese-fluency.md` | Qualitative evaluation of Vietnamese fluency and failure modes |
| `systemd/llama-cpu.service` | User systemd service (CPU, port 8888) |
| `systemd/llama-gpu.service` | User systemd service (GPU, port 8889) |
| `repo/` | llama.cpp source + `build/bin/llama-server` |
| `sweep_gpu_config.sh` | Grid sweep: test `-ngl` x `-c` x `-t` x `--spec-type` combos, measure TTFT + tok/s → `tuning/gpu/` |
| `sweep-gpu.md` | Sweep tool documentation |
| `run/` | Server PID and log files (gitignored) |

## Curated Models

All Q4_K_M quant unless noted. Shared between CPU (`-ngl 0`, `-t 8`, `-c 8192`) and GPU (`-ngl 99`, `-c 8192`, `-ctk q8_0 -ctv q8_0`; use `--ngl N` for partial offload). QAT models use Q4_0 quantization (quantization-aware training):

| Key | Model | Size |
|-----|-------|------|
| `gemma4-e2b` | Gemma 4 E2B (Dense 2.3B) | 2.9 GB |
| `gemma4-e4b` | Gemma 4 E4B (Dense 4.5B) | 4.7 GB |
| `qwen2.5-0.5b` | Qwen2.5 0.5B | 469 MB |
| `qwen2.5-1.5b` | Qwen2.5 1.5B | 1.1 GB |
| `qwen2.5-3b` | Qwen2.5 3B | 2.0 GB |
| `qwen2.5-coder-1.5b` | Qwen2.5 Coder 1.5B | 1.1 GB |
| `llama3.2-1b` | Llama 3.2 1B | 771 MB |
| `llama3.2-3b` | Llama 3.2 3B | 1.9 GB |
| `smollm3-3b` | SmolLM3 3B | 1.8 GB |
| `qwen3.5-0.8b` | Qwen3.5 0.8B | 533 MB |
| `qwen3.5-2b` | Qwen3.5 2B | 1.3 GB |
| `qwen3.5-4b` | Qwen3.5 4B | 2.7 GB |
| `gemma2-2b` | Gemma 2 2B IT (Dense) | 1.6 GB |
| `deepseek-r1-1.5b` | DeepSeek-R1-Distill-Qwen-1.5B | 1.1 GB |
| `phi4-mini` | Phi-4 Mini 3.8B (Microsoft) | 2.4 GB |
| `gemma4-qat-e2b` | Gemma 4 E2B QAT (Q4_0, Dense 2.3B) | 3.4 GB |
| `gemma4-qat-e4b` | Gemma 4 E4B QAT (Q4_0, Dense 4.5B) | 5.2 GB |
| `gemma4-qat-12b` | Gemma 4 12B QAT (Q4_0, Dense, Unified) | 7.0 GB |
| `gemma4-qat-26b-a4b` | Gemma 4 26B-A4B QAT (Q4_0, MoE ~3.8B act) | 14.4 GB |
| `gemma4-qat-31b` | Gemma 4 31B QAT (Q4_0, Dense) | 17.7 GB |
| `qwen3.6-35b-a3b` | Qwen 3.6 35B-A3B (UD-Q4_K_M, MoE ~3B act) | 22.1 GB |
| `qwen3.6-27b` | Qwen 3.6 27B (Q4_K_M, Dense) | 16.8 GB |

## Why CPU-Only LLMs?

GPU pricing for LLM inference can be expensive:
- **Cloud GPU**: $1-4/hr (A10G/H100) — adds up fast for long-running services
- **Local GPU**: $300-4,000+ for consumer GPUs (RTX 3060 → RTX 4090). For local hosting:
  - **Budget Sweet Spot**: Low-cost GPUs with 12GB–16GB VRAM (e.g., RTX 3060 12GB or RTX 4060 Ti 16GB, costing $280–$450) can host models up to 14.4 GB (such as Gemma 4 26B-A4B MoE or Gemma 4 12B) entirely in VRAM, delivering near-instant TTFT and 15–30 tok/s decode throughput (with MoE models like **Gemma 4 26B-A4B** running at **80+ tok/s** on this workstation's RTX 4060 Ti 16GB).
  - **High-End Value "Gold Standard"**: Used RTX 3090 24GB cards (typically $650–$800 used) remain the undisputed best local choice, providing 24GB VRAM and high memory bandwidth (936 GB/s) to fit large models (like Gemma 4 31B or Qwen 3.6 35B) entirely in VRAM, or run 72B models with partial offloading.
- **Power/heat**: GPUs draw 200-350W+ and need cooling

The numbers in this repo (1.7–58 tok/s) come from a **10th-gen Intel i7-10700** (8C/16T, 2020). Newer hardware can do significantly better:
- **Apple Silicon** (M1/M2/M3/M4): Unified memory architecture gives the CPU direct access to GPU-speed bandwidth. A base M2 runs small LLMs at 10-20 tok/s without a discrete GPU.
- **Newer x86** (Arrow Lake, Zen 5): Larger caches and faster memory improve memory-bound inference. Expect 1.5-2x throughput over 10th-gen at the same core count.
- **Server CPUs** (EPYC, Xeon): More cores and memory channels offset the lack of a GPU for batch workloads.

Even at 5-10 tok/s, CPU-only inference is useful for non-interactive workloads where latency doesn't matter but **cost, privacy, and portability** do:

| Use Case | Why CPU Works |
|---|---|
| **Batch summarization** | Queue documents, collect results later. Throughput is total output/time, not per-second speed. |
| **Code review / linting** | Feed code, get feedback async. Developer keeps working while waiting. |
| **Data extraction & classification** | Tag items, extract fields from thousands of documents. Short outputs, high volume. |
| **Translation** | Translate large text files or subtitles offline. |
| **Report generation** | Fill templates with LLM-generated text nightly. |
| **Privacy-sensitive tasks** | No data leaves the machine. No API costs, no rate limits, no vendor lock-in. |
| **Edge / air-gapped environments** | Runs on any x86 server with 64 GB RAM. No GPU needed. |

**Rule of thumb**: If a human is waiting for the response interactively, aim for 20+ tok/s (small models like Qwen 2.5-0.5B, Llama 3.2-1B). However, Mixture-of-Experts (MoE) models like **Gemma 4 26B-A4B** achieve **~11 tok/s** on CPU by only activating ~3.8B parameters per token. This makes them highly useful for semi-interactive use cases where you need the reasoning quality of a 26B model at near-interactive speeds. For completely offline batch pipelines, even 2-5 tok/s (larger dense models like Gemma 4 QAT 12B/31B) is fine — just queue more work.

## Gemma 4 QAT vs Q4_K_M Comparison

See [reports/gemma4-qat-comparison.md](reports/gemma4-qat-comparison.md) for a detailed side-by-side comparison of Gemma 4 E2B/E4B with post-training Q4_K_M vs quantization-aware-trained Q4_0. Short summary: QAT Q4_0 wins per-token speed and TTFT across all metrics; wall time is highly variable depending on response verbosity.

## Multiple Servers

Run different models on different ports simultaneously:

```bash
./serve_cpu.sh gemma4-qat-26b-a4b 8888   # primary CPU (matches systemd service)
./serve_gpu.sh gemma4-e2b 8889   # primary GPU (matches systemd service)
./serve_cpu.sh qwen2.5-0.5b 8081 # fast sidecar
./stop.sh 8081                    # kill just the sidecar
```

## Benchmarking

> **Important: Run only one benchmark at a time.** The machine has 8 cores / 16 threads. Running multiple benchmarks simultaneously (or a benchmark alongside an example generation) will distort results and may cause OOM/timeouts. Always wait for the current run to fully complete before starting the next.

### Per-model flow (think + nothink + examples)

For each backend (CPU or GPU), run all three steps to get complete data. **Prefer `nohup` to avoid shell timeout — thinking models can take 5-10+ minutes per step.**

```bash
# --- GPU example: qwen2.5-0.5b ---
nohup bash run_gpu_benchmarks.sh qwen2.5-0.5b > /tmp/bench_gpu_think.log 2>&1 &
nohup bash run_gpu_benchmarks.sh --no-reasoning qwen2.5-0.5b > /tmp/bench_gpu_nothink.log 2>&1 &
nohup ./generate_examples_gpu.sh qwen2.5-0.5b > /tmp/examples_gpu.log 2>&1 &

# --- CPU example: qwen2.5-0.5b ---
nohup bash run_cpu_benchmarks.sh qwen2.5-0.5b > /tmp/bench_cpu_think.log 2>&1 &
nohup bash run_cpu_benchmarks.sh --no-reasoning qwen2.5-0.5b > /tmp/bench_cpu_nothink.log 2>&1 &
nohup ./generate_examples_cpu.sh qwen2.5-0.5b > /tmp/examples_cpu.log 2>&1 &

# Monitor progress
cat /tmp/bench_gpu_think.log
ls results/gpu/qwen2.5-0.5b*.txt    # check which results exist
ls examples/gpu/qwen2.5-0.5b*.md    # check which examples exist
```

### Full suite

> **Important: Run only one step at a time.** Wait for the previous step to fully complete before starting the next. Running multiple benchmarks simultaneously will distort results and may cause OOM/timeouts.

```bash
# CPU — all models (thinking ON, default) → results/cpu/*_think.txt
nohup bash run_cpu_benchmarks.sh > /tmp/bench_cpu_think.log 2>&1 &

# CPU — all models (thinking OFF, fast) → results/cpu/*_nothink.txt
nohup bash run_cpu_benchmarks.sh --no-reasoning > /tmp/bench_cpu_nothink.log 2>&1 &

# GPU — all models (thinking ON, default) → results/gpu/*_think.txt
nohup bash run_gpu_benchmarks.sh > /tmp/bench_gpu_think.log 2>&1 &

# GPU — all models (thinking OFF, fast) → results/gpu/*_nothink.txt
nohup bash run_gpu_benchmarks.sh --no-reasoning > /tmp/bench_gpu_nothink.log 2>&1 &

# Generate examples — all models
nohup ./generate_examples_cpu.sh > /tmp/examples_cpu.log 2>&1 &
nohup ./generate_examples_gpu.sh > /tmp/examples_gpu.log 2>&1 &

# Monitor progress
cat /tmp/bench_gpu_think.log
ls results/gpu/*.txt | wc -l    # count completed results
ls examples/gpu/*.md | wc -l    # count completed examples

# Specific models only
nohup bash run_gpu_benchmarks.sh qwen2.5-0.5b llama3.2-1b > /tmp/bench_gpu_think.log 2>&1 &
nohup bash run_gpu_benchmarks.sh --no-reasoning qwen2.5-0.5b > /tmp/bench_gpu_nothink.log 2>&1 &
nohup ./generate_examples_gpu.sh qwen2.5-0.5b > /tmp/examples_gpu.log 2>&1 &

# Analyze results
uv run python scripts/analyze_results.py                          # all sections
uv run python scripts/analyze_results.py --section overview       # model rankings
uv run python scripts/analyze_results.py --section per-question  # per-Q breakdown
uv run python scripts/analyze_results.py --section comparison     # think vs nothink
uv run python scripts/analyze_results.py --section stability      # question variance
uv run python scripts/analyze_results.py --sort avg_decode_speed  # sort by decode speed
uv run python scripts/analyze_results.py --sort avg_ttft          # sort by TTFT
uv run python scripts/analyze_results.py --dir results/gpu       # analyze GPU results
```

## API

OpenAI-compatible at `http://localhost:<port>/v1`:

```bash
curl http://localhost:8888/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma-4-E2B-it-Q4_K_M.gguf","messages":[{"role":"user","content":"hello"}],"stream":true}'
```

## Running as a Linux Service

The server runs as **user systemd services** (no root needed). CPU on port 8888, GPU on port 8889.

### Setup

Service files reference `%h/local-llm-lab`. Copy them and edit the paths to match your repo:

```bash
cp systemd/*.service ~/.config/systemd/user/
```

Then open each file and change `%h/local-llm-lab` to your repo path (e.g. `%h/workspaces/local-llm-lab`).

```bash
nano ~/.config/systemd/user/llama-gpu.service
```

Reload:

```bash
systemctl --user daemon-reload
```

### CPU service

```bash
systemctl --user enable --now llama-cpu.service
systemctl --user status llama-cpu.service
journalctl --user -u llama-cpu.service -f
systemctl --user stop llama-cpu.service
```

### GPU service

```bash
systemctl --user enable --now llama-gpu.service
systemctl --user status llama-gpu.service
journalctl --user -u llama-gpu.service -f
systemctl --user stop llama-gpu.service
```

### Auto-start on boot (linger)

For services to start at boot before you log in:

```bash
sudo loginctl enable-linger $(whoami)
```

Verify: `loginctl show-user $(whoami) | grep Linger` should show `Linger=yes`.

### Changing the model

Open the service file in an editor and change the `ExecStart` line. For example, to switch the CPU service from `gemma4-qat-26b-a4b` to `llama3.2-1b`:

```bash
nano ~/.config/systemd/user/llama-cpu.service
```

Change:
```
ExecStart=%h/local-llm-lab/serve_cpu.sh gemma4-qat-26b-a4b 8888
```
to:
```
ExecStart=%h/local-llm-lab/serve_cpu.sh llama3.2-1b 8888
```

Then:
```bash
systemctl --user daemon-reload
systemctl --user restart llama-cpu.service
```

### Tuning flags (`-ngl`, `-c`, speculative decoding, etc.)

For context size, GPU layers, KV cache quantization, speculative decoding, and other tuning, see [server-config.md](server-config.md).

## Server Configuration

See [server-config.md](server-config.md) for all `llama-server` flags and how to apply them via systemd or directly.

To find optimal settings, run the [GPU config sweep](sweep-gpu.md): `nohup ./sweep_gpu_config.sh > /tmp/sweep.log 2>&1 &`

## Adding a New Model

See `add-model-flow.md` for the full workflow: download GGUF → add to `serve_cpu.sh` → profile → update `reports/cpu.md`.

Note: When adding a model, update the `MODELS` dictionary in **both** `serve_cpu.sh` and `serve_gpu.sh`.

## Custom Models Directory

By default, models are stored in `./models/` inside the project. To use a custom path, set the `LOCAL_LLM_MODELS` environment variable:

```bash
# Use a shared models directory
LOCAL_LLM_MODELS=/data/models ./serve_gpu.sh qwen2.5-0.5b
LOCAL_LLM_MODELS=/data/models ./serve_cpu.sh gemma4-qat-26b-a4b 8888

# Benchmarks with custom path
LOCAL_LLM_MODELS=/data/models bash run_gpu_benchmarks.sh
LOCAL_LLM_MODELS=/data/models bash run_gpu_benchmarks.sh --no-reasoning qwen2.5-0.5b

# Also works for examples
LOCAL_LLM_MODELS=/data/models ./generate_examples_gpu.sh

# Set once in your shell for the session
export LOCAL_LLM_MODELS=/data/models
./serve_gpu.sh qwen2.5-0.5b    # will look in /data/models/
```

Models not found in the custom path will be auto-downloaded there.

## Downloading Models

Models are auto-downloaded by `serve_cpu.sh`/`serve_gpu.sh` via `wget`, but HuggingFace's CDN can throttle to ~20 KB/s. For faster downloads, use the `hf` CLI (installed with this project):

```bash
# Download a specific GGUF file to the models/ directory
uv run hf download <repo> <filename> --local-dir models/

# Examples
uv run hf download unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf --local-dir models/
uv run hf download unsloth/Phi-4-mini-instruct-GGUF Phi-4-mini-instruct-Q4_K_M.gguf --local-dir models/
uv run hf download bartowski/gemma-2-2b-it-GGUF gemma-2-2b-it-Q4_K_M.gguf --local-dir models/
```

If `hf` is not installed: `uv add huggingface_hub`.

## Glossary

| Abbreviation | Full Name | Description |
|---|---|---|
| **TTFT** | Time to First Token | How long until the first output token arrives (ms). Lower = more responsive. Client-side measurement. |
| **TPOT** | Time Per Output Token (client) | Average inter-chunk latency (ms). **Deprecated** — use Decode Speed instead. In think mode this includes reasoning chunks, making it inaccurate. |
| **Decode Speed** | predicted\_per\_second | Actual tokens generated per second (from llama.cpp server). The real generation throughput. |
| **Decode Time** | predicted\_per\_token\_ms | Milliseconds per generated token. `1000 / decode_speed`. |
| **Prefill Time** | prompt\_ms | Time to process the prompt tokens before generation starts. Lower = faster first response. |
| **Prefill Speed** | prompt\_per\_second | Prompt tokens processed per second. Higher = better GPU utilization for prompt. |
| **TTOT** | Total Time of Test | Total wall-clock duration for one question including TTFT + all token generation. |
| **CoT** | Chain-of-Thought | Model reasons step-by-step before answering (think mode). |
| **QAT** | Quantization-Aware Training | Model trained with quantization in mind (Q4_0), typically more accurate than post-training quant. |
| **MoE** | Mixture of Experts | Architecture where only a subset of params are active per token. Total params >> active params. |
| **Q4_K_M** | 4-bit quantization | Post-training quantization with mixed precision (K-quants). Good balance of size/quality. |
| **Q4_0** | 4-bit quantization | Uniform 4-bit quant. Used by QAT models. Slightly less efficient per-bit than Q4_K_M. |

## Notes

- Server defaults to thinking mode (chain-of-thought). Pass `--no-reasoning` for fast direct answers.
- `scripts/ask.py` and `scripts/reflect.py` always show `[think]` reasoning tokens.
- `scripts/profile_client.py --reasoning` shows `[think]` tokens; default hides them (`[out]` only).
- SmolLM3 3B has a ~3s cold-start penalty on first request
- Large models (>VRAM) need partial GPU offload: `./serve_gpu.sh <model> --ngl N` where N is the number of layers to offload. Benchmarks and examples accept `--ngl N` too.
- See [reports/cpu.md](reports/cpu.md) for full CPU benchmarks
- See [reports/gpu.md](reports/gpu.md) for full GPU benchmarks
