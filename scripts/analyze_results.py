#!/usr/bin/env python3
import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()

PROMPTS = {
    "Q01": "software architecture",
    "Q02": "neural networks learn",
    "Q03": "TCP vs UDP",
    "Q04": "garbage collection Python",
    "Q05": "microservices",
    "Q06": "closure in programming",
    "Q07": "CAP theorem",
    "Q08": "DNS resolution",
    "Q09": "design patterns",
    "Q10": "database transactions",
}

METRIC_RE = re.compile(
    r"\[(Q\d{2})\]\s+TTFT=([\d.]+)ms\s+Total=([\d.]+)s"
)

TIMINGS_RE = re.compile(
    r"\[timings\]\s+prompt_n=(\d+),\s*prompt_ms=([\d.]+),\s*prompt_per_token_ms=([\d.]+),\s*prompt_per_second=([\d.]+),\s*predicted_n=(\d+),\s*predicted_ms=([\d.]+),\s*predicted_per_token_ms=([\d.]+),\s*predicted_per_second=([\d.]+)"
    )

FAILED_RE = re.compile(r"Failed\.")


def parse_result_file(filepath: Path) -> dict:
    data = {"model": None, "questions": {}, "failed": []}
    text = filepath.read_text(errors="replace")

    stem = filepath.stem
    if "_think" in stem:
        data["mode"] = "think"
    elif "_nothink" in stem:
        data["mode"] = "nothink"
    else:
        data["mode"] = "unknown"

    data["model"] = stem.replace("_think", "").replace("_nothink", "")

    for m in METRIC_RE.finditer(text):
        qid = m.group(1)
        q_data = {
            "ttft_ms": float(m.group(2)),
            "total_s": float(m.group(3)),
        }
        data["questions"][qid] = q_data

    for m in TIMINGS_RE.finditer(text):
        qid = None
        timings_pos = m.start()
        search_region = text[:timings_pos]
        for prev_line in reversed(search_region.split("\n")):
            qm = METRIC_RE.search(prev_line)
            if qm:
                qid = qm.group(1)
                break
        if qid and qid in data["questions"]:
            data["questions"][qid].update({
                "server_prompt_n": int(m.group(1)),
                "server_prompt_ms": float(m.group(2)),
                "server_prompt_per_token_ms": float(m.group(3)),
                "server_prompt_per_second": float(m.group(4)),
                "server_predicted_n": int(m.group(5)),
                "server_predicted_ms": float(m.group(6)),
                "server_predicted_per_token_ms": float(m.group(7)),
                "server_predicted_per_second": float(m.group(8)),
            })

    return data


def load_all_results(results_dir: Path) -> list[dict]:
    results = []
    for f in sorted(results_dir.glob("*.txt")):
        if f.name == "summary.txt":
            continue
        parsed = parse_result_file(f)
        results.append(parsed)
    return results


def print_overview_table(results: list[dict], sort_by: str = "avg_decode_speed"):
    modes = sorted(set(r["mode"] for r in results))

    for mode in modes:
        mode_results = [r for r in results if r["mode"] == mode]
        console.print(f"\n[bold cyan]=== Overview: {mode} mode ===[/bold cyan]")

        table = Table(
            title=f"Model Performance ({mode})",
            show_lines=True,
            title_style="bold",
        )
        table.add_column("Model", style="bold", min_width=18)
        table.add_column("Questions", justify="right")
        table.add_column("Avg TTFT", justify="right")
        table.add_column("Avg Decode (tok/s)", justify="right", style="green bold")
        table.add_column("Avg Total", justify="right")

        rows = []
        for r in mode_results:
            qs = r["questions"]
            if not qs:
                continue
            n = len(qs)
            avg_ttft = sum(v["ttft_ms"] for v in qs.values()) / n
            avg_total = sum(v["total_s"] for v in qs.values()) / n

            total_pred_n = sum(v.get("server_predicted_n", 0) for v in qs.values())
            total_pred_ms = sum(v.get("server_predicted_ms", 0) for v in qs.values())
            avg_decode_speed = (total_pred_n / (total_pred_ms / 1000)) if total_pred_ms > 0 else 0

            rows.append((r["model"], n, avg_ttft, avg_decode_speed, avg_total))

        sort_idx = {"avg_ttft": 2, "avg_decode_speed": 3, "avg_total": 4}[sort_by]
        reverse = sort_by in ("avg_decode_speed",)
        rows.sort(key=lambda x: x[sort_idx], reverse=reverse)

        for model, n, avg_ttft, avg_decode_speed, avg_total in rows:
            table.add_row(
                model,
                str(n),
                f"{avg_ttft:,.1f}",
                f"{avg_decode_speed:,.2f}",
                f"{avg_total:,.1f}",
            )

        console.print(table)


