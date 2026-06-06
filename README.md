# Rust vs C++ vs R in Bioinformatics

Benchmark suite serving as an appendix to my bachelor thesis at Leiden University. It compares the performance of four bioinformatics algorithms across existing Rust, C++, and R implementations. This repository contains all related benchmark code, datasets and scripts.

## Repository structure

```
benchmarks/
  kmp/              KMP exact pattern matching   (Rust + C++)
  smith_waterman/   Smith-Waterman alignment     (Rust + C++)
  needleman_wunsch/ Needleman-Wunsch alignment   (Rust + R)
  tree_traversal/   Phylogenetic tree traversal  (Rust + C++ + R)
  common/cpp/       Shared C++ memory-tracking header
  data/             Prepared inputs and raw source files
orchestrator/       Python scripts that run all benchmarks and collect results
scripts/            Figure generation and data preparation scripts
results/            Written here after running benchmarks
pixi.toml           Reproducible environment (R, Rust, Python, build tools)
pixi.lock           Pinned package versions
```

## Algorithms and input sizes

| Algorithm        | Languages    | Input sizes             |
| ---------------- | ------------ | ----------------------- |
| KMP              | Rust, C++    | 1k, 10k, 100k, 1M bytes |
| Smith-Waterman   | Rust, C++    | 100, 500, 1k, 5k bp     |
| Needleman-Wunsch | Rust, R      | 100, 500, 1k, 5k bp     |
| Tree traversal   | Rust, C++, R | 100, 1k, 10k, 100k tips |

All languages use the same input files derived from real biological data: the _E. coli_ K-12 MG1655 genome (NCBI NC_000913.3) and the Open Tree of Life synthetic supertree v16.1.

## Reproducing the benchmarks yourself

See [BENCHMARKING.md](BENCHMARKING.md) for setup instructions and a system configuration checklist.

---

**Bachelor Thesis** | Leiden University | 2026
