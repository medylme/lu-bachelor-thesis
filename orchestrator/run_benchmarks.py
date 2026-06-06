"""
run_benchmarks.py - orchestrate all benchmarks and collect results.

Usage:
    python -m orchestrator.run_benchmarks [options]
    python orchestrator/run_benchmarks.py [options]

Options:
    --rust-only     Run only Rust benchmarks
    --cpp-only      Run only C++ benchmarks
    --r-only        Run only R benchmarks
    --mem-only      Run only memory-measurement steps (skip timing)
    --time-only     Run only timing steps (skip memory measurement)
    --output-dir    Directory to write results.csv and results.parquet
                    (default: results/)

Output schema (results/results.csv):
    algorithm, language, n, time_ns_median, time_ns_ci_lo, time_ns_ci_hi,
    peak_bytes

Each row is one (algorithm, language, input-size) triple.
"""

from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any
import pandas as pd
from orchestrator.parsers import (
    parse_bench_csv,
    parse_criterion_dir,
    parse_dhat_stdout,
    parse_google_benchmark,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCH_ROOT = REPO_ROOT / "benchmarks"
RESULTS_ROOT = REPO_ROOT / "results"

RUST_CRATES = [
    ("kmp",               BENCH_ROOT / "kmp" / "rust",               1_000_000),
    ("smith_waterman",    BENCH_ROOT / "smith_waterman" / "rust",    5_000),
    ("needleman_wunsch",  BENCH_ROOT / "needleman_wunsch" / "rust",  5_000),
    ("tree_traversal",    BENCH_ROOT / "tree_traversal" / "rust",    100_000),
]

CPP_DIRS = [
    ("kmp",              BENCH_ROOT / "kmp" / "cpp"),
    ("smith_waterman",   BENCH_ROOT / "smith_waterman" / "cpp"),
    ("tree_traversal",   BENCH_ROOT / "tree_traversal" / "cpp"),
]

R_DIRS = [
    ("needleman_wunsch", BENCH_ROOT / "needleman_wunsch" / "r"),
    ("tree_traversal",   BENCH_ROOT / "tree_traversal" / "r"),
]

def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"  $ {' '.join(cmd)}", flush=True)
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=False,
        text=True,
        check=check,
    )