def print_per_question_tables(results: list[dict], sort_by: str = "server_predicted_per_second"):
    modes = sorted(set(r["mode"] for r in results))
    all_qids = [f"Q{i:02d}" for i in range(1, 11)]

    for mode in modes:
        mode_results = [r for r in results if r["mode"] == mode]
        console.print(f"\n[bold cyan]=== Per-Question: {mode} mode ===[/bold cyan]")

        for qid in all_qids:
            label = PROMPTS.get(qid, qid)
            console.print(f"\n[bold]{qid}: {label}[/bold]")

            table = Table(show_lines=True)
            table.add_column("Model", style="bold", min_width=18)
            table.add_column("TTFT (ms)", justify="right")
            table.add_column("Decode (tok/s)", justify="right", style="green bold")
            table.add_column("Total (s)", justify="right")

            rows = []
            for r in mode_results:
                if qid in r["questions"]:
                    q = r["questions"][qid]
                    decode_speed = q.get("server_predicted_per_second", 0)
                    rows.append((
                        r["model"],
                        q["ttft_ms"],
                        decode_speed,
                        q["total_s"],
                    ))

            sort_idx = {"ttft_ms": 1, "server_predicted_per_second": 2, "total_s": 3}.get(sort_by, 2)
            reverse = sort_by == "server_predicted_per_second"
            rows.sort(key=lambda x: x[sort_idx], reverse=reverse)

            for model, ttft, decode_speed, total in rows:
                table.add_row(
                    model,
                    f"{ttft:,.1f}",
                    f"{decode_speed:,.2f}",
                    f"{total:,.1f}",
                )

            console.print(table)


def print_comparison_table(results: list[dict]):
    think = {r["model"]: r for r in results if r["mode"] == "think"}
    nothink = {r["model"]: r for r in results if r["mode"] == "nothink"}
    common = sorted(set(think.keys()) & set(nothink.keys()))

    if not common:
        console.print("[yellow]No models have both think and nothink results.[/yellow]")
        return

    console.print(f"\n[bold cyan]=== Think vs No-Think Comparison ===[/bold cyan]")

    table = Table(show_lines=True, title="Think vs No-Think Overhead")
    table.add_column("Model", style="bold", min_width=18)
    table.add_column("Think TTFT", justify="right")
    table.add_column("NoThink TTFT", justify="right")
    table.add_column("Think Decode", justify="right", style="green")
    table.add_column("NoThink Decode", justify="right", style="green")
    table.add_column("TTFT Δ%", justify="right")
    table.add_column("Decode Δ%", justify="right")

    rows = []
    for model in common:
        t_qs = think[model]["questions"]
        nt_qs = nothink[model]["questions"]
        n_t = len(t_qs)
        n_nt = len(nt_qs)
        if n_t == 0 or n_nt == 0:
            continue

        t_ttft = sum(v["ttft_ms"] for v in t_qs.values()) / n_t
        nt_ttft = sum(v["ttft_ms"] for v in nt_qs.values()) / n_nt

        t_pred_n = sum(v.get("server_predicted_n", 0) for v in t_qs.values())
        t_pred_ms = sum(v.get("server_predicted_ms", 0) for v in t_qs.values())
        t_decode = (t_pred_n / (t_pred_ms / 1000)) if t_pred_ms > 0 else 0

        nt_pred_n = sum(v.get("server_predicted_n", 0) for v in nt_qs.values())
        nt_pred_ms = sum(v.get("server_predicted_ms", 0) for v in nt_qs.values())
        nt_decode = (nt_pred_n / (nt_pred_ms / 1000)) if nt_pred_ms > 0 else 0

        ttft_delta = ((t_ttft - nt_ttft) / nt_ttft * 100) if nt_ttft > 0 else 0
        decode_delta = ((t_decode - nt_decode) / nt_decode * 100) if nt_decode > 0 else 0

        rows.append((
            model, t_ttft, nt_ttft, t_decode, nt_decode,
            ttft_delta, decode_delta,
        ))

    rows.sort(key=lambda x: x[5])

    for model, t_ttft, nt_ttft, t_decode, nt_decode, ttft_d, decode_d in rows:
        table.add_row(
            model,
            f"{t_ttft:,.1f}",
            f"{nt_ttft:,.1f}",
            f"{t_decode:,.2f}",
            f"{nt_decode:,.2f}",
            f"{ttft_d:+.1f}%",
            f"{decode_d:+.1f}%",
        )

    console.print(table)


