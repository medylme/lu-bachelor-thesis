"""
parsers.py - pure parsing functions, no subprocess calls.

Each function returns a list of dicts with the schema:
    algorithm       str   e.g. "kmp"
    language        str   e.g. "rust"
    n               int   input size (bytes, bp, or tips depending on algo)
    time_ns_median  float median wall-clock time in nanoseconds
    time_ns_ci_lo   float lower bound of 95 % bootstrapped CI (ns)
    time_ns_ci_hi   float upper bound of 95 % bootstrapped CI (ns)
    peak_bytes      int | None  peak heap allocation in bytes (None if N/A)
"""

from __future__ import annotations

import csv
import json
import math
from io import StringIO
from pathlib import Path
from typing import Any


def _row(
    algorithm: str,
    language: str,
    n: int,
    time_ns_median: float,
    time_ns_ci_lo: float,
    time_ns_ci_hi: float,
    peak_bytes: int | None = None,
) -> dict[str, Any]:
    return {
        "algorithm": algorithm,
        "language": language,
        "n": n,
        "time_ns_median": time_ns_median,
        "time_ns_ci_lo": time_ns_ci_lo,
        "time_ns_ci_hi": time_ns_ci_hi,
        "peak_bytes": peak_bytes,
    }


def _parse_n_from_name(name: str) -> int | None:
    """Extract the trailing integer from a Criterion bench name like 'kmp/1000'."""
    parts = name.rsplit("/", 1)
    try:
        return int(parts[-1])
    except ValueError:
        return None


def parse_criterion_dir(crate_dir: Path, algorithm: str) -> list[dict[str, Any]]:
    """
    Walk target/criterion/<algo>/<n>/new/estimates.json and extract timing rows.

    Criterion stores one estimates.json per (bench group, parameter) pair.
    The directory layout is:
        <crate_dir>/target/criterion/<group>/<param>/new/estimates.json

    All point estimates and CI bounds are in nanoseconds.
    """
    results: list[dict[str, Any]] = []
    criterion_root = crate_dir / "target" / "criterion"
    if not criterion_root.exists():
        return results

    for estimates_path in criterion_root.rglob("*/new/estimates.json"):
        try:
            data = json.loads(estimates_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        # The parameter (input size) is the grandparent directory name.
        n = _parse_n_from_name(str(estimates_path.parent.parent))
        if n is None:
            continue

        median = data.get("median", {})
        ci = median.get("confidence_interval", {})
        results.append(
            _row(
                algorithm=algorithm,
                language="rust",
                n=n,
                time_ns_median=median.get("point_estimate", math.nan),
                time_ns_ci_lo=ci.get("lower_bound", math.nan),
                time_ns_ci_hi=ci.get("upper_bound", math.nan),
            )
        )
    return results


def parse_dhat_stdout(stdout: str, algorithm: str, language: str, n: int) -> dict[str, Any] | None:
    """
    Parse the single-line JSON emitted by examples/mem.rs or mem.cpp:
        {"peak_bytes": 12345}
    Returns a partial row dict (only peak_bytes filled in) or None on error.
    """
    try:
        data = json.loads(stdout.strip())
        return {"algorithm": algorithm, "language": language, "n": n,
                "peak_bytes": int(data["peak_bytes"])}
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


# two-tailed t critical values at α=0.05 for common repetition counts.
# scipy.stats.t.ppf(0.975, df) where df = repetitions - 1.
_T_CRIT: dict[int, float] = {
    5:  2.776,
    10: 2.262,
    20: 2.093,
    30: 2.045,
}
_T_CRIT_FALLBACK = 2.0  # large-sample approximation


def parse_google_benchmark(
    json_path: Path,
    algorithm: str,
    repetitions: int = 1,
) -> list[dict[str, Any]]:
    """
    Parse a --benchmark_out_format=json file produced by Google Benchmark.

    Single-run mode (repetitions=1, legacy):
        Each entry has run_type="iteration". We use real_time as the point
        estimate and set ci_lo = ci_hi = real_time (zero-width CI).

    Repeated-run mode (repetitions=K, --benchmark_report_aggregates_only=true):
        Each benchmark produces four aggregate entries with aggregate_name in
        {"mean", "median", "stddev", "cv"}. We use the median as the point
        estimate and compute a 95% t-interval on the mean:
            CI = mean ± t_{α/2, K-1} x stddev / sqrt(K)
        This matches the 95% bootstrapped CI that Criterion reports for Rust.
    """
    results: list[dict[str, Any]] = []
    if not json_path.exists():
        return results

    try:
        data = json.loads(json_path.read_text())
    except (json.JSONDecodeError, OSError):
        return results

    # Separate aggregate entries from plain iteration entries.
    # Key: base benchmark name (aggregate suffix stripped).
    aggregates: dict[str, dict[str, float]] = {}
    singles: list[dict] = []

    for entry in data.get("benchmarks", []):
        agg_name: str = entry.get("aggregate_name", "")
        raw_name: str = entry.get("name", "")
        if agg_name:
            suffix = f"_{agg_name}"
            base = raw_name[: -len(suffix)] if raw_name.endswith(suffix) else raw_name
            aggregates.setdefault(base, {})[agg_name] = entry.get("real_time", math.nan)
        else:
            singles.append(entry)

    if aggregates:
        t_crit = _T_CRIT.get(repetitions, _T_CRIT_FALLBACK)
        sqrt_k = math.sqrt(max(repetitions, 1))
        for base_name, agg in aggregates.items():
            n = _parse_n_from_name(base_name)
            if n is None:
                continue
            median = agg.get("median", math.nan)
            mean   = agg.get("mean",   math.nan)
            stddev = agg.get("stddev", math.nan)
            if not (math.isnan(mean) or math.isnan(stddev)):
                half_width = t_crit * stddev / sqrt_k
                ci_lo = mean - half_width
                ci_hi = mean + half_width
            else:
                ci_lo = ci_hi = median
            results.append(
                _row(
                    algorithm=algorithm,
                    language="cpp",
                    n=n,
                    time_ns_median=median,
                    time_ns_ci_lo=ci_lo,
                    time_ns_ci_hi=ci_hi,
                )
            )
    else:
        for entry in singles:
            n = _parse_n_from_name(entry.get("name", ""))
            if n is None:
                continue
            t = entry.get("real_time", math.nan)
            results.append(
                _row(
                    algorithm=algorithm,
                    language="cpp",
                    n=n,
                    time_ns_median=t,
                    time_ns_ci_lo=t,
                    time_ns_ci_hi=t,
                )
            )
    return results


def parse_bench_csv(csv_text: str) -> list[dict[str, Any]]:
    """
    Parse the CSV written to stdout by the R bench.R scripts.

    Expected columns (written by write.csv):
        algorithm, language, n, min_ns, median_ns,
        itr_per_sec, mem_alloc_bytes, n_gc

    bench_time values have already been converted to raw nanoseconds by
    as.numeric() in the R script; bench_bytes to bytes.
    """
    results: list[dict[str, Any]] = []
    reader = csv.DictReader(StringIO(csv_text))
    for row in reader:
        try:
            results.append(
                _row(
                    algorithm=row["algorithm"],
                    language=row["language"],
                    n=int(row["n"]),
                    time_ns_median=float(row["median_ns"]),
                    time_ns_ci_lo=float(row["min_ns"]),
                    time_ns_ci_hi=float(row["median_ns"]),
                    peak_bytes=int(float(row["mem_alloc_bytes"])),
                )
            )
        except (KeyError, ValueError):
            continue
    return results