def run_capture(cmd: list[str], cwd: Path) -> str:
    print(f"  $ {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"    STDERR: {proc.stderr.strip()}", file=sys.stderr)
    return proc.stdout


def bench_rust_timing(algo: str, crate_dir: Path) -> list[dict[str, Any]]:
    print(f"\n[rust timing] {algo}")
    run(["cargo", "bench", "--quiet"], cwd=crate_dir)
    return parse_criterion_dir(crate_dir, algo)


def bench_rust_memory(algo: str, crate_dir: Path, largest_n: int) -> dict[str, Any] | None:
    print(f"\n[rust memory] {algo}")
    stdout = run_capture(
        ["cargo", "run", "--release", "--quiet", "--example", "mem"],
        cwd=crate_dir,
    )
    return parse_dhat_stdout(stdout, algo, "rust", largest_n)


def build_cpp(cpp_dir: Path) -> bool:
    build_dir = cpp_dir / "build"
    build_dir.mkdir(exist_ok=True)
    r = run(
        ["cmake", "-S", str(cpp_dir), "-B", str(build_dir),
         "-DCMAKE_BUILD_TYPE=Release"],
        cwd=cpp_dir,
        check=False,
    )
    if r.returncode != 0:
        print(f"  cmake configure failed for {cpp_dir}", file=sys.stderr)
        return False
    r = run(["cmake", "--build", str(build_dir), "--parallel"], cwd=cpp_dir, check=False)
    if r.returncode != 0:
        print(f"  cmake build failed for {cpp_dir}", file=sys.stderr)
        return False
    return True


CPP_BENCH_REPETITIONS = 10

def bench_cpp_timing(algo: str, cpp_dir: Path, results_dir: Path) -> list[dict[str, Any]]:
    print(f"\n[cpp timing] {algo}")
    if not build_cpp(cpp_dir):
        return []
    build_dir = cpp_dir / "build"
    out_json = results_dir / f"{algo}_cpp.json"
    bench_bin = build_dir / "bench"
    run(
        [str(bench_bin),
         f"--benchmark_out={out_json}",
         "--benchmark_out_format=json",
         "--benchmark_time_unit=ns",
         f"--benchmark_repetitions={CPP_BENCH_REPETITIONS}",
         "--benchmark_report_aggregates_only=true"],
        cwd=cpp_dir,
    )
    return parse_google_benchmark(out_json, algo, repetitions=CPP_BENCH_REPETITIONS)


def bench_cpp_memory(algo: str, cpp_dir: Path, largest_n: int) -> dict[str, Any] | None:
    print(f"\n[cpp memory] {algo}")
    build_dir = cpp_dir / "build"
    if not (build_dir / "mem").exists() and not build_cpp(cpp_dir):
        return None
    stdout = run_capture([str(build_dir / "mem")], cwd=cpp_dir)
    return parse_dhat_stdout(stdout, algo, "cpp", largest_n)


def bench_r(algo: str, r_dir: Path, results_dir: Path) -> list[dict[str, Any]]:
    print(f"\n[r bench] {algo}")
    csv_path = results_dir / f"{algo}_r.csv"
    bench_script = r_dir / "bench.R"
    stdout = run_capture(["Rscript", str(bench_script)], cwd=r_dir)
    csv_path.write_text(stdout)
    return parse_bench_csv(stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all thesis benchmarks.")
    parser.add_argument("--rust-only",  action="store_true")
    parser.add_argument("--cpp-only",   action="store_true")
    parser.add_argument("--r-only",     action="store_true")
    parser.add_argument("--mem-only",   action="store_true")
    parser.add_argument("--time-only",  action="store_true")
    parser.add_argument("--output-dir", type=Path, default=RESULTS_ROOT)
    args = parser.parse_args()

    run_rust = not (args.cpp_only or args.r_only)
    run_cpp  = not (args.rust_only or args.r_only)
    run_r    = not (args.rust_only or args.cpp_only)
    do_time  = not args.mem_only
    do_mem   = not args.time_only

    results_dir: Path = args.output_dir
    results_dir.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict[str, Any]] = []
    mem_rows: dict[tuple[str, str, int], int] = {}

    # rust
    if run_rust:
        for algo, crate_dir, largest_n in RUST_CRATES:
            if do_time:
                all_rows.extend(bench_rust_timing(algo, crate_dir))
            if do_mem:
                m = bench_rust_memory(algo, crate_dir, largest_n)
                if m:
                    mem_rows[(algo, "rust", largest_n)] = m["peak_bytes"]

    # c++
    if run_cpp:
        cpp_largest = {
            "kmp": 1_000_000,
            "smith_waterman": 5_000,
            "tree_traversal": 100_000,
        }
        for algo, cpp_dir in CPP_DIRS:
            if do_time:
                all_rows.extend(bench_cpp_timing(algo, cpp_dir, results_dir))
            if do_mem:
                m = bench_cpp_memory(algo, cpp_dir, cpp_largest[algo])
                if m:
                    mem_rows[(algo, "cpp", cpp_largest[algo])] = m["peak_bytes"]

    # r
    if run_r:
        for algo, r_dir in R_DIRS:
            rows = bench_r(algo, r_dir, results_dir)
            for row in rows:
                # R bench::mark already includes mem_alloc_bytes per row
                pb = row.pop("peak_bytes", None)
                all_rows.append(row)
                if pb is not None:
                    mem_rows[(row["algorithm"], "r", row["n"])] = pb

    # merge peak_bytes into timing rows
    for row in all_rows:
        key = (row["algorithm"], row["language"], row["n"])
        if row.get("peak_bytes") is None:
            row["peak_bytes"] = mem_rows.get(key)

    # write results
    if not all_rows:
        print("\nNo results collected - check for build errors above.")
        return

    df = pd.DataFrame(all_rows, columns=[
        "algorithm", "language", "n",
        "time_ns_median", "time_ns_ci_lo", "time_ns_ci_hi",
        "peak_bytes",
    ])
    df = df.sort_values(["algorithm", "language", "n"]).reset_index(drop=True)

    csv_out = results_dir / "results.csv"
    parquet_out = results_dir / "results.parquet"
    df.to_csv(csv_out, index=False)
    df.to_parquet(parquet_out, index=False)

    print(f"\nResults written to:\n  {csv_out}\n  {parquet_out}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
