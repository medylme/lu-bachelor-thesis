// measures peak heap allocation of sw_align_default at n=5_000.
// prints {"peak_bytes": <N>} to stdout.

#[global_allocator]
static ALLOC: dhat::Alloc = dhat::Alloc;

use std::hint::black_box;
use std::path::Path;

fn data_path(file: &str) -> std::path::PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../data/prepared")
        .join(file)
}

fn main() {
    let seq_a = std::fs::read(data_path("seq_pair_a.txt"))
        .expect("seq_pair_a.txt not found - run benchmarks/data/prepare_data.py first");
    let seq_b = std::fs::read(data_path("seq_pair_b.txt"))
        .expect("seq_pair_b.txt not found - run benchmarks/data/prepare_data.py first");

    let _profiler = dhat::Profiler::builder().testing().build();

    black_box(smith_waterman::sw_align_default(black_box(&seq_a), black_box(&seq_b)));

    let stats = dhat::HeapStats::get();
    println!("{{\"peak_bytes\": {}}}", stats.max_bytes);
}