def print_question_stability(results: list[dict]):
    modes = sorted(set(r["mode"] for r in results))
    all_qids = [f"Q{i:02d}" for i in range(1, 11)]

    for mode in modes:
        mode_results = [r for r in results if r["mode"] == mode]
        console.print(f"\n[bold cyan]=== Question Variance: {mode} mode ===[/bold cyan]")
        console.print("(std dev across models — lower = more consistent across models)\n")

        table = Table(show_lines=True)
        table.add_column("Question", style="bold", min_width=10)
        table.add_column("Topic", min_width=22)
        table.add_column("Mean TTFT", justify="right")
        table.add_column("Std TTFT", justify="right")
        table.add_column("Mean Decode", justify="right")
        table.add_column("Std Decode", justify="right")

        for qid in all_qids:
            ttfts, decode_speeds = [], []
            for r in mode_results:
                if qid in r["questions"]:
                    ttfts.append(r["questions"][qid]["ttft_ms"])
                    ds = r["questions"][qid].get("server_predicted_per_second", 0)
                    if ds > 0:
                        decode_speeds.append(ds)

            if not ttfts:
                continue

            import statistics
            n = len(ttfts)
            mean_ttft = sum(ttfts) / n
            std_ttft = statistics.stdev(ttfts) if n > 1 else 0

            if decode_speeds:
                n_ds = len(decode_speeds)
                mean_decode = sum(decode_speeds) / n_ds
                std_decode = statistics.stdev(decode_speeds) if n_ds > 1 else 0
            else:
                mean_decode = 0
                std_decode = 0

            table.add_row(
                qid,
                PROMPTS.get(qid, ""),
                f"{mean_ttft:,.1f}",
                f"{std_ttft:,.1f}",
                f"{mean_decode:,.2f}",
                f"{std_decode:,.2f}",
            )

        console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Analyze CPU benchmark results")
    parser.add_argument(
        "--dir", type=str, default="results/cpu",
        help="Results directory (default: results/cpu)",
    )
    parser.add_argument(
        "--sort", type=str, default="avg_decode_speed",
        choices=["avg_ttft", "avg_decode_speed", "avg_total", "ttft_ms", "server_predicted_per_second", "total_s"],
        help="Sort metric (default: avg_decode_speed)",
    )
    parser.add_argument(
        "--section", type=str, default="all",
        choices=["all", "overview", "per-question", "comparison", "stability"],
        help="Which sections to show (default: all)",
    )
    args = parser.parse_args()

    results_dir = Path(args.dir)
    if not results_dir.exists():
        console.print(f"[red]Directory not found: {results_dir}[/red]")
        sys.exit(1)

    results = load_all_results(results_dir)
    if not results:
        console.print("[red]No result files found.[/red]")
        sys.exit(1)

    console.print(f"[bold]Loaded {len(results)} result files from {results_dir}[/bold]")
    models = sorted(set(r["model"] for r in results))
    console.print(f"Models: {', '.join(models)}\n")

    section = args.section

    if section in ("all", "overview"):
        print_overview_table(results, sort_by=args.sort)

    if section in ("all", "per-question"):
        print_per_question_tables(results, sort_by=args.sort)

    if section in ("all", "comparison"):
        print_comparison_table(results)

    if section in ("all", "stability"):
        print_question_stability(results)


if __name__ == "__main__":
    main()
