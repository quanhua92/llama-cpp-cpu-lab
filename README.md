# Local LLM Lab

LLM serving and benchmarking using [llama.cpp](https://github.com/ggml-org/llama.cpp). Supports both CPU and GPU backends.

**Machine:** Intel i7-10700 (8C/16T, 2.9–4.8 GHz) · 64 GB RAM · x86_64
**llama.cpp:** [`4da6370`](https://github.com/ggml-org/llama.cpp/commit/4da6370d43f55a3f5ad576c5a1528b6ba9c53258)

## Contents

- [Benchmark Reports](#benchmark-reports)
- [Quick Start](#quick-start)
- [Curated Models](#curated-models)
- [Gemma 4 QAT vs Q4_K_M Comparison](#gemma-4-qat-vs-q4_k_m-comparison)
- [Multiple Servers](#multiple-servers)
- [Benchmarking](#benchmarking)
- [API](#api)
- [Running as a Linux Service](#running-as-a-linux-service)
- [Adding a New Model](#adding-a-new-model)
- [Downloading Models](#downloading-models)
- [Notes](#notes)

## Benchmark Reports

- [CPU Report](reports/cpu.md)
- [GPU Report](reports/gpu.md)
- [Gemma 4 QAT vs Q4_K_M Comparison](reports/gemma4-qat-comparison.md)

## Quick Start

```bash
# CPU server (default gemma4-e2b on port 8080)
./serve_cpu.sh

# GPU server (default gemma4-e2b on port 8080)
./serve_gpu.sh

# Or pick a model + port
./serve_cpu.sh qwen2.5-0.5b 8081
./serve_gpu.sh qwen2.5-0.5b 8081

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

# Run full benchmark suite (CPU)
bash run_cpu_benchmarks.sh

# Run full benchmark suite (GPU)
bash run_gpu_benchmarks.sh
```

## Files

| File | Purpose |
|------|---------|
| `serve_cpu.sh` | Start llama-server (CPU, `-ngl 0`) on any port with any curated model |
| `serve_gpu.sh` | Start llama-server (GPU, `-ngl 99`) on any port with any curated model |
| `stop.sh` | Kill server by port (default 8080) |
| `scripts/ask.py` | Single streaming LLM call: shows `[think]` + `[out]` + timing |
| `scripts/reflect.py` | Reflection agent: generate → critique → revise (3-step loop) |
| `scripts/profile_client.py` | Streaming benchmark: TTFT, TPOT, tok/s |
| `examples/ask_example.md` | Example `ask.py` output (Vietnamese: letter to the future) |
| `examples/reflect_example.md` | Example `reflect.py` output (Vietnamese: robot chef introduces Phở) |
| `run_cpu_benchmarks.sh` | Run profile across all models (CPU) → `results/cpu/` |
| `run_gpu_benchmarks.sh` | Run profile across all models (GPU) → `results/gpu/` |
| `add-model-flow.md` | Guide for adding new GGUF models |
| `reports/cpu.md` | CPU benchmark results and analysis |
| `reports/gpu.md` | GPU benchmark results and analysis |
| `reports/gemma4-qat-comparison.md` | Gemma 4 QAT Q4_0 vs Q4_K_M benchmark comparison |
| `systemd/llama-cpu.service` | User systemd service (CPU, port 8888) |
| `systemd/llama-gpu.service` | User systemd service (GPU, port 8889) |
| `repo/` | llama.cpp source + `build/bin/llama-server` |
| `run/` | Server PID and log files (gitignored) |

## Curated Models

All Q4_K_M quant, shared between CPU (`-ngl 0`, `-t 8`, `-c 8192`) and GPU (`-ngl 99`, `-c 8192`). QAT models use Q4_0 quantization (quantization-aware training):

| Key | Model | Size |
|-----|-------|------|
| `gemma4-e2b` | Gemma 4 E2B (MoE 2.3B act) | 2.9 GB |
| `gemma4-e4b` | Gemma 4 E4B (MoE 4.5B act) | 4.7 GB |
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
| `gemma4-qat-e2b` | Gemma 4 E2B QAT (Q4_0, MoE 2.3B act) | 3.4 GB |
| `gemma4-qat-e4b` | Gemma 4 E4B QAT (Q4_0, MoE 4.5B act) | 5.2 GB |
| `gemma4-qat-12b` | Gemma 4 12B QAT (Q4_0, Dense) | 7.0 GB |
| `gemma4-qat-26b` | Gemma 4 26B-A4B QAT (Q4_0, MoE ~4B act) | 14.4 GB |
| `gemma4-qat-31b` | Gemma 4 31B QAT (Q4_0, Dense) | 17.7 GB |

## Gemma 4 QAT vs Q4_K_M Comparison

See [reports/gemma4-qat-comparison.md](reports/gemma4-qat-comparison.md) for a detailed side-by-side comparison of Gemma 4 E2B/E4B with post-training Q4_K_M vs quantization-aware-trained Q4_0. Short summary: QAT Q4_0 wins per-token speed and TTFT across all metrics; Q4_K_M wins no-think wall time only due to less verbose output.

## Multiple Servers

Run different models on different ports simultaneously:

```bash
./serve_cpu.sh gemma4-e2b 8888   # primary CPU (matches systemd service)
./serve_gpu.sh gemma4-e2b 8889   # primary GPU (matches systemd service)
./serve_cpu.sh qwen2.5-0.5b 8081 # fast sidecar
./stop.sh 8081                    # kill just the sidecar
```

## Benchmarking

```bash
# CPU — all models (thinking ON, default) → results/cpu/*_think.txt
bash run_cpu_benchmarks.sh

# CPU — all models (thinking OFF, fast) → results/cpu/*_nothink.txt
bash run_cpu_benchmarks.sh --no-reasoning

# GPU — all models (thinking ON, default) → results/gpu/*_think.txt
bash run_gpu_benchmarks.sh

# GPU — all models (thinking OFF, fast) → results/gpu/*_nothink.txt
bash run_gpu_benchmarks.sh --no-reasoning

# Specific models only
bash run_cpu_benchmarks.sh qwen2.5-0.5b llama3.2-1b
bash run_gpu_benchmarks.sh --no-reasoning qwen2.5-0.5b
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

```bash
# Symlink service files into systemd
ln -s ~/llama-cpp/systemd/llama-cpu.service ~/.config/systemd/user/
ln -s ~/llama-cpp/systemd/llama-gpu.service ~/.config/systemd/user/
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

Edit the service file:

```bash
# Change gemma4-e2b to another model key (CPU)
sed -i 's/gemma4-e2b/llama3.2-1b/' ~/.config/systemd/user/llama-cpu.service

# Reload and restart
systemctl --user daemon-reload
systemctl --user restart llama-cpu.service
```

## Adding a New Model

See `add-model-flow.md` for the full workflow: download GGUF → add to `serve_cpu.sh` → profile → update `reports/cpu.md`.

Note: When adding a model, update the `MODELS` dictionary in **both** `serve_cpu.sh` and `serve_gpu.sh`.

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

## Notes

- Server defaults to thinking mode (chain-of-thought). Pass `--no-reasoning` for fast direct answers.
- `scripts/ask.py` and `scripts/reflect.py` always show `[think]` reasoning tokens.
- `scripts/profile_client.py --reasoning` shows `[think]` tokens; default hides them (`[out]` only).
- SmolLM3 3B has a ~3s cold-start penalty on first request
- See [reports/cpu.md](reports/cpu.md) for full CPU benchmarks across all 20 models
- See [reports/gpu.md](reports/gpu.md) for full GPU benchmarks across all 16 models
