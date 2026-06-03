# CPU Small Model Bench

CPU-only LLM serving and benchmarking using [llama.cpp](https://github.com/ggml-org/llama.cpp).

**Machine:** Intel i7-10700 (8C/16T, 2.9–4.8 GHz) · 64 GB RAM · x86_64 · CPU only (no GPU)
**llama.cpp:** [`4da6370`](https://github.com/ggml-org/llama.cpp/commit/4da6370d43f55a3f5ad576c5a1528b6ba9c53258)

## Quick Start

```bash
# Start server (Gemma 4 E2B on port 8080)
./serve.sh

# Or pick a model + port
./serve.sh qwen2.5-0.5b 8081

# Disable thinking for speed
./serve.sh gemma4-e2b --no-reasoning

# Profile client defaults to port 8080. Service runs on 8888.

# Kill a server
./stop.sh
./stop.sh 8888
./stop.sh 8081

# Profile latency ([out] only; server thinks but [think] hidden)
uv run python profile_client.py

# Show [think] reasoning tokens in output
uv run python profile_client.py --reasoning

# Run full benchmark suite
bash run_benchmarks.sh
```

## Files

| File | Purpose |
|------|---------|
| `serve.sh` | Start llama-server on any port with any curated model |
| `stop.sh` | Kill server by port (default 8080) |
| `profile_client.py` | Streaming benchmark: TTFT, TPOT, tok/s |
| `run_benchmarks.sh` | Run profile across all models sequentially |
| `add-model-flow.md` | Guide for adding new GGUF models |
| `report.md` | Full benchmark results and analysis |
| `repo/` | llama.cpp source + `build/bin/llama-server` |

## Curated Models

All Q4_K_M quant, optimized for CPU (`-ngl 0`, `-t 8`, `-c 8192`):

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

## Multiple Servers

Run different models on different ports simultaneously:

```bash
./serve.sh gemma4-e2b 8888   # primary (matches systemd service)
./serve.sh qwen2.5-0.5b 8081  # fast sidecar
./stop.sh 8081                 # kill just the sidecar
```

## Benchmarking

```bash
# All models (thinking ON, default) → *_think.txt
bash run_benchmarks.sh

# All models (thinking OFF, fast) → *_nothink.txt
bash run_benchmarks.sh --no-reasoning

# Specific models only
bash run_benchmarks.sh qwen2.5-0.5b llama3.2-1b
bash run_benchmarks.sh --no-reasoning qwen2.5-0.5b
```

Results saved to `/tmp/llama_bench_results/<key>_think.txt` or `*_nothink.txt`.

## API

OpenAI-compatible at `http://localhost:<port>/v1`:

```bash
curl http://localhost:8888/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma-4-E2B-it-Q4_K_M.gguf","messages":[{"role":"user","content":"hello"}],"stream":true}'
```

## Running as a Linux Service

The server runs as a **user systemd service** (no root needed) on **port 8888**.

### Service file

Located at `~/.config/systemd/user/llama-server.service`:

```ini
[Unit]
Description=llama.cpp LLM Server (gemma4-e2b)
After=network.target

[Service]
Type=forking
WorkingDirectory=%h/llama-cpp
PIDFile=%h/llama-cpp/server.8888.pid
ExecStart=%h/llama-cpp/serve.sh gemma4-e2b 8888
ExecStop=%h/llama-cpp/stop.sh 8888
Restart=on-failure
RestartSec=5
StandardOutput=append:%h/llama-cpp/server.8888.log
StandardError=append:%h/llama-cpp/server.8888.log

[Install]
WantedBy=default.target
```

### Commands

```bash
# Enable auto-start on boot
systemctl --user enable llama-server.service

# Start now
systemctl --user start llama-server.service

# Check status
systemctl --user status llama-server.service

# View logs
journalctl --user -u llama-server.service -f

# Stop
systemctl --user stop llama-server.service

# Disable auto-start
systemctl --user disable llama-server.service
```

### Auto-start on boot (linger)

For the service to start at boot before you log in:

```bash
sudo loginctl enable-linger $(whoami)
```

Verify: `loginctl show-user $(whoami) | grep Linger` should show `Linger=yes`.

### Changing the model

Edit the service file:

```bash
# Change gemma4-e2b to another model key
sed -i 's/gemma4-e2b/llama3.2-1b/' ~/.config/systemd/user/llama-server.service

# Reload and restart
systemctl --user daemon-reload
systemctl --user restart llama-server.service
```

## Adding a New Model

See `add-model-flow.md` for the full workflow: download GGUF → add to `serve.sh` → profile → update `report.md`.

## Notes

- Server defaults to thinking mode (chain-of-thought). Pass `--no-reasoning` to serve.sh for fast direct answers.
- `profile_client.py --reasoning` shows `[think]` tokens; default hides them (`[out]` only).
- SmolLM3 3B has a ~3s cold-start penalty on first request
- See `report.md` for full benchmarks across all 12 models
