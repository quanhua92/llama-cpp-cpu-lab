import argparse
import asyncio
import json
import os
import time

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8080)
parser.add_argument("--output-dir", required=True)
parser.add_argument("--model-key", required=True)
parser.add_argument("--prompts", default="ask,reflect", help="Comma-separated list: ask,reflect")
parser.add_argument("--question", default=None, help="Custom question (saves as custom)")
parser.add_argument("--name", default=None, help="Custom output name (used with --question)")
parser.add_argument("--skip-existing", action="store_true")
args = parser.parse_args()

API_BASE = f"http://localhost:{args.port}/v1"
API_URL = f"{API_BASE}/chat/completions"
MODELS_URL = f"{API_BASE}/models"

PROMPTS = {
    "ask": "viết một bức thư gửi tương lai, 100 năm sau, từ một người sống ở Việt Nam năm 2026",
    "reflect": "giả sử bạn là một đầu bếp chuyên nghiệp, hãy giới thiệu món ăn đặc trưng của Việt Nam cho du khách nước ngoài",
}


async def fetch_model_name(client: httpx.AsyncClient) -> str:
    try:
        resp = await client.get(MODELS_URL, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            models = data.get("data", [])
            if models:
                return models[0].get("id", "unknown")
    except Exception:
        pass
    return "unknown"


async def call_llm(client, messages, model_name, max_tokens=4096):
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": True,
        "max_tokens": max_tokens,
        "temperature": 0.0,
    }

    start_time = time.perf_counter()
    ttft = None
    thinking = ""
    content = ""
    completion_tokens = 0

    try:
        async with client.stream("POST", API_URL, json=payload, timeout=300.0) as stream:
            if stream.status_code != 200:
                body = await stream.aread()
                return None, f"Server error {stream.status_code}: {body.decode()[:200]}"

            async for line in stream.aiter_lines():
                if not line.strip():
                    continue
                if ttft is None:
                    ttft = time.perf_counter() - start_time
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        data = json.loads(line[6:])
                        timings = data.get("timings", {})
                        if timings:
                            completion_tokens = timings.get("predicted_n", completion_tokens)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        if delta.get("reasoning_content"):
                            thinking += delta["reasoning_content"]
                        if delta.get("content"):
                            content += delta["content"]
                    except Exception:
                        pass

            total_duration = time.perf_counter() - start_time
            gen_time = total_duration - ttft if ttft else total_duration
            tok_per_sec = completion_tokens / gen_time if gen_time > 0 else 0

            return {
                "ttft_ms": ttft * 1000 if ttft else 0,
                "total_time_s": total_duration,
                "tok_s": tok_per_sec,
                "tokens": completion_tokens,
                "thinking": thinking,
                "content": content,
            }, None
    except Exception as e:
        return None, f"Request failed: {e}"


async def generate_ask(client, prompt, model_name):
    result, error = await call_llm(
        client,
        [{"role": "user", "content": prompt}],
        model_name,
    )
    if error:
        return None, error
    return {"steps": [{"label": "Initial Generation", "result": result}]}, None


async def generate_reflect(client, prompt, model_name):
    messages = [{"role": "user", "content": prompt}]

    result1, error = await call_llm(client, messages, model_name, max_tokens=1024)
    if error:
        return None, error

    draft = result1["content"]

    critique_prompt = f"""Critique this response to the task: "{prompt}"

Response:
{draft}

Provide specific, actionable feedback on:
1. Clarity and coherence
2. Completeness
3. Accuracy
4. Structure
5. Areas for improvement

Be concise but thorough."""

    messages.append({"role": "assistant", "content": draft})
    messages.append({"role": "user", "content": critique_prompt})

    result2, error = await call_llm(client, messages, model_name, max_tokens=1024)
    if error:
        return None, error

    critique = result2["content"]

    revision_prompt = f"""Original Task: {prompt}

Original Response:
{draft}

Critique:
{critique}

Revise the original response incorporating the critique feedback. Improve clarity, completeness, and accuracy while maintaining the core message."""

    messages.append({"role": "assistant", "content": critique})
    messages.append({"role": "user", "content": revision_prompt})

    result3, error = await call_llm(client, messages, model_name, max_tokens=2048)
    if error:
        return None, error

    return {
        "steps": [
            {"label": "Initial Generation", "result": result1},
            {"label": "Self-Critique", "result": result2},
            {"label": "Revision", "result": result3},
        ]
    }, None


