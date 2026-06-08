# Server Tuning Reference

Flags passed to `llama-server` via `serve_gpu.sh` / `serve_cpu.sh`.

## Core Flags

| Flag | Default | Effect |
|------|---------|--------|
| `-ngl N` | 99 (all) | Layers offloaded to GPU. Lower = less VRAM, slower decode but fits bigger models. |
| `-c N` | 8192 | Context window (prompt + output tokens, including thinking). More = longer conversations, uses more VRAM. |
| `-t N` | 8 | CPU threads for decode. |
| `-tb N` | same as `-t` | CPU threads for prefill/batch processing. Use more on high-core CPUs (e.g. `-tb 24` on i9-13900K). |

## Memory & Performance

| Flag | Description |
|------|-------------|
| `--mlock` | Lock model in RAM, prevents swap. Recommended for CPU server on dedicated machines. |
| `-ctk q8_0 -ctv q8_0` | Quantize KV cache to Q8. ~50% VRAM savings, almost zero quality loss, minimal speed impact. The safe default for GPU servers. Enables 32K+ context on 16GB VRAM. |
| `-ctk q4_0 -ctv q4_0` | Q4 KV cache. ~75% VRAM savings but noticeable quality loss on complex tasks. Slower generation without TurboQuant. Only use when you need maximum context and q8 isn't enough. |
| `-ctk q4_0 -ctv q8_0` | Asymmetric: Q4 for K, Q8 for V. The Value cache directly affects output quality, so keeping V at Q8 preserves answer accuracy while K at Q4 saves space. Good compromise. |
| `--poll N` | Busy-wait polling level (0 = off, 50 = default). Reduces latency at cost of idle CPU usage. Set to 0 to save power. |
| `--prio N` | Process priority: low(-1), normal(0), medium(1), high(2), realtime(3). Default: 0. |
| `-ub N` | Physical batch size (default 512). Tune for GPU memory. |

## Speculative Decoding

Speculative decoding predicts multiple tokens per step instead of one, boosting throughput. The GPU verifies guesses in parallel — correct guesses are "free" tokens.

| Flag | Description |
|------|-------------|
| `--spec-type ngram-simple` | Looks at recent token history for repeated patterns (n-grams) to predict next tokens. Zero extra VRAM, no draft model needed. Best for text with repetition (code, lists). Free speed boost. |
| `--spec-type draft-eagle3` | Eagle3 speculative decoding variant. |
| `-md model.gguf` | Use a small GGUF as draft model for speculative decoding. More accurate guesses but costs extra VRAM. |
| `--spec-default` | Auto-enable default speculative config. |

## Editing the Systemd Service

Open the service file in your editor and change the `ExecStart` line:

```bash
# GPU service
nano ~/.config/systemd/user/llama-gpu.service

# CPU service
nano ~/.config/systemd/user/llama-cpu.service
```

### Initial setup (copy and edit)

Copy the service files and edit the paths to match your repo:

```bash
cp systemd/*.service ~/.config/systemd/user/
```

Then open each file and change `%h/local-llm-lab` to your repo path (e.g. `%h/workspaces/local-llm-lab`).

### Example: increase context

Change the `ExecStart` line from:

```
ExecStart=%h/local-llm-lab/serve_gpu.sh gemma4-qat-26b-a4b 8889
```

to:

```
ExecStart=%h/local-llm-lab/serve_gpu.sh gemma4-qat-26b-a4b 8889 -c 16384
```

### Example: partial GPU offload for large model

```
ExecStart=%h/local-llm-lab/serve_gpu.sh qwen3.6-35b-a3b 8889 --ngl 40
```

### Example: change model

```
ExecStart=%h/local-llm-lab/serve_gpu.sh llama3.2-1b 8889
```

Then reload and restart:

```bash
systemctl --user daemon-reload
systemctl --user restart llama-gpu.service
```

## Applying Flags to serve_gpu.sh / serve_cpu.sh

For non-service usage, pass flags directly. The serve scripts forward extra arguments to `llama-server`:

```bash
# Larger context
./serve_gpu.sh gemma4-qat-26b-a4b -c 16384

# KV cache quantization
./serve_gpu.sh gemma4-qat-26b-a4b -ctk q8_0 -ctv q8_0

# Speculative decoding
./serve_gpu.sh gemma4-qat-26b-a4b --spec-type ngram-simple

# More batch threads (good for high-core CPUs)
./serve_gpu.sh gemma4-qat-26b-a4b -tb 24

# Lock model in RAM (CPU server)
./serve_cpu.sh gemma4-qat-26b-a4b --mlock
```

## Presets

Copy-paste ready `ExecStart` lines for the systemd service.

### GPU: Default (14B MoE, full VRAM, KV8)

```
ExecStart=%h/local-llm-lab/serve_gpu.sh gemma4-qat-26b-a4b 8889 -ctk q8_0 -ctv q8_0
```

Best for: RTX 4060 Ti 16GB with models <= 14GB. All layers on GPU, 8K context, KV8 quantization halves cache VRAM — fits up to 32K context at full GPU offload.

### GPU: Large Model (21B MoE, partial offload)

```
ExecStart=%h/local-llm-lab/serve_gpu.sh qwen3.6-35b-a3b 8889 --ngl 40
```

Best for: Models larger than VRAM. Offloads 40 layers to GPU, rest runs on CPU. Slower but fits.

### GPU: Max Context (64K context, KV quant)

```
ExecStart=%h/local-llm-lab/serve_gpu.sh gemma4-qat-26b-a4b 8889 -c 65536 -ctk q8_0 -ctv q8_0
```

Best for: Long conversations, document summarization. KV quant halves cache VRAM — fits 64K context with all layers on GPU.

### GPU: Speed (speculative decoding)

```
ExecStart=%h/local-llm-lab/serve_gpu.sh gemma4-qat-26b-a4b 8889 --spec-type ngram-simple
```

Best for: Maximum throughput. Ngram speculative decoding adds no extra VRAM cost.

### GPU: High-Core CPU Prefill (i9-13900K)

```
ExecStart=%h/local-llm-lab/serve_gpu.sh gemma4-qat-26b-a4b 8889 -tb 24 --prio high
```

Best for: High-core CPUs (24+ threads). Uses more threads for prompt processing, raises priority.

### CPU: Dedicated Server (lock in RAM)

```
ExecStart=%h/local-llm-lab/serve_cpu.sh gemma4-qat-26b-a4b 8888 --mlock -tb 8 --poll 0
```

Best for: CPU-only machines with plenty of RAM. Locks model to prevent swap, saves power with no polling.

## Testing

After changing config or restarting the service, smoke test it:

```bash
# Quick ask (shows [think] + [out] + timing)
uv run python scripts/ask.py "what is 2+2?" --port 8889

# Benchmark suite (10 questions, hides [think], shows TTFT + decode speed)
uv run python scripts/profile_client.py --port 8889

# Benchmark with think tokens visible
uv run python scripts/profile_client.py --port 8889 --reasoning

# Check GPU usage
nvidia-smi

# Check service status
systemctl --user status llama-gpu.service
journalctl --user -u llama-gpu.service --no-pager -n 20
```
