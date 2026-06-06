# Reproducing the benchmarks

## Prerequisites

**Pixi** manages the full software environment (R, Rust, Python, CMake, all packages). Install it once:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

**A C++ compiler** (GCC >= 12 or Clang >= 17) must also be installed at the system level, because the C++ benchmarks link against your system's standard library:

```bash
# Debian / Ubuntu / WSL2
sudo apt install build-essential
```

## Setup

```bash
# 1. install the pinned environment
pixi install

# 2. prepare benchmark input files (one-time)
pixi run python benchmarks/data/prepare_data.py

# 3. build all benchmarks
pixi run build

# 4. run all benchmarks
pixi run bench
```

Results are written to `results/results.csv`.

Individual targets:

| Command               | What it runs                   |
| --------------------- | ------------------------------ |
| `pixi run build`      | All Rust crates + C++ targets  |
| `pixi run bench`      | All languages, timing + memory |
| `pixi run bench-rust` | Rust only                      |
| `pixi run bench-cpp`  | C++ only                       |
| `pixi run bench-r`    | R only                         |
| `pixi run bench-mem`  | Memory measurements only       |
| `pixi run clean`      | Remove build artefacts         |

## System configuration checklist

Benchmark numbers are sensitive to what else the CPU is doing. These steps should help to reduce noise and make results comparable to the thesis numbers. Without them, run-to-run variation might be high enough to blur small differences. Note that besides this list, there are likely more platform-specific optimizations you can do.

**Before each benchmark session:**

- [ ] **Close background applications.** Obviously, background applications can generate CPU overhead at unpredictable intervals.

- [ ] **Disable CPU boost / turbo boost.** This ensures all benchmarks run at a static frequency. For most PCs this can be done in BIOS/UEFI (probably).

- [ ] **Disable hyperthreading (SMT).** SMT adds noise to timing. Disable in BIOS/UEFI as well.

- [ ] **Pin to a single CPU core.** Running on a fixed core avoids the OS migrating the process mid-benchmark:

  ```bash
  taskset -c 2 pixi run bench
  ```

## Output schema (`results/results.csv`)

| Column         | Type  | Description                                                   |
| -------------- | ----- | ------------------------------------------------------------- |
| algorithm      | str   | `kmp`, `smith_waterman`, `needleman_wunsch`, `tree_traversal` |
| language       | str   | `rust`, `cpp`, `r`                                            |
| n              | int   | input size (bytes for KMP; bp for SW/NW; tips for tree)       |
| time_ns_median | float | median wall-clock time, nanoseconds                           |
| time_ns_ci_lo  | float | lower CI bound (95%; methodology differs per harness)         |
| time_ns_ci_hi  | float | upper CI bound                                                |
| peak_bytes     | int   | peak heap allocation in bytes                                 |

The CI methodology differs between Criterion (Rust), Google Benchmark (C++), and bench (R).

## Manual setup (without pixi)

If pixi is not an option, the equivalent system requirements are:

| Dependency    | Minimum version | Notes                         |
| ------------- | --------------- | ----------------------------- |
| Linux x86-64  | -               | Only supported platform       |
| Rust (rustup) | stable >= 1.86  | Criterion + dhat              |
| GCC or Clang  | >= 12 / >= 17   | C++20 required for KMP/SeqAn3 |
| CMake         | >= 3.20         | C++ build system              |
| R             | >= 4.4          | bench harness + Bioconductor  |
| Python        | >= 3.10         | orchestrator                  |

R packages:

```r
install.packages(c("ape", "bench"))
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")
BiocManager::install(c("Biostrings", "pwalign"))
```

Python dependencies:

```bash
pip install pandas pyarrow
```

Build and run:

```bash
make build && make bench
```

## Results

After running, `results/results.csv` contains one row per (algorithm, language, input size) triple with median wall-clock time, 95% confidence interval bounds, and peak heap allocation.