def write_ask_output(output_dir, model_key, model_filename, prompt, data):
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{model_key}_ask.md")

    step = data["steps"][0]
    r = step["result"]

    lines = [
        f"Model: {model_filename}",
        "",
        "=" * 60,
        f"> {prompt}",
        "=" * 60,
        "",
    ]
    if r["thinking"]:
        lines.append(f" [think] {r['thinking']}")
    if r["content"]:
        lines.append(f"   [out] {r['content']}")
    lines.extend([
        "",
        "=" * 60,
        f"TTFT: {r['ttft_ms']:.0f}ms | {r['tok_s']:.1f} tok/s | {r['total_time_s']:.1f}s total ({r['tokens']} tokens)",
    ])

    with open(filepath, "w") as f:
        f.write("\n".join(lines) + "\n")

    return filepath


def write_reflect_output(output_dir, model_key, model_filename, prompt, data):
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{model_key}_reflect.md")

    lines = [
        f"Model: {model_filename}",
        "",
        "=" * 60,
        f"Reflection Task: {prompt}",
        "=" * 60,
    ]

    total_time = 0
    total_tokens = 0
    all_tps = []

    for i, step in enumerate(data["steps"]):
        r = step["result"]
        total_time += r["total_time_s"]
        total_tokens += r["tokens"]
        all_tps.append(r["tok_s"])

        label = step["label"]
        lines.append("")
        lines.append(f"\n[STEP {i+1}] {label}")
        lines.append("-" * 40)
        if r["thinking"]:
            lines.append(f"      [think] {r['thinking']}")
        if r["content"]:
            lines.append(f"        [out] {r['content']}")

    avg_tps = sum(all_tps) / len(all_tps) if all_tps else 0

    lines.extend([
        "",
        "=" * 60,
        "FINAL RESULT",
        "=" * 60,
        data["steps"][-1]["result"]["content"],
        "",
        "=" * 60,
        f"Total time: {total_time:.1f}s",
        f"Total tokens: {total_tokens}",
        f"Avg throughput: {avg_tps:.1f} tok/s",
    ])

    with open(filepath, "w") as f:
        f.write("\n".join(lines) + "\n")

    return filepath


async def main():
    os.makedirs(args.output_dir, exist_ok=True)

    async with httpx.AsyncClient() as client:
        model_filename = await fetch_model_name(client)
        print(f"Model: {model_filename}")

        prompt_list = PROMPTS.copy()
        if args.question:
            prompt_list["custom"] = args.question
        if args.name:
            prompt_list = {args.name: prompt_list.pop("custom")}

        selected = [p.strip() for p in args.prompts.split(",")]
        for name in list(prompt_list.keys()):
            if name not in selected:
                del prompt_list[name]

        for prompt_name, prompt in prompt_list.items():
            outfile = os.path.join(args.output_dir, f"{args.model_key}_{prompt_name}.md")
            if args.skip_existing and os.path.exists(outfile):
                print(f"  [{prompt_name}] Skipping (exists): {outfile}")
                continue

            print(f"  [{prompt_name}] Generating...")
            data, error = None, None

            if prompt_name == "reflect":
                data, error = await generate_reflect(client, prompt, model_filename)
            else:
                data, error = await generate_ask(client, prompt, model_filename)

            if error:
                print(f"  [{prompt_name}] ERROR: {error}")
                continue

            if prompt_name == "reflect":
                filepath = write_reflect_output(args.output_dir, args.model_key, model_filename, prompt, data)
                total_tokens = sum(s["result"]["tokens"] for s in data["steps"])
            else:
                filepath = write_ask_output(args.output_dir, args.model_key, model_filename, prompt, data)
                total_tokens = data["steps"][0]["result"]["tokens"]

            print(f"  [{prompt_name}] Done: {filepath} ({total_tokens} tokens)")
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(main())
