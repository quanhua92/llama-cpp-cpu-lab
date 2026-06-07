# Examples

Per-model example outputs for debugging and quality comparison.

## Structure

- `cpu/` — Per-model outputs generated on CPU (i7-10700)
- `gpu/` — Per-model outputs generated on GPU

## Generating

```bash
# All models (CPU)
./generate_examples_cpu.sh

# Single model
./generate_examples_cpu.sh gemma4-qat-26b-a4b

# Only ask or only reflect
./generate_examples_cpu.sh --prompts ask
./generate_examples_cpu.sh --prompts reflect

# Custom question (saves as _custom.md, or --name to pick suffix)
./generate_examples_cpu.sh --question "explain quantum computing in Vietnamese"
./generate_examples_cpu.sh --question "explain recursion" --name recursion

# No-think mode (faster, no reasoning)
./generate_examples_cpu.sh --no-reasoning

# Skip already-generated files
./generate_examples_cpu.sh --skip-existing

# Large models (12B+) take 10-20 min per prompt. Use nohup to avoid timeout:
nohup ./generate_examples_cpu.sh gemma4-qat-12b > /tmp/examples.log 2>&1 &
nohup ./generate_examples_cpu.sh gemma4-qat-26b-a4b > /tmp/examples.log 2>&1 &
nohup ./generate_examples_cpu.sh gemma4-qat-31b > /tmp/examples.log 2>&1 &

# GPU
./generate_examples_gpu.sh
```

Each model produces `{model}_ask.md` and `{model}_reflect.md` with `[think]` reasoning, `[out]` answer, and timing (TTFT, tok/s, total tokens).
